import json
from pathlib import Path

import pytest

from pipeline.factory import build_default_pipeline

BASE_DIR = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def pipeline():
    return build_default_pipeline(BASE_DIR)


def _load_fixture(name: str) -> dict:
    with open(FIXTURES / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_recall_chile_triggers_pr001_high(pipeline):
    brief = pipeline.run(_load_fixture("recall_jeep_chile.json"))
    assert brief["priority"] == "HIGH"
    assert "PR-001" in brief["rules_triggered"]["priority_rules"]
    assert brief["section"] == "Riesgos reputacionales"
    assert "EvaluarComunicado" in brief["recommendations"]
    assert "EvaluarQyA" in brief["recommendations"]
    assert "Jeep" in brief["brand"]
    assert brief["event_type_source"] == "explicit"


def test_puretech_internacional_triggers_pr002_medium(pipeline):
    brief = pipeline.run(_load_fixture("puretech_internacional.json"))
    assert brief["priority"] == "MEDIUM"
    assert "PR-002" in brief["rules_triggered"]["priority_rules"]
    assert "PR-001" not in brief["rules_triggered"]["priority_rules"]


def test_lanzamiento_stellantis_triggers_pr004(pipeline):
    brief = pipeline.run(_load_fixture("lanzamiento_jeep_renegade.json"))
    assert brief["priority"] == "MEDIUM"
    assert "PR-004" in brief["rules_triggered"]["priority_rules"]


def test_anac_resultados_triggers_pr011(pipeline):
    brief = pipeline.run(_load_fixture("anac_resultados.json"))
    assert brief["priority"] == "MEDIUM"
    assert "PR-011" in brief["rules_triggered"]["priority_rules"]


def test_latin_ncap_triggers_pr013_high(pipeline):
    brief = pipeline.run(_load_fixture("latin_ncap_resultado.json"))
    assert brief["priority"] == "HIGH"
    assert "PR-013" in brief["rules_triggered"]["priority_rules"]


def test_lanzamiento_competidor_triggers_pr010(pipeline):
    brief = pipeline.run(_load_fixture("lanzamiento_competidor.json"))
    assert brief["priority"] == "LOW"
    assert "PR-010" in brief["rules_triggered"]["priority_rules"]
    assert brief["brand"] == []


def test_premio_triggers_pr008(pipeline):
    brief = pipeline.run(_load_fixture("premio_peugeot.json"))
    assert brief["priority"] == "LOW"
    assert "PR-008" in brief["rules_triggered"]["priority_rules"]


def test_regulacion_triggers_pr012(pipeline):
    brief = pipeline.run(_load_fixture("regulacion_ev.json"))
    assert brief["priority"] == "MEDIUM"
    assert "PR-012" in brief["rules_triggered"]["priority_rules"]


def test_noticia_sin_marca_no_rules_match(pipeline):
    brief = pipeline.run(_load_fixture("noticia_sin_marca.json"))
    assert brief["priority"] is None
    assert brief["rules_triggered"]["priority_rules"] == []
    assert brief["recommendations"] == []


def test_pending_rule_never_fires_even_with_matching_event_type(pipeline):
    """PR-014 (Comparativa) está PENDING/disabled — no debe activarse
    aunque el event_type más cercano disponible coincida."""
    brief = pipeline.run(_load_fixture("comparativa_no_soportada.json"))
    assert "PR-014" not in brief["rules_triggered"]["priority_rules"]


def test_unknown_source_id_raises_clear_error(pipeline):
    with pytest.raises(ValueError, match="source_id"):
        pipeline.run({
            "title": "Noticia con fuente inexistente",
            "summary": "",
            "source_id": "source.no_existe",
            "event_type": "Lanzamiento",
        })


def test_unknown_event_type_raises_clear_error(pipeline):
    with pytest.raises(ValueError, match="event_type"):
        pipeline.run({
            "title": "Noticia con event_type inválido",
            "summary": "",
            "source_id": "source.emol",
            "event_type": "TipoInventado",
        })


def test_audit_trail_includes_rulebook_version(pipeline):
    brief = pipeline.run(_load_fixture("recall_jeep_chile.json"))
    assert brief["audit"]["priority_rulebook_version"] == "0.2.0"
    assert brief["audit"]["recommendation_rulebook_version"] == "0.2.0"


# ---------------------------------------------------------------------
# Event Detection (Sprint 3): event_type ahora es opcional
# ---------------------------------------------------------------------

def test_event_type_inferred_when_not_provided(pipeline):
    brief = pipeline.run(_load_fixture("recall_sin_event_type.json"))
    assert brief["event_type"] == "Recall"
    assert brief["event_type_source"] == "inferred"
    assert brief["priority"] == "HIGH"  # PR-001 debe seguir disparando vía inferencia


def test_event_type_undetected_does_not_crash_pipeline(pipeline):
    brief = pipeline.run(_load_fixture("texto_no_clasificable.json"))
    assert brief["event_type"] is None
    assert brief["event_type_source"] == "undetected"
    assert brief["priority"] is None
    assert brief["rules_triggered"]["priority_rules"] == []
