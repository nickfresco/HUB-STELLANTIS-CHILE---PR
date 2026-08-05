import os
from pathlib import Path

import pytest

from email_delivery.config import (
    EmailConfig,
    EmailConfigError,
    MissingCredentialError,
    load_email_config,
)
from email_delivery.mailer import build_email_message, build_plain_text_summary, send_email
from tests.helpers.fake_smtp_server import FakeSMTPServer

BASE_DIR = Path(__file__).parent.parent
REAL_CONFIG_PATH = BASE_DIR / "config" / "email_config.yaml"


# ---------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------

def test_loads_real_email_config_without_errors():
    config = load_email_config(REAL_CONFIG_PATH)
    assert config.smtp_host == "smtp.gmail.com"
    assert config.smtp_port == 587
    assert config.use_tls is True
    assert len(config.recipients) >= 1


def test_email_config_never_contains_a_literal_password():
    """Verificación explícita del requisito de seguridad: el archivo
    de configuración committeado no debe contener nada que parezca una
    contraseña real — solo nombres de variables de entorno."""
    raw_text = REAL_CONFIG_PATH.read_text(encoding="utf-8")
    assert "password:" not in raw_text.lower()
    assert "PR_HUB_SMTP_PASSWORD" in raw_text  # el nombre de la variable sí debe estar


def test_missing_required_field_raises_config_error(tmp_path):
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("smtp_host: 'smtp.example.com'\n", encoding="utf-8")  # falta sender_email, recipients
    with pytest.raises(EmailConfigError):
        load_email_config(bad_config)


def test_empty_recipients_list_raises_config_error(tmp_path):
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text(
        "smtp_host: 'smtp.example.com'\nsender_email: 'a@b.com'\nrecipients: []\n", encoding="utf-8"
    )
    with pytest.raises(EmailConfigError):
        load_email_config(bad_config)


def test_resolve_username_raises_when_env_var_missing(monkeypatch):
    config = EmailConfig(
        smtp_host="smtp.example.com", smtp_port=587, use_tls=True,
        sender_email="a@b.com", sender_name="PR HUB", recipients=["c@d.com"],
        subject_template="Test {fecha}",
        username_env_var="PR_HUB_TEST_USER_NOT_SET",
        password_env_var="PR_HUB_TEST_PASS_NOT_SET",
    )
    monkeypatch.delenv("PR_HUB_TEST_USER_NOT_SET", raising=False)
    with pytest.raises(MissingCredentialError):
        config.resolve_username()


def test_resolve_username_and_password_read_from_env(monkeypatch):
    config = EmailConfig(
        smtp_host="smtp.example.com", smtp_port=587, use_tls=True,
        sender_email="a@b.com", sender_name="PR HUB", recipients=["c@d.com"],
        subject_template="Test {fecha}",
        username_env_var="PR_HUB_TEST_USER",
        password_env_var="PR_HUB_TEST_PASS",
    )
    monkeypatch.setenv("PR_HUB_TEST_USER", "usuario_de_prueba")
    monkeypatch.setenv("PR_HUB_TEST_PASS", "clave_de_prueba")
    assert config.resolve_username() == "usuario_de_prueba"
    assert config.resolve_password() == "clave_de_prueba"


# ---------------------------------------------------------------------
# Construcción del mensaje MIME
# ---------------------------------------------------------------------

def _sample_config(**overrides):
    base = dict(
        smtp_host="localhost", smtp_port=25, use_tls=False,
        sender_email="prhub@example.com", sender_name="PR HUB",
        recipients=["coordinador@example.com"],
        subject_template="PR HUB — Daily Brief {fecha}",
        username_env_var="PR_HUB_TEST_USER", password_env_var="PR_HUB_TEST_PASS",
    )
    base.update(overrides)
    return EmailConfig(**base)


def test_build_email_message_has_html_and_plain_text_parts():
    config = _sample_config()
    message = build_email_message(
        html_content="<html><body><h1>Hola</h1></body></html>",
        plain_text="Hola en texto plano",
        config=config,
        fecha="04-08-2026",
    )
    assert message.is_multipart()
    html_part = message.get_body(preferencelist=("html",))
    text_part = message.get_body(preferencelist=("plain",))
    assert html_part is not None
    assert text_part is not None
    assert "<h1>Hola</h1>" in html_part.get_content()
    assert "Hola en texto plano" in text_part.get_content()


def test_build_email_message_subject_and_headers():
    config = _sample_config(recipients=["a@x.com", "b@y.com"])
    message = build_email_message("<p>x</p>", "x", config, fecha="04-08-2026")
    assert message["Subject"] == "PR HUB — Daily Brief 04-08-2026"
    assert "prhub@example.com" in message["From"]
    assert "a@x.com" in message["To"]
    assert "b@y.com" in message["To"]


def test_build_plain_text_summary_includes_executive_summary():
    digest = {
        "meta": {"fecha_legible": "martes 4 de agosto de 2026"},
        "resumen_ejecutivo": ["Se procesaron 5 noticias hoy.", "Sin alertas de prioridad alta."],
        "counts": {"flash_alerts": 0, "stellantis": 2, "competencia": 1, "industria": 2, "oportunidades": 1},
    }
    text = build_plain_text_summary(digest)
    assert "Se procesaron 5 noticias hoy." in text
    assert "Flash Alerts: 0" in text
    assert "Oportunidades: 1" in text


# ---------------------------------------------------------------------
# Envío real por SMTP (contra un servidor real, no un mock)
# ---------------------------------------------------------------------

@pytest.fixture
def fake_smtp_server():
    server = FakeSMTPServer()
    server.start()
    yield server
    server.stop()


def test_send_email_real_smtp_conversation(fake_smtp_server, monkeypatch):
    """El test central del módulo: usa smtplib de verdad (no un mock)
    para completar una conversación SMTP real contra un servidor real,
    y confirma que el contenido exacto llegó."""
    monkeypatch.setenv("PR_HUB_TEST_USER", "usuario_de_prueba")
    monkeypatch.setenv("PR_HUB_TEST_PASS", "clave_de_prueba")

    config = _sample_config(
        smtp_host=fake_smtp_server.host,
        smtp_port=fake_smtp_server.port,
        use_tls=False,
        recipients=["coordinador@example.com"],
    )
    message = build_email_message(
        html_content="<html><body><h1>Daily Brief real</h1></body></html>",
        plain_text="Daily Brief real (texto plano)",
        config=config,
        fecha="04-08-2026",
    )

    send_email(message, config)

    assert len(fake_smtp_server.received_messages) == 1
    received = fake_smtp_server.received_messages[0]
    assert "prhub@example.com" in received["mail_from"]
    assert any("coordinador@example.com" in r for r in received["rcpt_to"])
    assert "Daily Brief real" in received["data"]  # el HTML llegó de verdad, vía SMTP real
    assert "Daily Brief real (texto plano)" in received["data"]  # y el texto plano también


def test_send_email_raises_missing_credential_before_connecting(fake_smtp_server, monkeypatch):
    """Si faltan las credenciales, no debe intentar conectar siquiera
    — la validación ocurre antes del socket."""
    monkeypatch.delenv("PR_HUB_TEST_USER", raising=False)
    monkeypatch.delenv("PR_HUB_TEST_PASS", raising=False)

    config = _sample_config(smtp_host=fake_smtp_server.host, smtp_port=fake_smtp_server.port, use_tls=False)
    message = build_email_message("<p>x</p>", "x", config, fecha="04-08-2026")

    with pytest.raises(MissingCredentialError):
        send_email(message, config)

    assert fake_smtp_server.received_messages == []  # no llegó nada


def test_send_email_to_multiple_recipients(fake_smtp_server, monkeypatch):
    monkeypatch.setenv("PR_HUB_TEST_USER", "usuario_de_prueba")
    monkeypatch.setenv("PR_HUB_TEST_PASS", "clave_de_prueba")

    config = _sample_config(
        smtp_host=fake_smtp_server.host, smtp_port=fake_smtp_server.port, use_tls=False,
        recipients=["uno@example.com", "dos@example.com"],
    )
    message = build_email_message("<p>x</p>", "x", config, fecha="04-08-2026")
    send_email(message, config)

    received = fake_smtp_server.received_messages[0]
    all_rcpt = " ".join(received["rcpt_to"])
    assert "uno@example.com" in all_rcpt
    assert "dos@example.com" in all_rcpt
