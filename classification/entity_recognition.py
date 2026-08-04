"""
Entity Recognition — detección determinística de Brand, Competitor,
Organization y Product en el texto de una noticia, por coincidencia
contra canonicalId / displayName / aliases de la Knowledge Base.

Corresponde a: Parte 2B, secciones 3.3 y 4.4 (incluye
disambiguationContext para alias ambiguos). Ningún componente de este
módulo usa IA ni NLP probabilístico — es matching de texto puro,
consistente con ADR-001 (determinismo).

NOTA (deuda técnica): esto NO implementa el Taxonomy Engine completo.
Solo resuelve "qué entidades se mencionan", no "qué EventType/Category
corresponde". El event_type se toma directo del input (ver
models/fact.py) hasta que el Taxonomy Engine se implemente.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List

from knowledge_base.loader import Entity, KnowledgeBase


@dataclass
class DetectedEntities:
    brands: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)


def _contains_word(text_lower: str, value_lower: str) -> bool:
    """Coincidencia por palabra completa, no por subcadena.

    Bug real encontrado al procesar noticias reales (Sprint 5, modo de
    entrenamiento): el chequeo anterior (`value_lower in text_lower`)
    hacía match de "ds" dentro de "Ads" (como en "premios Ads People
    Like") y de "auto" dentro de "automotriz", generando una detección
    falsa de la marca DS Automobiles en una noticia que no la mencionaba
    en absoluto. \\b exige límite de palabra a ambos lados.
    """
    pattern = r"\b" + re.escape(value_lower) + r"\b"
    return re.search(pattern, text_lower) is not None


def _matches_entity(text_lower: str, entity: Entity) -> bool:
    if not entity.active:
        return False

    # Mapa texto_candidato(lower) -> contexto requerido (o None si no
    # aplica). Se construye primero desde 'aliases', de modo que si el
    # displayName coincide textualmente con un alias que sí tiene
    # disambiguationContext, ese requisito prevalezca — evita que el
    # mismo texto quede "sin contexto" solo por venir de displayName
    # (bug corregido en el Sprint 4: antes, displayName == alias.value
    # se evaluaba como dos candidatos independientes y el primero, sin
    # contexto, producía un falso positivo).
    value_context: dict = {}
    for alias_entry in entity.aliases:
        if isinstance(alias_entry, dict):
            value = alias_entry["value"]
            context_words = alias_entry.get("disambiguationContext")
        else:
            value = alias_entry
            context_words = None
        value_context.setdefault(value.lower(), context_words)

    value_context.setdefault(entity.display_name.lower(), None)

    for value_lower, context_words in value_context.items():
        if not _contains_word(text_lower, value_lower):
            continue

        if context_words:
            if any(_contains_word(text_lower, cw.lower()) for cw in context_words):
                return True
            # El texto candidato apareció pero ninguna palabra de
            # contexto requerido está presente -> no se confirma la
            # coincidencia (evita falsos positivos, Parte 2B sección 4.4).
            continue

        return True

    return False


def detect_entities(text: str, kb: KnowledgeBase) -> DetectedEntities:
    text_lower = text.lower()

    return DetectedEntities(
        brands=[e.canonical_id for e in kb.brands if _matches_entity(text_lower, e)],
        competitors=[e.canonical_id for e in kb.competitors if _matches_entity(text_lower, e)],
        organizations=[e.canonical_id for e in kb.organizations if _matches_entity(text_lower, e)],
        products=[e.canonical_id for e in kb.all_products() if _matches_entity(text_lower, e)],
    )
