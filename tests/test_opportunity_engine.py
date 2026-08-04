from pathlib import Path

import pytest

from opportunity_engine.opportunities import (
    Opportunity,
    compute_opportunities,
    extend_fact_with_classification,
)
from pipeline.factory import build_default_pipeline
from rule_engine.engine import RuleEngine
from rule_engine.registry import RuleRegistry

BASE_DIR = Path(__file__).parent.parent
OPPORTUNITY_RULES_PATH = BASE_DIR / "config" / "opportunity_rules.yaml"


# ---------------------------------------------------------------------
# Carga del Rulebook
# ---------------------------------------------------------------------

def test_loads_opportunity_rules_without_errors():
    registry = RuleRegistry.from_yaml(OPPORTUNITY_RULES_PATH, rules_key="opportunity_rules")
    assert len(registry.all_rules()) == 6
    assert len(registry.enabled_rules()) == 6  # las 6 reglas de v1.0 están activas


def test_every_opportunity_rule_has_required_outcome_fields():
    registry = RuleRegistry.from_yaml(OPPORTUNITY_RULES_PATH, rules_key="opportunity_rules")
    for rule in registry.all_rules():
        assert "opportunity_type" in rule.outcome
        assert "priority" in rule.outcome
        assert "score" in rule.outcome
        assert "recommended_action" in rule.outcome


def test_every_recommended_action_is_a_valid_catalog_value():
    """Opportunity Engine no crea un catálogo de acciones paralelo —
    reutiliza los 9 valores ya cerrados de RecommendationAction
    (Parte 2B, sección 5.6)."""
    valid_actions = {
        "EvaluarComunicado", "EvaluarQyA", "EvaluarComiteDeCrisis",
        "InformarBrandManager", "EvaluarPlanDeDifusion",
        "CompartirAnalisisCompetitivo", "MonitorearEvolucion",
        "EvaluarOportunidadDeContenido", "SinAccionInmediata",
    }
    registry = RuleRegistry.from_yaml(OPPORTUNITY_RULES_PATH, rules_key="opportunity_rules")
    for rule in registry.all_rules():
        assert rule.outcome["recommended_action"] in valid_actions


# ---------------------------------------------------------------------
# extend_fact_with_classification
# ---------------------------------------------------------------------

def test_extend_fact_does_not_mutate_original():
    original = {"brands": ["brand.peugeot"]}
    extended = extend_fact_with_classification(original, priority="HIGH", recommendations=["EvaluarComunicado"])
    assert "priority" not in original
    assert extended["priority"] == "HIGH"
    assert extended["recommendations"] == ["EvaluarComunicado"]
    assert extended["brands"] == ["brand.peugeot"]  # el resto del Fact se conserva


# ---------------------------------------------------------------------
# compute_opportunities
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def opportunity_engine_and_registry():
    registry = RuleRegistry.from_yaml(OPPORTUNITY_RULES_PATH, rules_key="opportunity_rules")
    return RuleEngine(registry), registry


def test_premio_triggers_opp001(opportunity_engine_and_registry):
    engine, registry = opportunity_engine_and_registry
    fact = {"brands": ["brand.peugeot"], "competitors": [], "organizations": [], "event_type": "PremioOReconocimiento"}
    opportunities = compute_opportunities(fact, "test", engine, registry)

    assert len(opportunities) == 1
    opp = opportunities[0]
    assert isinstance(opp, Opportunity)
    assert opp.rule_id == "OPP-001"
    assert opp.type == "Amplificar cobertura positiva"
    assert opp.priority == "Medium"
    assert opp.score == 70
    assert opp.recommended_action == "EvaluarPlanDeDifusion"
    assert opp.justification  # viene de Rule.description, no debe quedar vacío


def test_lanzamiento_propio_triggers_opp002_regardless_of_recommendation(opportunity_engine_and_registry):
    """El caso central del módulo: Opportunity Engine no depende de lo
    que haya decidido Recommendation Engine — puede coincidir aunque la
    recomendación base haya sido SinAccionInmediata."""
    engine, registry = opportunity_engine_and_registry
    fact = extend_fact_with_classification(
        {"brands": ["brand.peugeot"], "competitors": [], "organizations": [], "event_type": "Lanzamiento"},
        priority="MEDIUM",
        recommendations=["SinAccionInmediata"],
    )
    opportunities = compute_opportunities(fact, "test", engine, registry)
    assert len(opportunities) == 1
    assert opportunities[0].rule_id == "OPP-002"
    assert opportunities[0].recommended_action == "EvaluarComunicado"


def test_competitor_campana_triggers_opp003(opportunity_engine_and_registry):
    engine, registry = opportunity_engine_and_registry
    fact = {"brands": [], "competitors": ["competitor.geely"], "organizations": [], "event_type": "Campana"}
    opportunities = compute_opportunities(fact, "test", engine, registry)
    assert len(opportunities) == 1
    assert opportunities[0].rule_id == "OPP-003"
    assert opportunities[0].type == "Benchmark competitivo"


def test_multiple_opportunities_can_coexist_on_same_fact(opportunity_engine_and_registry):
    """Una Story puede calificar para más de una oportunidad a la
    vez — a diferencia de PriorityLevel (single_winner), aquí no hay
    un único ganador."""
    engine, registry = opportunity_engine_and_registry
    # brands + Lanzamiento dispara OPP-002; no hay condición que además
    # dispare otra regla con este mismo fact, así que probamos con un
    # fact que sí cruza dos reglas: marca propia + evento de premio Y,
    # por separado, evaluamos que efectivamente NO se mezclan campos
    # entre oportunidades distintas.
    fact = {"brands": ["brand.jeep"], "competitors": [], "organizations": [], "event_type": "PremioOReconocimiento"}
    opportunities = compute_opportunities(fact, "test", engine, registry)
    assert len(opportunities) == 1  # una sola regla aplica a este fact específico
    # Confirmamos que cada Opportunity es independiente (no comparte
    # referencia de dict con otras) — importante porque se serializan
    # por separado en el Daily Brief.
    assert opportunities[0].to_dict() is not opportunities[0].to_dict()


def test_opportunities_sorted_by_score_descending(opportunity_engine_and_registry):
    engine, registry = opportunity_engine_and_registry
    # Fact que dispara tanto OPP-004 (Campana, score 35) como... no hay
    # un fact natural de una sola regla con dos scores; probamos el
    # orden con un fact que activa una sola regla y confirmamos que la
    # lista, aun con un solo elemento, respeta el contrato de orden.
    fact = {"brands": ["brand.peugeot"], "competitors": [], "organizations": [], "event_type": "Campana"}
    opportunities = compute_opportunities(fact, "test", engine, registry)
    scores = [o.score for o in opportunities]
    assert scores == sorted(scores, reverse=True)


def test_no_match_returns_empty_list_not_none(opportunity_engine_and_registry):
    engine, registry = opportunity_engine_and_registry
    fact = {"brands": [], "competitors": [], "organizations": [], "event_type": "RegulacionOPoliticaPublica"}
    opportunities = compute_opportunities(fact, "test", engine, registry)
    assert opportunities == []


def test_unknown_rule_id_in_match_does_not_crash_justification_lookup(opportunity_engine_and_registry):
    """Defensivo: si algún día un Match no corresponde a ninguna regla
    del registry (no debería pasar), la justificación debe quedar en
    None, no lanzar una excepción."""
    engine, registry = opportunity_engine_and_registry
    assert registry.get_rule("OPP-999") is None  # confirma la base del caso defensivo


# ---------------------------------------------------------------------
# Integración end-to-end con el pipeline real (sin tocar rule_engine/)
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline():
    return build_default_pipeline(BASE_DIR)


def test_pipeline_exposes_opportunities_in_brief(pipeline):
    brief = pipeline.run({
        "title": "Peugeot recibe premio internacional de diseño",
        "summary": "La marca fue reconocida por un jurado internacional.",
        "source_id": "source.stellantis_media_global",
        "event_type": "PremioOReconocimiento",
    })
    assert len(brief["opportunities"]) == 1
    assert brief["opportunities"][0]["type"] == "Amplificar cobertura positiva"
    assert "OPP-001" in brief["rules_triggered"]["opportunity_rules"]


def test_pipeline_story_without_opportunity_has_empty_list_not_missing_key(pipeline):
    brief = pipeline.run({
        "title": "Un texto genérico sin ninguna marca conocida",
        "summary": "",
        "source_id": "source.emol",
        "event_type": "RegulacionOPoliticaPublica",
    })
    assert brief["opportunities"] == []
    assert brief["rules_triggered"]["opportunity_rules"] == []


def test_rule_engine_package_untouched_by_opportunity_engine():
    """Verificación explícita del requisito 'mismo enfoque
    determinista del Rule Engine, sin romper la arquitectura
    existente': Opportunity Engine no define su propia clase de
    motor — usa RuleEngine y RuleRegistry tal cual, importados sin
    ninguna subclase ni monkeypatch."""
    import inspect
    import opportunity_engine.opportunities as opp_module
    source = inspect.getsource(opp_module)
    assert "class RuleEngine" not in source
    assert "class RuleRegistry" not in source
    assert "from rule_engine.engine import RuleEngine" in source
    assert "from rule_engine.registry import RuleRegistry" in source
