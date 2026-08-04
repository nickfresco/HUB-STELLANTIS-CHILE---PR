"""
Deduplication — detección determinística de artículos duplicados
dentro de una misma ejecución de ingesta.

Regla mínima de este sprint: dos artículos son duplicados si comparten
la misma URL, o el mismo título normalizado (minúsculas, sin acentos,
sin puntuación, espacios colapsados).

TODO (deuda técnica, deliberadamente fuera de este sprint): esto NO
detecta reformulaciones de un mismo hecho publicadas con títulos
distintos por medios distintos (ej. "Jeep anuncia recall en Chile" vs.
"Recall afecta a modelos Jeep vendidos en el país"). Eso requeriría
fuzzy matching (similitud de texto, embeddings) o el concepto completo
de Story vs. NewsItem descrito en la arquitectura original (Parte 2B),
ninguno de los cuales existe todavía en este código — este sprint es
infraestructura de ingesta, no motor de decisión, y deduplicación
"inteligente" es exactamente ese tipo de decisión.
"""

from __future__ import annotations
import re
import unicodedata
from typing import Any, Dict, List, Set, Tuple

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")


def normalize_title(title: str) -> str:
    """minúsculas, sin acentos, sin puntuación, espacios colapsados.
    Uso exclusivamente interno para comparar — nunca se muestra."""
    nfkd = unicodedata.normalize("NFKD", title.lower())
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    no_punct = _PUNCT_RE.sub(" ", no_accents)
    return _SPACE_RE.sub(" ", no_punct).strip()


def deduplicate(articles: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Devuelve (artículos_únicos, cantidad_removida). Conserva el
    primer artículo visto de cada duplicado, en el orden de entrada —
    determinista: la misma lista de entrada siempre produce el mismo
    resultado, sin depender de qué feed se procesó primero más allá del
    orden ya dado."""
    seen_urls: Set[str] = set()
    seen_titles: Set[str] = set()
    unique: List[Dict[str, Any]] = []
    removed = 0

    for article in articles:
        url = article.get("source_url") or ""
        norm_title = normalize_title(article.get("title") or "")

        is_duplicate = (url and url in seen_urls) or (norm_title and norm_title in seen_titles)
        if is_duplicate:
            removed += 1
            continue

        if url:
            seen_urls.add(url)
        if norm_title:
            seen_titles.add(norm_title)
        unique.append(article)

    return unique, removed
