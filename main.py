#!/usr/bin/env python3
"""
Stellantis PR Intelligence Hub — MVP funcional (Sprint 3)

Pipeline:
    Input JSON -> Entity Recognition -> Event Detection ->
    Priority Rule Engine -> Recommendation Engine ->
    Daily Brief Generator -> Output JSON

Uso:
    python main.py noticia.json
"""

import json
import sys
from pathlib import Path

from pipeline.factory import build_default_pipeline

BASE_DIR = Path(__file__).parent


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python main.py <noticia.json>", file=sys.stderr)
        sys.exit(1)

    news_path = Path(sys.argv[1])
    if not news_path.exists():
        print(f"Archivo no encontrado: {news_path}", file=sys.stderr)
        sys.exit(1)

    with open(news_path, "r", encoding="utf-8") as f:
        news_dict = json.load(f)

    pipeline = build_default_pipeline(BASE_DIR)
    result = pipeline.run(news_dict)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
