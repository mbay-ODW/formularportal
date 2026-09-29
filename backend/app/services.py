"""Geschäftslogik, die Admin-API, Kundenportal und MCP gemeinsam nutzen."""
from __future__ import annotations

import logging
from typing import Any

from app import branding, config, db, forms, hero, notify, pdf

log = logging.getLogger(__name__)

LOCKED = ("eingereicht", "geprueft")


class NotFound(Exception):
    pass


class Invalid(Exception):
    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details


# ---- Links ----------------------------------------------------------------------
def portal_url(vorgang: dict[str, Any]) -> str:
    return f"{config.PUBLIC_BASE_URL}/p/{vorgang['token']}"


def form_url(formular: dict[str, Any]) -> str:
    return f"{config.PUBLIC_BASE_URL}/f/{formular['token']}"


# ---- Ansichten ----------------------------------------------------------------
def kunde_label(v: dict[str, Any]) -> str:
    sd = v.get("stammdaten") or {}
    name = " ".join(x for x in [sd.get("eig_vorname"), sd.get("eig_nachname")] if x)
    return v.get("kunde_name") or name or sd.get("eig_firma") or ""


def objekt_label(v: dict[str, Any]) -> str:
    sd = v.get("stammdaten") or {}
    street = " ".join(x for x in [sd.get("obj_strasse"), sd.get("obj_hausnr")] if x)
    city = " ".join(x for x in [sd.get("obj_plz"), sd.get("obj_ort")] if x)
    return ", ".join(x for x in [street, city] if x)


def formular_summary(f: dict[str, Any], v: dict[str, Any] | None = None) -> dict[str, Any]:
    form = forms.get(f["form_key"]) or {}
    out = {k: f[k] for k in ("id", "vorgang_id", "form_key", "status", "freigegeben",
                             "created_at", "updated_at", "submitted_at", "expires_at",
                             "abgelaufen", "hero_document_id")}
    out |= {"title": form.get("title", f["form_key"]), "nr": form.get("nr"),
            "audience": form.get("audience"), "link": form_url(f)}
    if v is not None and form:
        merged = forms.merged_data(form, f["data"], v["stammdaten"])
        total = len([x for x in forms.input_fields(form) if x.get("required")])
        missing = forms.missing_required(form, merged)
        out["pflicht_offen"] = len(missing)
        out["pflicht_gesamt"] = total
    return out


def vorgang_view(v: dict[str, Any]) -> dict[str, Any]:
    fl = db.list_formulare(v["id"])
    return v | {"portal_link": portal_url(v), "kunde": kunde_label(v),
                "objekt": objekt_label(v),
                "formulare": [formular_summary(f, v) for f in fl]}


def formular_view(f: dict[str, Any], v: dict[str, Any]) -> dict[str, Any]:
    form = forms.get(f["form_key"], branding.load())
    if not form:
        raise NotFound(f"Formular-Definition {f['form_key']} unbekannt")
    merged = forms.merged_data(form, f["data"], v["stammdaten"])
    return formular_summary(f, v) | {
        "form": form, "data": merged, "locked": f["status"] in LOCKED,
        "fehlend": forms.missing_required(form, merged),
        "vorgang": {"id": v["id"], "titel": v["titel"], "kunde": kunde_label(v),
                    "objekt": objekt_label(v), "hero_project_id": v.get("hero_project_id"),
                    "hero_ref": v.get("hero_ref")},
    }


def load(fid: int) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    f = db.get_formular(fid)
    if not f:
        raise NotFound("Formular nicht gefunden")
    v = db.get_vorgang(f["vorgang_id"])
    form = forms.get(f["form_key"])
    if not v or not form:
        raise NotFound("Vorgang oder Formular-Definition fehlt")
    return f, v, form


# ---- Vorgänge ----------------------------------------------------------------------
def add_forms(vid: int, keys: list[str]) -> list[dict[str, Any]]:
    created = []
    existing = {f["form_key"] for f in db.list_formulare(vid)}
    for k in keys:
        form = forms.get(k)
        if not form:
            raise Invalid(f"Unbekanntes Formular: {k}")
        if k in existing:
            continue
        created.append(db.create_formular(vid, k, freigegeben=form["audience"] != "berater"))
        db.log(vid, created[-1]["id"], "berater", "formular_hinzugefuegt", form["title"])
        existing.add(k)
    return created


async def create_vorgang(titel: str = "", kunde_name: str = "", kunde_email: str = "",
                         stammdaten: dict | None = None, formulare: list[str] | None = None,
                         paket: str | None = None, hero_project_id: int | None = None,
                         notiz: str = "") -> dict[str, Any]:
    sd = dict(stammdaten or {})
    hero_ref, contact_id = "", None
    if hero_project_id:
        p = await hero.get_project(int(hero_project_id))
        if not p:
            raise Invalid(f"HERO-Projekt {hero_project_id} nicht gefunden")
        summ = hero.project_summary(p)
        sd = hero.project_to_stammdaten(p) | sd
        hero_ref, contact_id = summ["hero_ref"], summ["contact_id"]
        kunde_name = kunde_name or summ["kunde"]
        kunde_email = kunde_email or summ["kunde_email"]
        titel = titel or f"{summ['hero_ref']} {summ['name']}".strip()
    if not kunde_name:
        kunde_name = " ".join(x for x in [sd.get("eig_vorname"), sd.get("eig_nachname")] if x)
    kunde_email = kunde_email or sd.get("eig_email") or ""
    titel = titel or kunde_name or "Neuer Vorgang"
    v = db.create_vorgang(titel, kunde_name, kunde_email, sd, hero_project_id=hero_project_id,
                          hero_ref=hero_ref, hero_contact_id=contact_id, notiz=notiz)
    keys = list(formulare or [])
    if paket:
        if paket not in forms.PAKETE:
            raise Invalid(f"Unbekanntes Paket: {paket}")
        keys = forms.PAKETE[paket] + [k for k in keys if k not in forms.PAKETE[paket]]
    if keys:
        add_forms(v["id"], keys)
    return vorgang_view(db.get_vorgang(v["id"]))  # type: ignore[arg-type]


async def hero_sync(vid: int, overwrite: bool = False) -> dict[str, Any]:
    v = db.get_vorgang(vid)
    if not v:
        raise NotFound("Vorgang nicht gefunden")
    if not v.get("hero_project_id"):
        raise Invalid("Vorgang ist nicht mit einem HERO-Projekt verknüpft")
    p = await hero.get_project(int(v["hero_project_id"]))
    if not p:
        raise Invalid("HERO-Projekt nicht gefunden")
    imported = hero.project_to_stammdaten(p)
    sd = dict(v["stammdaten"])
    changed = []
    for k, val in imported.items():
        if overwrite or sd.get(k) in (None, "", []):
            if sd.get(k) != val:
                sd[k] = val
                changed.append(k)
    db.update_vorgang(vid, stammdaten=sd)
    db.log(vid, None, "berater", "hero_import", ", ".join(changed) or "keine Änderungen")
    return {"uebernommen": changed}


# ---- Formulare ---------------------------------------------------------------------
def save_data(fid: int, data: dict[str, Any], akteur: str, *, replace: bool = False,
              allow_locked: bool = False) -> dict[str, Any]:
    f, v, form = load(fid)
    if f["status"] in LOCKED and not allow_locked:
        raise Invalid("Formular ist bereits eingereicht und gesperrt")
    cleaned = forms.clean(form, data)
    new = cleaned if replace else {**f["data"], **cleaned}
    status = f["status"]
    if status == "entwurf" and akteur == "kunde":
        status = "in_bearbeitung"
    db.update_formular(fid, data=new, status=status)
    shared = forms.split_shared(form, cleaned)
    if shared:
        db.merge_stammdaten(v["id"], shared)
    f, v, _ = load(fid)
    return formular_view(f, v)


def submit(fid: int, data: dict[str, Any] | None, akteur: str) -> dict[str, Any]:
    if data:
        save_data(fid, data, akteur, allow_locked=akteur != "kunde")
    f, v, form = load(fid)
    if f["status"] in LOCKED and akteur == "kunde":
        raise Invalid("Formular wurde bereits eingereicht")
    merged = forms.merged_data(form, f["data"], v["stammdaten"])
    missing = forms.missing_required(form, merged)
    if missing:
        raise Invalid("Pflichtangaben fehlen", missing)
    snapshot = forms.clean(form, merged)
    db.update_formular(fid, data=snapshot, status="eingereicht", submitted_at=db.now())
    db.log(v["id"], fid, akteur, "eingereicht", form["title"])
    f, v, _ = load(fid)
    return formular_view(f, v)


def render_pdf(fid: int, blank: bool = False, fillable: bool = False) -> tuple[bytes, str]:
    f, v, _ = load(fid)
    settings = branding.load()
    form = forms.get(f["form_key"], settings)
    merged = forms.merged_data(form, f["data"], v["stammdaten"])
    meta = {"kunde": kunde_label(v), "objekt": objekt_label(v),
            "submitted_at": f.get("submitted_at")}
    name = pdf.filename(form, kunde_label(v))
    if fillable:
        name = name.replace(".pdf", "_ausfuellbar.pdf")
    return (pdf.render(form, merged, blank=blank, fillable=fillable, meta=meta,
                       settings=settings), name)


def set_status(fid: int, status: str, akteur: str) -> dict[str, Any]:
    if status not in db.STATUS:
        raise Invalid(f"Status muss einer von {', '.join(db.STATUS)} sein")
    f, v, form = load(fid)
    fields: dict[str, Any] = {"status": status}
    if status == "eingereicht" and not f.get("submitted_at"):
        fields["submitted_at"] = db.now()
    if status in ("entwurf", "in_bearbeitung"):
        fields["submitted_at"] = None
    db.update_formular(fid, **fields)
    db.log(v["id"], fid, akteur, f"status_{status}", form["title"])
    f, v, _ = load(fid)
    return formular_view(f, v)


async def upload_to_hero(fid: int, akteur: str,
                         document_type_id: int | None = None) -> dict[str, Any]:
    f, v, form = load(fid)
    if not v.get("hero_project_id"):
        raise Invalid("Vorgang ist nicht mit einem HERO-Projekt verknüpft")
    data, name = render_pdf(fid)
    res = await hero.upload_pdf(int(v["hero_project_id"]), name, data, document_type_id)
    doc_id = str(res.get("id") or "")
    db.update_formular(fid, hero_document_id=doc_id)
    db.log(v["id"], fid, akteur, "hero_upload", f"{form['title']} → Dokument {doc_id}")
    await hero.add_logbook(int(v["hero_project_id"]),
                           f"Formularportal: „{form['title']}“ als PDF abgelegt.")
    return {"hero_document": res, "dateiname": name}


# ---- Nach dem Einreichen ------------------------------------------------------------
async def after_submit(fid: int) -> None:
    """Benachrichtigung + optional HERO-Upload. Fehler landen im Ereignisprotokoll."""
    try:
        f, v, form = load(fid)
    except NotFound:
        return
    s = branding.load()
    to = s.get("benachrichtigung_email") or s.get("email")
    kunde = kunde_label(v) or v["titel"]
    admin_link = f"{config.PUBLIC_BASE_URL}/vorgang/{v['id']}"
    if to and notify.smtp_configured():
        try:
            data, name = render_pdf(fid)
            notify.send_mail(
                to, f"Formular eingereicht: {form['title']} – {kunde}",
                f"{kunde} hat das Formular „{form['title']}“ eingereicht.\n\n"
                f"Vorgang: {v['titel']}\nObjekt: {objekt_label(v) or '–'}\n\n"
                f"Im Portal ansehen: {admin_link}\n\nDas PDF liegt dieser Mail bei.",
                from_name=s.get("firma", ""), attachments=[(name, data, "application/pdf")])
            db.log(v["id"], fid, "system", "mail_berater", to)
        except Exception as e:  # noqa: BLE001
            log.exception("Mail fehlgeschlagen")
            db.log(v["id"], fid, "system", "mail_fehler", str(e))
    kunde_mail = (v["stammdaten"].get("fu_email") if form["audience"] == "fachunternehmen"
                  else v["stammdaten"].get("eig_email") or v.get("kunde_email"))
    if kunde_mail and s.get("kopie_an_kunde") == "ja" and notify.smtp_configured():
        try:
            data, name = render_pdf(fid)
            notify.send_mail(
                kunde_mail, f"Ihre Angaben: {form['title']}",
                f"Guten Tag,\n\nvielen Dank – wir haben Ihr Formular „{form['title']}“ "
                "erhalten. Eine Kopie Ihrer Angaben finden Sie im Anhang.\n\n"
                f"Viele Grüße\n{s.get('inhaber') or ''}\n{s.get('firma') or ''}\n"
                f"{s.get('telefon') or ''}",
                reply_to=s.get("email") or "", from_name=s.get("firma", ""),
                attachments=[(name, data, "application/pdf")])
            db.log(v["id"], fid, "system", "kopie_an_kunde", kunde_mail)
        except Exception as e:  # noqa: BLE001
            log.exception("Kopie an Kunden fehlgeschlagen")
            db.log(v["id"], fid, "system", "mail_fehler", str(e))
    notify.push(f"Formular eingereicht: {kunde}", form["title"], click=admin_link)
    if config.HERO_AUTO_UPLOAD and v.get("hero_project_id") and hero.configured():
        try:
            await upload_to_hero(fid, "system")
        except Exception as e:  # noqa: BLE001
            log.exception("HERO-Upload fehlgeschlagen")
            db.log(v["id"], fid, "system", "hero_fehler", str(e))


def send_link(v: dict[str, Any], to: str, link: str, titel: str, nachricht: str = "") -> None:
    s = branding.load()
    anrede = kunde_label(v)
    body = (f"Guten Tag{(' ' + anrede) if anrede else ''},\n\n"
            + (nachricht.strip() + "\n\n" if nachricht.strip() else "")
            + f"über den folgenden Link erreichen Sie {titel}:\n\n{link}\n\n"
            "Ihre Eingaben werden automatisch gespeichert – Sie können jederzeit "
            "unterbrechen und später weitermachen.\n\n"
            f"Viele Grüße\n{s.get('inhaber') or ''}\n{s.get('firma') or ''}\n"
            f"{s.get('telefon') or ''}\n{s.get('website') or ''}").strip() + "\n"
    notify.send_mail(to, f"{s.get('firma') or 'Energieberatung'}: Ihre Formulare",
                     body, reply_to=s.get("email") or "", from_name=s.get("firma", ""))
