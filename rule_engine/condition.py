"""
Evaluador de condiciones del Rule Engine.

Completamente agnóstico de dominio: no conoce "Stellantis", "Recall" ni
ningún concepto de negocio. Solo sabe evaluar árboles de condiciones
AND/OR/NOT sobre un Fact (un diccionario plano de campo -> valor).

Formato de condición (YAML), ya usado en priority_rules.yml y
recommendation_rules.yml:

    and:
      - field: brands
        operator: exists
      - field: event_type
        operator: equals
        value: Recall
      - or:
          - field: market_impact
            operator: in
            value: [Chile]
          - field: source_country
            operator: equals
            value: Chile

Operadores soportados (subconjunto del modelo de condición de la
Parte 2B, sección 6.2, suficiente para el Rulebook v0.2):
    equals, in, exists, not_exists, greater_than, less_than
"""

from __future__ import annotations
from typing import Any, Dict


class ConditionError(ValueError):
    """Se lanza cuando una condición está mal formada o usa un
    operador/campo no soportado."""


_LEAF_KEYS = {"field", "operator"}


def evaluate_condition(condition: Dict[str, Any], fact: Dict[str, Any]) -> bool:
    """Evalúa recursivamente una condición contra un Fact.

    Una condición es, en cada nivel, exactamente una de:
      - un nodo compuesto: {"and": [cond, ...]} | {"or": [cond, ...]} | {"not": cond}
      - una condición hoja: {"field": ..., "operator": ..., "value": ...}
    """
    if not isinstance(condition, dict) or not condition:
        raise ConditionError(f"Condición vacía o mal formada: {condition!r}")

    if "and" in condition:
        sub_conditions = condition["and"]
        if not isinstance(sub_conditions, list) or not sub_conditions:
            raise ConditionError("'and' debe ser una lista no vacía de condiciones")
        return all(evaluate_condition(c, fact) for c in sub_conditions)

    if "or" in condition:
        sub_conditions = condition["or"]
        if not isinstance(sub_conditions, list) or not sub_conditions:
            raise ConditionError("'or' debe ser una lista no vacía de condiciones")
        return any(evaluate_condition(c, fact) for c in sub_conditions)

    if "not" in condition:
        return not evaluate_condition(condition["not"], fact)

    if _LEAF_KEYS.issubset(condition.keys()):
        return _evaluate_leaf(condition, fact)

    raise ConditionError(
        f"Condición no reconocida (se esperaba 'and'/'or'/'not' o un nodo "
        f"hoja con 'field'+'operator'): {condition!r}"
    )


def _evaluate_leaf(condition: Dict[str, Any], fact: Dict[str, Any]) -> bool:
    field = condition["field"]
    operator = condition["operator"]
    value = condition.get("value")

    fact_value = fact.get(field)

    if operator == "equals":
        return fact_value == value

    if operator == "in":
        if not isinstance(value, list):
            raise ConditionError(f"El operador 'in' requiere una lista como value, se recibió: {value!r}")
        if isinstance(fact_value, list):
            return any(v in value for v in fact_value)
        return fact_value in value

    if operator == "exists":
        if isinstance(fact_value, list):
            return len(fact_value) > 0
        return fact_value is not None

    if operator == "not_exists":
        if isinstance(fact_value, list):
            return len(fact_value) == 0
        return fact_value is None

    if operator == "greater_than":
        return fact_value is not None and fact_value > value

    if operator == "less_than":
        return fact_value is not None and fact_value < value

    raise ConditionError(f"Operador no soportado: {operator!r}")
