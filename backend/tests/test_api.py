import base64
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

from app import config, forms, pdf



def _sig() -> str:
    buf = io.BytesIO()
    Image.new("RGBA", (300, 100), (14, 42, 64, 255)).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


SIG = _sig()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.sqlite3")
    monkeypatch.setattr(config, "ADMIN_GUARD", "header")
    monkeypatch.setattr(config, "INTERNAL_API_KEY", "geheim")
    from app.main import app
    with TestClient(app) as c:
        c.headers.update({"X-Portal-Zone": "admin"})
        yield c


def _pdf_text(data: bytes) -> str:
    return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)


def test_katalog_vollstaendig(client):
    r = client.get("/api/forms")
    assert r.status_code == 200
    assert [f["nr"] for f in r.json()["formulare"]] == list(range(1, 21))
    for paket, keys in r.json()["pakete"].items():
        assert all(k in forms.REGISTRY for k in keys), paket


def test_admin_schutz(client):
    anon = TestClient(client.app)
    assert anon.get("/api/vorgaenge").status_code == 403
    assert anon.get("/api/vorgaenge", headers={"X-Portal-Zone": "public"}).status_code == 403
    assert anon.get("/api/vorgaenge",
                    headers={"Authorization": "Bearer geheim"}).status_code == 200
    assert anon.get("/api/public/branding").status_code == 200


@pytest.mark.parametrize("key", list(forms.REGISTRY))
def test_blanko_pdf(client, key):
    r = client.get(f"/api/forms/{key}/pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")
    assert forms.REGISTRY[key]["title"].split("–")[0].strip()[:20] in _pdf_text(r.content)


def test_ablauf_kunde_fuellt_aus_und_reicht_ein(client):
    v = client.post("/api/vorgaenge", json={
        "stammdaten": {"eig_vorname": "Erika", "eig_nachname": "Muster"},
        "paket": "iSFP / Energieberatung"}).json()
    assert v["kunde"] == "Erika Muster"
    assert len(v["formulare"]) == len(forms.PAKETE["iSFP / Energieberatung"])
    b = next(f for f in v["formulare"] if f["form_key"] == "datenblatt_b")
    assert b["freigegeben"] is False  # Berater-Formular nicht im Kundenportal

    portal = client.get(f"/api/public/p/{v['token']}").json()
    assert {f["title"] for f in portal["formulare"]} >= {"Stammdatenblatt Eigentümer / "
                                                         "Antragsteller"}
    assert all(f["audience"] != "berater" for f in portal["formulare"])

    f1 = next(f for f in v["formulare"] if f["form_key"] == "stammdaten_eigentuemer")
    token = f1["link"].rsplit("/", 1)[1]
    view = client.get(f"/api/public/f/{token}").json()
    assert view["data"]["eig_vorname"] == "Erika"  # aus Stammdaten vorbelegt

    r = client.put(f"/api/public/f/{token}", json={"data": {
        "eig_strasse": "Hauptstraße", "eig_hausnr": "1", "eig_plz": "64711",
        "eig_ort": "Erbach", "unbekannt": "x"}})
    assert r.status_code == 200 and r.json()["status"] == "in_bearbeitung"

    r = client.post(f"/api/public/f/{token}/submit", json={"data": {}})
    assert r.status_code == 422
    assert {m["key"] for m in r.json()["fehlend"]} >= {"eig_email", "eig_rolle",
                                                       "unterschrift"}

    r = client.post(f"/api/public/f/{token}/submit", json={"data": {
        "eig_email": "erika@example.org", "eig_rolle": "Alleineigentümer/in",
        "eig_selbstnutzung": "ja", "eig_datenschutz": True, "eig_richtigkeit": True,
        "unterschrift": SIG}})
    assert r.status_code == 200, r.text
    assert r.json()["locked"] is True
    # gesperrt: weitere Kundenänderungen abgelehnt
    assert client.put(f"/api/public/f/{token}", json={"data": {"eig_ort": "X"}}).status_code \
        == 422

    # Geteilte Stammdaten stehen im nächsten Formular bereit
    f2 = next(f for f in v["formulare"] if f["form_key"] == "checkliste_ebw")
    ebw = client.get(f"/api/formulare/{f2['id']}").json()
    assert ebw["data"]["eig_ort"] == "Erbach"
    assert ebw["data"]["eig_email"] == "erika@example.org"
    assert "unterschrift" not in ebw["data"]  # Unterschriften werden nie geteilt

    text = _pdf_text(client.get(f"/api/public/f/{token}/pdf").content)
    assert "Erika" in text and "Erbach" in text

    ev = client.get(f"/api/vorgaenge/{v['id']}/ereignisse").json()
    assert any(e["aktion"] == "eingereicht" for e in ev)


def test_agent_fuellt_formular(client):
    v = client.post("/api/vorgaenge", json={"titel": "Test", "formulare": [
        "fue_gebaeudehuelle"]}).json()
    fid = v["formulare"][0]["id"]
    view = client.get(f"/api/formulare/{fid}").json()
    assert view["data"]["fue_b_wb"] is True  # Default laut Standardregel
    r = client.put(f"/api/formulare/{fid}", json={"data": {
        "fue_bauteile": [{"bauteil": "Dach", "dicke": 180, "lambda": 0.023, "u_ist": 0.14,
                          "u_max": 0.14}], "fu_firma": "Dach GmbH"}})
    assert r.status_code == 200
    assert r.json()["data"]["fue_bauteile"][0]["bauteil"] == "Dach"
    vv = client.get(f"/api/vorgaenge/{v['id']}").json()
    assert vv["stammdaten"]["fu_firma"] == "Dach GmbH"
    assert client.post(f"/api/formulare/{fid}/status", json={"status": "geprueft"}).json()[
        "status"] == "geprueft"


def test_show_if_pflichtfelder():
    form = forms.get("checkliste_ebw")
    base = {k: True for k in forms.field_keys(form) if k.startswith("ebw_e_")}
    miss = {m["key"] for m in forms.missing_required(
        form, base | {"ebw_antragsteller": "Privatperson (Eigentümer/in)"})}
    assert "ebw_deminimis" not in miss
    miss = {m["key"] for m in forms.missing_required(
        form, base | {"ebw_antragsteller": "Unternehmen / Freiberufler/in"})}
    assert "ebw_deminimis" in miss


def test_pdf_filename():
    assert pdf.filename(forms.get("vertrag_heizung"), "Müller").endswith("Müller.pdf")


def test_hero_mapping():
    from app import hero
    sd = hero.project_to_stammdaten({
        "contact": {"title": "Frau", "first_name": "Anna", "last_name": "Beispiel",
                    "email": "a@b.de", "address": {"street": "Am Markt 12a", "zipcode": "64720",
                                                   "city": "Michelstadt"}},
        "address": {"street": "Am Markt 12a", "zipcode": "64720", "city": "Michelstadt"}})
    assert sd["eig_strasse"] == "Am Markt" and sd["eig_hausnr"] == "12a"
    assert sd["obj_gleich_wohnadresse"] == "ja"
    assert hero.split_street("Illigstraße 11") == ("Illigstraße", "11")
    assert hero.split_street("Weg ohne Nummer") == ("Weg ohne Nummer", "")


def test_defekte_unterschrift_bricht_pdf_nicht():
    data = pdf.render(forms.get("stammdaten_gebaeude"),
                      {"unterschrift": "data:image/png;base64,AAAA"})
    assert data.startswith(b"%PDF")


def test_beschreibbares_pdf(client):
    r = client.get("/api/forms/checkliste_beg_em/pdf")
    fields = PdfReader(io.BytesIO(r.content)).get_fields()
    assert fields and "eig_nachname" in fields and "em_huelle__0" in fields
    v = client.post("/api/vorgaenge", json={"formulare": ["stammdaten_gebaeude"],
                                           "stammdaten": {"obj_ort": "Erbach"}}).json()
    fid = v["formulare"][0]["id"]
    r = client.get(f"/api/formulare/{fid}/pdf?ausfuellbar=true")
    fields = PdfReader(io.BytesIO(r.content)).get_fields()
    assert fields["obj_ort"].get("/V") == "Erbach"


def test_platzhalter_aus_firmenkopf(client):
    client.put("/api/einstellungen", json={"firma": "Testfirma GmbH", "strasse": "Weg 1",
                                           "plz_ort": "12345 Ort", "email": "a@b.de"})
    f = client.get("/api/forms/beratungsvertrag").json()
    texte = " ".join(x.get("text", "") for s_ in f["sections"] for x in s_["fields"])
    assert "Testfirma GmbH, Weg 1, 12345 Ort" in texte and "{{" not in texte
    text = _pdf_text(client.get("/api/forms/beratungsvertrag/pdf?ausfuellbar=false").content)
    assert "Testfirma GmbH" in text
