from training.report_renderer import render_training_report

_META = {"noticias_procesadas": 1, "fecha_legible": "hoy", "hora_generacion": "00:00", "tiempo_ejecucion_segundos": 0.1}


def _brief(**overrides):
    base = {
        "story": "Noticia de prueba",
        "brand": ["Peugeot"],
        "competitors": [],
        "event_type": "Recall",
        "event_type_source": "explicit",
        "priority": "HIGH",
        "recommendations": ["EvaluarComunicado"],
        "why_it_matters": "Recall Stellantis con impacto en Chile",
        "source": {"name": "Emol", "tier": "Tier 1"},
        "source_url": "https://example.com/noticia",
        "rules_triggered": {"priority_rules": ["PR-001"], "recommendation_rules": ["PR-001"]},
    }
    base.update(overrides)
    return base


def test_report_contains_manual_validation_controls():
    html = render_training_report([_brief()], [], _META)
    assert 'name="correct_0"' in html
    assert 'value="si"' in html
    assert 'value="no"' in html
    assert 'id="brand_correct_0"' in html
    assert 'id="priority_correct_0"' in html
    assert 'id="recommendation_correct_0"' in html
    assert 'id="comments_0"' in html


def test_report_shows_detected_brand_and_rule():
    html = render_training_report([_brief()], [], _META)
    assert "Peugeot" in html
    assert "PR-001" in html
    assert "EvaluarComunicado" in html or "Evaluar comunicado" in html


def test_report_shows_dash_when_no_brand_detected():
    html = render_training_report([_brief(brand=[], competitors=[])], [], _META)
    assert "ninguna detectada" in html


def test_report_handles_missing_source_url_without_link():
    html = render_training_report([_brief(source_url=None)], [], _META)
    # No debe generar un <a href="None">
    assert 'href="None"' not in html


def test_report_includes_errors_block_when_present():
    html = render_training_report([], [{"file": "roto.json", "error": "campo faltante"}], _META)
    assert "roto.json" in html
    assert "no se pudieron procesar" in html


def test_report_embeds_system_data_for_export():
    html = render_training_report([_brief()], [], _META)
    assert "SYSTEM_DATA" in html
    assert "downloadValidations" in html
    assert '"system_priority": "HIGH"' in html


def test_report_no_ai_no_network_calls_in_script():
    """Verificación de alcance: el JS no debe hacer fetch/XHR a ningún
    servicio externo — todo debe ser local (Blob + download)."""
    html = render_training_report([_brief()], [], _META)
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "new Blob(" in html
