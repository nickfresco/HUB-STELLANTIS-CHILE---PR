from pathlib import Path

import pytest

from rss.feed_loader import FeedConfigError, enabled_feeds, load_feed_sources

CONFIG_PATH = Path(__file__).parent.parent / "config" / "rss_sources.yml"


def test_loads_real_rss_sources_yml_without_errors():
    feeds = load_feed_sources(CONFIG_PATH)
    assert len(feeds) > 0


def test_every_feed_has_id_and_source_id():
    feeds = load_feed_sources(CONFIG_PATH)
    for f in feeds:
        assert f.id
        assert f.source_id


def test_disabled_feeds_are_excluded_from_enabled_feeds():
    feeds = load_feed_sources(CONFIG_PATH)
    disabled = [f for f in feeds if not f.enabled]
    assert len(disabled) > 0  # AutoTest/Motor1/Reuters/Stellantis Media/ANAC, por diseño
    result = enabled_feeds(feeds)
    for f in disabled:
        assert f not in result


def test_feeds_without_url_are_excluded_even_if_marked_enabled():
    feeds = [f for f in load_feed_sources(CONFIG_PATH) if f.source_id in ("source.autotest", "source.motor1")]
    assert all(f.url is None for f in feeds)
    assert all(f not in enabled_feeds(load_feed_sources(CONFIG_PATH)) for f in feeds)


def test_missing_feeds_key_raises_error(tmp_path):
    bad_config = tmp_path / "bad.yml"
    bad_config.write_text("version: '1.0.0'\nnotfeeds: []\n", encoding="utf-8")
    with pytest.raises(FeedConfigError):
        load_feed_sources(bad_config)


def test_feed_missing_required_field_is_skipped_not_fatal(tmp_path):
    bad_config = tmp_path / "partial.yml"
    bad_config.write_text(
        "version: '1.0.0'\n"
        "feeds:\n"
        "  - id: rss.sin_source_id\n"
        "    url: 'https://example.cl/feed.xml'\n"
        "  - id: rss.valido\n"
        "    source_id: source.emol\n"
        "    url: 'https://example.cl/feed2.xml'\n",
        encoding="utf-8",
    )
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        feeds = load_feed_sources(bad_config)
        assert len(w) == 1  # advierte sobre el feed inválido...

    assert len(feeds) == 1  # ...pero no aborta la carga del resto
    assert feeds[0].id == "rss.valido"
