"""
RSS Feed Loader — carga config/rss_sources.yml.

Mismo patrón que rule_engine/loader.py (Sprint 3): un feed mal formado
se rechaza individualmente, con warning, sin abortar la carga completa
del archivo. Ningún feed se descarga desde aquí — este módulo solo
sabe leer configuración.
"""

from __future__ import annotations
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

REQUIRED_FIELDS = {"id", "source_id"}


class FeedConfigError(ValueError):
    pass


@dataclass(frozen=True)
class FeedConfig:
    id: str
    source_id: str
    url: Optional[str]
    enabled: bool = True
    verified: bool = False
    todo: Optional[str] = None


def load_feed_sources(path: "str | Path") -> List[FeedConfig]:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or "feeds" not in raw:
        raise FeedConfigError(f"El archivo {path} no contiene la clave 'feeds'")

    feeds: List[FeedConfig] = []
    for i, entry in enumerate(raw["feeds"]):
        missing = REQUIRED_FIELDS - entry.keys()
        if missing:
            warnings.warn(f"[{path.name}] Feed #{i} rechazado: faltan campos {missing}")
            continue
        feeds.append(
            FeedConfig(
                id=entry["id"],
                source_id=entry["source_id"],
                url=entry.get("url"),
                enabled=entry.get("enabled", True),
                verified=entry.get("verified", False),
                todo=entry.get("todo"),
            )
        )
    return feeds


def enabled_feeds(feeds: List[FeedConfig]) -> List[FeedConfig]:
    """Feeds listos para descargarse: habilitados y con URL configurada.
    Un feed con enabled=true pero url=null (no debería ocurrir, pero se
    protege igual) se trata como no descargable, no como error."""
    return [f for f in feeds if f.enabled and f.url]
