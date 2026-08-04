"""
RSS/Atom Parser — convierte el XML crudo de un feed en una lista de
artículos normalizados a nivel de estructura (RawArticle).

Decisión deliberada: usa xml.etree.ElementTree (librería estándar) en
vez de una librería como feedparser. No fue posible confirmar en este
entorno de desarrollo que feedparser esté disponible para quien clone
el repositorio (no hay acceso a red para instalarla y probarla aquí),
así que se prefirió stdlib — con soporte explícito para los dos
formatos ampliamente usados por medios chilenos e internacionales:
RSS 2.0 y Atom. Si en el futuro se confirma feedparser como dependencia
viable, este módulo es el único que habría que reemplazar — el resto
del pipeline de ingesta (fetcher, normalizer, deduplication) no conoce
ni le importa qué biblioteca de parseo se usa.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

_ATOM_NS = "{http://www.w3.org/2005/Atom}"


@dataclass(frozen=True)
class RawArticle:
    title: str
    summary: str
    url: str
    published_at: Optional[str]  # ISO 8601, o None si no se pudo interpretar


class FeedParseError(Exception):
    """Se lanza cuando el XML no pudo interpretarse en absoluto — ni
    como XML válido, ni como RSS 2.0, ni como Atom."""


def parse_feed_content(xml_content: str) -> List[RawArticle]:
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise FeedParseError(f"XML mal formado: {e}") from e

    if root.tag == "rss":
        return _parse_rss2(root)

    if root.tag in (f"{_ATOM_NS}feed", "feed"):
        return _parse_atom(root)

    raise FeedParseError(f"Formato de feed no reconocido (elemento raíz: '{root.tag}')")


def _text(el: Optional[ET.Element]) -> str:
    return (el.text or "").strip() if el is not None else ""


def _parse_pubdate(raw: Optional[str]) -> Optional[str]:
    """Formato RFC 822, el que usa RSS 2.0 (ej. 'Mon, 04 Aug 2026 10:00:00 -0400')."""
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except (TypeError, ValueError):
        return None


def _parse_iso_date(raw: Optional[str]) -> Optional[str]:
    """Formato ISO 8601, el que usa Atom (ej. '2026-08-04T10:00:00Z')."""
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.strip().replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def _parse_rss2(root: ET.Element) -> List[RawArticle]:
    channel = root.find("channel")
    if channel is None:
        raise FeedParseError("RSS 2.0 sin elemento <channel>")

    articles: List[RawArticle] = []
    for item in channel.findall("item"):
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        summary = _text(item.find("description"))
        pub_date = _parse_pubdate(_text(item.find("pubDate")) or None)

        if not title or not link:
            continue  # sin título o sin URL no es un artículo utilizable

        articles.append(RawArticle(title=title, summary=summary, url=link, published_at=pub_date))

    return articles


def _atom_link(entry: ET.Element) -> str:
    """Atom permite múltiples <link> (rel=alternate, rel=self, etc.) —
    se prioriza 'alternate' o sin rel (que es el equivalente implícito
    a 'alternate'), igual que hacen los lectores RSS reales."""
    links = entry.findall(f"{_ATOM_NS}link")
    if not links:
        return ""
    for link in links:
        if link.get("rel") in (None, "alternate"):
            return link.get("href", "")
    return links[0].get("href", "")


def _parse_atom(root: ET.Element) -> List[RawArticle]:
    articles: List[RawArticle] = []
    for entry in root.findall(f"{_ATOM_NS}entry"):
        title = _text(entry.find(f"{_ATOM_NS}title"))
        link = _atom_link(entry)

        summary_el = entry.find(f"{_ATOM_NS}summary")
        if summary_el is None:
            summary_el = entry.find(f"{_ATOM_NS}content")
        summary = _text(summary_el)

        raw_date = _text(entry.find(f"{_ATOM_NS}updated")) or _text(entry.find(f"{_ATOM_NS}published"))
        pub_date = _parse_iso_date(raw_date or None)

        if not title or not link:
            continue

        articles.append(RawArticle(title=title, summary=summary, url=link, published_at=pub_date))

    return articles
