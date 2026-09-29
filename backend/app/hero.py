"""HERO-Anbindung: Kunden/Projekte als Stammdaten übernehmen, fertige PDFs hochladen.

Feldnamen gegen das Live-Schema geprüft (project_matches(ids|search),
contacts(search), Customer.birth_date). Der Datei-Upload läuft zweistufig wie im
hero-mcp-server: REST-Upload (x-auth-token) → GraphQL ``upload_document``.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

from app import config

_CONTACT = ("id nr title first_name last_name company_name email phone_home phone_mobile "
            "birth_date address { street city zipcode }")
_PROJECT = ("id name project_nr display_id measure { name } current_project_match_status "
            "{ name } address { street city zipcode } contact { " + _CONTACT + " }")

Q_SEARCH_PROJECTS = ("query($s: String, $n: Int) { project_matches(search: $s, first: $n) { "
                     + _PROJECT + " } }")
Q_PROJECT = "query($ids: [Int]) { project_matches(ids: $ids) { " + _PROJECT + " } }"
Q_SEARCH_CONTACTS = ("query($s: String, $n: Int) { contacts(search: $s, first: $n) { "
                     + _CONTACT + " } }")
M_UPLOAD = """
mutation($uuid: String!, $pid: Int!, $dt: Int!) {
  upload_document(
    document: { project_match_id: $pid, type: "file_upload", document_type_id: $dt }
    file_upload_uuid: $uuid
    target: project_match
    target_id: $pid
  ) { id nr type }
}
"""
M_LOGBOOK = """
mutation($entry: LogbookEntryInput) { add_logbook_entry(logbook_entry: $entry) { id } }
"""


class HeroError(RuntimeError):
    pass


def configured() -> bool:
    return bool(config.HERO_TOKEN)


async def gql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    if not configured():
        raise HeroError("HERO ist nicht konfiguriert (FP_HERO_TOKEN fehlt).")
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(config.HERO_GRAPHQL_URL, json={"query": query,
                                                        "variables": variables or {}},
                         headers={"Authorization": f"Bearer {config.HERO_TOKEN}",
                                  "Accept": "application/json"})
    if r.status_code >= 400:
        raise HeroError(f"HERO HTTP {r.status_code}: {r.text[:200]}")
    body = r.json()
    if body.get("errors"):
        raise HeroError(f"HERO: {body['errors']}")
    return body.get("data") or {}


# ---- Mapping auf Formularschlüssel -----------------------------------------------
_STREET_RE = re.compile(r"^(.*?)[\s,]+(\d+\s*[a-zA-Z]?(?:\s*[-/]\s*\d+\s*[a-zA-Z]?)?)$")


def split_street(street: str) -> tuple[str, str]:
    street = (street or "").strip()
    m = _STREET_RE.match(street)
    return (m.group(1).strip(), m.group(2).replace(" ", "")) if m else (street, "")


def contact_to_stammdaten(c: dict[str, Any] | None) -> dict[str, Any]:
    c = c or {}
    addr = c.get("address") or {}
    strasse, nr = split_street(addr.get("street") or "")
    anrede = (c.get("title") or "").strip()
    out = {
        "eig_anrede": anrede if anrede in ("Herr", "Frau", "Divers", "Firma") else None,
        "eig_vorname": c.get("first_name") or None,
        "eig_nachname": c.get("last_name") or None,
        "eig_firma": c.get("company_name") or None,
        "eig_email": c.get("email") or None,
        "eig_telefon": c.get("phone_home") or None,
        "eig_mobil": c.get("phone_mobile") or None,
        "eig_geburtsdatum": (c.get("birth_date") or "")[:10] or None,
        "eig_strasse": strasse or None,
        "eig_hausnr": nr or None,
        "eig_plz": addr.get("zipcode") or None,
        "eig_ort": addr.get("city") or None,
    }
    return {k: v for k, v in out.items() if v}


def address_to_objekt(addr: dict[str, Any] | None) -> dict[str, Any]:
    addr = addr or {}
    strasse, nr = split_street(addr.get("street") or "")
    out = {"obj_strasse": strasse, "obj_hausnr": nr, "obj_plz": addr.get("zipcode"),
           "obj_ort": addr.get("city")}
    return {k: v for k, v in out.items() if v}


def _kunde_name(c: dict[str, Any]) -> str:
    name = " ".join(x for x in [c.get("first_name"), c.get("last_name")] if x).strip()
    return name or (c.get("company_name") or "")


def project_summary(p: dict[str, Any]) -> dict[str, Any]:
    c = p.get("contact") or {}
    a = p.get("address") or {}
    return {
        "project_id": p.get("id"),
        "hero_ref": p.get("project_nr") or p.get("display_id") or str(p.get("id")),
        "name": p.get("name") or "",
        "measure": (p.get("measure") or {}).get("name", ""),
        "status": (p.get("current_project_match_status") or {}).get("name", ""),
        "kunde": _kunde_name(c),
        "kunde_email": c.get("email") or "",
        "contact_id": c.get("id"),
        "adresse": " ".join(x for x in [a.get("street"), a.get("zipcode"), a.get("city")] if x),
    }


def project_to_stammdaten(p: dict[str, Any]) -> dict[str, Any]:
    sd = contact_to_stammdaten(p.get("contact"))
    sd |= address_to_objekt(p.get("address"))
    eig_addr = (sd.get("eig_strasse"), sd.get("eig_plz"))
    obj_addr = (sd.get("obj_strasse"), sd.get("obj_plz"))
    if all(eig_addr) and eig_addr == obj_addr:
        sd["obj_gleich_wohnadresse"] = "ja"
    return sd


# ---- Abfragen ---------------------------------------------------------------------
async def search_projects(q: str, limit: int = 15) -> list[dict[str, Any]]:
    if not q.strip():
        return []
    data = await gql(Q_SEARCH_PROJECTS, {"s": q.strip(), "n": max(1, min(limit, 50))})
    return [project_summary(p) for p in data.get("project_matches") or []]


async def get_project(project_id: int) -> dict[str, Any] | None:
    data = await gql(Q_PROJECT, {"ids": [int(project_id)]})
    items = data.get("project_matches") or []
    return items[0] if items else None


async def search_contacts(q: str, limit: int = 15) -> list[dict[str, Any]]:
    if not q.strip():
        return []
    data = await gql(Q_SEARCH_CONTACTS, {"s": q.strip(), "n": max(1, min(limit, 50))})
    return [{"contact_id": c.get("id"), "kunde": _kunde_name(c), "email": c.get("email") or "",
             "firma": c.get("company_name") or "",
             "adresse": " ".join(x for x in [(c.get("address") or {}).get("street"),
                                             (c.get("address") or {}).get("zipcode"),
                                             (c.get("address") or {}).get("city")] if x),
             "stammdaten": contact_to_stammdaten(c)}
            for c in data.get("contacts") or []]


# ---- Upload -----------------------------------------------------------------------
async def upload_pdf(project_id: int, filename: str, data: bytes,
                     document_type_id: int | None = None) -> dict[str, Any]:
    if not configured():
        raise HeroError("HERO ist nicht konfiguriert (FP_HERO_TOKEN fehlt).")
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(config.HERO_UPLOAD_URL,
                         files={"file": (filename, data, "application/pdf")},
                         headers={"x-auth-token": config.HERO_TOKEN,
                                  "Accept": "application/json"})
    if r.status_code >= 400:
        raise HeroError(f"HERO-Upload HTTP {r.status_code}: {r.text[:200]}")
    body = r.json()
    uuid = (body.get("data") or {}).get("uuid") or body.get("uuid")
    if not uuid:
        raise HeroError(f"HERO-Upload ohne uuid: {str(body)[:200]}")
    res = await gql(M_UPLOAD, {"uuid": uuid, "pid": int(project_id),
                               "dt": int(document_type_id or config.HERO_DOCUMENT_TYPE_ID)})
    return res.get("upload_document") or {}


async def add_logbook(project_id: int, text: str) -> None:
    """Best effort: Logbucheintrag am Projekt (Fehler werden ignoriert)."""
    try:
        await gql(M_LOGBOOK, {"entry": {"target": "project_match", "target_id": int(project_id),
                                        "custom_text": text}})
    except (HeroError, httpx.HTTPError):
        pass
