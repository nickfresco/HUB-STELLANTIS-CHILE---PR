#!/usr/bin/env python3
"""
Stellantis PR Intelligence Hub — Modo de Entrenamiento (Sprint 5)

Procesa noticias reales de training/examples/ (o --input), corre el
pipeline existente sobre cada una (sin modificarlo), genera el Daily
Brief como hasta ahora, y además training_report.html: un reporte de
validación manual para comparar el criterio del Rule Engine contra el
criterio real del Coordinador de PR.

No implementa aprendizaje automático — el reporte se completa a mano
en el navegador; el botón "Descargar validaciones" solo exporta un
JSON localmente, sin conexión a ningún servicio.

Uso:
    python run_training.py
    python run_training.py --input otra_carpeta/
"""

from __future__ import annotations
import argparse
import time
from datetime import datetime
from pathlib import Path

from daily.aggregator import build_digest
from daily.html_renderer import render_html
from pipeline.factory import build_default_pipeline
from run_daily import _fecha_legible, process_daily_input
from training.report_renderer import render_training_report

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_DIR = BASE_DIR / "training" / "examples"
DEFAULT_BRIEF_OUTPUT = BASE_DIR / "training_daily_brief.html"
DEFAULT_REPORT_OUTPUT = BASE_DIR / "training_report.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Modo de entrenamiento: procesa noticias reales y genera el reporte de validación.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_DIR, help="Carpeta con las noticias a procesar (JSON).")
    parser.add_argument("--brief-output", type=Path, default=DEFAULT_BRIEF_OUTPUT, help="Archivo del Daily Brief de estas noticias.")
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT, help="Archivo del reporte de validación.")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Carpeta de entrada no encontrada: {args.input}")
        raise SystemExit(1)

    start = time.perf_counter()
    pipeline = build_default_pipeline(BASE_DIR)
    # Reutiliza tal cual la misma función resiliente de run_daily.py — el
    # pipeline y el manejo de errores son exactamente los mismos, solo
    # cambia de dónde vienen las noticias.
    briefs, errors = process_daily_input(pipeline, args.input)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    meta = {
        "fecha_legible": _fecha_legible(now),
        "hora_generacion": now.strftime("%H:%M"),
        "noticias_procesadas": len(briefs),
        "tiempo_ejecucion_segundos": elapsed,
    }

    # 1. El Daily Brief, exactamente como hasta ahora (mismo aggregator
    #    y renderer del Sprint 4, sin ningún cambio).
    digest = build_digest(briefs, meta)
    brief_html = render_html(digest, briefs, errors)
    args.brief_output.write_text(brief_html, encoding="utf-8")

    # 2. El reporte de validación manual, nuevo en este sprint.
    report_html = render_training_report(briefs, errors, meta)
    args.report_output.write_text(report_html, encoding="utf-8")

    print(f"Daily Brief de entrenamiento: {args.brief_output}")
    print(f"Reporte de validación:        {args.report_output}")
    print(f"  Noticias procesadas: {len(briefs)}  |  Errores: {len(errors)}  |  Tiempo: {elapsed:.2f}s")
    if errors:
        print("  Errores encontrados:")
        for e in errors:
            print(f"    - {e['file']}: {e['error']}")


if __name__ == "__main__":
    main()
