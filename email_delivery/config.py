"""
Email Delivery — carga de configuración.

Principio de seguridad, no negociable: config/email_config.yaml NUNCA
contiene una contraseña ni un usuario real — solo el NOMBRE de la
variable de entorno donde vive cada uno. El valor en sí se lee del
entorno en tiempo de ejecución, nunca se escribe a disco, nunca se
commitea. Si la variable de entorno no está definida cuando hace falta,
se lanza un error explícito — no se envía nada con credenciales vacías
ni se asume un valor por defecto inseguro.
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml

DEFAULT_SMTP_PORT = 587
DEFAULT_SUBJECT_TEMPLATE = "PR HUB — Daily Brief {fecha}"
DEFAULT_USERNAME_ENV_VAR = "PR_HUB_SMTP_USERNAME"
DEFAULT_PASSWORD_ENV_VAR = "PR_HUB_SMTP_PASSWORD"


class EmailConfigError(ValueError):
    pass


class MissingCredentialError(EmailConfigError):
    """Se lanza cuando falta la variable de entorno de usuario o
    contraseña — nunca se envía un correo con credenciales vacías."""


@dataclass(frozen=True)
class EmailConfig:
    smtp_host: str
    smtp_port: int
    use_tls: bool
    sender_email: str
    sender_name: str
    recipients: List[str]
    subject_template: str
    username_env_var: str
    password_env_var: str

    def resolve_username(self) -> str:
        value = os.environ.get(self.username_env_var)
        if not value:
            raise MissingCredentialError(
                f"Falta la variable de entorno '{self.username_env_var}' "
                f"(usuario SMTP). No se envía ningún correo sin credenciales reales."
            )
        return value

    def resolve_password(self) -> str:
        value = os.environ.get(self.password_env_var)
        if not value:
            raise MissingCredentialError(
                f"Falta la variable de entorno '{self.password_env_var}' "
                f"(contraseña/App Password SMTP). No se envía ningún correo sin credenciales reales."
            )
        return value


def load_email_config(path: "str | Path") -> EmailConfig:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    required = {"smtp_host", "sender_email", "recipients"}
    missing = required - raw.keys()
    if missing:
        raise EmailConfigError(f"Faltan campos obligatorios en {path}: {missing}")

    recipients = raw["recipients"]
    if not isinstance(recipients, list) or not recipients:
        raise EmailConfigError(f"'recipients' debe ser una lista no vacía en {path}")

    return EmailConfig(
        smtp_host=raw["smtp_host"],
        smtp_port=int(raw.get("smtp_port", DEFAULT_SMTP_PORT)),
        use_tls=bool(raw.get("use_tls", True)),
        sender_email=raw["sender_email"],
        sender_name=raw.get("sender_name", "PR HUB"),
        recipients=recipients,
        subject_template=raw.get("subject_template", DEFAULT_SUBJECT_TEMPLATE),
        username_env_var=raw.get("username_env_var", DEFAULT_USERNAME_ENV_VAR),
        password_env_var=raw.get("password_env_var", DEFAULT_PASSWORD_ENV_VAR),
    )
