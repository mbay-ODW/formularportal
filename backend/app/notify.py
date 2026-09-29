"""Benachrichtigungen: SMTP-Mail (mit PDF-Anhang) und optional ntfy-Push.

Beides ist optional – ohne Konfiguration wird still übersprungen und das
Ergebnis im Ereignisprotokoll vermerkt.
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import httpx

from app import config

log = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(config.SMTP_HOST and config.SMTP_FROM)


def send_mail(to: str, subject: str, body: str, *, reply_to: str = "", from_name: str = "",
              attachments: list[tuple[str, bytes, str]] | None = None) -> None:
    if not smtp_configured():
        raise RuntimeError("SMTP ist nicht konfiguriert (FP_SMTP_HOST/FP_SMTP_FROM).")
    msg = EmailMessage()
    msg["From"] = formataddr((from_name, config.SMTP_FROM)) if from_name else config.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid()
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    for name, data, mime in attachments or []:
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)
    ctx = ssl.create_default_context()
    if config.SMTP_SECURITY == "ssl":
        with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, context=ctx, timeout=30) as s:
            _login_send(s, msg)
    else:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as s:
            if config.SMTP_SECURITY == "starttls":
                s.starttls(context=ctx)
            _login_send(s, msg)


def _login_send(s: smtplib.SMTP, msg: EmailMessage) -> None:
    if config.SMTP_USER:
        s.login(config.SMTP_USER, config.SMTP_PASSWORD)
    s.send_message(msg)


def ntfy_configured() -> bool:
    return bool(config.NTFY_URL and config.NTFY_TOPIC)


def push(title: str, message: str, click: str = "") -> None:
    if not ntfy_configured():
        return
    # Titel als Query-Parameter, damit Umlaute sauber ankommen (Header sind ASCII).
    params = {"title": title, "tags": "memo"}
    if click:
        params["click"] = click
    headers = {"Authorization": f"Bearer {config.NTFY_TOKEN}"} if config.NTFY_TOKEN else {}
    try:
        httpx.post(f"{config.NTFY_URL}/{config.NTFY_TOPIC}", content=message.encode("utf-8"),
                   params=params, headers=headers, timeout=10)
    except httpx.HTTPError as e:  # Push ist nice-to-have
        log.warning("ntfy fehlgeschlagen: %s", e)
