from datetime import date
from pathlib import Path

import pytest
import yaml

from rss.ingest import ingest_feed, run_ingestion
from rss.feed_loader import FeedConfig

FIXTURES = Path(__file__).parent / "fixtures" / "rss"


def _file_url(name: str) -> str:
    return f"file://{FIXTURES / name}"


def test_ingest_feed_returns_normalized_dicts():
    feed = FeedConfig(id="rss.test", source_id="source.emol", url=_file_url("valid_rss2.xml"))
    articles = ingest_feed(feed)
    assert len(articles) == 2
    assert all(a["source_id"] == "source.emol" for a in articles)
    assert all("title" in a and "summary" in a and "source_url" in a for a in articles)


def test_ingest_feed_decodes_cdata_entities_end_to_end():
    """Cierra el ciclo parser (preserva CDATA literal) + normalizer
    (decodifica y limpia) -> el resultado final que ve Entity
    Recognition debe quedar en texto plano, sin '&amp;' ni HTML."""
    feed = FeedConfig(id="rss.test", source_id="source.emol", url=_file_url("valid_rss2.xml"))
    articles = ingest_feed(feed)
    jeep_article = next(a for a in articles if "Jeep" in a["title"])
    assert "&amp;" not in jeep_article["summary"]
    assert "<" not in jeep_article["summary"]
    assert "&" in jeep_article["summary"]  # decodificado a texto plano


def test_ingest_feed_propagates_error_for_broken_xml():
    feed = FeedConfig(id="rss.test", source_id="source.emol", url=_file_url("malformed.xml"))
    with pytest.raises(Exception):
        ingest_feed(feed)


# ---------------------------------------------------------------------
# run_ingestion: orquestación completa, incluyendo fallos parciales
# ---------------------------------------------------------------------

def _write_config(tmp_path: Path, feeds: list) -> Path:
    config_path = tmp_path / "rss_sources.yml"
    config_path.write_text(yaml.safe_dump({"version": "1.0.0", "feeds": feeds}), encoding="utf-8")
    return config_path


def test_run_ingestion_writes_dated_json_file(tmp_path):
    feeds = [{"id": "rss.a", "source_id": "source.emol", "url": _file_url("valid_rss2.xml"), "enabled": True}]
    config_path = _write_config(tmp_path, feeds)
    output_dir = tmp_path / "output"

    result = run_ingestion(config_path, output_dir, target_date=date(2026, 8, 4))

    assert result.output_path == output_dir / "2026-08-04.json"
    assert result.output_path.exists()
    assert len(result.articles) == 2
    assert result.feeds_attempted == 1
    assert result.feeds_succeeded == 1
    assert result.feed_errors == []


def test_run_ingestion_continues_when_one_feed_fails(tmp_path):
    """El caso central de 'graceful failures' pedido por el sprint: un
    feed roto no debe impedir que los demás se procesen."""
    feeds = [
        {"id": "rss.roto", "source_id": "source.emol", "url": _file_url("malformed.xml"), "enabled": True},
        {"id": "rss.bueno", "source_id": "source.la_tercera", "url": _file_url("valid_atom.xml"), "enabled": True},
    ]
    config_path = _write_config(tmp_path, feeds)
    output_dir = tmp_path / "output"

    result = run_ingestion(config_path, output_dir, target_date=date(2026, 8, 4))

    assert result.feeds_attempted == 2
    assert result.feeds_succeeded == 1
    assert len(result.feed_errors) == 1
    assert result.feed_errors[0]["feed_id"] == "rss.roto"
    assert len(result.articles) == 2  # los 2 artículos del feed que sí funcionó


def test_run_ingestion_with_all_feeds_failing_does_not_crash(tmp_path):
    """Caso límite real (encontrado en este mismo sprint contra feeds
    de verdad): si TODOS los feeds fallan, la ingesta debe terminar
    igual, con una lista vacía y el archivo de salida escrito, no con
    una excepción sin capturar."""
    feeds = [
        {"id": "rss.roto1", "source_id": "source.emol", "url": _file_url("malformed.xml"), "enabled": True},
        {"id": "rss.roto2", "source_id": "source.la_tercera", "url": "file:///no/existe.xml", "enabled": True},
    ]
    config_path = _write_config(tmp_path, feeds)
    output_dir = tmp_path / "output"

    result = run_ingestion(config_path, output_dir, target_date=date(2026, 8, 4))

    assert result.feeds_succeeded == 0
    assert len(result.feed_errors) == 2
    assert result.articles == []
    assert result.output_path.exists()
    assert result.output_path.read_text(encoding="utf-8").strip() == "[]"


def test_run_ingestion_deduplicates_across_feeds(tmp_path):
    """Dos feeds distintos que republican el mismo artículo (misma URL)
    deben terminar deduplicados en el resultado combinado."""
    feeds = [
        {"id": "rss.a", "source_id": "source.emol", "url": _file_url("with_duplicates.xml"), "enabled": True},
    ]
    config_path = _write_config(tmp_path, feeds)
    output_dir = tmp_path / "output"

    result = run_ingestion(config_path, output_dir, target_date=date(2026, 8, 4))

    assert result.duplicates_removed == 2
    assert len(result.articles) == 2


def test_run_ingestion_skips_disabled_feeds(tmp_path):
    feeds = [
        {"id": "rss.activo", "source_id": "source.emol", "url": _file_url("valid_rss2.xml"), "enabled": True},
        {"id": "rss.inactivo", "source_id": "source.reuters", "url": _file_url("valid_atom.xml"), "enabled": False},
    ]
    config_path = _write_config(tmp_path, feeds)
    output_dir = tmp_path / "output"

    result = run_ingestion(config_path, output_dir, target_date=date(2026, 8, 4))

    assert result.feeds_attempted == 1  # el deshabilitado ni se intenta
    assert len(result.articles) == 2  # solo los del feed activo (RSS2), no los del Atom deshabilitado
