"""Formular-Katalog (12 Formulare für den kompletten Beratungsprozess)."""
from __future__ import annotations

from typing import Any

from app.forms import checklisten, datenblaetter, nachweise, stammdaten, vertraege
from app.forms._dsl import (clean, defaults, field_keys, input_fields, is_shared,
                            missing_required, shared_keys)

_ALL = (stammdaten.FORMS + datenblaetter.FORMS + checklisten.FORMS + nachweise.FORMS
        + vertraege.FORMS)
REGISTRY: dict[str, dict[str, Any]] = {f["key"]: f for f in sorted(_ALL, key=lambda f: f["nr"])}

AUDIENCE_LABEL = {"kunde": "Kunde", "berater": "Energieberater", "fachunternehmen":
                  "Fachunternehmen"}

# Empfohlene Pakete für neue Vorgänge.
PAKETE: dict[str, list[str]] = {
    "iSFP / Energieberatung": ["stammdaten_eigentuemer", "stammdaten_gebaeude", "datenblatt_a",
                               "datenblatt_b", "checkliste_ebw"],
    "BEG EM Gebäudehülle": ["stammdaten_eigentuemer", "stammdaten_gebaeude",
                            "checkliste_beg_em", "vertrag_beg_em", "fue_gebaeudehuelle"],
    "Heizungstausch": ["stammdaten_eigentuemer", "stammdaten_gebaeude",
                       "checkliste_heizungstausch", "vertrag_heizung", "fue_heizungstechnik"],
    "Mehrfamilienhaus / WEG": ["stammdaten_eigentuemer", "stammdaten_gebaeude", "datenblatt_c",
                               "datenblatt_b", "checkliste_ebw"],
}


def get(key: str) -> dict[str, Any] | None:
    return REGISTRY.get(key)


def catalog() -> list[dict[str, Any]]:
    return [{k: f[k] for k in ("key", "nr", "title", "short", "audience", "category",
                               "description", "version")}
            | {"audience_label": AUDIENCE_LABEL[f["audience"]],
               "anzahl_felder": len(input_fields(f))}
            for f in REGISTRY.values()]


def merged_data(form: dict[str, Any], data: dict[str, Any],
                stammdaten: dict[str, Any]) -> dict[str, Any]:
    """Formularwerte + vorgangsweite Stammdaten (+ Defaults) für die Anzeige."""
    out = defaults(form)
    for k in shared_keys(form):
        if stammdaten.get(k) not in (None, "", []):
            out[k] = stammdaten[k]
    for k, v in data.items():
        if v is not None:
            out[k] = v
    return out


def split_shared(form: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    keys = shared_keys(form)
    return {k: v for k, v in data.items() if k in keys and v not in (None, "", [])}


__all__ = ["REGISTRY", "PAKETE", "get", "catalog", "merged_data", "split_shared", "clean",
           "missing_required", "field_keys", "input_fields", "is_shared"]
