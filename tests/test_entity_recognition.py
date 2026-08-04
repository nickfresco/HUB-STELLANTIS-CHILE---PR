from pathlib import Path

from classification.entity_recognition import detect_entities
from knowledge_base.loader import KnowledgeBase

KB_PATH = Path(__file__).parent.parent / "config" / "knowledge_base"


def load_kb() -> KnowledgeBase:
    return KnowledgeBase(KB_PATH)


def test_detects_brand_by_display_name():
    kb = load_kb()
    result = detect_entities("Peugeot presenta su nuevo modelo eléctrico", kb)
    assert "brand.peugeot" in result.brands


def test_detects_competitor():
    kb = load_kb()
    result = detect_entities("Toyota lanza nueva pickup en el mercado", kb)
    assert "competitor.toyota" in result.competitors


def test_jeep_alias_requires_disambiguation_context():
    """'jeep' en minúscula sin contexto NO debe activar un falso positivo
    (Parte 2B, sección 4.4)."""
    kb = load_kb()
    result_without_context = detect_entities(
        "El vehículo quedó atrapado, fue rescatado por un jeep del ejército", kb
    )
    # Sin ninguna palabra de contexto de la marca (Wrangler, Compass, etc.)
    # no debería confirmarse como la marca Jeep.
    assert "brand.jeep" not in result_without_context.brands

    result_with_context = detect_entities(
        "El nuevo Jeep Wrangler llega a Chile con tecnología 4x4", kb
    )
    assert "brand.jeep" in result_with_context.brands


def test_no_entities_detected_returns_empty_lists():
    kb = load_kb()
    result = detect_entities("Un texto genérico sin ninguna marca conocida", kb)
    assert result.brands == []
    assert result.competitors == []


def test_ds_alias_does_not_false_positive_inside_other_words():
    """Bug real encontrado con noticias reales (Sprint 5): 'ds' es
    subcadena de 'Ads', y 'auto' es subcadena de 'automotriz'. Sin
    límites de palabra, ambas condiciones se cumplían y DS Automobiles
    se detectaba en una noticia que no la mencionaba en absoluto."""
    kb = load_kb()
    result = detect_entities(
        "La campaña ganó un premio en los Ads People Like, siendo la única marca automotriz presente", kb
    )
    assert "brand.ds_automobiles" not in result.brands


def test_word_boundary_matching_still_detects_real_mentions():
    kb = load_kb()
    result = detect_entities("El nuevo DS Automobiles llega a Chile con tecnología francesa", kb)
    assert "brand.ds_automobiles" in result.brands
