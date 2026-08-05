"""
Fake SMTP Server — servidor SMTP mínimo, solo para pruebas, que
permite verificar de verdad la conversación que hace smtplib (EHLO,
AUTH LOGIN, MAIL FROM, RCPT TO, DATA, QUIT) sin depender de un
servidor SMTP real ni de credenciales de nadie.

No es un mock de smtplib: es un servidor de socket real escuchando en
localhost. Lo que se prueba contra él es el mismo código
(email_delivery/mailer.py:send_email, que usa smtplib.SMTP tal cual)
que hablaría con Gmail — solo cambia el destino.

Limitación reconocida y documentada, no oculta: no implementa STARTTLS
(requeriría certificados TLS reales para probarse de verdad, no solo
simularse). Prueba la conversación SMTP en texto plano, que es la base
sobre la que STARTTLS agrega una capa de cifrado — la negociación TLS
en sí es código maduro de smtplib/ssl (librería estándar), no código
de este proyecto, así que no es lo que este test double necesita
volver a demostrar.
"""

from __future__ import annotations
import base64
import socket
import threading
from typing import List, Optional


class FakeSMTPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 0):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((host, port))
        self._socket.listen(1)
        self.host, self.port = self._socket.getsockname()
        self.received_messages: List[dict] = []
        self._thread: Optional[threading.Thread] = None
        self._stop = False

    def start(self) -> None:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop = True
        try:
            self._socket.close()
        except OSError:
            pass
        if self._thread:
            self._thread.join(timeout=2)

    def _serve(self) -> None:
        while not self._stop:
            try:
                conn, _ = self._socket.accept()
            except OSError:
                break
            try:
                self._handle(conn)
            except (ConnectionError, OSError):
                pass

    def _handle(self, conn: socket.socket) -> None:
        with conn:
            conn.sendall(b"220 fake-smtp.local ESMTP\r\n")
            mail_from = None
            rcpt_to: List[str] = []
            f = conn.makefile("rwb")

            while True:
                line = f.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").rstrip("\r\n")
                upper = text.upper()

                if upper.startswith("EHLO") or upper.startswith("HELO"):
                    conn.sendall(b"250-fake-smtp.local\r\n250 AUTH LOGIN\r\n")
                elif upper.startswith("STARTTLS"):
                    # No implementado a propósito (ver docstring del módulo).
                    conn.sendall(b"502 STARTTLS no soportado por este servidor de pruebas\r\n")
                elif upper.startswith("AUTH LOGIN"):
                    conn.sendall(b"334 " + base64.b64encode(b"Username:") + b"\r\n")
                    f.readline()  # usuario en base64 — no se valida, es servidor de pruebas
                    conn.sendall(b"334 " + base64.b64encode(b"Password:") + b"\r\n")
                    f.readline()  # contraseña en base64 — no se valida
                    conn.sendall(b"235 Authentication successful\r\n")
                elif upper.startswith("MAIL FROM"):
                    mail_from = text
                    conn.sendall(b"250 OK\r\n")
                elif upper.startswith("RCPT TO"):
                    rcpt_to.append(text)
                    conn.sendall(b"250 OK\r\n")
                elif upper.startswith("DATA"):
                    conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                    data_lines = []
                    while True:
                        data_line = f.readline()
                        if data_line in (b".\r\n", b".\n", b""):
                            break
                        data_lines.append(data_line)
                    conn.sendall(b"250 OK: message queued\r\n")
                    self.received_messages.append({
                        "mail_from": mail_from,
                        "rcpt_to": list(rcpt_to),
                        "data": b"".join(data_lines).decode("utf-8", errors="replace"),
                    })
                elif upper.startswith("QUIT"):
                    conn.sendall(b"221 Bye\r\n")
                    break
                else:
                    conn.sendall(b"250 OK\r\n")
