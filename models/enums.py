"""
Catálogos cerrados de dominio (Parte 2B, sección 5). Se definen como
constantes simples (no Enum de Python) para que el mapeo 1:1 con el
YAML sea directo y no requiera conversión de tipos al leer/escribir.
"""

PRIORITY_LEVELS = ["Critical", "High", "Medium", "Low"]

RECOMMENDATION_ACTIONS = [
    "EvaluarComunicado",
    "EvaluarQyA",
    "EvaluarComiteDeCrisis",
    "InformarBrandManager",
    "EvaluarPlanDeDifusion",
    "CompartirAnalisisCompetitivo",
    "MonitorearEvolucion",
    "EvaluarOportunidadDeContenido",
    "SinAccionInmediata",
]

# TODO (deuda técnica, Parte 3): esta es una simplificación de las 10
# secciones reales del Daily Brief. El MVP solo asigna UNA sección por
# noticia, sin las reglas completas de selección/diversidad de la
# Parte 3. Suficiente para validar el flujo de punta a punta.
DAILY_BRIEF_SECTIONS = [
    "Riesgos reputacionales",
    "Resumen Ejecutivo",
    "Radar de noticias",
]
