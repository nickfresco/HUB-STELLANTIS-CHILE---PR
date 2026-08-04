"""
Verifica la propiedad más importante del pipeline: que cada etapa se
pueda reemplazar por una implementación distinta sin tocar las demás
etapas ni el orquestador — condición explícitamente pedida para el
Sprint 3.
"""

from pathlib import Path
from typing import Any, Dict

from knowledge_base.loader import KnowledgeBase
from pipeline.factory import build_default_pipeline
from pipeline.pipeline import PRHubPipeline
from pipeline.stages import (
    DailyBriefGeneratorStage,
    EventDetectionStage,
    PriorityRuleEngineStage,
    RecommendationEngineStage,
)
from rule_engine.engine import RuleEngine
from rule_engine.registry import RuleRegistry

BASE_DIR = Path(__file__).parent.parent
KB_PATH = BASE_DIR / "config" / "knowledge_base"


class FakeEntityRecognitionStage:
    """Etapa de reemplazo: en vez de matching por Knowledge Base, fuerza
    una marca fija — simula un futuro componente NLP más avanzado."""

    def __init__(self, forced_brand: str):
        self.forced_brand = forced_brand

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from classification.entity_recognition import DetectedEntities
        context["entities"] = DetectedEntities(brands=[self.forced_brand])
        return context


def test_entity_recognition_stage_is_swappable():
    kb = KnowledgeBase(KB_PATH)
    priority_registry = RuleRegistry.from_yaml(
        BASE_DIR / "config" / "rules" / "priority_rules.yml", rules_key="priority_rules"
    )
    recommendation_registry = RuleRegistry.from_yaml(
        BASE_DIR / "config" / "rules" / "recommendation_rules.yml", rules_key="recommendation_rules"
    )

    pipeline = PRHubPipeline(
        kb,
        stages=[
            FakeEntityRecognitionStage(forced_brand="brand.peugeot"),  # etapa reemplazada
            EventDetectionStage(kb),
            PriorityRuleEngineStage(RuleEngine(priority_registry)),
            RecommendationEngineStage(RuleEngine(recommendation_registry)),
            DailyBriefGeneratorStage(kb),
        ],
    )

    # Texto sin ninguna marca detectable por keyword, pero la etapa
    # falsa fuerza "brand.peugeot" de todos modos.
    brief = pipeline.run({
        "title": "Un titular genérico sin marcas mencionadas",
        "summary": "",
        "source_id": "source.emol",
        "event_type": "Lanzamiento",
    })
    assert "Peugeot" in brief["brand"]
    assert "PR-004" in brief["rules_triggered"]["priority_rules"]  # la regla igual se dispara


def test_default_pipeline_builds_five_stages_in_order():
    pipeline = build_default_pipeline(BASE_DIR)
    stage_names = [type(s).__name__ for s in pipeline.stages]
    assert stage_names == [
        "EntityRecognitionStage",
        "EventDetectionStage",
        "PriorityRuleEngineStage",
        "RecommendationEngineStage",
        "DailyBriefGeneratorStage",
    ]
