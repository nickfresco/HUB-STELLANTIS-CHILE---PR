"""
Knowledge Base Loader — carga brands.yml, competitors.yml,
organizations.yml, models.yml, technologies.yml, sources.yml,
taxonomy.yml y event_types.yml, y expone métodos de consulta.

Corresponde a: Parte 5, sección 3 (Config Engine) y sección 8
(inventario de archivos de configuración).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass(frozen=True)
class Entity:
    """Representación genérica de Brand / Competitor / Organization /
    Product — todas comparten la misma forma (Parte 2B, sección 3.3)."""
    canonical_id: str
    display_name: str
    aliases: List[Dict[str, Any]] = field(default_factory=list)
    active: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)  # market, monitoring_priority, competitive_priority, type, organization_type...


@dataclass(frozen=True)
class Source:
    canonical_id: str
    display_name: str
    tier: str
    type: str
    country: str
    acquisition_method: Optional[str] = None


class KnowledgeBase:
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.brands: List[Entity] = []
        self.competitors: List[Entity] = []
        self.organizations: List[Entity] = []
        self.models: List[Entity] = []
        self.technologies: List[Entity] = []
        self.sources: List[Source] = []
        self.categories: List[Dict[str, Any]] = []
        self.event_types: List[str] = []
        self._load_all()

    # ------------------------------------------------------------------
    # Carga
    # ------------------------------------------------------------------
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        path = self.base_path / filename
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_all(self) -> None:
        self.brands = self._load_entities("brands.yml", "brands")
        self.competitors = self._load_entities("competitors.yml", "competitors")
        self.organizations = self._load_entities("organizations.yml", "organizations")
        self.models = self._load_entities("models.yml", "models")
        self.technologies = self._load_entities("technologies.yml", "technologies")
        self.sources = self._load_sources("sources.yml")
        self.categories = self._load_yaml("taxonomy.yml")["categories"]
        self.event_types = [e["id"] for e in self._load_yaml("event_types.yml")["event_types"]]

    def _load_entities(self, filename: str, key: str) -> List[Entity]:
        raw = self._load_yaml(filename)
        entities = []
        known_fields = {"canonicalId", "displayName", "aliases", "active"}
        for item in raw.get(key, []):
            extra = {k: v for k, v in item.items() if k not in known_fields}
            entities.append(
                Entity(
                    canonical_id=item["canonicalId"],
                    display_name=item["displayName"],
                    aliases=item.get("aliases", []),
                    active=item.get("active", True),
                    extra=extra,
                )
            )
        return entities

    def _load_sources(self, filename: str) -> List[Source]:
        raw = self._load_yaml(filename)
        return [
            Source(
                canonical_id=item["canonicalId"],
                display_name=item["displayName"],
                tier=item["tier"],
                type=item["type"],
                country=item["country"],
                acquisition_method=item.get("acquisition_method"),
            )
            for item in raw.get("sources", [])
        ]

    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------
    def all_products(self) -> List[Entity]:
        return self.models + self.technologies

    def get_source(self, canonical_id: str) -> Optional[Source]:
        for s in self.sources:
            if s.canonical_id == canonical_id:
                return s
        return None

    def is_valid_event_type(self, event_type: str) -> bool:
        return event_type in self.event_types

    def stellantis_brand_ids(self) -> List[str]:
        return [b.canonical_id for b in self.brands if b.active]
