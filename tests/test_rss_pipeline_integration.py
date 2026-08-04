"""
Verifica el requisito más importante del Sprint 9: el JSON que produce
la ingesta RSS debe poder procesarse con el pipeline EXISTENTE
(pipeline/factory.py, sin ningún cambio) — la ingesta es una fuente de
datos nueva, no una reimplementación del Rule Engine.
"""

from datetime import date
from pathlib import Path

import yaml

from pipeline.factory import build_default_pipeline
from rss.ingest import run_ingestion

BASE_DIR = Path(__file__).parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "rss"


def _file_url(name: str) -> str:
    return f"file://{FIXTURES / name}"


def test_rss_ingested_json_is_consumable_by_existing_pipeline(tmp_path):
    feeds = [
        {"id": "rss.a", "source_id": "source.emol", "url": _file_url("valid_rss2.xml"), "enabled": True},
        {"id": "rss.b", "source_id": "source.la_tercera", "url": _file_url("valid_atom.xml"), "enabled": True},
    ]
    config_path = tmp_path / "rss_sources.yml"
    config_path.write_text(yaml.safe_dump({"version": "1.0.0", "feeds": feeds}), encoding="utf-8")

    ingestion = run_ingestion(config_path, tmp_path / "output", target_date=date(2026, 8, 4))
    assert len(ingestion.articles) == 4  # 2 de valid_rss2.xml + 2 de valid_atom.xml

    pipeline = build_default_pipeline(BASE_DIR)
    briefs = [pipeline.run(article) for article in ingestion.articles]

    assert len(briefs) == 4
    # La noticia de Peugeot (Lanzamiento) debe clasificar igual que
    # cualquier otra noticia de Lanzamiento de marca Stellantis — la
    # prueba de que el Rule Engine no sabe ni le importa que esto vino
    # de RSS en vez de un archivo escrito a mano.
    peugeot_brief = next(b for b in briefs if "Peugeot" in b["story"])
    assert "Peugeot" in peugeot_brief["brand"]


def test_rss_output_file_is_directly_loadable_by_run_daily_process_input(tmp_path):
    """El archivo data/daily_input/YYYY-MM-DD.json que escribe la
    ingesta debe ser exactamente lo que run_daily.process_daily_input
    espera como 'archivo único' — sin ningún paso de adaptación
    intermedio."""
    from run_daily import process_daily_input

    feeds = [{"id": "rss.a", "source_id": "source.emol", "url": _file_url("valid_rss2.xml"), "enabled": True}]
    config_path = tmp_path / "rss_sources.yml"
    config_path.write_text(yaml.safe_dump({"version": "1.0.0", "feeds": feeds}), encoding="utf-8")

    ingestion = run_ingestion(config_path, tmp_path / "output", target_date=date(2026, 8, 4))

    pipeline = build_default_pipeline(BASE_DIR)
    briefs, errors = process_daily_input(pipeline, ingestion.output_path)

    assert errors == []
    assert len(briefs) == 2
