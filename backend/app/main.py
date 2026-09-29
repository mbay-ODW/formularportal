"""Formularportal – FastAPI-Backend.

Zonen:
  /api/public/*  Kundenportal (Token-Links, ohne Login; eigener Traefik-Router)
  /api/*         Verwaltung (hinter Authelia; zusätzlich Zonen-Header bzw.
                 interner API-Key für den MCP-Container)
"""
from __future__ import annotations

import hmac
import logging
from contextlib import asynccontextmanager
from typing import Any
from urllib.parse import quote

from fastapi import (APIRouter, BackgroundTasks, Body, Depends, FastAPI, File, HTTPException,
                     Request, UploadFile)
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel, Field

from app import branding, config, db, forms, hero, notify, pdf, services
from app.services import Invalid, NotFound

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")



@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Formularportal", docs_url=None, redoc_url=None, lifespan=lifespan)


@app.exception_handler(NotFound)
async def _nf(_r: Request, e: NotFound):
    return JSONResponse({"detail": str(e)}, status_code=404)


@app.exception_handler(Invalid)
async def _inv(_r: Request, e: Invalid):
    return JSONResponse({"detail": str(e), "fehlend": e.details}, status_code=422)


@app.exception_handler(hero.HeroError)
async def _hero(_r: Request, e: hero.HeroError):
    return JSONResponse({"detail": str(e)}, status_code=502)


def _pdf_response(data: bytes, name: str, inline: bool = True) -> Response:
    disp = "inline" if inline else "attachment"
    ascii_name = name.encode("ascii", "ignore").decode() or "formular.pdf"
    return Response(data, media_type="application/pdf", headers={
        "Content-Disposition": f"{disp}; filename=\"{ascii_name}\"; "
                               f"filename*=UTF-8''{quote(name)}",
        "Cache-Control": "no-store"})


@app.get("/api/health")
def health():
    return {"status": "ok"}


# =============================================================================
# Öffentlicher Bereich (Kundenportal)
# =============================================================================
public = APIRouter(prefix="/api/public", tags=["public"])


def _public_formular(token: str) -> tuple[dict, dict]:
    f = db.get_formular_by_token(token)
    if not f:
        raise HTTPException(404, "Link ungültig")
    if f["abgelaufen"]:
        raise HTTPException(410, "Dieser Link ist abgelaufen. Bitte fordern Sie einen neuen an.")
    v = db.get_vorgang(f["vorgang_id"])
    if not v or v["archiviert"]:
        raise HTTPException(404, "Link ungültig")
    return f, v


def _public_view(f: dict, v: dict) -> dict[str, Any]:
    view = services.formular_view(f, v)
    return {"token": f["token"], "status": view["status"], "locked": view["locked"],
            "form": view["form"], "data": view["data"], "fehlend": view["fehlend"],
            "submitted_at": f.get("submitted_at"),
            "portal_token": v["token"] if f["freigegeben"] else None,
            "kunde": view["vorgang"]["kunde"], "objekt": view["vorgang"]["objekt"],
            "branding": branding.public()}


async def _json_limited(request: Request) -> dict[str, Any]:
    raw = await request.body()
    if len(raw) > config.MAX_FORM_PAYLOAD_BYTES:
        raise HTTPException(413, "Daten zu groß")
    try:
        body = await request.json()
    except ValueError:
        raise HTTPException(400, "Ungültiges JSON") from None
    if not isinstance(body, dict):
        raise HTTPException(400, "Objekt erwartet")
    return body


@public.get("/branding")
def public_branding():
    return branding.public()


@public.get("/logo")
def public_logo():
    p = branding.logo_path()
    return FileResponse(p, headers={"Cache-Control": "public, max-age=300"})


@public.get("/p/{token}")
def public_portal(token: str):
    v = db.get_vorgang_by_token(token)
    if not v or v["archiviert"]:
        raise HTTPException(404, "Link ungültig")
    items = []
    for f in db.list_formulare(v["id"]):
        if not f["freigegeben"] or f["abgelaufen"]:
            continue
        form = forms.get(f["form_key"]) or {}
        items.append({"token": f["token"], "title": form.get("title"), "nr": form.get("nr"),
                      "description": form.get("description"), "status": f["status"],
                      "audience": form.get("audience"), "updated_at": f["updated_at"]})
    return {"kunde": services.kunde_label(v), "objekt": services.objekt_label(v),
            "titel": v["titel"], "formulare": items, "branding": branding.public()}


@public.get("/f/{token}")
def public_form(token: str):
    f, v = _public_formular(token)
    return _public_view(f, v)


@public.put("/f/{token}")
async def public_save(token: str, request: Request):
    f, v = _public_formular(token)
    body = await _json_limited(request)
    services.save_data(f["id"], body.get("data") or {}, "kunde")
    f, v = _public_formular(token)
    view = _public_view(f, v)
    return {"status": view["status"], "fehlend": view["fehlend"], "gespeichert": db.now()}


@public.post("/f/{token}/submit")
async def public_submit(token: str, request: Request, bg: BackgroundTasks):
    f, v = _public_formular(token)
    body = await _json_limited(request)
    services.submit(f["id"], body.get("data") or {}, "kunde")
    bg.add_task(services.after_submit, f["id"])
    f, v = _public_formular(token)
    return _public_view(f, v)


@public.get("/f/{token}/pdf")
def public_pdf(token: str):
    f, _ = _public_formular(token)
    data, name = services.render_pdf(f["id"])
    return _pdf_response(data, name)


app.include_router(public)


# =============================================================================
# Verwaltung
# =============================================================================
def admin_guard(request: Request) -> str:
    """Liefert den Akteur (Authelia-User) oder wirft 403."""
    user = request.headers.get("remote-user") or request.headers.get("x-forwarded-user") or ""
    auth = request.headers.get("authorization", "")
    if config.INTERNAL_API_KEY and auth.startswith("Bearer ") and hmac.compare_digest(
            auth[7:], config.INTERNAL_API_KEY):
        return "agent"
    if config.ADMIN_GUARD == "off":
        return user or "berater"
    if request.headers.get("x-portal-zone") == "admin":
        return user or "berater"
    raise HTTPException(403, "Kein Zugriff")


admin = APIRouter(prefix="/api", tags=["admin"], dependencies=[Depends(admin_guard)])


class VorgangIn(BaseModel):
    titel: str = ""
    kunde_name: str = ""
    kunde_email: str = ""
    stammdaten: dict[str, Any] = Field(default_factory=dict)
    formulare: list[str] = Field(default_factory=list)
    paket: str | None = None
    hero_project_id: int | None = None
    notiz: str = ""


class VorgangPatch(BaseModel):
    titel: str | None = None
    kunde_name: str | None = None
    kunde_email: str | None = None
    stammdaten: dict[str, Any] | None = None
    hero_project_id: int | None = None
    hero_ref: str | None = None
    notiz: str | None = None
    archiviert: bool | None = None


class FormularPatch(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    replace: bool = False


class LinkMail(BaseModel):
    email: str = ""
    nachricht: str = ""


@admin.get("/me")
def me(akteur: str = Depends(admin_guard)):
    return {"user": akteur, "hero": hero.configured(), "smtp": notify.smtp_configured(),
            "ntfy": notify.ntfy_configured(), "hero_auto_upload": config.HERO_AUTO_UPLOAD,
            "public_base_url": config.PUBLIC_BASE_URL}


# ---- Katalog -----------------------------------------------------------------------
@admin.get("/forms")
def form_catalog():
    return {"formulare": forms.catalog(), "pakete": forms.PAKETE}


@admin.get("/forms/{key}")
def form_def(key: str):
    f = forms.get(key)
    if not f:
        raise HTTPException(404, "Unbekanntes Formular")
    return f


@admin.get("/forms/{key}/pdf")
def form_blank_pdf(key: str):
    f = forms.get(key)
    if not f:
        raise HTTPException(404, "Unbekanntes Formular")
    return _pdf_response(pdf.render(f, blank=True), pdf.filename(f, "Vorlage"))


# ---- Vorgänge ------------------------------------------------------------------------
@admin.get("/vorgaenge")
def vorgaenge(q: str = "", archiviert: bool = False):
    out = []
    for v in db.list_vorgaenge(q, archiviert):
        out.append(v | {"kunde": services.kunde_label(v), "objekt": services.objekt_label(v)})
    return out


@admin.post("/vorgaenge", status_code=201)
async def vorgang_neu(body: VorgangIn):
    return await services.create_vorgang(**body.model_dump())


@admin.get("/vorgaenge/{vid}")
def vorgang(vid: int):
    v = db.get_vorgang(vid)
    if not v:
        raise HTTPException(404, "Vorgang nicht gefunden")
    return services.vorgang_view(v)


@admin.patch("/vorgaenge/{vid}")
def vorgang_patch(vid: int, body: VorgangPatch, akteur: str = Depends(admin_guard)):
    if not db.get_vorgang(vid):
        raise HTTPException(404, "Vorgang nicht gefunden")
    v = db.update_vorgang(vid, **body.model_dump(exclude_none=True))
    db.log(vid, None, akteur, "vorgang_geaendert",
           ", ".join(body.model_dump(exclude_none=True).keys()))
    return services.vorgang_view(v)  # type: ignore[arg-type]


@admin.delete("/vorgaenge/{vid}", status_code=204)
def vorgang_loeschen(vid: int):
    db.delete_vorgang(vid)
    return Response(status_code=204)


@admin.get("/vorgaenge/{vid}/ereignisse")
def vorgang_ereignisse(vid: int):
    return db.list_ereignisse(vid)


@admin.post("/vorgaenge/{vid}/formulare", status_code=201)
def vorgang_formulare(vid: int, keys: list[str] = Body(..., embed=True)):
    if not db.get_vorgang(vid):
        raise HTTPException(404, "Vorgang nicht gefunden")
    services.add_forms(vid, keys)
    return services.vorgang_view(db.get_vorgang(vid))  # type: ignore[arg-type]


@admin.post("/vorgaenge/{vid}/hero-sync")
async def vorgang_hero_sync(vid: int, overwrite: bool = False):
    return await services.hero_sync(vid, overwrite)


@admin.post("/vorgaenge/{vid}/link-senden")
def vorgang_link_senden(vid: int, body: LinkMail, akteur: str = Depends(admin_guard)):
    v = db.get_vorgang(vid)
    if not v:
        raise HTTPException(404, "Vorgang nicht gefunden")
    to = body.email or v["kunde_email"] or v["stammdaten"].get("eig_email")
    if not to:
        raise HTTPException(422, "Keine E-Mail-Adresse hinterlegt")
    services.send_link(v, to, services.portal_url(v), "Ihre Formulare", body.nachricht)
    db.log(vid, None, akteur, "link_gesendet", to)
    return {"gesendet_an": to}


@admin.post("/vorgaenge/{vid}/neuer-link")
def vorgang_neuer_link(vid: int, akteur: str = Depends(admin_guard)):
    v = db.get_vorgang(vid)
    if not v:
        raise HTTPException(404, "Vorgang nicht gefunden")
    with db.connect() as con:
        con.execute("UPDATE vorgang SET token=? WHERE id=?", (db.new_token(), vid))
    db.log(vid, None, akteur, "portal_link_erneuert")
    return services.vorgang_view(db.get_vorgang(vid))  # type: ignore[arg-type]


# ---- Formulare -------------------------------------------------------------------------
@admin.get("/formulare/{fid}")
def formular(fid: int):
    f, v, _ = services.load(fid)
    return services.formular_view(f, v)


@admin.put("/formulare/{fid}")
def formular_speichern(fid: int, body: FormularPatch, akteur: str = Depends(admin_guard)):
    return services.save_data(fid, body.data, akteur, replace=body.replace, allow_locked=True)


@admin.post("/formulare/{fid}/einreichen")
def formular_einreichen(fid: int, bg: BackgroundTasks, akteur: str = Depends(admin_guard)):
    view = services.submit(fid, None, akteur)
    bg.add_task(services.after_submit, fid)
    return view


@admin.post("/formulare/{fid}/status")
def formular_status(fid: int, status: str = Body(..., embed=True),
                    akteur: str = Depends(admin_guard)):
    return services.set_status(fid, status, akteur)


@admin.patch("/formulare/{fid}")
def formular_patch(fid: int, freigegeben: bool = Body(..., embed=True)):
    services.load(fid)
    db.update_formular(fid, freigegeben=freigegeben)
    f, v, _ = services.load(fid)
    return services.formular_summary(f, v)


@admin.post("/formulare/{fid}/neuer-link")
def formular_neuer_link(fid: int, akteur: str = Depends(admin_guard)):
    f, v, form = services.load(fid)
    db.update_formular(fid, token=db.new_token(), expires_at=db.expiry())
    db.log(v["id"], fid, akteur, "formular_link_erneuert", form["title"])
    f, v, _ = services.load(fid)
    return services.formular_summary(f, v)


@admin.post("/formulare/{fid}/link-senden")
def formular_link_senden(fid: int, body: LinkMail, akteur: str = Depends(admin_guard)):
    f, v, form = services.load(fid)
    to = body.email or (v["stammdaten"].get("fu_email") if form["audience"] == "fachunternehmen"
                        else v["kunde_email"] or v["stammdaten"].get("eig_email"))
    if not to:
        raise HTTPException(422, "Keine E-Mail-Adresse angegeben")
    services.send_link(v, to, services.form_url(f), f"das Formular „{form['title']}“",
                       body.nachricht)
    db.log(v["id"], fid, akteur, "link_gesendet", f"{form['title']} → {to}")
    return {"gesendet_an": to}


@admin.get("/formulare/{fid}/pdf")
def formular_pdf(fid: int, download: bool = False):
    data, name = services.render_pdf(fid)
    return _pdf_response(data, name, inline=not download)


@admin.post("/formulare/{fid}/hero-upload")
async def formular_hero_upload(fid: int, akteur: str = Depends(admin_guard),
                               document_type_id: int | None = None):
    return await services.upload_to_hero(fid, akteur, document_type_id)


@admin.delete("/formulare/{fid}", status_code=204)
def formular_loeschen(fid: int, akteur: str = Depends(admin_guard)):
    f, v, form = services.load(fid)
    db.delete_formular(fid)
    db.log(v["id"], None, akteur, "formular_entfernt", form["title"])
    return Response(status_code=204)


# ---- HERO ----------------------------------------------------------------------------
@admin.get("/hero/projekte")
async def hero_projekte(q: str = "", limit: int = 15):
    if not hero.configured():
        return []
    return await hero.search_projects(q, limit)


@admin.get("/hero/kontakte")
async def hero_kontakte(q: str = "", limit: int = 15):
    if not hero.configured():
        return []
    return await hero.search_contacts(q, limit)


# ---- Einstellungen -----------------------------------------------------------------------
@admin.get("/einstellungen")
def einstellungen():
    return branding.load() | {"eigenes_logo": branding.has_custom_logo()}


@admin.put("/einstellungen")
def einstellungen_speichern(body: dict[str, Any] = Body(...)):
    return branding.save(body) | {"eigenes_logo": branding.has_custom_logo()}


@admin.post("/einstellungen/logo")
async def logo_upload(file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > config.MAX_LOGO_BYTES:
        raise HTTPException(413, "Logo größer als 2 MB")
    try:
        branding.save_logo(data, file.filename or "")
    except ValueError as e:
        raise HTTPException(422, str(e)) from None
    return {"ok": True}


@admin.delete("/einstellungen/logo")
def logo_loeschen():
    branding.delete_logo()
    return {"ok": True}


@admin.post("/einstellungen/testmail")
def testmail(akteur: str = Depends(admin_guard)):
    s = branding.load()
    to = s.get("benachrichtigung_email") or s.get("email")
    if not to:
        raise HTTPException(422, "Keine Benachrichtigungs-Adresse hinterlegt")
    notify.send_mail(to, "Formularportal: Testmail",
                     f"Der Mailversand funktioniert.\n\nAusgelöst von: {akteur}",
                     from_name=s.get("firma", ""))
    return {"gesendet_an": to}


app.include_router(admin)
