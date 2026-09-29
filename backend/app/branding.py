"""Branding/Einstellungen: Firmenkopf für Portal und PDFs, Logo im Daten-Volume."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app import config

SETTINGS_FILE = "einstellungen.json"
_LOGO_EXTS = (".png", ".jpg", ".jpeg")
DEFAULT_LOGO = Path(__file__).parent / "assets" / "logo_default.png"

# Vorbelegung = GEB-CI (Petrol/Grün/Navy). Alles im UI änderbar.
DEFAULTS: dict[str, Any] = {
    "firma": "Energieberatung Odenwaldkreis",
    "inhaber": "",
    "zusatz": "Energieeffizienz-Experte für Förderprogramme des Bundes",
    "strasse": "",
    "plz_ort": "",
    "telefon": "",
    "email": "",
    "website": "",
    "farbe_primaer": "#0b6e7f",
    "farbe_akzent": "#3fa535",
    "farbe_text": "#0e2a40",
    "benachrichtigung_email": "",
    "kopie_an_kunde": "ja",
    "portal_begruessung": "Vielen Dank für Ihr Vertrauen. Bitte füllen Sie die folgenden "
                          "Formulare aus – Ihre Eingaben werden automatisch gespeichert.",
    "fusszeile": "",
}

_HEX = "0123456789abcdefABCDEF"


def _path() -> Path:
    return config.DATA_DIR / SETTINGS_FILE


def load() -> dict[str, Any]:
    out = dict(DEFAULTS)
    p = _path()
    if p.exists():
        try:
            out.update(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return out


def save(partial: dict[str, Any]) -> dict[str, Any]:
    cur = load()
    for k, v in partial.items():
        if k not in DEFAULTS or v is None:
            continue
        v = str(v).strip()[:1000]
        if k.startswith("farbe_") and not (len(v) == 7 and v[0] == "#" and all(c in _HEX
                                                                             for c in v[1:])):
            continue
        cur[k] = v
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _path().write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur


def public(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    s = settings or load()
    keys = ("firma", "inhaber", "zusatz", "strasse", "plz_ort", "telefon", "email", "website",
            "farbe_primaer", "farbe_akzent", "farbe_text", "portal_begruessung", "fusszeile")
    return {k: s.get(k, "") for k in keys} | {"logo_url": "/api/public/logo"}


# ---- Logo ---------------------------------------------------------------------
def logo_path() -> Path:
    for ext in _LOGO_EXTS:
        p = config.DATA_DIR / f"logo{ext}"
        if p.exists():
            return p
    return DEFAULT_LOGO


def has_custom_logo() -> bool:
    return logo_path() != DEFAULT_LOGO


def save_logo(data: bytes, filename: str) -> Path:
    ext = Path(filename or "").suffix.lower()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        ext = ".png"
    elif data[:3] == b"\xff\xd8\xff":
        ext = ".jpg"
    if ext not in _LOGO_EXTS:
        raise ValueError("Nur PNG oder JPG erlaubt.")
    delete_logo()
    p = config.DATA_DIR / f"logo{ext}"
    p.write_bytes(data)
    return p


def delete_logo() -> None:
    for ext in _LOGO_EXTS:
        (config.DATA_DIR / f"logo{ext}").unlink(missing_ok=True)
