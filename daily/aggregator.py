"""
Daily Aggregator — toma la lista de briefs ya generados por el
pipeline (uno por noticia) y los agrupa en la estructura que necesita
el Daily HTML. No vuelve a evaluar ninguna regla de negocio: solo
reorganiza resultados que el Rule Engine ya calculó.

Reglas de agrupación (decisiones de presentación, no de negocio):

  - Flash Alerts: toda noticia con priority en {HIGH, CRITICAL}.
  - Stellantis / Competencia / Industria: el resto de las noticias
    (para no repetir el mismo titular dos veces en el correo). Una
    noticia va a Stellantis si tiene al menos una marca del grupo; si
    no, a Competencia si tiene al menos un competidor; si no tiene
    ninguna de las dos, a Industria.
  - Oportunidades PR: una entrada por cada RecommendationAction
    "accionable" (ver daily/labels.py) de CUALQUIER noticia del día,
    incluyendo las que ya aparecen en Flash Alerts — a diferencia de
    las secciones anteriores, aquí sí puede repetirse el origen,
    porque la sección responde una pregunta distinta ("qué hacer"),
    no "qué pasó".
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from daily.labels import OPPORTUNITY_ACTIONS, action_label, benchmark_text, industry_text

HIGH_PRIORITY_VALUES = {"HIGH", "CRITICAL", "High", "Critical"}

STELLANTIS_BRAND_ORDER = [
    "Peugeot", "Citroën", "Opel", "DS Automobiles", "Fiat", "Jeep", "RAM", "Leapmotor",
]


def _is_flash_alert(brief: Dict[str, Any]) -> bool:
    return brief.get("priority") in HIGH_PRIORITY_VALUES


def build_digest(briefs: List[Dict[str, Any]], meta: Dict[str, Any]) -> Dict[str, Any]:
    flash_alerts = [b for b in briefs if _is_flash_alert(b)]
    remaining = [b for b in briefs if not _is_flash_alert(b)]

    stellantis_by_brand: Dict[str, List[Dict[str, Any]]] = {}
    competencia_by_brand: Dict[str, List[Dict[str, Any]]] = {}
    industria: List[Dict[str, Any]] = []

    for brief in remaining:
        if brief.get("brand"):
            for brand in brief["brand"]:
                stellantis_by_brand.setdefault(brand, []).append(brief)
        elif brief.get("competitors"):
            for competitor in brief["competitors"]:
                competencia_by_brand.setdefault(competitor, []).append(brief)
        else:
            industria.append(brief)

    # Ordenar las marcas Stellantis en un orden fijo y predecible (no
    # alfabético "porque sí" — es el mismo orden ya usado en toda la
    # especificación del proyecto, Parte 2A en adelante).
    stellantis_ordered = [
        (brand, stellantis_by_brand[brand])
        for brand in STELLANTIS_BRAND_ORDER
        if brand in stellantis_by_brand
    ]
    # Cualquier marca que no esté en el orden fijo (no debería ocurrir,
    # pero no se pierde silenciosamente si pasa) se agrega al final.
    for brand, items in stellantis_by_brand.items():
        if brand not in STELLANTIS_BRAND_ORDER:
            stellantis_ordered.append((brand, items))

    competencia_ordered = sorted(competencia_by_brand.items(), key=lambda kv: kv[0])

    # Comentario de benchmark por noticia de competencia (plantilla
    # determinística por event_type, ver daily/labels.py).
    competencia_with_commentary = [
        (
            brand,
            [
                {**brief, "benchmark_commentary": benchmark_text(brief.get("event_type"))}
                for brief in items
            ],
        )
        for brand, items in competencia_ordered
    ]

    industria_with_commentary = [
        {**brief, "industry_commentary": industry_text(brief.get("event_type"))}
        for brief in industria
    ]

    opportunities = _build_opportunities(briefs)

    return {
        "meta": meta,
        "resumen_ejecutivo": _build_resumen_ejecutivo(flash_alerts, opportunities, meta),
        "flash_alerts": flash_alerts,
        "stellantis": stellantis_ordered,
        "competencia": competencia_with_commentary,
        "industria": industria_with_commentary,
        "oportunidades": opportunities,
        "counts": {
            "flash_alerts": len(flash_alerts),
            "stellantis": sum(len(v) for _, v in stellantis_ordered),
            "competencia": sum(len(v) for _, v in competencia_ordered),
            "industria": len(industria),
            "oportunidades": len(opportunities),
        },
    }


def _build_opportunities(briefs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    opportunities = []
    for brief in briefs:
        for action in brief.get("recommendations", []):
            if action in OPPORTUNITY_ACTIONS:
                opportunities.append({
                    "action": action,
                    "action_label": action_label(action),
                    "story": brief["story"],
                    "brand": (brief.get("brand") or brief.get("competitors") or ["—"])[0],
                    "priority": brief.get("priority"),
                })
    return opportunities


def _build_resumen_ejecutivo(
    flash_alerts: List[Dict[str, Any]],
    opportunities: List[Dict[str, Any]],
    meta: Dict[str, Any],
) -> List[str]:
    """Máximo 3 bullets, generados por plantilla (no IA), respondiendo
    exactamente qué pasó / qué requiere atención / qué oportunidades
    existen, tal como pide el brief del Sprint 4."""
    bullets: List[str] = []

    # 1. ¿Qué pasó?
    bullets.append(
        f"Se procesaron {meta['noticias_procesadas']} noticias hoy "
        f"({len(flash_alerts)} de prioridad alta)."
    )

    # 2. ¿Qué requiere atención?
    if flash_alerts:
        top = flash_alerts[0]
        brand_txt = ", ".join(top.get("brand") or top.get("competitors") or []) or "industria"
        bullets.append(f"Atención hoy: \"{top['story']}\" ({brand_txt}).")
    else:
        bullets.append("Sin alertas de prioridad alta hoy — jornada de monitoreo estándar.")

    # 3. ¿Qué oportunidades existen?
    if opportunities:
        bullets.append(
            f"Se identificaron {len(opportunities)} oportunidades de PR accionables para hoy."
        )
    else:
        bullets.append("No se identificaron oportunidades de PR accionables hoy.")

    return bullets[:3]
