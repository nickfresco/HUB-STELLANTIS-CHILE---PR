from pathlib import Path

from classification.event_detection import infer_event_type
from knowledge_base.loader import KnowledgeBase

KB_PATH = Path(__file__).parent.parent / "config" / "knowledge_base"


def load_kb() -> KnowledgeBase:
    return KnowledgeBase(KB_PATH)


def test_infers_recall_from_keyword():
    kb = load_kb()
    assert infer_event_type("La marca activa un recall preventivo por falla de frenos", kb) == "Recall"


def test_infers_lanzamiento_from_keyword():
    kb = load_kb()
    assert infer_event_type("La marca lanza oficialmente su nuevo modelo compacto", kb) == "Lanzamiento"


def test_infers_premio_over_generic_terms():
    kb = load_kb()
    assert infer_event_type("El modelo recibió un premio internacional de diseño", kb) == "PremioOReconocimiento"


def test_returns_none_when_no_keyword_matches():
    kb = load_kb()
    assert infer_event_type("Un texto sin ninguna palabra clave reconocible", kb) is None


def test_deterministic_same_text_same_result():
    kb = load_kb()
    text = "ANAC publica los resultados financieros del mes"
    assert infer_event_type(text, kb) == infer_event_type(text, kb)
