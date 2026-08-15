from pathlib import Path

from knowledge_base.loader import KnowledgeBase

KB_PATH = Path(__file__).parent.parent / "config" / "knowledge_base"


def load_kb() -> KnowledgeBase:
    return KnowledgeBase(KB_PATH)


def test_loads_all_brands():
    kb = load_kb()
    assert len(kb.brands) == 8
    ids = {b.canonical_id for b in kb.brands}
    assert "brand.jeep" in ids
    assert "brand.peugeot" in ids


def test_loads_sources_with_required_fields():
    kb = load_kb()
    source = kb.get_source("source.emol")
    assert source is not None
    assert source.tier == "Tier 1"
    assert source.country == "Chile"


def test_unknown_source_returns_none():
    kb = load_kb()
    assert kb.get_source("source.no_existe") is None


def test_event_type_catalog_validation():
    kb = load_kb()
    assert kb.is_valid_event_type("Recall") is True
    assert kb.is_valid_event_type("Comparativa") is False  # brecha de catálogo documentada (PR-014)


def test_all_products_combines_models_and_technologies():
    kb = load_kb()
    ids = {p.canonical_id for p in kb.all_products()}
    assert "product.puretech" in ids  # technologies.yml
    assert "product.jeep_renegade" in ids  # models.yml


def test_event_type_keywords_loaded_for_every_catalog_event_type():
    kb = load_kb()
    assert "recall" in kb.event_type_keywords["Recall"]
    assert set(kb.event_type_keywords.keys()) <= set(kb.event_types)
