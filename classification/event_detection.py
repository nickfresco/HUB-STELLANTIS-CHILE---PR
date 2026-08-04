"""
Event Detection — inferencia determinística de EventType a partir de
palabras clave, usada únicamente cuando `event_type` no viene informado
en el input.

Sin IA, sin NLP probabilístico: un diccionario de keywords por
EventType (heurística documentada, no una regla de negocio del
Rulebook — es infraestructura de clasificación, análoga a un Taxonomy
Engine mínimo). Si ninguna keyword coincide, devuelve None de forma
explícita en vez de adivinar — es responsabilidad del llamador decidir
qué hacer ante un event_type no determinado (hoy: la noticia
simplemente no dispara ninguna regla que dependa de event_type).

TODO (deuda técnica): este diccionario de keywords es una aproximación
de MVP. Un Taxonomy Engine real (Parte 2A) debería vivir en
configuración (YAML), no hardcodeado en Python. Se deja aquí,
documentado, para no bloquear el MVP por una discusión de arquitectura
que ya se decidió posponer.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from knowledge_base.loader import KnowledgeBase

# Orden = orden de desempate cuando dos EventType empatan en cantidad
# de keywords encontradas (gana el primero de esta lista).
_EVENT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "Recall": ["recall", "retiro preventivo", "campaña preventiva", "falla de fábrica", "defecto de fabrica"],
    "ResultadoDeSeguridad": ["ncap", "prueba de choque", "resultado de seguridad", "crash test"],
    "DenunciaOControversia": ["denuncia", "demanda colectiva", "controversia", "reclamo de consumidor"],
    "InvestigacionOficial": ["investigación oficial", "abre investigación", "sumario"],
    "Lanzamiento": ["lanza", "lanzamiento", "presenta oficialmente", "debuta", "estreno"],
    "ActualizacionDeProducto": ["actualiza", "actualización de modelo", "rediseño", "nueva versión del"],
    "InnovacionTecnologica": ["innovación tecnológica", "nueva tecnología", "presenta tecnología"],
    "AlianzaOAcuerdoComercial": ["alianza", "acuerdo comercial", "joint venture", "sociedad estratégica"],
    "ResultadoFinanciero": ["resultados financieros", "ventas del mes", "participación de mercado", "ingresos"],
    "Campana": ["campaña publicitaria", "spot publicitario", "campaña de marketing"],
    "CoberturaEditorial": ["reseña", "test drive", "prueba de manejo", "análisis del modelo"],
    "PremioOReconocimiento": ["premio", "reconocimiento", "galardón", "distinción"],
    "ResultadoDeportivo": ["rally", "competencia deportiva", "motorsport", "carrera"],
    "IniciativaESG": ["sustentabilidad", "iniciativa esg", "responsabilidad social", "medioambiente"],
    "TendenciaDeMercado": ["tendencia de mercado", "panorama del mercado", "análisis de mercado"],
    "DeclaracionOVoceria": ["declaró", "declaración de", "entrevista con", "vocero", "afirmó"],
    "RegulacionOPoliticaPublica": ["nueva ley", "normativa", "arancel", "regulación", "incentivo tributario", "decreto"],
}


def infer_event_type(text: str, kb: KnowledgeBase) -> Optional[str]:
    """Devuelve el EventType con más keywords coincidentes en el texto,
    o None si ninguno coincide. Determinístico: mismo texto -> mismo
    resultado siempre."""
    text_lower = text.lower()
    best_event_type: Optional[str] = None
    best_count = 0

    for event_type in kb.event_types:
        keywords = _EVENT_TYPE_KEYWORDS.get(event_type, [])
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_event_type = event_type

    return best_event_type
