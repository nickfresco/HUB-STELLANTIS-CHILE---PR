#!/usr/bin/env python3
"""
Sprint 9.5 — Production Dry Run

Toma UN feed RSS verificado (Diario Financiero, el primero marcado
`verified: true` en config/rss_sources.yml), corre el pipeline de
producción completo tal como lo ejecutaría `run_daily.py`, genera
daily_brief.html y training_report.html, y mide el tiempo de cada
etapa por separado.

Diferencia respecto a una corrida real de producción: la descarga del
feed no pasa por rss/fetcher.py con una petición HTTP en vivo, sino por
un archivo local (df_live_fetch.xml) que contiene el contenido REAL
que ese feed devolvió — obtenido con la herramienta web_fetch de Claude
en vez de una petición HTTP directa desde este entorno, porque el
proxy de salida del entorno de desarrollo bloquea df.cl (ver
EXECUTION_REPORT.md, sección 1). Por eso el tiempo de "descarga" no se
mide aquí como representativo — se mide todo lo demás (parseo,
normalización, deduplicación, clasificación, generación de reportes),
que es exactamente el mismo código que correría en producción.

Uso:
    python sprint_9_5/run_and_measure.py
"""

from __future__ import annotations
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from daily.aggregator import build_digest  # noqa: E402
from daily.html_renderer import render_html  # noqa: E402
from pipeline.factory import build_default_pipeline  # noqa: E402
from run_daily import _fecha_legible, process_daily_input  # noqa: E402
from rss.deduplication import deduplicate  # noqa: E402
from rss.feed_loader import FeedConfig  # noqa: E402
from rss.ingest import ingest_feed  # noqa: E402
from rss.parser import parse_feed_content  # noqa: E402
from training.report_renderer import render_training_report  # noqa: E402

SPRINT_DIR = Path(__file__).parent
LIVE_FEED_XML = SPRINT_DIR / "df_live_fetch.xml"
TARGET_DATE = date(2026, 8, 4)

FEED = FeedConfig(
    id="rss.diario_financiero",
    source_id="source.diario_financiero",
    url=f"file://{LIVE_FEED_XML}",
    enabled=True,
    verified=True,
)

timings: dict = {}


def _timed(label: str, fn):
    start = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - start
    timings[label] = elapsed
    return result


def main() -> None:
    total_start = time.perf_counter()

    print(f"Feed: {FEED.source_id}  (Diario Financiero — 'verified: true' en config/rss_sources.yml)")
    print(f"Contenido: {LIVE_FEED_XML.name} ({LIVE_FEED_XML.stat().st_size} bytes, "
          f"obtenido en vivo vía web_fetch — ver EXECUTION_REPORT.md sección 1)\n")

    # --- Ingesta: parseo + normalización (rss/ingest.py:ingest_feed) ---
    articles = _timed("1_parse_and_normalize", lambda: ingest_feed(FEED))
    print(f"[1] Parseo + normalización:  {timings['1_parse_and_normalize']*1000:.2f} ms  "
          f"({len(articles)} artículos)")

    # --- Deduplicación ---
    unique_articles, removed = _timed("2_deduplication", lambda: deduplicate(articles))
    print(f"[2] Deduplicación:            {timings['2_deduplication']*1000:.2f} ms  "
          f"({removed} duplicados removidos, {len(unique_articles)} únicos)")

    # --- Escribir data/daily_input/YYYY-MM-DD.json (igual que producción) ---
    output_dir = REPO_ROOT / "data" / "daily_input"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{TARGET_DATE.isoformat()}.json"

    def _write_json():
        json_path.write_text(json.dumps(unique_articles, indent=2, ensure_ascii=False), encoding="utf-8")

    _timed("3_write_json", _write_json)
    print(f"[3] Escritura del JSON:       {timings['3_write_json']*1000:.2f} ms  -> {json_path.relative_to(REPO_ROOT)}")

    # --- Pipeline existente (Entity Recognition -> Event Detection -> Priority -> Recommendation) ---
    pipeline = _timed("4_build_pipeline", lambda: build_default_pipeline(REPO_ROOT))
    print(f"[4] Construcción del pipeline (carga Knowledge Base + Rulebook): {timings['4_build_pipeline']*1000:.2f} ms")

    briefs, errors = _timed("5_process_pipeline", lambda: process_daily_input(pipeline, json_path))
    print(f"[5] Clasificación (pipeline.run x {len(unique_articles)}): {timings['5_process_pipeline']*1000:.2f} ms  "
          f"({len(briefs)} procesadas, {len(errors)} errores)")

    # --- Daily Brief ---
    now = datetime.now()
    meta = {
        "fecha_legible": _fecha_legible(now),
        "hora_generacion": now.strftime("%H:%M"),
        "noticias_procesadas": len(briefs),
        "tiempo_ejecucion_segundos": 0.0,  # se completa más abajo con el total real
    }

    digest = _timed("6_build_digest", lambda: build_digest(briefs, meta))
    print(f"[6] Agregación (Daily Brief): {timings['6_build_digest']*1000:.2f} ms")

    daily_html = _timed("7_render_daily_brief", lambda: render_html(digest, briefs, errors))
    (SPRINT_DIR / "daily_brief.sprint9_5.html").write_text(daily_html, encoding="utf-8")
    print(f"[7] Render Daily Brief HTML:  {timings['7_render_daily_brief']*1000:.2f} ms")

    # --- Training Report ---
    training_html = _timed("8_render_training_report", lambda: render_training_report(briefs, errors, meta))
    (SPRINT_DIR / "training_report.sprint9_5.html").write_text(training_html, encoding="utf-8")
    print(f"[8] Render Training Report:   {timings['8_render_training_report']*1000:.2f} ms")

    # Copiar el JSON de ingesta también a sprint_9_5/ para dejar todo junto,
    # y retirarlo de data/daily_input/ — este dry run usa una muestra
    # curada de 8 noticias, no una ingesta real del día, así que no debe
    # quedar mezclado ahí con los datos ficticios del Sprint 4.
    (SPRINT_DIR / "daily_input.sprint9_5.json").write_text(
        json.dumps(unique_articles, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    json_path.unlink()

    total_elapsed = time.perf_counter() - total_start
    timings["TOTAL_measured_stages"] = total_elapsed

    print(f"\nTOTAL (etapas medidas, sin la descarga en vivo): {total_elapsed*1000:.2f} ms  "
          f"({total_elapsed:.3f} s)")

    # Guardar timings crudos para referencia en el EXECUTION_REPORT.md
    (SPRINT_DIR / "timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")

    print("\nArtefactos generados en sprint_9_5/:")
    print("  - daily_input.sprint9_5.json")
    print("  - daily_brief.sprint9_5.html")
    print("  - training_report.sprint9_5.html")
    print("  - timings.json")


if __name__ == "__main__":
    main()
