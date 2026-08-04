"""
PRHubPipeline — orquesta las etapas en el orden acordado. No contiene
lógica de negocio propia: solo construye el contexto inicial (resuelve
la Source desde la Knowledge Base, que es validación de entrada, no
una etapa del diagrama) y ejecuta las etapas en secuencia.
"""

from __future__ import annotations
from typing import Any, Dict, List, Protocol

from knowledge_base.loader import KnowledgeBase
from models.fact import NewsInput


class PipelineStage(Protocol):
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]: ...


class PRHubPipeline:
    def __init__(self, kb: KnowledgeBase, stages: List[PipelineStage]):
        self.kb = kb
        self.stages = stages

    def run(self, news_dict: Dict[str, Any]) -> Dict[str, Any]:
        news = NewsInput.from_dict(news_dict)

        source = self.kb.get_source(news.source_id)
        if source is None:
            raise ValueError(
                f"source_id '{news.source_id}' no existe en sources.yml. "
                f"Todo NewsInput debe referenciar una fuente ya registrada en la Knowledge Base."
            )

        context: Dict[str, Any] = {
            "news": news,
            "source": source,
            "text": f"{news.title} {news.summary}",
        }

        for stage in self.stages:
            context = stage.run(context)

        return context["output"]
