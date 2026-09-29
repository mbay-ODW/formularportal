"""Formular-Katalog für den kompletten Beratungs- und Förderprozess."""
from __future__ import annotations

import copy
import re
from typing import Any

from app.forms import (auftrag, checklisten, datenblaetter, nachweise, stammdaten, umsetzung,
                       vertraege)
from app.forms._dsl import (clean, defaults, field_keys, input_fields, is_shared,
                            missing_required, shared_keys)

_ALL = (stammdaten.FORMS + datenblaetter.FORMS + checklisten.FORMS + nachweise.FORMS
        + vertraege.FORMS + auftrag.FORMS + umsetzung.FORMS)
REGISTRY: dict[str, dict[str, Any]] = {f["key"]: f for f in sorted(_ALL, key=lambda f: f["nr"])}

AUDIENCE_LABEL = {"kunde": "Kunde", "berater": "Energieberater", "fachunternehmen":
                  "Fachunternehmen"}

# Empfohlene Pakete für neue Vorgänge.
_START = ["beratungsvertrag", "datenschutz_einwilligung", "stammdaten_eigentuemer",
          "stammdaten_gebaeude"]
PAKETE: dict[str, list[str]] = {
    "iSFP / Energieberatung": _START + ["vollmacht_datenabfrage", "datenblatt_a", "datenblatt_b",
                                        "checkliste_ebw", "abschluss_isfp"],
    "BEG EM Gebäudehülle": _START + ["checkliste_beg_em", "vertrag_beg_em",
                                     "protokoll_baubegleitung", "fue_gebaeudehuelle"],
    "Fenstertausch (BEG EM)": _START + ["checkliste_beg_em", "vertrag_beg_em",
                                        "kenntnisnahme_lueftung", "fue_gebaeudehuelle"],
    "Heizungstausch": _START + ["checkliste_heizungstausch", "vertrag_heizung",
                                "fue_heizungstechnik"],
    "Mehrfamilienhaus / WEG": _START + ["vollmacht_datenabfrage", "datenblatt_c", "datenblatt_b",
                                        "checkliste_ebw", "abschluss_isfp"],
    "Energieausweis": ["beratungsvertrag", "datenschutz_einwilligung",
                       "datenerhebung_energieausweis"],
}


_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def _fill(text: str, values: dict[str, str]) -> str:
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(1)) or "…", text)


def get(key: str, settings: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Formular-Definition; mit ``settings`` werden {{platzhalter}} in Info-Texten ersetzt."""
    form = REGISTRY.get(key)
    if form is None or settings is None:
        return form
    values = {k: str(v or "") for k, v in settings.items()}
    values["anschrift"] = ", ".join(x for x in [values.get("strasse"), values.get("plz_ort")]
                                    if x)
    out = copy.deepcopy(form)
    for sec in out["sections"]:
        for f in sec["fields"]:
            if f["type"] == "info" and "{{" in f.get("text", ""):
                f["text"] = _fill(f["text"], values)
    return out


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
