"""
Etiquetas y plantillas de texto usadas por el Daily HTML.

Todo aquí es determinístico: diccionarios fijos, sin IA ni generación
de texto libre. No es una regla de negocio nueva (no toca prioridad ni
recomendación) — es únicamente lenguaje de presentación para que las
secciones Competencia, Industria y Oportunidades PR se lean redactadas
por una persona, no como un volcado de datos.

TODO (deuda técnica): estas plantillas son deliberadamente genéricas
por event_type. Cuando exista un Prompt Maestro real (Parte 4) que
redacte esto con contexto completo de cada noticia, estas plantillas
dejan de ser necesarias.
"""

from __future__ import annotations
from typing import Dict, Optional

# Texto de exhibición para cada RecommendationAction del catálogo
# (Parte 2B, sección 5.6). No agrega valores nuevos al catálogo, solo
# los traduce a una frase legible.
ACTION_LABELS: Dict[str, str] = {
    "EvaluarComunicado": "Evaluar comunicado oficial",
    "EvaluarQyA": "Preparar Q&A para prensa",
    "EvaluarComiteDeCrisis": "Convocar comité de crisis",
    "InformarBrandManager": "Informar a Brand Manager",
    "EvaluarPlanDeDifusion": "Evaluar plan de difusión / adaptación local",
    "CompartirAnalisisCompetitivo": "Compartir benchmark competitivo con el equipo",
    "MonitorearEvolucion": "Monitorear evolución",
    "EvaluarOportunidadDeContenido": "Proponer contenido Always On",
    "SinAccionInmediata": "Sin acción inmediata",
}

# Subconjunto de acciones que se muestran en "Oportunidades PR" — se
# excluyen las pasivas (SinAccionInmediata, MonitorearEvolucion) porque
# la sección pide "oportunidades accionables", no el listado completo
# de recomendaciones.
OPPORTUNITY_ACTIONS = {
    "EvaluarComunicado",
    "EvaluarQyA",
    "EvaluarPlanDeDifusion",
    "CompartirAnalisisCompetitivo",
    "EvaluarOportunidadDeContenido",
    "InformarBrandManager",
    "EvaluarComiteDeCrisis",
}

# "¿Por qué es un benchmark útil?" — una frase por EventType, para la
# sección Competencia. Sin nombre de marca (se antepone aparte).
BENCHMARK_TEMPLATES: Dict[str, str] = {
    "Lanzamiento": "Sirve como referencia de posicionamiento y mensaje de producto en el segmento.",
    "Campana": "Vale la pena analizar el mecanismo de la campaña: qué earned media generó y si es replicable.",
    "ResultadoFinanciero": "Da contexto sobre participación de mercado y presión competitiva real en Chile.",
    "InnovacionTecnologica": "Marca el estándar de conversación técnica que la prensa espera del segmento.",
    "PremioOReconocimiento": "Referencia útil para calibrar qué atributos está premiando la prensa especializada.",
    "AlianzaOAcuerdoComercial": "Puede anticipar movimientos de distribución o financiamiento relevantes para el mercado.",
    "ResultadoDeportivo": "Aporta contexto de la estrategia de marca vía motorsport del competidor.",
    "TendenciaDeMercado": "Ayuda a entender hacia dónde se mueve la conversación de industria.",
}
DEFAULT_BENCHMARK_TEXT = "Movimiento de la competencia a monitorear; sin patrón de benchmark predefinido para este tipo de evento."

# "¿Por qué importa para Stellantis?" — una frase por EventType, para
# la sección Industria (noticias sin marca ni competidor asociado).
INDUSTRY_TEMPLATES: Dict[str, str] = {
    "RegulacionOPoliticaPublica": "Cambios regulatorios afectan directamente costos, homologación o incentivos del portafolio Stellantis.",
    "ResultadoFinanciero": "El desempeño agregado del mercado es el contexto contra el que se leen los resultados propios.",
    "TendenciaDeMercado": "Las tendencias de industria anticipan qué preguntas hará la prensa especializada.",
    "IniciativaESG": "La agenda de sustentabilidad del sector es un tema recurrente en la conversación pública del rubro.",
    "InnovacionTecnologica": "Referencia del nivel de innovación que el mercado chileno empieza a esperar como estándar.",
    "InvestigacionOficial": "Investigaciones sectoriales pueden anticipar el escrutinio regulatorio futuro para toda la industria.",
}
DEFAULT_INDUSTRY_TEXT = "Contexto general de industria relevante para el panorama competitivo del día."


def action_label(action: str) -> str:
    return ACTION_LABELS.get(action, action)


def benchmark_text(event_type: Optional[str]) -> str:
    if event_type is None:
        return DEFAULT_BENCHMARK_TEXT
    return BENCHMARK_TEMPLATES.get(event_type, DEFAULT_BENCHMARK_TEXT)


def industry_text(event_type: Optional[str]) -> str:
    if event_type is None:
        return DEFAULT_INDUSTRY_TEXT
    return INDUSTRY_TEMPLATES.get(event_type, DEFAULT_INDUSTRY_TEXT)
