"""
Normalizer — convierte un RawArticle (salida cruda del parser) al
mismo formato de diccionario que ya consume NewsInput.from_dict
(models/fact.py, sin cambios). No reimplementa ni reinterpreta el
modelo de entrada existente — solo lo rellena con datos limpios.
"""

from __future__ import annotations
import re
from html import unescape
from typing import Any, Dict

from rss.feed_loader import FeedConfig
from rss.parser import RawArticle

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
MAX_SUMMARY_LENGTH = 600


def _clean_text(text: str) -> str:
    """Los <description>/<summary> de RSS y Atom suelen traer HTML
    embebido (<p>, <a>, entidades &nbsp;/&amp;, etc.) — se limpia antes
    de que llegue a Entity Recognition, que espera texto plano."""
    without_tags = _HTML_TAG_RE.sub(" ", text)
    unescaped = unescape(without_tags)
    return _WHITESPACE_RE.sub(" ", unescaped).strip()


def normalize_article(article: RawArticle, feed: FeedConfig) -> Dict[str, Any]:
    """Devuelve un dict con exactamente las claves que
    NewsInput.from_dict ya sabe leer — title, summary, source_id,
    published_at, source_url. event_type y market_impact se dejan sin
    informar a propósito: la clasificación sigue siendo trabajo del
    pipeline existente (Entity/Event Detection), no de la ingesta."""
    summary = _clean_text(article.summary)
    if len(summary) > MAX_SUMMARY_LENGTH:
        summary = summary[:MAX_SUMMARY_LENGTH].rsplit(" ", 1)[0] + "…"

    return {
        "title": _clean_text(article.title),
        "summary": summary,
        "source_id": feed.source_id,
        "published_at": article.published_at,
        "source_url": article.url,
    }
