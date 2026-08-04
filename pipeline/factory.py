"""
Factory del pipeline estándar del MVP. Aislar el ensamblado aquí
permite que main.py y los tests construyan el mismo pipeline sin
duplicar las rutas de configuración ni el orden de las etapas.
"""

from __future__ import annotations
from pathlib import Path

from knowledge_base.loader import KnowledgeBase
from pipeline.pipeline import PRHubPipeline
from pipeline.stages import (
    DailyBriefGeneratorStage,
    EntityRecognitionStage,
    EventDetectionStage,
    PriorityRuleEngineStage,
    RecommendationEngineStage,
)
from rule_engine.engine import RuleEngine
from rule_engine.registry import RuleRegistry


def build_default_pipeline(base_dir: Path) -> PRHubPipeline:
    kb = KnowledgeBase(base_dir / "config" / "knowledge_base")

    priority_registry = RuleRegistry.from_yaml(
        base_dir / "config" / "rules" / "priority_rules.yml", rules_key="priority_rules"
    )
    recommendation_registry = RuleRegistry.from_yaml(
        base_dir / "config" / "rules" / "recommendation_rules.yml", rules_key="recommendation_rules"
    )

    stages = [
        EntityRecognitionStage(kb),
        EventDetectionStage(kb),
        PriorityRuleEngineStage(RuleEngine(priority_registry)),
        RecommendationEngineStage(RuleEngine(recommendation_registry)),
        DailyBriefGeneratorStage(kb, priority_registry),
    ]
    return PRHubPipeline(kb, stages)
