"""Charakterisierung des MCP-Servers: Auth, Tool-Liste, Aufrufe, Fehlerform.

Die interne API und die Authelia-Introspection sind gemockt. Aufruf aus dem Repo-Wurzelverzeichnis:
python -m pytest tests_mcp
"""
from __future__ import annotations

import base64
import importlib
import json

import httpx
import pytest
from starlette.testclient import TestClient

srv = importlib.import_module("mcp.server")

KEY = "testkey"
INTROSPECT = "http://authelia.test/api/oidc/introspection"
ACCEPT = "application/json, text/event-stream"
AUTH = {"Authorization": f"Bearer {KEY}", "Accept": ACCEPT}
REAL_ASYNC_CLIENT = httpx.AsyncClient


class Api:
    """Merkt sich Aufrufe und beantwortet sie wie die interne API."""

    def __init__(self) -> None:
        self.calls: list[httpx.Request] = []
        self.routes: dict[tuple[str, str], httpx.Response] = {}

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if str(request.url) == INTROSPECT:
            form = dict(p.split("=") for p in request.content.decode().split("&"))
            return httpx.Response(200, json={"active": form.get("token") == "oidc-gut"})
        return self.routes.get((request.method, request.url.path),
                               httpx.Response(404, text="nicht gefunden"))


@pytest.fixture(scope="module")
def client():
    with TestClient(srv.app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def api(monkeypatch):
    mock = Api()

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(mock.handler)
        return REAL_ASYNC_CLIENT(*args, **kwargs)

    monkeypatch.setattr(srv.httpx, "AsyncClient", factory)
    monkeypatch.setattr(srv, "API_URL", "http://backend.test")
    monkeypatch.setattr(srv, "INTERNAL_API_KEY", "intern")
    monkeypatch.setattr(srv, "MCP_API_KEY", KEY)
    monkeypatch.setattr(srv, "OIDC_INTROSPECTION_URL", INTROSPECT)
    monkeypatch.setattr(srv, "OIDC_CLIENT_ID", "cid")
    monkeypatch.setattr(srv, "OIDC_CLIENT_SECRET", "csecret")
    return mock


def rpc(method, params=None, rid=1):
    body = {"jsonrpc": "2.0", "id": rid, "method": method}
    if params is not None:
        body["params"] = params
    return body


LIST = rpc("tools/list")


def call(client, name, arguments=None):
    r = client.post("/mcp", headers=AUTH, json=rpc("tools/call", {"name": name, "arguments": arguments or {}}))
    assert r.status_code == 200
    return r.json()


# ---- Auth -------------------------------------------------------------------
def test_ohne_token_401(client):
    r = client.post("/mcp", headers={"Accept": ACCEPT}, json=LIST)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == 'Bearer realm="formularportal-mcp"'
    assert r.json() == {"detail": "Nicht autorisiert (Authelia-Login oder Bearer-Token nötig)"}


def test_falscher_bearer_401(client):
    r = client.post("/mcp", headers={"Authorization": "Bearer falsch", "Accept": ACCEPT}, json=LIST)
    assert r.status_code == 401


def test_anderes_schema_401(client):
    r = client.post("/mcp", headers={"Authorization": f"Basic {KEY}", "Accept": ACCEPT}, json=LIST)
    assert r.status_code == 401


def test_bearer_akzeptiert(client):
    assert client.post("/mcp", headers=AUTH, json=LIST).status_code == 200


def test_query_token_akzeptiert(client):
    assert client.post(f"/mcp?t={KEY}", headers={"Accept": ACCEPT}, json=LIST).status_code == 200


def test_query_token_falsch_401(client):
    assert client.post("/mcp?t=falsch", headers={"Accept": ACCEPT}, json=LIST).status_code == 401


def test_header_hat_vorrang_vor_query(client):
    r = client.post(f"/mcp?t={KEY}", headers={"Authorization": "Bearer falsch", "Accept": ACCEPT}, json=LIST)
    assert r.status_code == 401


def test_oidc_introspection_akzeptiert(client, api):
    r = client.post("/mcp", headers={"Authorization": "Bearer oidc-gut", "Accept": ACCEPT}, json=LIST)
    assert r.status_code == 200
    req = api.calls[0]
    assert str(req.url) == INTROSPECT
    assert req.headers["authorization"] == "Basic " + base64.b64encode(b"cid:csecret").decode()


def test_oidc_inaktiv_401(client):
    r = client.post("/mcp", headers={"Authorization": "Bearer oidc-alt", "Accept": ACCEPT}, json=LIST)
    assert r.status_code == 401


def test_statischer_key_fragt_authelia_nicht(client, api):
    client.post("/mcp", headers=AUTH, json=LIST)
    assert api.calls == []


def test_externer_host_wird_nicht_abgelehnt(client):
    r = client.post("http://formulare-mcp.example.com/mcp", headers=AUTH, json=LIST)
    assert r.status_code == 200


# ---- Routen ohne Auth -------------------------------------------------------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_root(client):
    assert client.get("/").json()["endpoint"] == "/mcp"


def test_get_mcp_405(client):
    assert client.get("/mcp").status_code == 405


# ---- Protokoll --------------------------------------------------------------
def test_initialize_altes_protokoll(client):
    r = client.post("/mcp", headers=AUTH, json=rpc("initialize", {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"}}))
    res = r.json()["result"]
    assert res["protocolVersion"] == "2024-11-05"
    assert res["serverInfo"]["name"] == "formularportal-mcp"
    assert res["serverInfo"]["version"] == "1.0.0"
    assert "tools" in res["capabilities"]
    assert res["instructions"] == srv.INSTRUCTIONS


def test_ping(client):
    assert client.post("/mcp", headers=AUTH, json=rpc("ping")).json()["result"] == {}


def test_notification_ohne_antwortkoerper(client):
    r = client.post("/mcp", headers=AUTH, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert r.status_code == 202


def test_tools_list_vollstaendig_ohne_initialize(client):
    tools = client.post("/mcp", headers=AUTH, json=LIST).json()["result"]["tools"]
    assert len(tools) == 19
    got = {t["name"]: {k: t.get(k) for k in ("description", "inputSchema")} for t in tools}
    want = {t["name"]: {k: t.get(k) for k in ("description", "inputSchema")} for t in srv.TOOLS}
    assert got == want


def test_katalog_und_handler_passen(client):
    assert {t["name"] for t in srv.TOOLS} == set(srv.TOOL_HANDLERS)


def test_unbekannte_methode(client):
    r = client.post("/mcp", headers=AUTH, json=rpc("gibt/es/nicht"))
    assert r.json()["error"]["code"] == -32601


# ---- tools/call -------------------------------------------------------------
def test_tool_aufruf_gegen_gemockte_api(client, api):
    api.routes[("GET", "/api/forms")] = httpx.Response(200, json=[{"key": "vollmacht", "title": "Vollmächte"}])
    res = call(client, "formulare_katalog")["result"]
    assert res["content"] == [{"type": "text", "text": json.dumps(
        [{"key": "vollmacht", "title": "Vollmächte"}], ensure_ascii=False, indent=2)}]
    assert not res.get("isError")
    assert api.calls[0].headers["authorization"] == "Bearer intern"


def test_tool_post_body(client, api):
    api.routes[("POST", "/api/formulare/5/status")] = httpx.Response(200, json={"id": 5})
    call(client, "formular_status_setzen", {"id": 5, "status": "geprueft"})
    assert json.loads(api.calls[0].content) == {"status": "geprueft"}


def test_aufruf_ohne_arguments(client, api):
    api.routes[("GET", "/api/forms")] = httpx.Response(200, json=[])
    r = client.post("/mcp", headers=AUTH, json=rpc("tools/call", {"name": "formulare_katalog"}))
    assert r.json()["result"]["content"][0]["text"] == "[]"


def test_pdf_als_resource_mit_blob(client, api):
    api.routes[("GET", "/api/formulare/5/pdf")] = httpx.Response(
        200, content=b"%PDF-1.7", headers={"content-disposition": 'attachment; filename="f.pdf"'})
    content = call(client, "formular_pdf", {"id": 5})["result"]["content"]
    assert content[0] == {"type": "text", "text": "PDF erzeugt: f.pdf (0 KB)"}
    assert content[1] == {"type": "resource", "resource": {
        "uri": "formularportal://formular/5/pdf", "mimeType": "application/pdf",
        "blob": base64.b64encode(b"%PDF-1.7").decode()}}


# ---- Fehlerform -------------------------------------------------------------
def test_unbekanntes_tool_ist_rpc_fehler(client):
    assert call(client, "gibt_es_nicht")["error"] == {"code": -32601, "message": "Unbekanntes Tool: gibt_es_nicht"}


def test_api_fehler_ist_iserror(client, api):
    api.routes[("GET", "/api/forms")] = httpx.Response(400, json={"detail": "kaputt"})
    res = call(client, "formulare_katalog")["result"]
    assert res["isError"] is True
    assert res["content"] == [{"type": "text", "text": 'API 400: {"detail": "kaputt"}'}]


def test_fehlendes_argument_ist_iserror(client):
    res = call(client, "formular_pdf", {})["result"]
    assert res["isError"] is True
    assert res["content"] == [{"type": "text", "text": "Ungültige Argumente: 'id'"}]


def test_falscher_argumenttyp_ist_iserror(client):
    res = call(client, "formular_pdf", {"id": "abc"})["result"]
    assert res["isError"] is True
    assert res["content"][0]["text"].startswith("Ungültige Argumente: ")


def test_unerwarteter_fehler_ist_rpc_fehler(client, api, monkeypatch):
    def kaputt(request):
        raise httpx.ConnectError("keine Verbindung")

    monkeypatch.setattr(api, "handler", kaputt)
    body = call(client, "formulare_katalog")
    assert "result" not in body
    assert body["error"] == {"code": -32603, "message": "Tool-Fehler: keine Verbindung"}


# ---- JSON-RPC-Batch ---------------------------------------------------------
def test_batch(client):
    r = client.post("/mcp", headers=AUTH, json=[rpc("ping", rid=1), rpc("tools/list", rid=2)])
    assert [m["id"] for m in r.json()] == [1, 2]
