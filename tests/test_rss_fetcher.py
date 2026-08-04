from pathlib import Path

import pytest

from rss.fetcher import FeedFetchError, fetch_feed_content

FIXTURES = Path(__file__).parent / "fixtures" / "rss"


def test_fetch_local_file_via_file_scheme():
    url = f"file://{FIXTURES / 'valid_rss2.xml'}"
    content = fetch_feed_content(url)
    assert "<rss" in content
    assert "Jeep Wrangler" in content


def test_fetch_missing_local_file_raises_feed_fetch_error():
    with pytest.raises(FeedFetchError):
        fetch_feed_content("file:///ruta/que/no/existe.xml")


def test_fetch_unsupported_scheme_raises_feed_fetch_error():
    with pytest.raises(FeedFetchError):
        fetch_feed_content("ftp://example.cl/feed.xml")


def test_fetch_unreachable_host_raises_feed_fetch_error_not_generic_exception():
    """No debe propagar requests.RequestException cruda — debe quedar
    envuelta en FeedFetchError, que es lo que rss/ingest.py sabe
    capturar para continuar con los demás feeds."""
    with pytest.raises(FeedFetchError):
        fetch_feed_content("https://este-host-no-existe.invalid/feed.xml", timeout=3)
