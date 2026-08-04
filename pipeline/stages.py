"""
Etapas del pipeline (Sprint 3):

    Input JSON -> Entity Recognition -> Event Detection ->
    Priority Rule Engine -> Recommendation Engine ->
    Daily Brief Generator -> Output JSON

Cada etapa es una clase con un único método run(context) -> context.
Cada una lee y escribe SOLO las claves del contexto que le
corresponden — esto es lo que permite reemplazar cualquier etapa en
el futuro (p. ej. Entity Recognition por un componente NLP más
avanzado, o Event Detection por un Taxonomy Engine real) sin modificar
las demás, conforme a lo acordado.
"""

from __future__ import annotations
from typing import Any, Dict

from brief.generator import build_daily_brief
from classification.entity_recognition import detect_entities
from classification.event_detection import infer_event_type
from knowledge_base.loader import KnowledgeBase
from rule_engine.engine import RuleEngine


class EntityRecognitionStage:
    """Lee:  context['text']
    Escribe: context['entities']"""

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context["entities"] = detect_entities(context["text"], self.kb)
        return context


class EventDetectionStage:
    """Lee:  context['news'], context['text']
    Escribe: context['event_type'], context['event_type_source']

    Si NewsInput.event_type viene informado, se valida contra el
    catálogo (event_types.yml) y se usa tal cual. Si no viene, se
    infiere de forma determinística por palabras clave — nunca con IA.
    """

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        news = context["news"]

        if news.event_type:
            if not self.kb.is_valid_event_type(news.event_type):
                raise ValueError(
                    f"event_type '{news.event_type}' no existe en event_types.yml."
                )
            context["event_type"] = news.event_type
            context["event_type_source"] = "explicit"
        else:
            inferred = infer_event_type(context["text"], self.kb)
            context["event_type"] = inferred
            context["event_type_source"] = "inferred" if inferred else "undetected"

        return context


class PriorityRuleEngineStage:
    """Lee:  context['entities'], context['event_type'], context['news'], context['source']
    Escribe: context['fact'], context['priority_result']"""

    def __init__(self, engine: RuleEngine):
        self.engine = engine

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context["fact"] = _assemble_fact(context)
        context["priority_result"] = self.engine.evaluate(
            fact=context["fact"],
            fact_reference=context["news"].title,
            resolution_strategy="single_winner",
            outcome_field="priority",
        )
        return context


class RecommendationEngineStage:
    """Lee:  context['fact']
    Escribe: context['recommendation_result']"""

    def __init__(self, engine: RuleEngine):
        self.engine = engine

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context["recommendation_result"] = self.engine.evaluate(
            fact=context["fact"],
            fact_reference=context["news"].title,
            resolution_strategy="accumulate_all",
            outcome_field="recommendations",
        )
        return context


class DailyBriefGeneratorStage:
    """Lee:  todo el contexto acumulado por las etapas anteriores
    Escribe: context['output'] (el JSON final del Daily Brief)"""

    def __init__(self, kb: KnowledgeBase, priority_registry=None):
        self.kb = kb
        self.priority_registry = priority_registry

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context["output"] = build_daily_brief(context, self.kb, self.priority_registry)
        return context


def _assemble_fact(context: Dict[str, Any]) -> Dict[str, Any]:
    """Ensambla el Fact plano que consume el Rule Engine a partir de lo
    que ya produjeron Entity Recognition y Event Detection. Es una
    función pura (sin I/O), separada para que sea trivial de testear."""
    entities = context["entities"]
    news = context["news"]
    source = context["source"]
    return {
        "brands": entities.brands,
        "competitors": entities.competitors,
        "organizations": entities.organizations,
        "products": entities.products,
        "event_type": context["event_type"],
        "market_impact": news.market_impact,
        "tone": news.tone,
        "source_country": source.country,
        "source_tier": source.tier,
    }
