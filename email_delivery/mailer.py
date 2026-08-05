"""
Email Delivery — construcción del mensaje y envío por SMTP.

daily/html_renderer.py ya produce HTML "email-safe" (tablas + estilos
inline, pensado desde el Sprint 4 para Gmail/Outlook) — este módulo no
vuelve a tocar ese HTML. Su único trabajo es empaquetarlo en un mensaje
MIME válido (multipart/alternative: texto plano + HTML, el estándar
para que un cliente sin soporte HTML igual reciba algo legible) y
entregarlo por SMTP.

Nada de esto usa IA ni genera contenido — el texto plano es una
plantilla determinística derivada del mismo `digest` que ya arma
daily/aggregator.py, y el envío es smtplib de la librería estándar.
"""

from __future__ import annotations
import smtplib
from email.message import EmailMessage
from typing import Any, Dict

from email_delivery.config import EmailConfig


def build_plain_text_summary(digest: Dict[str, Any]) -> str:
    """Versión de texto plano del Daily Brief — no es el brief
    completo, es un resumen suficiente para un cliente de correo sin
    soporte HTML, con una nota explícita de que la versión completa
    está en la parte HTML del mismo mensaje."""
    meta = digest["meta"]
    counts = digest["counts"]
    lines = [
        f"PR HUB — Daily Brief — {meta.get('fecha_legible', '')}",
        "",
        "Resumen ejecutivo:",
    ]
    for bullet in digest.get("resumen_ejecutivo", []):
        lines.append(f"  - {bullet}")
    lines += [
        "",
        f"Flash Alerts: {counts['flash_alerts']}  |  Stellantis: {counts['stellantis']}  |  "
        f"Competencia: {counts['competencia']}  |  Industria: {counts['industria']}  |  "
        f"Oportunidades: {counts['oportunidades']}",
        "",
        "Este correo incluye la versión completa en HTML. Si tu cliente de "
        "correo no la muestra, abre daily_brief.html directamente.",
    ]
    return "\n".join(lines)


def build_email_message(html_content: str, plain_text: str, config: EmailConfig, fecha: str) -> EmailMessage:
    """Arma un mensaje multipart/alternative — texto plano primero,
    HTML después (orden estándar: los clientes de correo muestran la
    última alternativa que sepan renderizar, que debe ser la más rica)."""
    message = EmailMessage()
    message["Subject"] = config.subject_template.format(fecha=fecha)
    message["From"] = f"{config.sender_name} <{config.sender_email}>"
    message["To"] = ", ".join(config.recipients)
    message.set_content(plain_text)
    message.add_alternative(html_content, subtype="html")
    return message


def send_email(message: EmailMessage, config: EmailConfig, timeout: int = 30) -> None:
    """Envía el mensaje por SMTP real. Lanza MissingCredentialError
    (desde config.resolve_username/resolve_password) si faltan las
    variables de entorno — nunca intenta login con credenciales
    vacías."""
    username = config.resolve_username()
    password = config.resolve_password()

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=timeout) as smtp:
        smtp.ehlo()
        if config.use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)
