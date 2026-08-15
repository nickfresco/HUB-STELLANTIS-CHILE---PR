"""
Event Detection — inferencia determinística de EventType a partir de
palabras clave, usada únicamente cuando `event_type` no viene informado
en el input.

Sin IA, sin NLP probabilístico: un diccionario de keywords por
EventType (heurística documentada, no una regla de negocio del
Rulebook — es infraestructura de clasificación, análoga a un Taxonomy
Engine mínimo), cargado desde config/knowledge_base/event_type_keywords.yml
junto con el resto de la Knowledge Base. Si ninguna keyword coincide,
devuelve None de forma explícita en vez de adivinar — es
responsabilidad del llamador decidir qué hacer ante un event_type no
determinado (hoy: la noticia simplemente no dispara ninguna regla que
dependa de event_type).

Nota (deuda técnica): esto sigue siendo una heurística de MVP, no un
Taxonomy Engine real (Parte 2A) — no hay aliases, pesos ni soporte
multi-idioma. Esa discusión de arquitectura más amplia sigue postergada;
lo único resuelto aquí es que las keywords ya no están hardcodeadas en
Python (ver event_type_keywords.yml).
"""

from __future__ import annotations
from typing import Optional

from knowledge_base.loader import KnowledgeBase


def infer_event_type(text: str, kb: KnowledgeBase) -> Optional[str]:
    """Devuelve el EventType con más keywords coincidentes en el texto,
    o None si ninguno coincide. Determinístico: mismo texto -> mismo
    resultado siempre. El orden de desempate cuando dos EventType
    empatan en cantidad de keywords lo define el orden de las entradas
    en event_type_keywords.yml (gana la primera)."""
    text_lower = text.lower()
    best_event_type: Optional[str] = None
    best_count = 0

    for event_type in kb.event_types:
        keywords = kb.event_type_keywords.get(event_type, [])
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_event_type = event_type

    return best_event_type
