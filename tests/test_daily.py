from daily.aggregator import build_digest
from daily.labels import action_label, benchmark_text, industry_text, OPPORTUNITY_ACTIONS


# ---------------------------------------------------------------------
# labels.py
# ---------------------------------------------------------------------

def test_action_label_known_value():
    assert action_label("EvaluarComunicado") == "Evaluar comunicado oficial"


def test_action_label_unknown_value_falls_back_to_raw():
    assert action_label("AlgoNoDefinido") == "AlgoNoDefinido"


def test_benchmark_text_known_event_type():
    assert "posicionamiento" in benchmark_text("Lanzamiento")


def test_benchmark_text_unknown_event_type_uses_default():
    assert benchmark_text("EventTypeInventado") == benchmark_text(None)


def test_industry_text_none_uses_default():
    assert industry_text(None) != ""


def test_sin_accion_inmediata_not_in_opportunity_actions():
    assert "SinAccionInmediata" not in OPPORTUNITY_ACTIONS
    assert "MonitorearEvolucion" not in OPPORTUNITY_ACTIONS


# ---------------------------------------------------------------------
# aggregator.py
# ---------------------------------------------------------------------

def _brief(story, priority=None, brand=None, competitors=None, recommendations=None, event_type=None):
    return {
        "story": story,
        "priority": priority,
        "brand": brand or [],
        "competitors": competitors or [],
        "recommendations": recommendations or [],
        "event_type": event_type,
        "source": {"name": "Fuente Test", "tier": "Tier 1"},
        "summary": story,
    }


_META = {"noticias_procesadas": 0, "hora_generacion": "00:00", "fecha_legible": "hoy", "tiempo_ejecucion_segundos": 0.0}


def test_high_priority_goes_to_flash_not_to_brand_section():
    briefs = [_brief("Recall Jeep", priority="HIGH", brand=["Jeep"])]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 1})
    assert digest["counts"]["flash_alerts"] == 1
    assert digest["counts"]["stellantis"] == 0  # no debe duplicarse en Stellantis


def test_medium_priority_brand_goes_to_stellantis():
    briefs = [_brief("Lanzamiento Peugeot", priority="MEDIUM", brand=["Peugeot"])]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 1})
    assert digest["counts"]["stellantis"] == 1
    assert digest["stellantis"][0][0] == "Peugeot"


def test_competitor_without_brand_goes_to_competencia():
    briefs = [_brief("Geely 3L Challenge", brand=[], competitors=["Geely"])]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 1})
    assert digest["counts"]["competencia"] == 1
    assert digest["counts"]["stellantis"] == 0


def test_no_brand_no_competitor_goes_to_industria():
    briefs = [_brief("ANAC resultados", priority="MEDIUM", event_type="ResultadoFinanciero")]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 1})
    assert digest["counts"]["industria"] == 1


def test_stellantis_brands_ordered_by_fixed_order_not_alphabetical():
    briefs = [
        _brief("Noticia RAM", priority="MEDIUM", brand=["RAM"]),
        _brief("Noticia Peugeot", priority="MEDIUM", brand=["Peugeot"]),
    ]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 2})
    brand_order = [brand for brand, _ in digest["stellantis"]]
    assert brand_order.index("Peugeot") < brand_order.index("RAM")  # orden fijo, no alfabético


def test_opportunity_actions_are_collected_across_all_briefs():
    briefs = [
        _brief("A", priority="HIGH", brand=["Jeep"], recommendations=["EvaluarComunicado"]),
        _brief("B", priority="LOW", brand=["Fiat"], recommendations=["SinAccionInmediata"]),
    ]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 2})
    assert digest["counts"]["oportunidades"] == 1  # solo la accionable, no SinAccionInmediata


def test_resumen_ejecutivo_has_at_most_three_bullets():
    briefs = [_brief("X", priority="HIGH", brand=["Jeep"], recommendations=["EvaluarComunicado"])]
    digest = build_digest(briefs, {**_META, "noticias_procesadas": 1})
    assert len(digest["resumen_ejecutivo"]) <= 3


def test_empty_day_does_not_crash():
    digest = build_digest([], {**_META, "noticias_procesadas": 0})
    assert digest["counts"]["flash_alerts"] == 0
    assert digest["flash_alerts"] == []
    assert len(digest["resumen_ejecutivo"]) <= 3
