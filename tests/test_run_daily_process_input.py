import json
from pathlib import Path

import pytest

from pipeline.factory import build_default_pipeline
from run_daily import process_daily_input

BASE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def pipeline():
    return build_default_pipeline(BASE_DIR)


# ---------------------------------------------------------------------
# Modo directorio — comportamiento original del Sprint 4, no debe cambiar
# ---------------------------------------------------------------------

def test_directory_mode_still_works_unchanged(pipeline):
    briefs, errors = process_daily_input(pipeline, BASE_DIR / "data" / "daily_input")
    assert len(briefs) == 14  # las 14 noticias ficticias del Sprint 4
    assert errors == []


# ---------------------------------------------------------------------
# Modo archivo único — nuevo en el Sprint 9
# ---------------------------------------------------------------------

def test_single_file_mode_with_valid_list(pipeline, tmp_path):
    news_list = [
        {"title": "Peugeot lanza modelo", "summary": "Resumen", "source_id": "source.emol", "event_type": "Lanzamiento"},
        {"title": "Toyota lanza modelo", "summary": "Resumen", "source_id": "source.emol", "event_type": "Lanzamiento"},
    ]
    input_file = tmp_path / "2026-08-04.json"
    input_file.write_text(json.dumps(news_list), encoding="utf-8")

    briefs, errors = process_daily_input(pipeline, input_file)

    assert len(briefs) == 2
    assert errors == []


def test_single_file_mode_reports_error_per_story_not_whole_file(pipeline, tmp_path):
    """Una noticia inválida dentro de la lista no debe tumbar el
    procesamiento de las demás — mismo principio de resiliencia que
    el modo directorio."""
    news_list = [
        {"title": "Noticia válida", "summary": "Resumen", "source_id": "source.emol", "event_type": "Lanzamiento"},
        {"title": "Noticia con fuente inexistente", "summary": "Resumen", "source_id": "source.no_existe"},
    ]
    input_file = tmp_path / "2026-08-04.json"
    input_file.write_text(json.dumps(news_list), encoding="utf-8")

    briefs, errors = process_daily_input(pipeline, input_file)

    assert len(briefs) == 1
    assert len(errors) == 1
    assert "2026-08-04.json[1]" in errors[0]["file"]


def test_single_file_mode_with_malformed_json_reports_error_not_crash(pipeline, tmp_path):
    input_file = tmp_path / "2026-08-04.json"
    input_file.write_text("{ esto no es JSON válido", encoding="utf-8")

    briefs, errors = process_daily_input(pipeline, input_file)

    assert briefs == []
    assert len(errors) == 1


def test_single_file_mode_with_non_list_json_reports_error(pipeline, tmp_path):
    input_file = tmp_path / "2026-08-04.json"
    input_file.write_text(json.dumps({"esto": "no es una lista"}), encoding="utf-8")

    briefs, errors = process_daily_input(pipeline, input_file)

    assert briefs == []
    assert len(errors) == 1
    assert "lista" in errors[0]["error"].lower()


def test_single_file_mode_with_empty_list(pipeline, tmp_path):
    input_file = tmp_path / "2026-08-04.json"
    input_file.write_text("[]", encoding="utf-8")

    briefs, errors = process_daily_input(pipeline, input_file)

    assert briefs == []
    assert errors == []
