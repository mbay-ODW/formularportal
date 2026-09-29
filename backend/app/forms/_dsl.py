"""Kleine DSL für Formular-Definitionen + Auswertung (Sichtbarkeit, Pflichtfelder).

Eine Formular-Definition ist reines JSON (wird so auch ans Frontend und an den
MCP-Server ausgeliefert):

    {key, title, short, nr, audience, category, description, version,
     sections: [{title, intro?, show_if?, fields: [...]}]}

Feld: {key, type, label, required?, options?, hint?, unit?, width?, show_if?,
       columns? (table), default?}

Typen: text, textarea, number, date, email, tel, select, radio, checks (Mehrfach),
       yesno, check (einzelne Bestätigung), table, signature, info (nur Text).

show_if: {"field": key, "equals": wert} | {"field": key, "in": [...]}
         | {"field": key, "contains": wert}   (für checks-Felder)

Schlüssel mit Präfix ``eig_`` (Eigentümer/Antragsteller), ``obj_`` (Objekt) und
``fu_`` (Fachunternehmen) sind vorgangsweit geteilt: einmal erfasst, stehen sie in
allen weiteren Formularen desselben Vorgangs vorbefüllt zur Verfügung.
"""
from __future__ import annotations

from typing import Any, Iterable

SHARED_PREFIXES = ("eig_", "obj_", "fu_")
INPUT_TYPES = {"text", "textarea", "number", "date", "email", "tel", "select", "radio",
               "checks", "yesno", "check", "table", "signature"}


def is_shared(key: str, type_: str = "text") -> bool:
    """Vorgangsweit geteilt? Unterschriften und Einzelbestätigungen nie."""
    if type_ in ("signature", "check") or key.endswith("_unterschrift"):
        return False
    return key.startswith(SHARED_PREFIXES)


# ---- Feld-Konstruktoren -----------------------------------------------------
def _f(type_: str, key: str, label: str, **kw: Any) -> dict[str, Any]:
    d: dict[str, Any] = {"key": key, "type": type_, "label": label}
    for k, v in kw.items():
        if v is not None:
            d[k] = v
    return d


def text(key, label, **kw):
    return _f("text", key, label, **kw)


def area(key, label, **kw):
    return _f("textarea", key, label, **kw)


def num(key, label, unit=None, **kw):
    return _f("number", key, label, unit=unit, **kw)


def date(key, label, **kw):
    return _f("date", key, label, **kw)


def email(key, label, **kw):
    return _f("email", key, label, **kw)


def tel(key, label, **kw):
    return _f("tel", key, label, **kw)


def select(key, label, options, **kw):
    return _f("select", key, label, options=list(options), **kw)


def radio(key, label, options, **kw):
    return _f("radio", key, label, options=list(options), **kw)


def checks(key, label, options, **kw):
    return _f("checks", key, label, options=list(options), **kw)


def yesno(key, label, **kw):
    return _f("yesno", key, label, **kw)


def check(key, label, **kw):
    return _f("check", key, label, **kw)


def table(key, label, columns, min_rows=1, **kw):
    cols = [c if isinstance(c, dict) else {"key": c[0], "label": c[1]} for c in columns]
    return _f("table", key, label, columns=cols, min_rows=min_rows, **kw)


def col(key, label, type_="text", options=None, unit=None):
    d: dict[str, Any] = {"key": key, "label": label, "type": type_}
    if options:
        d["options"] = list(options)
    if unit:
        d["unit"] = unit
    return d


def sign(key, label, **kw):
    return _f("signature", key, label, **kw)


def info(key, text_, **kw):
    return _f("info", key, "", text=text_, **kw)


def sec(title, *fields, intro=None, show_if=None):
    d: dict[str, Any] = {"title": title, "fields": list(fields)}
    if intro:
        d["intro"] = intro
    if show_if:
        d["show_if"] = show_if
    return d


def when(field, equals=None, in_=None, contains=None):
    d: dict[str, Any] = {"field": field}
    if equals is not None:
        d["equals"] = equals
    if in_ is not None:
        d["in"] = list(in_)
    if contains is not None:
        d["contains"] = contains
    return d


def ort_datum(prefix: str = "") -> list[dict[str, Any]]:
    return [text(f"{prefix}ort_unterschrift", "Ort", width="half"),
            date(f"{prefix}datum_unterschrift", "Datum", width="half")]


# ---- Auswertung -------------------------------------------------------------
def iter_fields(form: dict[str, Any]) -> Iterable[tuple[dict, dict]]:
    for s in form["sections"]:
        for f in s["fields"]:
            yield s, f


def input_fields(form: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for _, f in iter_fields(form) if f["type"] in INPUT_TYPES]


def field_keys(form: dict[str, Any]) -> set[str]:
    return {f["key"] for f in input_fields(form)}


def shared_keys(form: dict[str, Any]) -> set[str]:
    return {f["key"] for f in input_fields(form) if is_shared(f["key"], f["type"])}


def cond_ok(cond: dict | None, data: dict[str, Any]) -> bool:
    if not cond:
        return True
    v = data.get(cond["field"])
    if "equals" in cond:
        return v == cond["equals"]
    if "in" in cond:
        return v in cond["in"]
    if "contains" in cond:
        return isinstance(v, list) and cond["contains"] in v
    return bool(v)


def is_empty(field: dict[str, Any], v: Any) -> bool:
    t = field["type"]
    if v is None:
        return True
    if t == "check":
        return v is not True
    if t in ("checks",):
        return not v
    if t == "table":
        if not isinstance(v, list):
            return True
        return not any(any(str(c).strip() for c in (row or {}).values()) for row in v)
    if isinstance(v, str):
        return not v.strip()
    return False


def missing_required(form: dict[str, Any], data: dict[str, Any]) -> list[dict[str, str]]:
    out = []
    for s, f in iter_fields(form):
        if f["type"] not in INPUT_TYPES or not f.get("required"):
            continue
        if not cond_ok(s.get("show_if"), data) or not cond_ok(f.get("show_if"), data):
            continue
        if is_empty(f, data.get(f["key"])):
            out.append({"key": f["key"], "label": f["label"], "abschnitt": s["title"]})
    return out


def defaults(form: dict[str, Any]) -> dict[str, Any]:
    return {f["key"]: f["default"] for f in input_fields(form) if "default" in f}


def clean(form: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    """Nur bekannte Feldschlüssel übernehmen, Typen grob normalisieren."""
    fields = {f["key"]: f for f in input_fields(form)}
    out: dict[str, Any] = {}
    for k, v in (data or {}).items():
        f = fields.get(k)
        if not f:
            continue
        t = f["type"]
        if v is None or v == "":
            out[k] = None
        elif t == "number":
            try:
                out[k] = float(str(v).replace(",", ".")) if not isinstance(v, (int, float)) else v
            except ValueError:
                out[k] = str(v)
        elif t == "check":
            out[k] = bool(v)
        elif t == "checks":
            out[k] = [str(x) for x in v] if isinstance(v, list) else [str(v)]
        elif t == "table":
            cols = {c["key"] for c in f["columns"]}
            rows = v if isinstance(v, list) else []
            out[k] = [{c: ("" if r.get(c) is None else r.get(c)) for c in cols}
                      for r in rows[:200] if isinstance(r, dict)]
        elif t == "signature":
            s = str(v)
            out[k] = s if s.startswith("data:image/png;base64,") else None
        else:
            out[k] = str(v)[:5000]
    return out
