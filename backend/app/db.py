"""SQLite-Persistenz (Vorgänge, Formulare, Ereignisprotokoll).

Bewusst schlank: eine Datei im Daten-Volume, JSON-Spalten für Formularinhalte.
Jede Operation öffnet eine eigene Verbindung (WAL-Modus), damit FastAPI-Threads
sich nicht in die Quere kommen.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS vorgang (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    titel           TEXT NOT NULL,
    kunde_name      TEXT NOT NULL DEFAULT '',
    kunde_email     TEXT NOT NULL DEFAULT '',
    token           TEXT NOT NULL UNIQUE,
    hero_project_id INTEGER,
    hero_ref        TEXT NOT NULL DEFAULT '',
    hero_contact_id INTEGER,
    stammdaten      TEXT NOT NULL DEFAULT '{}',
    notiz           TEXT NOT NULL DEFAULT '',
    archiviert      INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS formular (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vorgang_id    INTEGER NOT NULL REFERENCES vorgang(id) ON DELETE CASCADE,
    form_key      TEXT NOT NULL,
    token         TEXT NOT NULL UNIQUE,
    status        TEXT NOT NULL DEFAULT 'entwurf',
    freigegeben   INTEGER NOT NULL DEFAULT 1,
    data          TEXT NOT NULL DEFAULT '{}',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    submitted_at  TEXT,
    expires_at    TEXT,
    hero_document_id TEXT
);
CREATE INDEX IF NOT EXISTS ix_formular_vorgang ON formular(vorgang_id);
CREATE TABLE IF NOT EXISTS ereignis (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    vorgang_id  INTEGER NOT NULL,
    formular_id INTEGER,
    ts          TEXT NOT NULL,
    akteur      TEXT NOT NULL,
    aktion      TEXT NOT NULL,
    details     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_ereignis_vorgang ON ereignis(vorgang_id);
"""

STATUS = ("entwurf", "in_bearbeitung", "eingereicht", "geprueft")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_token() -> str:
    return secrets.token_urlsafe(24)


def expiry() -> str | None:
    if config.LINK_TTL_DAYS <= 0:
        return None
    return (datetime.now(timezone.utc) + timedelta(days=config.LINK_TTL_DAYS)).isoformat(
        timespec="seconds"
    )


def is_expired(expires_at: str | None) -> bool:
    if not expires_at:
        return False
    return datetime.fromisoformat(expires_at) < datetime.now(timezone.utc)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(config.DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as con:
        con.execute("PRAGMA journal_mode = WAL")
        con.executescript(SCHEMA)


# ---- Mapping ----------------------------------------------------------------
def _vorgang(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["stammdaten"] = json.loads(d["stammdaten"] or "{}")
    d["archiviert"] = bool(d["archiviert"])
    return d


def _formular(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["data"] = json.loads(d["data"] or "{}")
    d["freigegeben"] = bool(d["freigegeben"])
    d["abgelaufen"] = is_expired(d.get("expires_at"))
    return d


# ---- Vorgänge ---------------------------------------------------------------
def create_vorgang(titel: str, kunde_name: str = "", kunde_email: str = "",
                   stammdaten: dict | None = None, hero_project_id: int | None = None,
                   hero_ref: str = "", hero_contact_id: int | None = None,
                   notiz: str = "") -> dict[str, Any]:
    ts = now()
    with connect() as con:
        cur = con.execute(
            "INSERT INTO vorgang (titel, kunde_name, kunde_email, token, hero_project_id, hero_ref,"
            " hero_contact_id, stammdaten, notiz, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (titel, kunde_name, kunde_email, new_token(), hero_project_id, hero_ref,
             hero_contact_id, json.dumps(stammdaten or {}, ensure_ascii=False), notiz, ts, ts),
        )
        vid = cur.lastrowid
    log(vid, None, "berater", "vorgang_angelegt", titel)
    return get_vorgang(vid)  # type: ignore[return-value]


def get_vorgang(vid: int) -> dict[str, Any] | None:
    with connect() as con:
        row = con.execute("SELECT * FROM vorgang WHERE id=?", (vid,)).fetchone()
    return _vorgang(row) if row else None


def get_vorgang_by_token(token: str) -> dict[str, Any] | None:
    with connect() as con:
        row = con.execute("SELECT * FROM vorgang WHERE token=?", (token,)).fetchone()
    return _vorgang(row) if row else None


def list_vorgaenge(q: str = "", archiviert: bool = False) -> list[dict[str, Any]]:
    sql = (
        "SELECT v.*, "
        " (SELECT COUNT(*) FROM formular f WHERE f.vorgang_id=v.id) AS anzahl_formulare,"
        " (SELECT COUNT(*) FROM formular f WHERE f.vorgang_id=v.id AND f.status='eingereicht')"
        "   AS anzahl_eingereicht,"
        " (SELECT COUNT(*) FROM formular f WHERE f.vorgang_id=v.id AND f.status='geprueft')"
        "   AS anzahl_geprueft"
        " FROM vorgang v WHERE v.archiviert=?"
    )
    args: list[Any] = [1 if archiviert else 0]
    if q.strip():
        sql += " AND (v.titel LIKE ? OR v.kunde_name LIKE ? OR v.hero_ref LIKE ? OR v.kunde_email LIKE ?)"
        like = f"%{q.strip()}%"
        args += [like, like, like, like]
    sql += " ORDER BY v.updated_at DESC"
    with connect() as con:
        rows = con.execute(sql, args).fetchall()
    return [_vorgang(r) for r in rows]


_VORGANG_FIELDS = ("titel", "kunde_name", "kunde_email", "hero_project_id", "hero_ref",
                   "hero_contact_id", "notiz", "archiviert")


def update_vorgang(vid: int, **fields: Any) -> dict[str, Any] | None:
    sets, args = [], []
    for k in _VORGANG_FIELDS:
        if k in fields and fields[k] is not None:
            sets.append(f"{k}=?")
            args.append(int(fields[k]) if k == "archiviert" else fields[k])
    if "stammdaten" in fields and fields["stammdaten"] is not None:
        sets.append("stammdaten=?")
        args.append(json.dumps(fields["stammdaten"], ensure_ascii=False))
    if not sets:
        return get_vorgang(vid)
    sets.append("updated_at=?")
    args += [now(), vid]
    with connect() as con:
        con.execute(f"UPDATE vorgang SET {', '.join(sets)} WHERE id=?", args)
    return get_vorgang(vid)


def merge_stammdaten(vid: int, values: dict[str, Any]) -> None:
    v = get_vorgang(vid)
    if not v:
        return
    sd = dict(v["stammdaten"])
    changed = False
    for k, val in values.items():
        if sd.get(k) != val:
            sd[k] = val
            changed = True
    if changed:
        update_vorgang(vid, stammdaten=sd)


def delete_vorgang(vid: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM formular WHERE vorgang_id=?", (vid,))
        con.execute("DELETE FROM ereignis WHERE vorgang_id=?", (vid,))
        con.execute("DELETE FROM vorgang WHERE id=?", (vid,))


def touch_vorgang(vid: int) -> None:
    with connect() as con:
        con.execute("UPDATE vorgang SET updated_at=? WHERE id=?", (now(), vid))


# ---- Formulare --------------------------------------------------------------
def create_formular(vid: int, form_key: str, freigegeben: bool = True,
                    data: dict | None = None) -> dict[str, Any]:
    ts = now()
    with connect() as con:
        cur = con.execute(
            "INSERT INTO formular (vorgang_id, form_key, token, freigegeben, data, created_at,"
            " updated_at, expires_at) VALUES (?,?,?,?,?,?,?,?)",
            (vid, form_key, new_token(), 1 if freigegeben else 0,
             json.dumps(data or {}, ensure_ascii=False), ts, ts, expiry()),
        )
        fid = cur.lastrowid
    touch_vorgang(vid)
    return get_formular(fid)  # type: ignore[return-value]


def get_formular(fid: int) -> dict[str, Any] | None:
    with connect() as con:
        row = con.execute("SELECT * FROM formular WHERE id=?", (fid,)).fetchone()
    return _formular(row) if row else None


def get_formular_by_token(token: str) -> dict[str, Any] | None:
    with connect() as con:
        row = con.execute("SELECT * FROM formular WHERE token=?", (token,)).fetchone()
    return _formular(row) if row else None


def list_formulare(vid: int) -> list[dict[str, Any]]:
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM formular WHERE vorgang_id=? ORDER BY id", (vid,)
        ).fetchall()
    return [_formular(r) for r in rows]


def update_formular(fid: int, **fields: Any) -> dict[str, Any] | None:
    sets, args = [], []
    for k in ("status", "submitted_at", "expires_at", "hero_document_id", "token"):
        if k in fields:
            sets.append(f"{k}=?")
            args.append(fields[k])
    if "freigegeben" in fields and fields["freigegeben"] is not None:
        sets.append("freigegeben=?")
        args.append(1 if fields["freigegeben"] else 0)
    if "data" in fields and fields["data"] is not None:
        sets.append("data=?")
        args.append(json.dumps(fields["data"], ensure_ascii=False))
    if not sets:
        return get_formular(fid)
    sets.append("updated_at=?")
    args += [now(), fid]
    with connect() as con:
        con.execute(f"UPDATE formular SET {', '.join(sets)} WHERE id=?", args)
    f = get_formular(fid)
    if f:
        touch_vorgang(f["vorgang_id"])
    return f


def delete_formular(fid: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM formular WHERE id=?", (fid,))


# ---- Ereignisse -------------------------------------------------------------
def log(vid: int, fid: int | None, akteur: str, aktion: str, details: str = "") -> None:
    with connect() as con:
        con.execute(
            "INSERT INTO ereignis (vorgang_id, formular_id, ts, akteur, aktion, details)"
            " VALUES (?,?,?,?,?,?)",
            (vid, fid, now(), akteur, aktion, details[:500]),
        )


def list_ereignisse(vid: int, limit: int = 100) -> list[dict[str, Any]]:
    with connect() as con:
        rows = con.execute(
            "SELECT * FROM ereignis WHERE vorgang_id=? ORDER BY id DESC LIMIT ?", (vid, limit)
        ).fetchall()
    return [dict(r) for r in rows]
