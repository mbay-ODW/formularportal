"""MCP-Server für das Formularportal.

Model Context Protocol über Streamable HTTP (ohne externe MCP-SDK), damit Agenten
Vorgänge anlegen, Formulare aus HERO/Unterlagen vorbefüllen, prüfen, einreichen
und als PDF ablegen können. Auth: statischer Bearer (MCP_API_KEY, Claude
Desktop/Code) oder Authelia-OIDC-Token (claude.ai-Connector, Introspection).
Der Server hält keinen State – er kapselt die interne API (FP_API_URL) und
authentifiziert sich dort mit dem internen API-Key.
"""
from __future__ import annotations

import base64
import hmac
import json
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

API_URL = os.environ.get("FP_API_URL", "http://backend:8000").rstrip("/")
INTERNAL_API_KEY = os.environ.get("FP_INTERNAL_API_KEY", "")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
OIDC_INTROSPECTION_URL = os.environ.get("OIDC_INTROSPECTION_URL", "")
OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "formularportal-mcp", "version": "1.0.0"}
INSTRUCTIONS = (
    "Formularportal der Energieberatung: 20 Formulare (Beratungsauftrag, Datenschutz, "
    "Vollmacht, Stammdaten, Datenblätter A/B/C, Checklisten EBW/BEG EM/Heizung, "
    "Fachunternehmererklärungen, Verträge, Eigenleistung, Baubegleitung, Lüftung, iSFP-Abschluss, "
    "Energieausweis). Typischer "
    "Ablauf: formulare_katalog → vorgang_anlegen (optional mit hero_project_id, dann sind "
    "Kundendaten vorbefüllt) → formular_schema lesen → formular_ausfuellen mit den "
    "Feldschlüsseln → formular_lesen zeigt fehlende Pflichtfelder → formular_einreichen "
    "bzw. kundenlink an den Kunden geben → hero_pdf_hochladen. Schlüssel mit eig_/obj_/fu_ "
    "gelten vorgangsweit und müssen nur einmal gesetzt werden. Unterschriften kann nur ein "
    "Mensch leisten – Formulare mit Pflicht-Unterschrift über den Kundenlink abschließen "
    "lassen. Nichts erfinden: fehlende Angaben leer lassen und im Ergebnis benennen."
)

app = FastAPI(title="Formularportal MCP", docs_url=None, redoc_url=None)


# ---- Auth -------------------------------------------------------------------------
async def _introspect(token: str) -> bool:
    if not (OIDC_INTROSPECTION_URL and OIDC_CLIENT_ID and OIDC_CLIENT_SECRET and token):
        return False
    basic = base64.b64encode(f"{OIDC_CLIENT_ID}:{OIDC_CLIENT_SECRET}".encode()).decode()
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(OIDC_INTROSPECTION_URL, data={"token": token},
                             headers={"Authorization": f"Basic {basic}",
                                      "Accept": "application/json"})
        return r.status_code == 200 and r.json().get("active") is True
    except Exception:  # noqa: BLE001
        return False


async def check_auth(request: Request) -> None:
    token = ""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        token = request.query_params.get("t", "")
    if token and MCP_API_KEY and hmac.compare_digest(token, MCP_API_KEY):
        return
    if await _introspect(token):
        return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                        "Nicht autorisiert (Authelia-Login oder Bearer-Token nötig)",
                        headers={"WWW-Authenticate": 'Bearer realm="formularportal-mcp"'})


# ---- HTTP zur internen API ------------------------------------------------------------
def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {INTERNAL_API_KEY}"} if INTERNAL_API_KEY else {}


async def _req(method: str, path: str, *, params: dict | None = None, body: Any = None,
               raw: bool = False) -> Any:
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.request(method, f"{API_URL}{path}", params=params, json=body,
                            headers=_headers())
    if r.status_code >= 400:
        try:
            detail = r.json()
        except ValueError:
            detail = r.text[:300]
        raise ToolError(f"API {r.status_code}: {json.dumps(detail, ensure_ascii=False)[:1500]}")
    if raw:
        return r
    return r.json() if r.content else {}


class ToolError(Exception):
    pass


def _txt(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _compact_field(f: dict[str, Any]) -> dict[str, Any]:
    keep = ("key", "type", "label", "required", "options", "unit", "hint", "show_if", "default")
    d = {k: f[k] for k in keep if k in f}
    if f["type"] == "table":
        d["columns"] = [{k: c[k] for k in ("key", "label", "type", "options", "unit") if k in c}
                        for c in f["columns"]]
    if f["type"] == "info":
        d = {"type": "info", "text": f.get("text")}
    return d


def _formular_kurz(v: dict[str, Any]) -> dict[str, Any]:
    return {"id": v["id"], "formular": v["title"], "form_key": v["form_key"],
            "status": v["status"], "gesperrt": v.get("locked"), "link": v.get("link"),
            "fehlende_pflichtfelder": v.get("fehlend"),
            "hero_document_id": v.get("hero_document_id")}


# ---- Tool-Handler ----------------------------------------------------------------------
async def h_katalog(_a):
    return _txt(await _req("GET", "/api/forms"))


async def h_schema(a):
    f = await _req("GET", f"/api/forms/{a['form_key']}")
    return _txt({"key": f["key"], "title": f["title"], "audience": f["audience"],
                 "abschnitte": [{"titel": s["title"], "show_if": s.get("show_if"),
                                 "felder": [_compact_field(x) for x in s["fields"]]}
                                for s in f["sections"]]})


async def h_vorgaenge(a):
    items = await _req("GET", "/api/vorgaenge", params={"q": a.get("suche", ""),
                                                        "archiviert": bool(a.get("archiviert"))})
    return _txt([{k: v.get(k) for k in ("id", "titel", "kunde", "objekt", "hero_ref",
                                        "hero_project_id", "anzahl_formulare",
                                        "anzahl_eingereicht", "anzahl_geprueft", "updated_at")}
                 for v in items])


def _vorgang_kurz(v: dict[str, Any]) -> dict[str, Any]:
    return {"id": v["id"], "titel": v["titel"], "kunde": v.get("kunde"),
            "objekt": v.get("objekt"), "kunde_email": v.get("kunde_email"),
            "hero_project_id": v.get("hero_project_id"), "hero_ref": v.get("hero_ref"),
            "portal_link": v.get("portal_link"), "notiz": v.get("notiz"),
            "stammdaten": v.get("stammdaten"),
            "formulare": [{k: f.get(k) for k in ("id", "title", "form_key", "status",
                                                 "freigegeben", "link", "pflicht_offen",
                                                 "pflicht_gesamt", "hero_document_id")}
                          for f in v.get("formulare", [])]}


async def h_vorgang(a):
    return _txt(_vorgang_kurz(await _req("GET", f"/api/vorgaenge/{int(a['id'])}")))


async def h_vorgang_anlegen(a):
    body = {k: a[k] for k in ("titel", "kunde_name", "kunde_email", "stammdaten", "formulare",
                              "paket", "hero_project_id", "notiz") if a.get(k) is not None}
    return _txt(_vorgang_kurz(await _req("POST", "/api/vorgaenge", body=body)))


async def h_vorgang_aktualisieren(a):
    vid = int(a["id"])
    body = {k: a[k] for k in ("titel", "kunde_name", "kunde_email", "notiz", "archiviert",
                              "hero_project_id", "hero_ref") if a.get(k) is not None}
    if isinstance(a.get("stammdaten"), dict):
        cur = await _req("GET", f"/api/vorgaenge/{vid}")
        body["stammdaten"] = {**cur.get("stammdaten", {}), **a["stammdaten"]}
    return _txt(_vorgang_kurz(await _req("PATCH", f"/api/vorgaenge/{vid}", body=body)))


async def h_formular_hinzufuegen(a):
    v = await _req("POST", f"/api/vorgaenge/{int(a['vorgang_id'])}/formulare",
                   body={"keys": a["formulare"]})
    return _txt(_vorgang_kurz(v))


async def h_formular_lesen(a):
    v = await _req("GET", f"/api/formulare/{int(a['id'])}")
    out = _formular_kurz(v) | {"daten": v["data"], "vorgang": v["vorgang"]}
    return _txt(out)


async def h_formular_ausfuellen(a):
    v = await _req("PUT", f"/api/formulare/{int(a['id'])}",
                   body={"data": a.get("daten") or {}, "replace": bool(a.get("ersetzen"))})
    unbekannt = sorted(set((a.get("daten") or {}).keys()) - set(v["data"].keys()))
    out = _formular_kurz(v)
    if unbekannt:
        out["ignorierte_schluessel"] = unbekannt
    return _txt(out)


async def h_formular_einreichen(a):
    return _txt(_formular_kurz(await _req("POST", f"/api/formulare/{int(a['id'])}/einreichen")))


async def h_status(a):
    return _txt(_formular_kurz(await _req("POST", f"/api/formulare/{int(a['id'])}/status",
                                          body={"status": a["status"]})))


async def h_pdf(a):
    params = {"ausfuellbar": "true"} if a.get("beschreibbar") else None
    r = await _req("GET", f"/api/formulare/{int(a['id'])}/pdf", params=params, raw=True)
    name = "formular.pdf"
    cd = r.headers.get("content-disposition", "")
    if 'filename="' in cd:
        name = cd.split('filename="', 1)[1].split('"', 1)[0]
    return {"content": [
        {"type": "text", "text": f"PDF erzeugt: {name} ({len(r.content) // 1024} KB)"},
        {"type": "resource", "resource": {"uri": f"formularportal://formular/{a['id']}/pdf",
                                          "mimeType": "application/pdf",
                                          "blob": base64.b64encode(r.content).decode()}}]}


async def h_kundenlink(a):
    v = await _req("GET", f"/api/vorgaenge/{int(a['vorgang_id'])}")
    return _txt({"portal_link": v["portal_link"],
                 "formulare": [{"formular": f["title"], "link": f["link"],
                                "im_portal_sichtbar": f["freigegeben"], "status": f["status"]}
                               for f in v["formulare"]]})


async def h_link_mail(a):
    body = {"email": a.get("email", ""), "nachricht": a.get("nachricht", "")}
    if a.get("formular_id"):
        return _txt(await _req("POST", f"/api/formulare/{int(a['formular_id'])}/link-senden",
                               body=body))
    return _txt(await _req("POST", f"/api/vorgaenge/{int(a['vorgang_id'])}/link-senden",
                           body=body))


async def h_hero_projekte(a):
    return _txt(await _req("GET", "/api/hero/projekte", params={"q": a["suche"],
                                                                "limit": a.get("limit", 15)}))


async def h_hero_kontakte(a):
    return _txt(await _req("GET", "/api/hero/kontakte", params={"q": a["suche"],
                                                                "limit": a.get("limit", 15)}))


async def h_hero_sync(a):
    return _txt(await _req("POST", f"/api/vorgaenge/{int(a['vorgang_id'])}/hero-sync",
                           params={"overwrite": bool(a.get("ueberschreiben"))}))


async def h_hero_upload(a):
    params = {"document_type_id": a["document_type_id"]} if a.get("document_type_id") else None
    return _txt(await _req("POST", f"/api/formulare/{int(a['id'])}/hero-upload", params=params))


async def h_ereignisse(a):
    return _txt(await _req("GET", f"/api/vorgaenge/{int(a['vorgang_id'])}/ereignisse"))


# ---- Tool-Katalog -------------------------------------------------------------------
_OBJ = {"type": "object"}
TOOLS: list[dict[str, Any]] = [
    {"name": "formulare_katalog", "description":
        "Listet alle Formulare (key, Titel, Zielgruppe Kunde/Berater/Fachunternehmen) und die "
        "vordefinierten Pakete (z. B. 'iSFP / Energieberatung', 'Heizungstausch').",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "formular_schema", "description":
        "Alle Felder eines Formulars mit Schlüssel, Typ, Optionen, Pflicht und show_if. "
        "Vor formular_ausfuellen aufrufen, um die exakten Feldschlüssel und erlaubten "
        "Optionswerte zu kennen. Typen: yesno erwartet 'ja'/'nein', check true/false, checks "
        "eine Liste von Optionen, table eine Liste von Zeilen-Objekten mit Spaltenschlüsseln, "
        "date 'JJJJ-MM-TT'.",
     "inputSchema": {"type": "object", "properties": {"form_key": {"type": "string"}},
                     "required": ["form_key"]}},
    {"name": "vorgaenge_liste", "description": "Vorgänge (Kunde/Objekt) mit Formularstatus.",
     "inputSchema": {"type": "object", "properties": {
         "suche": {"type": "string", "description": "Name, Titel, HERO-Nr. oder E-Mail"},
         "archiviert": {"type": "boolean"}}}},
    {"name": "vorgang_details", "description":
        "Ein Vorgang mit vorgangsweiten Stammdaten, Portal-Link und allen Formularen "
        "(Status, offene Pflichtfelder).",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}},
                     "required": ["id"]}},
    {"name": "vorgang_anlegen", "description":
        "Legt einen Vorgang an. Mit hero_project_id werden Kunde, Anschrift und Objekt aus HERO "
        "übernommen. 'paket' oder 'formulare' (Liste von form_keys) bestimmt die Formulare. "
        "'stammdaten' = geteilte Werte (eig_*, obj_*, fu_*).",
     "inputSchema": {"type": "object", "properties": {
         "titel": {"type": "string"}, "kunde_name": {"type": "string"},
         "kunde_email": {"type": "string"}, "stammdaten": _OBJ,
         "formulare": {"type": "array", "items": {"type": "string"}},
         "paket": {"type": "string"}, "hero_project_id": {"type": "integer"},
         "notiz": {"type": "string"}}}},
    {"name": "vorgang_aktualisieren", "description":
        "Ändert Titel, Kunde, E-Mail, Notiz, HERO-Verknüpfung oder Archivstatus; 'stammdaten' "
        "wird mit den vorhandenen Stammdaten zusammengeführt.",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "integer"}, "titel": {"type": "string"},
         "kunde_name": {"type": "string"}, "kunde_email": {"type": "string"},
         "notiz": {"type": "string"}, "archiviert": {"type": "boolean"},
         "hero_project_id": {"type": "integer"}, "hero_ref": {"type": "string"},
         "stammdaten": _OBJ}, "required": ["id"]}},
    {"name": "formular_hinzufuegen", "description": "Fügt einem Vorgang Formulare hinzu.",
     "inputSchema": {"type": "object", "properties": {
         "vorgang_id": {"type": "integer"},
         "formulare": {"type": "array", "items": {"type": "string"}}},
         "required": ["vorgang_id", "formulare"]}},
    {"name": "formular_lesen", "description":
        "Aktuelle Werte eines Formulars (inkl. vorbefüllter Stammdaten), Status und fehlende "
        "Pflichtfelder.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}},
                     "required": ["id"]}},
    {"name": "formular_ausfuellen", "description":
        "Setzt Feldwerte (daten = {feldschluessel: wert}). Standard: zusammenführen; "
        "ersetzen=true überschreibt alle Formularwerte. Unbekannte Schlüssel werden ignoriert "
        "und gemeldet. Geht auch bei eingereichten Formularen (Korrektur durch Berater).",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "integer"}, "daten": _OBJ, "ersetzen": {"type": "boolean"}},
         "required": ["id", "daten"]}},
    {"name": "formular_einreichen", "description":
        "Prüft Pflichtfelder und schließt das Formular ab (Status eingereicht, gesperrt für den "
        "Kunden, Benachrichtigung). Liefert bei Lücken die fehlenden Felder.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"}},
                     "required": ["id"]}},
    {"name": "formular_status_setzen", "description":
        "Status: entwurf | in_bearbeitung | eingereicht | geprueft. 'in_bearbeitung' entsperrt "
        "ein eingereichtes Formular wieder für den Kunden.",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "integer"},
         "status": {"type": "string", "enum": ["entwurf", "in_bearbeitung", "eingereicht",
                                               "geprueft"]}}, "required": ["id", "status"]}},
    {"name": "formular_pdf", "description":
        "Erzeugt das gebrandete PDF eines Formulars und gibt es als eingebettete Ressource "
        "(base64) zurück. beschreibbar=true liefert ein PDF mit Formularfeldern, vorbefüllt mit "
        "den bisherigen Angaben (zum Mailversand an Kunden).",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "integer"},
                                                      "beschreibbar": {"type": "boolean"}},
                     "required": ["id"]}},
    {"name": "kundenlink", "description":
        "Portal-Link des Vorgangs (alle freigegebenen Formulare) und Einzellinks je Formular "
        "(z. B. für das Fachunternehmen).",
     "inputSchema": {"type": "object", "properties": {"vorgang_id": {"type": "integer"}},
                     "required": ["vorgang_id"]}},
    {"name": "link_per_mail_senden", "description":
        "Schickt den Portal-Link (vorgang_id) oder einen Formular-Link (formular_id) per Mail. "
        "Ohne email an die hinterlegte Kunden- bzw. Fachunternehmer-Adresse.",
     "inputSchema": {"type": "object", "properties": {
         "vorgang_id": {"type": "integer"}, "formular_id": {"type": "integer"},
         "email": {"type": "string"}, "nachricht": {"type": "string"}}}},
    {"name": "hero_projekte_suchen", "description":
        "Sucht HERO-Projekte (Name, Nummer, Kunde, Ort) – liefert project_id für "
        "vorgang_anlegen.",
     "inputSchema": {"type": "object", "properties": {
         "suche": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["suche"]}},
    {"name": "hero_kontakte_suchen", "description":
        "Sucht HERO-Kontakte und liefert sie bereits als Stammdaten (eig_*) gemappt.",
     "inputSchema": {"type": "object", "properties": {
         "suche": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["suche"]}},
    {"name": "hero_stammdaten_abgleichen", "description":
        "Übernimmt Kunden- und Objektdaten aus dem verknüpften HERO-Projekt in die Stammdaten "
        "(Standard: nur leere Felder füllen).",
     "inputSchema": {"type": "object", "properties": {
         "vorgang_id": {"type": "integer"}, "ueberschreiben": {"type": "boolean"}},
         "required": ["vorgang_id"]}},
    {"name": "hero_pdf_hochladen", "description":
        "Lädt das PDF eines Formulars als Dokument in das verknüpfte HERO-Projekt und schreibt "
        "einen Logbucheintrag.",
     "inputSchema": {"type": "object", "properties": {
         "id": {"type": "integer", "description": "Formular-id"},
         "document_type_id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "vorgang_ereignisse", "description": "Ereignisprotokoll eines Vorgangs.",
     "inputSchema": {"type": "object", "properties": {"vorgang_id": {"type": "integer"}},
                     "required": ["vorgang_id"]}},
]

TOOL_HANDLERS = {
    "formulare_katalog": h_katalog, "formular_schema": h_schema,
    "vorgaenge_liste": h_vorgaenge, "vorgang_details": h_vorgang,
    "vorgang_anlegen": h_vorgang_anlegen, "vorgang_aktualisieren": h_vorgang_aktualisieren,
    "formular_hinzufuegen": h_formular_hinzufuegen, "formular_lesen": h_formular_lesen,
    "formular_ausfuellen": h_formular_ausfuellen, "formular_einreichen": h_formular_einreichen,
    "formular_status_setzen": h_status, "formular_pdf": h_pdf, "kundenlink": h_kundenlink,
    "link_per_mail_senden": h_link_mail, "hero_projekte_suchen": h_hero_projekte,
    "hero_kontakte_suchen": h_hero_kontakte, "hero_stammdaten_abgleichen": h_hero_sync,
    "hero_pdf_hochladen": h_hero_upload, "vorgang_ereignisse": h_ereignisse,
}


# ---- JSON-RPC / MCP ----------------------------------------------------------------
def rpc_result(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def rpc_error(rid, code, msg):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": msg}}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"name": "Formularportal MCP", "version": "1.0.0", "endpoint": "/mcp",
            "auth": "Bearer token (Authorization-Header oder ?t=<token>)"}


async def _handle(msg: dict[str, Any]) -> dict[str, Any] | None:
    method = msg.get("method")
    params = msg.get("params") or {}
    rid = msg.get("id")
    if method == "initialize":
        return rpc_result(rid, {"protocolVersion": PROTOCOL_VERSION,
                                "capabilities": {"tools": {}}, "serverInfo": SERVER_INFO,
                                "instructions": INSTRUCTIONS})
    if method and method.startswith("notifications/"):
        return None
    if method == "ping":
        return rpc_result(rid, {})
    if method == "tools/list":
        return rpc_result(rid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in TOOL_HANDLERS:
            return rpc_error(rid, -32601, f"Unbekanntes Tool: {name}")
        try:
            res = await TOOL_HANDLERS[name](args)
        except ToolError as e:
            return rpc_result(rid, {"content": [{"type": "text", "text": str(e)}],
                                    "isError": True})
        except (KeyError, ValueError, TypeError) as e:
            return rpc_result(rid, {"content": [{"type": "text",
                                                 "text": f"Ungültige Argumente: {e}"}],
                                    "isError": True})
        except Exception as e:  # noqa: BLE001
            return rpc_error(rid, -32603, f"Tool-Fehler: {e}")
        if isinstance(res, dict):
            return rpc_result(rid, res)
        return rpc_result(rid, {"content": [{"type": "text", "text": res}]})
    return rpc_error(rid, -32601, f"Methode nicht gefunden: {method}")


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    await check_auth(request)
    body = await request.json()
    if isinstance(body, list):  # JSON-RPC-Batch
        out = [r for r in [await _handle(m) for m in body] if r is not None]
        return JSONResponse(out) if out else JSONResponse({}, status_code=202)
    res = await _handle(body)
    if res is None:
        return JSONResponse({}, status_code=202)
    return JSONResponse(res)
