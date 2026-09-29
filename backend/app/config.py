"""Laufzeit-Konfiguration ausschließlich über Umgebungsvariablen.

Secrets (HERO-Token, SMTP-Passwort, interner API-Key) kommen aus dem
Portainer-Stack-Env und gehören nie ins Repo.
"""
from __future__ import annotations

import os
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None or v == "":
        return default
    return v.strip().lower() in ("1", "true", "yes", "ja", "on")


DATA_DIR = Path(os.environ.get("FP_DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "formularportal.sqlite3"

# Öffentliche Basis-URL für Kundenlinks (z. B. https://formulare.example.de).
PUBLIC_BASE_URL = os.environ.get("FP_PUBLIC_BASE_URL", "http://localhost:8090").rstrip("/")

# Admin-Schutz im Backend (zusätzlich zu Authelia vor dem Admin-Router):
#   "off"    – lokale Entwicklung, keine Prüfung
#   "header" – Admin-Endpunkte verlangen X-Portal-Zone: admin (setzt Traefik
#              nur auf dem Authelia-geschützten Router) ODER den internen
#              API-Key als Bearer (MCP-Container).
ADMIN_GUARD = os.environ.get("FP_ADMIN_GUARD", "off").strip().lower()
INTERNAL_API_KEY = os.environ.get("FP_INTERNAL_API_KEY", "")

# Kundenlinks laufen nach N Tagen ab (0 = nie).
LINK_TTL_DAYS = int(os.environ.get("FP_LINK_TTL_DAYS", "120") or 0)

# HERO (optional): Import von Kunden/Projekten + Upload fertiger PDFs.
HERO_GRAPHQL_URL = os.environ.get(
    "FP_HERO_URL", "https://login.hero-software.de/api/external/v7/graphql"
)
HERO_UPLOAD_URL = os.environ.get(
    "FP_HERO_UPLOAD_URL", "https://login.hero-software.de/app/v8/FileUploads/upload"
)
HERO_TOKEN = os.environ.get("FP_HERO_TOKEN", "")
# document_type_id für upload_document; 551120 = "Allgemein".
HERO_DOCUMENT_TYPE_ID = int(os.environ.get("FP_HERO_DOCUMENT_TYPE_ID", "551120") or 551120)
# Eingereichte Formulare automatisch ins verknüpfte HERO-Projekt hochladen.
HERO_AUTO_UPLOAD = _bool("FP_HERO_AUTO_UPLOAD", False)

# SMTP (optional): Benachrichtigung bei Einreichung + Link-Versand an Kunden.
SMTP_HOST = os.environ.get("FP_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("FP_SMTP_PORT", "587") or 587)
SMTP_USER = os.environ.get("FP_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("FP_SMTP_PASSWORD", "")
SMTP_FROM = os.environ.get("FP_SMTP_FROM", "")
SMTP_SECURITY = os.environ.get("FP_SMTP_SECURITY", "starttls").strip().lower()  # starttls|ssl|none

# ntfy (optional): Push bei Einreichung.
NTFY_URL = os.environ.get("FP_NTFY_URL", "").rstrip("/")
NTFY_TOPIC = os.environ.get("FP_NTFY_TOPIC", "")
NTFY_TOKEN = os.environ.get("FP_NTFY_TOKEN", "")

# Obergrenzen gegen Missbrauch der öffentlichen Endpunkte.
MAX_FORM_PAYLOAD_BYTES = int(os.environ.get("FP_MAX_FORM_PAYLOAD_BYTES", str(3 * 1024 * 1024)))
MAX_LOGO_BYTES = 2 * 1024 * 1024
