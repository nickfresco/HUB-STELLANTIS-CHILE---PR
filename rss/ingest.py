"""
RSS Ingestion Orchestrator — el punto de entrada del módulo rss/.

Encadena: leer config/rss_sources.yml -> descargar cada feed habilitado
-> parsear -> normalizar -> deduplicar globalmente -> escribir
data/daily_input/YYYY-MM-DD.json (una lista de noticias, en el formato
que ya consume NewsInput.from_dict, sin cambios).

Resiliente por diseño: si un feed falla (red, timeout, XML mal
formado, lo que sea), se registra el error y se continúa con los
demás — el mismo principio de resiliencia que ya aplica
run_daily.py a nivel de noticia individual (Parte 5, sección 10),
aplicado aquí a nivel de fuente.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from rss.deduplication import deduplicate
from rss.feed_loader import FeedConfig, enabled_feeds, load_feed_sources
from rss.fetcher import FeedFetchError, fetch_feed_content
from rss.normalizer import normalize_article
from rss.parser import FeedParseError, parse_feed_content


@dataclass
class IngestionResult:
    articles: List[Dict[str, Any]] = field(default_factory=list)
    feed_errors: List[Dict[str, str]] = field(default_factory=list)
    duplicates_removed: int = 0
    feeds_attempted: int = 0
    feeds_succeeded: int = 0
    output_path: Optional[Path] = None


def ingest_feed(feed: FeedConfig) -> List[Dict[str, Any]]:
    """Descarga y normaliza un único feed. Deja que las excepciones
    (FeedFetchError, FeedParseError) se propaguen — es
    responsabilidad de run_ingestion() decidir qué hacer con ellas,
    no de esta función."""
    raw_content = fetch_feed_content(feed.url)
    raw_articles = parse_feed_content(raw_content)
    return [normalize_article(a, feed) for a in raw_articles]


def run_ingestion(
    config_path: "str | Path",
    output_dir: "str | Path",
    target_date: Optional[date] = None,
) -> IngestionResult:
    target_date = target_date or date.today()
    feeds = enabled_feeds(load_feed_sources(config_path))

    result = IngestionResult(feeds_attempted=len(feeds))
    all_articles: List[Dict[str, Any]] = []

    for feed in feeds:
        try:
            all_articles.extend(ingest_feed(feed))
            result.feeds_succeeded += 1
        except (FeedFetchError, FeedParseError) as e:
            result.feed_errors.append({"feed_id": feed.id, "error": str(e)})
        except Exception as e:  # noqa: BLE001 — resiliencia intencional, ver docstring del módulo
            result.feed_errors.append({"feed_id": feed.id, "error": f"Error inesperado: {e}"})

    unique_articles, removed = deduplicate(all_articles)
    result.articles = unique_articles
    result.duplicates_removed = removed

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{target_date.isoformat()}.json"
    output_path.write_text(
        json.dumps(unique_articles, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    result.output_path = output_path

    return result
