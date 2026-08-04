from rss.deduplication import deduplicate, normalize_title


def _article(title, url, summary="resumen"):
    return {"title": title, "summary": summary, "source_id": "source.emol", "published_at": None, "source_url": url}


def test_normalize_title_strips_accents_case_and_punctuation():
    assert normalize_title("¡Jeep Anuncia RECALL en Chile!") == normalize_title("jeep anuncia recall en chile")


def test_normalize_title_collapses_whitespace():
    assert normalize_title("Peugeot   presenta el   2008") == "peugeot presenta el 2008"


def test_duplicate_by_same_url_is_removed():
    articles = [
        _article("Titulo A", "https://example.cl/nota-1"),
        _article("Titulo B distinto", "https://example.cl/nota-1"),
    ]
    unique, removed = deduplicate(articles)
    assert len(unique) == 1
    assert removed == 1
    assert unique[0]["title"] == "Titulo A"  # se conserva el primero visto


def test_duplicate_by_normalized_title_is_removed():
    articles = [
        _article("Fiat Topolino se suma a la flota del Vaticano", "https://example.cl/nota-1"),
        _article("¡Fiat Topolino se suma a la flota del Vaticano!", "https://example.cl/nota-1-republicada"),
    ]
    unique, removed = deduplicate(articles)
    assert len(unique) == 1
    assert removed == 1


def test_distinct_articles_are_not_removed():
    articles = [
        _article("Titulo A", "https://example.cl/nota-1"),
        _article("Titulo B", "https://example.cl/nota-2"),
        _article("Titulo C", "https://example.cl/nota-3"),
    ]
    unique, removed = deduplicate(articles)
    assert len(unique) == 3
    assert removed == 0


def test_empty_list_does_not_crash():
    unique, removed = deduplicate([])
    assert unique == []
    assert removed == 0


def test_deduplicate_is_deterministic_same_input_same_output():
    articles = [
        _article("Titulo A", "https://example.cl/nota-1"),
        _article("Titulo A", "https://example.cl/nota-1-otra-url"),
        _article("Titulo B", "https://example.cl/nota-2"),
    ]
    result1 = deduplicate(articles)
    result2 = deduplicate(articles)
    assert result1 == result2


def test_full_fixture_with_duplicates_end_to_end():
    """Usa el fixture real with_duplicates.xml a través de todo el
    parser + deduplicación, no solo diccionarios de prueba a mano."""
    from pathlib import Path
    from rss.feed_loader import FeedConfig
    from rss.normalizer import normalize_article
    from rss.parser import parse_feed_content

    xml = (Path(__file__).parent / "fixtures" / "rss" / "with_duplicates.xml").read_text(encoding="utf-8")
    raw_articles = parse_feed_content(xml)
    feed = FeedConfig(id="rss.test", source_id="source.emol", url="file://test")
    normalized = [normalize_article(a, feed) for a in raw_articles]

    unique, removed = deduplicate(normalized)

    assert len(raw_articles) == 4  # el fixture trae 4 items
    assert removed == 2  # 2 duplicados (uno por título, uno por URL)
    assert len(unique) == 2
    titles = {a["title"] for a in unique}
    assert "Fiat Topolino se suma a la flota del Vaticano" in titles
    assert "RAM 2500 rescata a vehículo militar atascado" in titles
