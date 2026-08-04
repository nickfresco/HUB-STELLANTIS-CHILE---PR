#!/usr/bin/env python3
"""
Stellantis PR Intelligence Hub — PR HUB Daily (Sprint 4)

Procesa todas las noticias JSON de data/daily_input/, corre el
pipeline existente (sin cambios de arquitectura) sobre cada una, y
genera daily_brief.html — un correo ejecutivo listo para revisar.

Uso:
    python run_daily.py [--input DIR] [--output ARCHIVO.html]
"""

from __future__ import annotations
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from daily.aggregator import build_digest
from daily.html_renderer import render_html
from pipeline.factory import build_default_pipeline

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_DIR = BASE_DIR / "data" / "daily_input"
DEFAULT_OUTPUT = BASE_DIR / "daily_brief.html"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha_legible(dt: datetime) -> str:
    return f"{DIAS[dt.weekday()]} {dt.day} de {MESES[dt.month - 1]} de {dt.year}"


def process_daily_input(pipeline, input_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Corre el pipeline sobre cada noticia*.json de input_dir.

    Resiliente por diseño (Parte 5, sección 10): una noticia mal
    formada o con datos inválidos no debe tumbar la ejecución del día
    completo — se registra como error y se continúa con las demás.
    """
    briefs: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []

    for path in sorted(input_dir.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                news_dict = json.load(f)
            brief = pipeline.run(news_dict)
            briefs.append(brief)
        except Exception as e:  # noqa: BLE001 — resiliencia intencional, ver docstring
            errors.append({"file": path.name, "error": str(e)})

    return briefs, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera el Daily Brief del día en HTML.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_DIR, help="Carpeta con las noticias del día (JSON).")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Archivo HTML de salida.")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Carpeta de entrada no encontrada: {args.input}")
        raise SystemExit(1)

    start = time.perf_counter()
    pipeline = build_default_pipeline(BASE_DIR)
    briefs, errors = process_daily_input(pipeline, args.input)
    elapsed = time.perf_counter() - start

    now = datetime.now()
    meta = {
        "fecha_legible": _fecha_legible(now),
        "hora_generacion": now.strftime("%H:%M"),
        "noticias_procesadas": len(briefs),
        "tiempo_ejecucion_segundos": elapsed,
    }

    digest = build_digest(briefs, meta)
    html_output = render_html(digest, briefs, errors)

    args.output.write_text(html_output, encoding="utf-8")

    print(f"Daily Brief generado: {args.output}")
    print(f"  Noticias procesadas: {len(briefs)}  |  Errores: {len(errors)}  |  Tiempo: {elapsed:.2f}s")
    print(f"  Flash Alerts: {digest['counts']['flash_alerts']}  ·  Stellantis: {digest['counts']['stellantis']}"
          f"  ·  Competencia: {digest['counts']['competencia']}  ·  Industria: {digest['counts']['industria']}"
          f"  ·  Oportunidades: {digest['counts']['oportunidades']}")
    if errors:
        print("  Errores encontrados (ver sección Debug del HTML):")
        for e in errors:
            print(f"    - {e['file']}: {e['error']}")


if __name__ == "__main__":
    main()
