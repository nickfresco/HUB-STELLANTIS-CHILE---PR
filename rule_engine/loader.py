"""
Rule Loader — carga un archivo de reglas (YAML) y lo convierte en
objetos Rule validados.

Una regla mal formada se rechaza individualmente (con warning), sin
abortar la carga completa del archivo, conforme a la Parte 5, sección 3
("ningún componente asume la responsabilidad de otro") y al principio
de resiliencia general del proyecto.
"""

from __future__ import annotations
import warnings
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from rule_engine.rules import Rule

REQUIRED_FIELDS = {"id", "condition", "outcome"}


class RuleLoadError(ValueError):
    pass


def load_rulebook(path: str | Path, rules_key: str) -> Tuple[str, List[Rule]]:
    """Carga un archivo de reglas.

    Args:
        path: ruta al archivo YAML.
        rules_key: nombre de la clave de nivel superior que contiene la
            lista de reglas (ej. "priority_rules", "recommendation_rules").
            El motor no asume ningún nombre fijo — quien lo invoca lo
            declara, manteniendo el motor agnóstico de dominio.

    Returns:
        (version, lista de Rule válidas)
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or rules_key not in raw:
        raise RuleLoadError(f"El archivo {path} no contiene la clave '{rules_key}'")

    version = raw.get("version", "0.0.0")
    rules: List[Rule] = []

    for i, entry in enumerate(raw[rules_key]):
        try:
            rules.append(_parse_rule(entry))
        except RuleLoadError as e:
            warnings.warn(f"[{path.name}] Regla #{i} rechazada: {e}")

    return version, rules


def _parse_rule(entry: Dict[str, Any]) -> Rule:
    missing = REQUIRED_FIELDS - entry.keys()
    if missing:
        raise RuleLoadError(f"faltan campos obligatorios {missing} en {entry!r}")

    return Rule(
        id=entry["id"],
        condition=entry["condition"],
        outcome=entry["outcome"],
        priority_weight=entry.get("priority_weight", 0),
        enabled=entry.get("enabled", True),
        description=entry.get("description"),
        todo=entry.get("todo"),
    )
