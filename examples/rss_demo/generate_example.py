#!/usr/bin/env python3
"""
Genera los artefactos de ejemplo de examples/rss_demo/: un JSON de
ingesta, un Daily Brief y un Training Report — usando los mismos
archivos XML de muestra que ya usan los tests (tests/fixtures/rss/),
NO feeds en vivo.

Por qué existe este script en vez de un rss_sources.demo.yml estático:
las URLs file:// necesitan una ruta absoluta, que depende de dónde se
clonó el repositorio — no se puede dejar escrita a mano en un YAML
committeado sin romperse en la máquina de otra persona. Este script
resuelve la ruta real en tiempo de ejecución (relativa a este mismo
archivo) y arma la configuración en memoria, así que funciona igual
sin importar dónde viva el repositorio.

En un entorno con acceso real a internet, no hace falta este script:
`python run_daily.py` ya hace todo esto contra config/rss_sources.yml
de verdad. Este demo existe porque el entorno donde se construyó este
sprint no tiene acceso a red saliente (ver README, sección de ingesta
RSS) y aun así había que demostrar el flujo completo funcionando de
punta a punta.

Uso:
    python examples/rss_demo/generate_example.py
"""

from __future__ import annotations
import sys
import yaml
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from daily.aggregator import build_digest  # noqa: E402
from daily.html_renderer import render_html  # noqa: E402
from pipeline.factory import build_default_pipeline  # noqa: E402
from run_daily import _fecha_legible, process_daily_input  # noqa: E402
from rss.ingest import run_ingestion  # noqa: E402
from training.report_renderer import render_training_report  # noqa: E402

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "rss"
DEMO_DIR = Path(__file__).parent
EXAMPLE_DATE = date(2026, 8, 4)


def _file_url(name: str) -> str:
    return f"file://{FIXTURES_DIR / name}"


def build_demo_config() -> Path:
    """Arma un rss_sources.yml temporal, con rutas absolutas correctas
    para ESTA máquina, sin depender de nada committeado a mano."""
    feeds = [
        {"id": "rss.demo_rss2", "source_id": "source.emol", "url": _file_url("valid_rss2.xml"), "enabled": True, "verified": True},
        {"id": "rss.demo_atom", "source_id": "source.la_tercera", "url": _file_url("valid_atom.xml"), "enabled": True, "verified": True},
        {"id": "rss.demo_con_duplicados", "source_id": "source.autocosmos", "url": _file_url("with_duplicates.xml"), "enabled": True, "verified": True},
        {"id": "rss.demo_feed_roto", "source_id": "source.reuters", "url": _file_url("malformed.xml"), "enabled": True, "verified": True},
    ]
    config_path = DEMO_DIR / "_generated_rss_sources.yml"
    config_path.write_text(yaml.safe_dump({"version": "1.0.0", "feeds": feeds}, allow_unicode=True), encoding="utf-8")
    return config_path


def main() -> None:
    config_path = build_demo_config()

    print("1/4 — Descargando feeds (locales, vía file://)...")
    ingestion = run_ingestion(config_path, DEMO_DIR, target_date=EXAMPLE_DATE)
    print(f"      Feeds: {ingestion.feeds_succeeded}/{ingestion.feeds_attempted} exitosos"
          f" | Artículos únicos: {len(ingestion.articles)}"
          f" | Duplicados removidos: {ingestion.duplicates_removed}")
    for e in ingestion.feed_errors:
        print(f"      ⚠ {e['feed_id']}: {e['error']}")

    # Se deja el JSON de ingesta con un nombre de ejemplo explícito, en
    # vez del nombre YYYY-MM-DD.json real, para no confundirlo con una
    # ingesta de producción real.
    example_json_path = DEMO_DIR / "daily_input.example.json"
    example_json_path.write_text(ingestion.output_path.read_text(encoding="utf-8"), encoding="utf-8")
    ingestion.output_path.unlink()  # no dejar el archivo con nombre de fecha real en examples/

    print("2/4 — Corriendo el pipeline existente sobre el JSON generado...")
    pipeline = build_default_pipeline(REPO_ROOT)
    briefs, errors = process_daily_input(pipeline, example_json_path)
    print(f"      Noticias procesadas: {len(briefs)} | Errores: {len(errors)}")

    now_meta = {
        "fecha_legible": _fecha_legible(__import__("datetime").datetime(2026, 8, 4, 8, 0)),
        "hora_generacion": "08:00",
        "noticias_procesadas": len(briefs),
        "tiempo_ejecucion_segundos": 0.0,
    }

    print("3/4 — Generando daily_brief.example.html...")
    digest = build_digest(briefs, now_meta)
    (DEMO_DIR / "daily_brief.example.html").write_text(render_html(digest, briefs, errors), encoding="utf-8")

    print("4/4 — Generando training_report.example.html...")
    (DEMO_DIR / "training_report.example.html").write_text(
        render_training_report(briefs, errors, now_meta), encoding="utf-8"
    )

    config_path.unlink()  # limpiar el YAML temporal, no es un artefacto a conservar

    print("\nListo. Ver examples/rss_demo/:")
    print("  - daily_input.example.json")
    print("  - daily_brief.example.html")
    print("  - training_report.example.html")


if __name__ == "__main__":
    main()
