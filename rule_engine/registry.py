"""
Rule Registry — mantiene en memoria el conjunto de reglas cargadas
desde un Rulebook, junto con su versión.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

from rule_engine.loader import load_rulebook
from rule_engine.rules import Rule


class RuleRegistry:
    def __init__(self, version: str, rules: List[Rule]):
        self.version = version
        self._rules = rules

    @classmethod
    def from_yaml(cls, path: str | Path, rules_key: str) -> "RuleRegistry":
        version, rules = load_rulebook(path, rules_key)
        return cls(version, rules)

    def enabled_rules(self) -> List[Rule]:
        return [r for r in self._rules if r.enabled]

    def all_rules(self) -> List[Rule]:
        return list(self._rules)

    def pending_rules(self) -> List[Rule]:
        """Reglas registradas pero deshabilitadas (deuda técnica declarada)."""
        return [r for r in self._rules if not r.enabled]

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Utilitario de lookup por id (Sprint 4, usado para mostrar la
        descripción de la regla ganadora en el Daily HTML). No cambia
        el comportamiento de carga/evaluación existente."""
        for r in self._rules:
            if r.id == rule_id:
                return r
        return None

    def __len__(self) -> int:
        return len(self._rules)
