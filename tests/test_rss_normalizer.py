from rss.feed_loader import FeedConfig
from rss.normalizer import normalize_article
from rss.parser import RawArticle

FEED = FeedConfig(id="rss.test", source_id="source.emol", url="file://test")


def test_normalize_strips_html_tags():
    article = RawArticle(title="Titulo", summary="<p>Texto con <b>negrita</b> y <a href='x'>link</a></p>", url="https://x.cl", published_at=None)
    result = normalize_article(article, FEED)
    assert "<" not in result["summary"]
    assert "Texto con negrita y link" == result["summary"]


def test_normalize_unescapes_html_entities():
    article = RawArticle(title="Stellantis &amp; Santander", summary="Alianza &nbsp;comercial", url="https://x.cl", published_at=None)
    result = normalize_article(article, FEED)
    assert result["title"] == "Stellantis & Santander"
    assert "&nbsp;" not in result["summary"]


def test_normalize_collapses_whitespace():
    article = RawArticle(title="Titulo", summary="Texto   con    espacios\n\nirregulares", url="https://x.cl", published_at=None)
    result = normalize_article(article, FEED)
    assert result["summary"] == "Texto con espacios irregulares"


def test_normalize_truncates_long_summary():
    long_summary = "palabra " * 200  # muy por sobre MAX_SUMMARY_LENGTH
    article = RawArticle(title="Titulo", summary=long_summary, url="https://x.cl", published_at=None)
    result = normalize_article(article, FEED)
    assert len(result["summary"]) <= 601  # 600 + el caracter de truncado "…"
    assert result["summary"].endswith("…")


def test_normalize_maps_source_id_from_feed_config():
    article = RawArticle(title="T", summary="S", url="https://x.cl", published_at="2026-08-04T10:00:00+00:00")
    result = normalize_article(article, FEED)
    assert result["source_id"] == "source.emol"
    assert result["source_url"] == "https://x.cl"
    assert result["published_at"] == "2026-08-04T10:00:00+00:00"


def test_normalize_output_is_compatible_with_newsinput_from_dict():
    """El contrato más importante de este módulo: lo que produce debe
    poder pasarle directo a NewsInput.from_dict sin adaptación."""
    from models.fact import NewsInput

    article = RawArticle(title="Titulo real", summary="Resumen real", url="https://x.cl/nota", published_at="2026-08-04T10:00:00+00:00")
    result = normalize_article(article, FEED)

    news = NewsInput.from_dict(result)
    assert news.title == "Titulo real"
    assert news.source_id == "source.emol"
    assert news.source_url == "https://x.cl/nota"
    assert news.event_type is None  # la ingesta no clasifica, eso sigue siendo trabajo del pipeline
