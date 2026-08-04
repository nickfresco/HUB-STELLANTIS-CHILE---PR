"""
RSS Fetcher — descarga el contenido crudo de un feed.

Deliberadamente separado de rss/parser.py: este módulo solo sabe
obtener bytes/texto desde alguna parte; el parser solo sabe interpretar
XML. Esto permite testear el parser con contenido local, sin red, y
testear el fetcher simulando fallos de red sin necesitar un feed real.

Soporta URLs `file://` además de `http(s)://` — no es un capricho: es
lo que permite generar ejemplos reales de ingesta (JSON, Daily Brief,
Training Report) en un entorno sin acceso a red saliente, ejecutando
el mismo código de producción contra archivos XML de muestra en lugar
de mockear la función. Ver tests/fixtures/rss/ y README para el detalle.
"""

from __future__ import annotations
from pathlib import Path
from urllib.parse import urlparse

import requests

DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_USER_AGENT = "PR-HUB-Ingestion/1.0 (+internal Stellantis Chile PR tool)"


class FeedFetchError(Exception):
    """Se lanza cuando un feed no pudo descargarse por cualquier motivo
    (red, timeout, HTTP 4xx/5xx, archivo local inexistente). Quien
    llama (rss/ingest.py) debe capturarla y continuar con los demás
    feeds — nunca dejar que un feed caído tumbe la ingesta completa."""


def fetch_feed_content(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> str:
    parsed = urlparse(url)

    if parsed.scheme == "file":
        return _fetch_local(parsed.path)

    if parsed.scheme in ("http", "https"):
        return _fetch_remote(url, timeout)

    raise FeedFetchError(f"Esquema de URL no soportado: '{parsed.scheme}' (url: {url})")


def _fetch_remote(url: str, timeout: int) -> str:
    try:
        response = requests.get(url, timeout=timeout, headers={"User-Agent": DEFAULT_USER_AGENT})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        raise FeedFetchError(f"No se pudo descargar '{url}': {e}") from e


def _fetch_local(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise FeedFetchError(f"No se pudo leer el archivo local '{path}': {e}") from e
