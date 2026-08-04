"""
Rule Engine — evalúa TODAS las reglas activas de un Registry contra un
Fact (nunca se detiene en la primera coincidencia, por auditabilidad),
y resuelve el resultado final según la estrategia indicada por quien
invoca el motor.

Estrategias:
    single_winner   -> un único resultado; gana la de mayor
                       priority_weight; empate resuelto por id de regla
                       (orden lexicográfico ascendente) para que el
                       resultado sea siempre reproducible.
    accumulate_all  -> todos los resultados se acumulan; los valores de
                       salida se deduplican, pero el Audit Trail
                       conserva cada coincidencia por separado.

El motor no sabe qué estrategia "corresponde" a qué tipo de regla de
negocio — eso lo decide quien lo invoca (ver knowledge_base y los
motores de Priority/Recommendation en brief/generator.py).
"""

from __future__ import annotations
from typing import Any, Dict, List

from rule_engine.condition import evaluate_condition
from rule_engine.registry import RuleRegistry
from rule_engine.rules import EvaluationResult, Match

VALID_STRATEGIES = {"single_winner", "accumulate_all"}


class RuleEngine:
    def __init__(self, registry: RuleRegistry):
        self.registry = registry

    def evaluate(
        self,
        fact: Dict[str, Any],
        fact_reference: str,
        resolution_strategy: str,
        outcome_field: str,
    ) -> EvaluationResult:
        """Evalúa el Fact contra todas las reglas activas.

        Args:
            fact: el diccionario de campo->valor a evaluar.
            fact_reference: identificador del Fact, para el Audit Trail.
            resolution_strategy: "single_winner" o "accumulate_all".
            outcome_field: qué clave del `outcome` de cada regla se
                acumula/gana (ej. "priority" o "recommendations"). El
                motor no conoce estos nombres de antemano.
        """
        if resolution_strategy not in VALID_STRATEGIES:
            raise ValueError(f"Estrategia de resolución no soportada: {resolution_strategy!r}")

        matches: List[Match] = []
        for rule in self.registry.enabled_rules():
            if evaluate_condition(rule.condition, fact):
                matches.append(
                    Match(rule_id=rule.id, outcome=rule.outcome, priority_weight=rule.priority_weight)
                )

        result = EvaluationResult(
            fact_reference=fact_reference,
            rulebook_version=self.registry.version,
            resolution_strategy=resolution_strategy,
        )
        result.matches = matches

        if not matches:
            result.final_outcome = None
            return result

        if resolution_strategy == "single_winner":
            # Desempate determinista: mayor priority_weight; en empate,
            # el id de regla más bajo en orden lexicográfico gana,
            # siempre de forma reproducible.
            top_weight = max(m.priority_weight for m in matches)
            tied = sorted([m for m in matches if m.priority_weight == top_weight], key=lambda m: m.rule_id)
            winner = tied[0]
            result.winning_rule_id = winner.rule_id
            result.final_outcome = winner.outcome

        else:  # accumulate_all
            accumulated: List[Any] = []
            for m in matches:
                values = m.outcome.get(outcome_field, [])
                if not isinstance(values, list):
                    values = [values]
                for v in values:
                    if v not in accumulated:
                        accumulated.append(v)
            result.final_outcome = {outcome_field: accumulated}

        return result
