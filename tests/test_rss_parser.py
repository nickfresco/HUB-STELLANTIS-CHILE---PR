from pathlib import Path

import pytest

from rss.parser import FeedParseError, parse_feed_content

FIXTURES = Path(__file__).parent / "fixtures" / "rss"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parses_rss2_items():
    articles = parse_feed_content(_read("valid_rss2.xml"))
    titles = [a.title for a in articles]
    assert "Jeep Wrangler recibe recall preventivo en Chile" in titles
    assert "Peugeot presenta el renovado 2008 en el mercado local" in titles


def test_rss2_item_without_link_is_skipped():
    articles = parse_feed_content(_read("valid_rss2.xml"))
    titles = [a.title for a in articles]
    assert "Nota sin link, debe descartarse" not in titles
    assert len(articles) == 2


def test_rss2_preserves_cdata_content_as_literal_text():
    """El contenido dentro de CDATA es texto literal por definición —
    XML no decodifica entidades ahí (para eso existe CDATA). El parser
    no debe intentar "arreglar" eso; decodificar entidades y limpiar
    HTML es trabajo de rss/normalizer.py, no de este módulo."""
    articles = parse_feed_content(_read("valid_rss2.xml"))
    jeep_article = next(a for a in articles if "Jeep" in a.title)
    assert "Jeep" in jeep_article.summary
    assert "&amp;" in jeep_article.summary  # literal, sin decodificar — correcto dentro de CDATA


def test_rss2_pubdate_parsed_to_iso():
    articles = parse_feed_content(_read("valid_rss2.xml"))
    jeep_article = next(a for a in articles if "Jeep" in a.title)
    assert jeep_article.published_at == "2026-08-04T09:15:00-04:00"


def test_parses_atom_entries():
    articles = parse_feed_content(_read("valid_atom.xml"))
    assert len(articles) == 2
    titles = [a.title for a in articles]
    assert "BYD Yuan Pro llega a Chile como híbrido enchufable" in titles
    assert "ANAC publica resultados de ventas del mes" in titles


def test_atom_prefers_alternate_link_over_self():
    articles = parse_feed_content(_read("valid_atom.xml"))
    byd_article = next(a for a in articles if "BYD" in a.title)
    assert byd_article.url == "https://example.cl/noticias/byd-yuan-pro"
    assert "self-link" not in byd_article.url


def test_atom_falls_back_to_content_when_no_summary():
    articles = parse_feed_content(_read("valid_atom.xml"))
    anac_article = next(a for a in articles if "ANAC" in a.title)
    assert "Reporte mensual" in anac_article.summary


def test_atom_updated_and_published_both_supported():
    articles = parse_feed_content(_read("valid_atom.xml"))
    byd_article = next(a for a in articles if "BYD" in a.title)
    anac_article = next(a for a in articles if "ANAC" in a.title)
    assert byd_article.published_at == "2026-08-04T10:30:00+00:00"
    assert anac_article.published_at == "2026-08-04T11:00:00-04:00"


def test_malformed_xml_raises_feed_parse_error():
    with pytest.raises(FeedParseError):
        parse_feed_content(_read("malformed.xml"))


def test_unknown_format_raises_feed_parse_error():
    with pytest.raises(FeedParseError):
        parse_feed_content(_read("unknown_format.xml"))


def test_empty_string_raises_feed_parse_error():
    with pytest.raises(FeedParseError):
        parse_feed_content("")
