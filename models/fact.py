"""
Fact — el objeto que se evalúa contra el Rule Engine.

Es una versión simplificada del modelo Story de la Parte 2B: incluye
solo los campos que el Rulebook v0.2 realmente usa en sus condiciones.
No implementa Story completa (no hay StoryState, no hay
deduplicación entre noticias — eso es deuda técnica declarada del MVP,
ver README).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NewsInput:
    """Tal como llega en el JSON de entrada (noticia.json).

    event_type ahora es OPCIONAL (Sprint 3): si no viene informado, la
    etapa EventDetectionStage del pipeline lo infiere de forma
    determinística (ver classification/event_detection.py)."""
    title: str
    summary: str
    source_id: str
    event_type: Optional[str] = None
    published_at: Optional[str] = None
    # TODO (deuda técnica, Story.market — Riesgo B de la revisión del
    # Rulebook v0.1): proxy explícito mientras no se resuelve el mapeo
    # formal de "mercado" en el modelo de dominio.
    market_impact: List[str] = field(default_factory=list)
    # TODO (deuda técnica, PR-003): placeholder manual mientras no
    # exista Sentiment Analysis real. Las reglas que dependen de esto
    # quedan PENDING (enabled: false) independientemente de este campo.
    tone: Optional[str] = None

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "NewsInput":
        return NewsInput(
            title=data["title"],
            summary=data.get("summary", ""),
            source_id=data["source_id"],
            event_type=data.get("event_type"),
            published_at=data.get("published_at"),
            market_impact=data.get("market_impact", []),
            tone=data.get("tone"),
        )
