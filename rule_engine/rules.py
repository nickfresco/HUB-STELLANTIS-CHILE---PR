"""
Modelos de datos del Rule Engine genérico.

Nada aquí conoce PriorityLevel, RecommendationAction ni ningún concepto
del dominio automotriz/PR. Eso vive exclusivamente en los archivos YAML
que se cargan en tiempo de ejecución.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Rule:
    """Una regla genérica: condición -> resultado."""
    id: str
    condition: Dict[str, Any]
    outcome: Dict[str, Any]
    priority_weight: int = 0
    enabled: bool = True
    description: Optional[str] = None
    todo: Optional[str] = None  # deuda técnica declarada explícitamente en el YAML


@dataclass(frozen=True)
class Match:
    """Una coincidencia: una regla cuya condición evaluó verdadero."""
    rule_id: str
    outcome: Dict[str, Any]
    priority_weight: int


@dataclass
class EvaluationResult:
    """Resultado completo y auditable de evaluar un Rulebook contra un Fact."""
    fact_reference: str
    rulebook_version: str
    resolution_strategy: str
    matches: List[Match] = field(default_factory=list)
    winning_rule_id: Optional[str] = None
    final_outcome: Optional[Dict[str, Any]] = None

    def matched_rule_ids(self) -> List[str]:
        return [m.rule_id for m in self.matches]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_reference": self.fact_reference,
            "rulebook_version": self.rulebook_version,
            "resolution_strategy": self.resolution_strategy,
            "matches": [
                {"rule_id": m.rule_id, "outcome": m.outcome, "priority_weight": m.priority_weight}
                for m in self.matches
            ],
            "winning_rule_id": self.winning_rule_id,
            "final_outcome": self.final_outcome,
        }
