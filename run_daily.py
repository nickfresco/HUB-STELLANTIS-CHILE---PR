#!/usr/bin/env python3
"""
Stellantis PR Intelligence Hub — PR HUB Daily (Sprint 4 + Sprint 9)

Comando único del día: descarga las noticias vía RSS (Sprint 9),
corre el pipeline existente (sin cambios de arquitectura) sobre cada
una, y genera tanto daily_brief.html como training_report.html —
listos para revisar cada mañana.

Flujo por defecto (sin --input):
    1. Descargar feeds RSS (config/rss_sources.yml)
    2. Generar data/daily_input/YYYY-MM-DD.json
    3. Ejecutar el Rule Engine sobre cada noticia
    4. Generar daily_brief.html
    5. Generar training_report.html

Uso:
    python run_daily.py                          # flujo completo con RSS
    python run_daily.py --skip-ingestion          # usa data/daily_input/ ficticio, sin red
    python run_daily.py --input archivo_o_carpeta # usa una fuente específica, sin red
"""

from __future__ import annotations
import argparse
import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from daily.aggregator import build_digest
from daily.html_renderer import render_html
from pipeline.factory import build_default_pipeline
from rss.ingest import run_ingestion
from training.report_renderer import render_training_report

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_DIR = BASE_DIR / "data" / "daily_input"
DEFAULT_RSS_SOURCES = BASE_DIR / "config" / "rss_sources.yml"
DEFAULT_OUTPUT = BASE_DIR / "daily_brief.html"
DEFAULT_REPORT_OUTPUT = BASE_DIR / "training_report.html"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha_legible(dt: datetime) -> str:
    return f"{DIAS[dt.weekday()]} {dt.day} de {MESES[dt.month - 1]} de {dt.year}"


def process_daily_input(pipeline, input_path: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Corre el pipeline sobre las noticias del día.

    Soporta dos formatos de entrada, sin duplicar la lógica de
    ejecución del pipeline entre ambos:

    - Un directorio con un archivo .json por noticia (formato
      original del Sprint 4, usado por los ejemplos ficticios de
      data/daily_input/). Comportamiento sin cambios respecto a
      versiones anteriores.
    - Un único archivo .json con una lista de noticias (formato que
      produce la ingesta RSS del Sprint 9 en
      data/daily_input/YYYY-MM-DD.json).

    Resiliente por diseño en ambos casos (Parte 5, sección 10): una
    noticia mal formada o con datos inválidos no debe tumbar la
    ejecución del día completo — se registra como error y se continúa
    con las demás.
    """
    briefs: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    if input_path.is_dir():
        for path in sorted(input_path.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    news_dict = json.load(f)
                briefs.append(pipeline.run(news_dict))
            except Exception as e:  # noqa: BLE001 — resiliencia intencional, ver docstring
                errors.append({"file": path.name, "error": str(e)})
        return briefs, errors

    # Archivo único: se espera una lista de noticias.
    try:
        items = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append({"file": input_path.name, "error": f"No se pudo leer el archivo: {e}"})
        return briefs, errors

    if not isinstance(items, list):
        errors.append({"file": input_path.name, "error": "Se esperaba una lista de noticias (JSON array)."})
        return briefs, errors

    for i, news_dict in enumerate(items):
        label = f"{input_path.name}[{i}]"
        try:
            briefs.append(pipeline.run(news_dict))
        except Exception as e:  # noqa: BLE001
            errors.append({"file": label, "error": str(e)})

    return briefs, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el Daily Brief y el Training Report del día.")
    parser.add_argument("--input", type=Path, default=None,
                         help="Carpeta o archivo JSON con las noticias del día. Si se da, se omite la ingesta RSS.")
    parser.add_argument("--skip-ingestion", action="store_true",
                         help=f"Omite la descarga RSS y usa el directorio ficticio por defecto ({DEFAULT_INPUT_DIR}), sin red.")
    parser.add_argument("--rss-sources", type=Path, default=DEFAULT_RSS_SOURCES, help="Catálogo de feeds RSS a usar.")
    parser.add_argument("--date", type=str, default=None, help="Fecha objetivo YYYY-MM-DD (por defecto, hoy). Afecta el nombre del JSON de ingesta.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Archivo HTML del Daily Brief.")
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT,
                         help="Archivo HTML del Training Report. Nota: comparte nombre por defecto con el que genera "
                              "run_training.py — si necesitas conservar ambos, usa rutas distintas.")
    args = parser.parse_args()

    start = time.perf_counter()

    if args.input is not None:
        input_path = args.input
    elif args.skip_ingestion:
        input_path = DEFAULT_INPUT_DIR
    else:
        target_date = date.fromisoformat(args.date) if args.date else date.today()
        print(f"Descargando feeds RSS ({args.rss_sources.name})...")
        ingestion = run_ingestion(args.rss_sources, DEFAULT_INPUT_DIR, target_date=target_date)
        print(f"  Feeds: {ingestion.feeds_succeeded}/{ingestion.feeds_attempted} exitosos"
              f"  |  Artículos únicos: {len(ingestion.articles)}"
              f"  |  Duplicados removidos: {ingestion.duplicates_removed}")
        if ingestion.feed_errors:
            print("  Feeds con error (se continuó con los demás):")
            for e in ingestion.feed_errors:
                print(f"    ⚠ {e['feed_id']}: {e['error']}")
        input_path = ingestion.output_path

    if not input_path.exists():
        print(f"Entrada no encontrada: {input_path}")
        raise SystemExit(1)

    pipeline = build_default_pipeline(BASE_DIR)
    briefs, errors = process_daily_input(pipeline, input_path)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    meta = {
        "fecha_legible": _fecha_legible(now),
        "hora_generacion": now.strftime("%H:%M"),
        "noticias_procesadas": len(briefs),
        "tiempo_ejecucion_segundos": elapsed,
    }

    # 4. Daily Brief — mismo aggregator/renderer del Sprint 4, sin cambios.
    digest = build_digest(briefs, meta)
    args.output.write_text(render_html(digest, briefs, errors), encoding="utf-8")

    # 5. Training Report — mismo renderer del Sprint 5, sin cambios; se
    # aplica sobre las noticias del día en vez de sobre training/examples/.
    args.report_output.write_text(render_training_report(briefs, errors, meta), encoding="utf-8")

    print(f"Daily Brief generado:    {args.output}")
    print(f"Training Report generado: {args.report_output}")
    print(f"  Noticias procesadas: {len(briefs)}  |  Errores: {len(errors)}  |  Tiempo total: {elapsed:.2f}s")
    print(f"  Flash Alerts: {digest['counts']['flash_alerts']}  ·  Stellantis: {digest['counts']['stellantis']}"
          f"  ·  Competencia: {digest['counts']['competencia']}  ·  Industria: {digest['counts']['industria']}"
          f"  ·  Oportunidades: {digest['counts']['oportunidades']}")
    if errors:
        print("  Noticias con error (ver sección Debug del Daily Brief):")
        for e in errors:
            print(f"    - {e['file']}: {e['error']}")


if __name__ == "__main__":
    main()
