"""
Daily Brief Generator — última etapa del pipeline. Ensambla el JSON de
salida a partir de todo lo que las etapas anteriores dejaron en el
contexto (entidades detectadas, event_type, resultados de Priority y
Recommendation Engine).

No genera las 10 secciones completas del Daily Brief de la Parte 3
(eso requiere agregación de varias Stories, no de una sola noticia) —
asigna una única sección por noticia como aproximación del MVP,
documentada como TODO en models/enums.py.

Sprint 4: se agregaron campos aditivos (competitors, organizations,
source, why_it_matters) requeridos por el Daily HTML — no cambia
ningún campo ni comportamiento ya existente, solo agrega información
adicional al mismo diccionario de salida.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

REPUTATIONAL_EVENT_TYPES = {"Recall", "DenunciaOControversia", "ResultadoDeSeguridad"}


def assign_section(priority: Optional[str], event_type: Optional[str]) -> str:
    """Mapeo simplificado prioridad/tipo -> sección del Daily Brief.
    TODO (Parte 3): reemplazar por las reglas completas de selección
    de contenido de las 10 secciones, que operan sobre el conjunto de
    Stories del día, no sobre una noticia aislada."""
    if event_type in REPUTATIONAL_EVENT_TYPES:
        return "Riesgos reputacionales"
    if priority in ("Critical", "High", "CRITICAL", "HIGH"):
        return "Resumen Ejecutivo"
    return "Radar de noticias"


def build_reasoning(priority_result, recommendation_result) -> str:
    """Redacción basada en plantilla (NO generativa/IA), trazable 1:1 a
    las reglas que se activaron — aplicación mínima, para el MVP, del
    principio de trazabilidad total (Parte 3, sección 3)."""
    parts: List[str] = []

    if priority_result.winning_rule_id:
        other_matches = [m for m in priority_result.matched_rule_ids() if m != priority_result.winning_rule_id]
        parts.append(
            f"Prioridad '{priority_result.final_outcome['priority']}' asignada por la regla "
            f"{priority_result.winning_rule_id}"
            + (f" (compitió con: {', '.join(other_matches)})" if other_matches else "")
            + "."
        )
    else:
        parts.append("Ninguna regla de prioridad coincidió; sin PriorityLevel asignado (sin fallback definido en este MVP).")

    if recommendation_result.matches:
        parts.append(f"Recomendaciones derivadas de: {', '.join(recommendation_result.matched_rule_ids())}.")
    else:
        parts.append("Ninguna regla de recomendación coincidió.")

    return " ".join(parts)


def _display_name(canonical_id: str, entities) -> str:
    for e in entities:
        if e.canonical_id == canonical_id:
            return e.display_name
    return canonical_id


def _why_it_matters(priority_result, priority_registry) -> Optional[str]:
    """Usa la descripción ya existente de la regla ganadora (Rule.description,
    definida en priority_rules.yml) como explicación de 'por qué importa'.
    No es texto generativo — es la descripción de negocio que ya estaba
    en el YAML, simplemente expuesta en el output."""
    if not priority_result.winning_rule_id or priority_registry is None:
        return None
    rule = priority_registry.get_rule(priority_result.winning_rule_id)
    return rule.description if rule else None


def build_daily_brief(context: Dict[str, Any], kb, priority_registry=None) -> Dict[str, Any]:
    news = context["news"]
    entities = context["entities"]
    event_type = context["event_type"]
    priority_result = context["priority_result"]
    recommendation_result = context["recommendation_result"]

    priority = priority_result.final_outcome["priority"] if priority_result.final_outcome else None
    recommendations = (
        recommendation_result.final_outcome["recommendations"]
        if recommendation_result.final_outcome
        else []
    )
    brand_names = [_display_name(bid, kb.brands) for bid in entities.brands]
    competitor_names = [_display_name(cid, kb.competitors) for cid in entities.competitors]
    organization_names = [_display_name(oid, kb.organizations) for oid in entities.organizations]

    source = context["source"]

    return {
        "story": news.title,
        "brand": brand_names,
        "competitors": competitor_names,
        "organizations": organization_names,
        "event_type": event_type,
        "event_type_source": context.get("event_type_source"),
        "priority": priority,
        "section": assign_section(priority, event_type),
        "recommendations": recommendations,
        "why_it_matters": _why_it_matters(priority_result, priority_registry),
        "source": {"name": source.display_name, "tier": source.tier},
        "rules_triggered": {
            "priority_rules": priority_result.matched_rule_ids(),
            "recommendation_rules": recommendation_result.matched_rule_ids(),
        },
        "summary": f"{news.title}. {news.summary}".strip(),
        "reasoning": build_reasoning(priority_result, recommendation_result),
        "audit": {
            "priority_rulebook_version": priority_result.rulebook_version,
            "recommendation_rulebook_version": recommendation_result.rulebook_version,
        },
    }
