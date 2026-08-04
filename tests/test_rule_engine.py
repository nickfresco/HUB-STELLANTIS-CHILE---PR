import pytest

from rule_engine.condition import ConditionError, evaluate_condition
from rule_engine.engine import RuleEngine
from rule_engine.registry import RuleRegistry
from rule_engine.rules import Rule


def test_and_condition():
    condition = {"and": [
        {"field": "brand", "operator": "equals", "value": "jeep"},
        {"field": "event_type", "operator": "equals", "value": "Recall"},
    ]}
    assert evaluate_condition(condition, {"brand": "jeep", "event_type": "Recall"}) is True
    assert evaluate_condition(condition, {"brand": "jeep", "event_type": "Lanzamiento"}) is False


def test_or_condition():
    condition = {"or": [
        {"field": "event_type", "operator": "equals", "value": "NuevaLey"},
        {"field": "event_type", "operator": "equals", "value": "NuevoIncentivo"},
    ]}
    assert evaluate_condition(condition, {"event_type": "NuevoIncentivo"}) is True
    assert evaluate_condition(condition, {"event_type": "Otro"}) is False


def test_nested_and_or():
    """Equivalente a PR-009: AND(a, b, OR(c, d, e))."""
    condition = {"and": [
        {"field": "competitor", "operator": "exists"},
        {"or": [
            {"field": "channel", "operator": "equals", "value": "prensa"},
            {"field": "channel", "operator": "equals", "value": "influencers"},
        ]},
    ]}
    assert evaluate_condition(condition, {"competitor": "x", "channel": "influencers"}) is True
    assert evaluate_condition(condition, {"competitor": "x", "channel": "otro"}) is False


def test_not_condition():
    condition = {"not": {"field": "market_impact", "operator": "exists"}}
    assert evaluate_condition(condition, {"market_impact": []}) is True
    assert evaluate_condition(condition, {"market_impact": ["Chile"]}) is False


def test_in_operator_with_list_fact_value():
    condition = {"field": "brands", "operator": "in", "value": ["brand.jeep", "brand.ram"]}
    assert evaluate_condition(condition, {"brands": ["brand.jeep"]}) is True
    assert evaluate_condition(condition, {"brands": ["brand.peugeot"]}) is False


def test_malformed_condition_raises():
    with pytest.raises(ConditionError):
        evaluate_condition({"unknown_key": []}, {})


# ---------------------------------------------------------------------
# Motor completo: resolución de conflictos
# ---------------------------------------------------------------------

def _registry_with(rules):
    return RuleRegistry(version="test-1.0", rules=rules)


def test_single_winner_resolves_by_weight():
    rules = [
        Rule(id="R1", condition={"field": "x", "operator": "exists"}, outcome={"priority": "LOW"}, priority_weight=1),
        Rule(id="R2", condition={"field": "x", "operator": "exists"}, outcome={"priority": "HIGH"}, priority_weight=3),
    ]
    engine = RuleEngine(_registry_with(rules))
    result = engine.evaluate({"x": 1}, fact_reference="test", resolution_strategy="single_winner", outcome_field="priority")
    assert result.winning_rule_id == "R2"
    assert result.final_outcome == {"priority": "HIGH"}
    assert set(result.matched_rule_ids()) == {"R1", "R2"}  # ambas quedan auditadas


def test_single_winner_tiebreak_is_deterministic():
    rules = [
        Rule(id="R2", condition={"field": "x", "operator": "exists"}, outcome={"priority": "A"}, priority_weight=2),
        Rule(id="R1", condition={"field": "x", "operator": "exists"}, outcome={"priority": "B"}, priority_weight=2),
    ]
    engine = RuleEngine(_registry_with(rules))
    result = engine.evaluate({"x": 1}, fact_reference="test", resolution_strategy="single_winner", outcome_field="priority")
    assert result.winning_rule_id == "R1"  # gana por orden lexicográfico de id, no por orden de declaración


def test_accumulate_all_deduplicates_values():
    rules = [
        Rule(id="R1", condition={"field": "x", "operator": "exists"}, outcome={"recommendations": ["A", "B"]}),
        Rule(id="R2", condition={"field": "x", "operator": "exists"}, outcome={"recommendations": ["B", "C"]}),
    ]
    engine = RuleEngine(_registry_with(rules))
    result = engine.evaluate({"x": 1}, fact_reference="test", resolution_strategy="accumulate_all", outcome_field="recommendations")
    assert result.final_outcome["recommendations"] == ["A", "B", "C"]
    assert len(result.matches) == 2  # ambas coincidencias quedan auditadas aunque el valor se dedup


def test_disabled_rule_never_matches():
    rules = [
        Rule(id="R1", condition={"field": "x", "operator": "exists"}, outcome={"priority": "HIGH"}, enabled=False),
    ]
    engine = RuleEngine(_registry_with(rules))
    result = engine.evaluate({"x": 1}, fact_reference="test", resolution_strategy="single_winner", outcome_field="priority")
    assert result.matches == []
    assert result.final_outcome is None


def test_no_matches_returns_none_outcome_not_error():
    rules = [
        Rule(id="R1", condition={"field": "x", "operator": "equals", "value": "no-va-a-coincidir"}, outcome={"priority": "HIGH"}),
    ]
    engine = RuleEngine(_registry_with(rules))
    result = engine.evaluate({"x": "otro"}, fact_reference="test", resolution_strategy="single_winner", outcome_field="priority")
    assert result.final_outcome is None
    assert result.winning_rule_id is None
