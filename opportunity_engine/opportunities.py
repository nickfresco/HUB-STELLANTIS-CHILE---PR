"""
Opportunity Engine v1.0 — genera oportunidades estratégicas de PR a
partir de una Story ya clasificada, usando el mismo Rule Engine
genérico y determinístico que Priority y Recommendation Engine
(rule_engine/), sin modificar ni un archivo de ese paquete.

No es un motor nuevo — es un consumidor nuevo del motor existente. La
única pieza propia de este módulo es:

  1. `extend_fact_with_classification()` — el Fact que evalúan Priority
     y Recommendation Engine no incluye su propio resultado (no puede,
     todavía no existía cuando se construyó). Opportunity Engine corre
     DESPUÉS de ambos, así que puede enriquecer ese mismo Fact con
     `priority` y `recommendations` ya resueltos antes de evaluarlo —
     esto es lo que permite, a futuro, escribir una regla de
     oportunidad que dependa de la prioridad ya asignada (v1.0 no trae
     ninguna regla así todavía, pero el campo queda disponible).

  2. `compute_opportunities()` — traduce cada coincidencia cruda del
     motor (`EvaluationResult.matches`, ya expuesto desde el Sprint 3
     para fines de auditoría) en un objeto Opportunity completo
     (tipo, prioridad, score, justificación, acción recomendada). No
     usa la estrategia de fusión `accumulate_all` del motor (que solo
     fusiona un campo de outcome en una lista plana) — lee los matches
     directamente porque cada Opportunity necesita conservar sus
     propios cuatro campos por separado, no solo un valor fusionado.

Sin aprendizaje automático, sin generación de texto libre: la
`justificacion` de cada oportunidad es la `description` ya escrita a
mano en config/opportunity_rules.yaml para esa regla — mismo patrón ya
usado para `why_it_matters` en brief/generator.py.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from rule_engine.engine import RuleEngine
from rule_engine.registry import RuleRegistry


@dataclass(frozen=True)
class Opportunity:
    rule_id: str
    type: str
    priority: str
    score: int
    justification: Optional[str]
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "type": self.type,
            "priority": self.priority,
            "score": self.score,
            "justification": self.justification,
            "recommended_action": self.recommended_action,
        }


def extend_fact_with_classification(
    fact: Dict[str, Any],
    priority: Optional[str],
    recommendations: List[str],
) -> Dict[str, Any]:
    """Devuelve un Fact nuevo (no muta el original) con dos campos
    adicionales disponibles para las condiciones de Opportunity Engine:
    `priority` y `recommendations`, ya resueltos por las etapas
    anteriores del pipeline."""
    extended = dict(fact)
    extended["priority"] = priority
    extended["recommendations"] = recommendations
    return extended


def compute_opportunities(
    fact: Dict[str, Any],
    fact_reference: str,
    engine: RuleEngine,
    registry: RuleRegistry,
) -> List[Opportunity]:
    """Evalúa el Fact contra el Rulebook de oportunidades y devuelve
    una Opportunity por cada regla que coincidió — nunca solo la de
    mayor score, todas quedan (una Story puede tener varias
    oportunidades simultáneas, a diferencia de PriorityLevel que es
    un único valor)."""
    result = engine.evaluate(
        fact=fact,
        fact_reference=fact_reference,
        resolution_strategy="accumulate_all",
        outcome_field="opportunity_type",
    )

    opportunities: List[Opportunity] = []
    for match in result.matches:
        rule = registry.get_rule(match.rule_id)
        opportunities.append(
            Opportunity(
                rule_id=match.rule_id,
                type=match.outcome.get("opportunity_type", ""),
                priority=match.outcome.get("priority", ""),
                score=match.outcome.get("score", 0),
                justification=rule.description if rule else None,
                recommended_action=match.outcome.get("recommended_action", ""),
            )
        )

    # Mayor score primero — es la señal de "qué tan fuerte es",
    # relevante para decidir qué mostrar primero en el Daily Brief.
    opportunities.sort(key=lambda o: o.score, reverse=True)
    return opportunities
