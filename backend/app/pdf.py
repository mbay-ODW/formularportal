"""PDF-Erzeugung (ausgefüllt oder als leere Druckvorlage) mit Branding.

ReportLab/Platypus statt HTML-Renderer: keine Systemabhängigkeiten außer einer
TTF-Schrift (DejaVu, im Image enthalten) für Umlaute und Ankreuzkästchen.
"""
from __future__ import annotations

import base64
import io
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (Flowable, Image, KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from app import branding
from app.forms._dsl import INPUT_TYPES, cond_ok

_FONT_DIRS = [Path("/usr/share/fonts/truetype/dejavu"), Path("/usr/share/fonts/dejavu")]
FONT, FONT_B = "Helvetica", "Helvetica-Bold"
BOX_ON, BOX_OFF = "[x]", "[  ]"
for _d in _FONT_DIRS:
    if (_d / "DejaVuSans.ttf").exists():
        pdfmetrics.registerFont(TTFont("DejaVu", str(_d / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_d / "DejaVuSans-Bold.ttf")))
        FONT, FONT_B = "DejaVu", "DejaVu-Bold"
        BOX_ON, BOX_OFF = "☒", "☐"
        break

PAGE_W, PAGE_H = A4
MARGIN_X = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X
WIDTHS = {"full": 1.0, "half": 0.5, "third": 1 / 3, "two-thirds": 2 / 3, "quarter": 0.25}


def _styles(s: dict[str, Any]) -> dict[str, ParagraphStyle]:
    ink = colors.HexColor(s.get("farbe_text") or "#0e2a40")
    prim = colors.HexColor(s.get("farbe_primaer") or "#0b6e7f")
    return {
        "title": ParagraphStyle("title", fontName=FONT_B, fontSize=15, leading=19,
                                textColor=prim, spaceAfter=2),
        "meta": ParagraphStyle("meta", fontName=FONT, fontSize=8.5, leading=11,
                               textColor=colors.HexColor("#5b6b70")),
        "h2": ParagraphStyle("h2", fontName=FONT_B, fontSize=10.5, leading=14, textColor=prim),
        "intro": ParagraphStyle("intro", fontName=FONT, fontSize=8.5, leading=11,
                                textColor=colors.HexColor("#5b6b70")),
        "label": ParagraphStyle("label", fontName=FONT, fontSize=7, leading=9,
                                textColor=colors.HexColor("#6b7a7e")),
        "value": ParagraphStyle("value", fontName=FONT, fontSize=9.5, leading=12, textColor=ink),
        "check": ParagraphStyle("check", fontName=FONT, fontSize=9, leading=12, textColor=ink),
        "info": ParagraphStyle("info", fontName=FONT, fontSize=8, leading=10.5, textColor=ink),
        "cell": ParagraphStyle("cell", fontName=FONT, fontSize=8, leading=10, textColor=ink),
        "cellh": ParagraphStyle("cellh", fontName=FONT_B, fontSize=7.5, leading=9.5,
                                textColor=colors.white),
    }


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def _fmt_date(v: str) -> str:
    try:
        return datetime.strptime(v[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return str(v)


def _fmt_num(v: Any) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    s = f"{f:,.2f}".rstrip("0").rstrip(".") if f % 1 else f"{int(f):,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _value_text(f: dict[str, Any], v: Any) -> str:
    t = f["type"]
    if v in (None, "", []):
        return ""
    if t == "date":
        return _fmt_date(v)
    if t == "number":
        return _fmt_num(v) + (f" {f['unit']}" if f.get("unit") else "")
    return str(v)


def _options_line(options: list[str], chosen: Any, multi: bool) -> str:
    sel = set(chosen or []) if multi else {chosen}
    return "&nbsp;&nbsp;&nbsp; ".join(f"{BOX_ON if o in sel else BOX_OFF}&nbsp;{escape(o)}"
                                      for o in options)


def _signature(v: Any, blank: bool) -> Any:
    if not blank and isinstance(v, str) and v.startswith("data:image/png;base64,"):
        try:
            raw = base64.b64decode(v.split(",", 1)[1])
            with PILImage.open(io.BytesIO(raw)) as probe:
                probe.load()  # defekte Daten hier abfangen, nicht erst beim Build
                iw, ih = probe.size
            h = 18 * mm
            w = min(70 * mm, h * iw / max(ih, 1))
            return Image(io.BytesIO(raw), width=w, height=h)
        except Exception:  # noqa: BLE001 – kaputte Signatur nicht das ganze PDF kosten lassen
            pass
    return Spacer(1, 18 * mm)


class AcroText(Flowable):
    """Beschreibbares Textfeld (AcroForm) an der aktuellen Position."""

    def __init__(self, name: str, width: float, height: float, value: Any = "",
                 multiline: bool = False):
        super().__init__()
        self.name, self.width, self.height = name, width, height
        self.value = "" if value in (None, []) else str(value)
        self.multiline = multiline

    def wrap(self, aw, ah):
        self.width = min(self.width, aw)
        return self.width, self.height

    def draw(self):
        self.canv.acroForm.textfield(
            name=self.name, value=self.value, x=0, y=0, width=self.width, height=self.height,
            fontName="Helvetica", fontSize=0 if self.multiline else 9, borderWidth=0.5,
            borderColor=colors.HexColor("#9fb3b8"), fillColor=colors.HexColor("#f7fafb"),
            textColor=colors.HexColor("#0e2a40"), forceBorder=True, relative=True,
            fieldFlags="multiline" if self.multiline else "")


class AcroCheck(Flowable):
    """Beschreibbares Ankreuzfeld (AcroForm)."""

    def __init__(self, name: str, checked: bool = False, size: float = 3.6 * mm):
        super().__init__()
        self.name, self.checked, self.size = name, checked, size

    def wrap(self, aw, ah):
        return self.size, self.size

    def draw(self):
        self.canv.acroForm.checkbox(
            name=self.name, checked=self.checked, x=0, y=0, size=self.size, buttonStyle="cross",
            borderWidth=0.5, borderColor=colors.HexColor("#6b7a7e"), fillColor=colors.white,
            textColor=colors.HexColor("#0e2a40"), forceBorder=True, relative=True)


class _Doc:
    def __init__(self, form: dict[str, Any], data: dict[str, Any], blank: bool,
                 settings: dict[str, Any], meta: dict[str, Any], fillable: bool = False):
        self.form, self.data, self.blank = form, data, blank
        self.fillable = fillable
        self.s = settings
        self.st = _styles(settings)
        self.meta = meta
        self.prim = colors.HexColor(settings.get("farbe_primaer") or "#0b6e7f")
        self.acc = colors.HexColor(settings.get("farbe_akzent") or "#3fa535")
        self.line = colors.HexColor("#d5dfe1")

    # -- Kopf/Fuß auf jeder Seite --
    def on_page(self, c: rl_canvas.Canvas, _doc) -> None:
        s = self.s
        top = PAGE_H - 12 * mm
        logo = branding.logo_path()
        x_text = MARGIN_X
        try:
            img = ImageReader(str(logo))
            iw, ih = img.getSize()
            h = 14 * mm
            w = min(40 * mm, h * iw / max(ih, 1))
            c.drawImage(img, MARGIN_X, top - h, width=w, height=h, mask="auto",
                        preserveAspectRatio=True)
            x_text = MARGIN_X + w + 4 * mm
        except Exception:  # noqa: BLE001
            pass
        c.setFillColor(self.prim)
        c.setFont(FONT_B, 11)
        c.drawString(x_text, top - 5 * mm, s.get("firma") or "")
        c.setFillColor(colors.HexColor("#5b6b70"))
        c.setFont(FONT, 7.5)
        line2 = " · ".join(x for x in [s.get("inhaber"), s.get("zusatz")] if x)
        line3 = " · ".join(x for x in [s.get("strasse"), s.get("plz_ort"), s.get("telefon"),
                                       s.get("email"), s.get("website")] if x)
        c.drawString(x_text, top - 9 * mm, line2)
        c.drawString(x_text, top - 12.5 * mm, line3)
        c.setStrokeColor(self.prim)
        c.setLineWidth(1.2)
        c.line(MARGIN_X, top - 16 * mm, PAGE_W - MARGIN_X, top - 16 * mm)
        c.setStrokeColor(self.acc)
        c.setLineWidth(0.6)
        c.line(MARGIN_X, top - 16.9 * mm, PAGE_W - MARGIN_X, top - 16.9 * mm)
        # Fuß
        c.setFont(FONT, 7)
        c.setFillColor(colors.HexColor("#6b7a7e"))
        foot = f"{self.form['title']} · Stand {self.form.get('version', '')}"
        if s.get("fusszeile"):
            foot += f" · {s['fusszeile']}"
        c.drawString(MARGIN_X, 10 * mm, foot[:150])
        c.drawRightString(PAGE_W - MARGIN_X, 10 * mm, f"Seite {c.getPageNumber()}")

    # -- Inhalt --
    def visible(self, cond) -> bool:
        return self.blank or self.fillable or cond_ok(cond, self.data)

    # -- beschreibbare Variante --
    def _opts(self, key: str, options: list[str], chosen: Any, multi: bool, width: float,
              inline: bool = False) -> Table:
        sel = set(chosen or []) if multi else {chosen}
        st = self.st["check"]
        cells = [[AcroCheck(f"{key}__{i}", o in sel), Paragraph(escape(o), st)]
                 for i, o in enumerate(options)]
        if inline:
            row = [c for pair in cells for c in pair]
            widths = [6 * mm, 20 * mm] * len(cells)
            tbl = Table([row], colWidths=widths, hAlign="LEFT")
        else:
            per = 2 if len(options) > 4 and width > 0.6 else 1
            rows = []
            for i in range(0, len(cells), per):
                chunk = cells[i:i + per]
                row = [c for pair in chunk for c in pair]
                row += ["", ""] * (per - len(chunk))
                rows.append(row)
            cw = CONTENT_W * width / per
            tbl = Table(rows, colWidths=[6 * mm, cw - 6 * mm] * per, hAlign="LEFT")
        tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                 ("TOPPADDING", (0, 0), (-1, -1), 1),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
        return tbl

    def fillable_cell(self, f: dict[str, Any], width: float) -> list[Any]:
        t, st = f["type"], self.st
        v = None if self.blank else self.data.get(f["key"])
        label = f["label"] + (" *" if f.get("required") else "")
        w = CONTENT_W * width - 6
        if t in ("select", "radio"):
            return [_p(label, st["label"]), self._opts(f["key"], f["options"], v, False, width)]
        if t == "checks":
            return [_p(label, st["label"]), self._opts(f["key"], f["options"], v, True, width)]
        if t == "yesno":
            return [_p(label, st["label"]),
                    self._opts(f["key"], ["ja", "nein"], v, False, width, inline=True)]
        if t == "check":
            tbl = Table([[AcroCheck(f["key"], v is True), Paragraph(escape(f["label"]),
                                                                  st["check"])]],
                        colWidths=[6 * mm, w - 6 * mm], hAlign="LEFT")
            tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                     ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
            return [tbl]
        if t == "signature":
            return [_signature(v, self.blank), _p(label, st["label"])]
        txt = _value_text(f, v) if v not in (None, "") else ""
        if t == "number" and v not in (None, ""):
            txt = _fmt_num(v)
        if t == "textarea":
            return [_p(label, st["label"]), AcroText(f["key"], w, 16 * mm, txt, multiline=True)]
        unit = f" [{f['unit']}]" if t == "number" and f.get("unit") else ""
        return [_p(label + unit, st["label"]), AcroText(f["key"], w, 6 * mm, txt)]

    def field_cell(self, f: dict[str, Any], width: float) -> list[Any]:
        if self.fillable:
            return self.fillable_cell(f, width)
        t, st = f["type"], self.st
        v = self.data.get(f["key"])
        label = f["label"] + (" *" if f.get("required") and self.blank else "")
        if t in ("select", "radio"):
            if self.blank or t == "radio":
                return [_p(label, st["label"]),
                        Paragraph(_options_line(f["options"], None if self.blank else v, False),
                                  st["check"])]
            return [_p(label, st["label"]), _p(_value_text(f, v) or "–", st["value"])]
        if t == "checks":
            return [_p(label, st["label"]),
                    Paragraph(_options_line(f["options"], None if self.blank else v, True),
                              st["check"])]
        if t == "yesno":
            return [_p(label, st["label"]),
                    Paragraph(_options_line(["ja", "nein"], None if self.blank else v, False),
                              st["check"])]
        if t == "check":
            on = (v is True) and not self.blank
            return [Paragraph(f"{BOX_ON if on else BOX_OFF} {escape(f['label'])}", st["check"])]
        if t == "signature":
            return [_signature(v, self.blank), _p(label, st["label"])]
        if t == "textarea":
            if self.blank:
                return [_p(label, st["label"]), Spacer(1, 16 * mm)]
            return [_p(label, st["label"]), _p(v or "–", st["value"])]
        if self.blank:
            return [_p(label, st["label"]), Spacer(1, 6 * mm)]
        return [_p(label, st["label"]), _p(_value_text(f, v) or "–", st["value"])]

    def table_flow(self, f: dict[str, Any]) -> list[Any]:
        st = self.st
        cols = f["columns"]
        header = [_p(c["label"] + (f" [{c['unit']}]" if c.get("unit") else ""), st["cellh"])
                  for c in cols]
        rows: list[list[Any]] = [header]
        data_rows = [] if self.blank else [r for r in (self.data.get(f["key"]) or [])
                                           if any(str(x).strip() for x in r.values())]
        for r in data_rows:
            rows.append([_p(_value_text({"type": c.get("type", "text"),
                                         "unit": None}, r.get(c["key"])), st["cell"])
                         for c in cols])
        n_empty = max(f.get("min_rows", 1) + (2 if self.blank else 0) - len(data_rows),
                      0 if data_rows else 1)
        if self.fillable:
            rows = [header]
            existing = [] if self.blank else list(self.data.get(f["key"]) or [])
            n = max(f.get("min_rows", 1) + 2, len(existing) + 1)
            cw = CONTENT_W / len(cols)
            for r in range(n):
                vals = existing[r] if r < len(existing) else {}
                rows.append([AcroText(f"{f['key']}_{r}_{c['key']}", cw - 4, 5.5 * mm,
                                      (vals or {}).get(c["key"], "")) for c in cols])
            data_rows = rows[1:]
            n_empty = 0
        for _ in range(n_empty):
            rows.append(["" for _ in cols])
        tbl = Table(rows, colWidths=[CONTENT_W / len(cols)] * len(cols), repeatRows=1,
                    rowHeights=[None] + [None if (i < len(data_rows) or self.fillable) else 7 * mm
                                         for i in range(len(rows) - 1)])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), self.prim),
            ("GRID", (0, 0), (-1, -1), 0.4, self.line),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        return [_p(f["label"], st["label"]), Spacer(1, 1 * mm), tbl, Spacer(1, 2 * mm)]

    def row_table(self, cells: list[tuple[dict, float]]) -> Table:
        widths = [CONTENT_W * w for _, w in cells]
        tbl = Table([[self.field_cell(f, w) for f, w in cells]], colWidths=widths)
        style = [("VALIGN", (0, 0), (-1, -1), "TOP"),
                 ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                 ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
        for i, (f, _) in enumerate(cells):
            if f["type"] not in ("check", "radio", "checks", "yesno"):
                style.append(("LINEBELOW", (i, 0), (i, 0), 0.5, self.line))
        tbl.setStyle(TableStyle(style))
        return tbl

    def section_flows(self, sec: dict[str, Any]) -> list[Any]:
        st = self.st
        out: list[Any] = [Spacer(1, 3 * mm), _p(sec["title"], st["h2"])]
        if sec.get("intro"):
            out.append(_p(sec["intro"], st["intro"]))
        out.append(Spacer(1, 1.5 * mm))
        row: list[tuple[dict, float]] = []
        used = 0.0

        def flush():
            nonlocal row, used
            if row:
                out.append(self.row_table(row))
                row, used = [], 0.0

        for f in sec["fields"]:
            if not self.visible(f.get("show_if")):
                continue
            t = f["type"]
            if t == "info":
                flush()
                box = Table([[_p(f["text"], st["info"])]], colWidths=[CONTENT_W])
                box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1),
                                          colors.HexColor("#eef5f6")),
                                         ("LEFTPADDING", (0, 0), (-1, -1), 5),
                                         ("TOPPADDING", (0, 0), (-1, -1), 4),
                                         ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
                out += [box, Spacer(1, 1.5 * mm)]
                continue
            if t == "table":
                flush()
                out += self.table_flow(f)
                continue
            if t not in INPUT_TYPES:
                continue
            w = WIDTHS.get(f.get("width", "full"), 1.0)
            if t in ("check", "checks", "textarea", "radio") and "width" not in f:
                w = 1.0
            if used + w > 1.001:
                flush()
            row.append((f, w))
            used += w
        flush()
        return out

    def build(self) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=MARGIN_X, rightMargin=MARGIN_X,
                                topMargin=34 * mm, bottomMargin=18 * mm,
                                title=self.form["title"], author=self.s.get("firma", ""))
        st = self.st
        story: list[Any] = [_p(self.form["title"], st["title"])]
        if self.fillable:
            story.append(_p("Beschreibbares PDF – am Computer ausfüllen, speichern und "
                            "per E-Mail zurücksenden, oder ausdrucken. * = Pflichtangabe",
                            st["meta"]))
        elif self.blank:
            story.append(_p("Druckvorlage – bitte in Druckbuchstaben ausfüllen. "
                            "* = Pflichtangabe", st["meta"]))
        else:
            parts = [self.meta.get("kunde"), self.meta.get("objekt")]
            if self.meta.get("submitted_at"):
                parts.append("eingereicht am " + _fmt_date(self.meta["submitted_at"]))
            parts.append("erstellt am " + datetime.now().strftime("%d.%m.%Y"))
            story.append(_p(" · ".join(p for p in parts if p), st["meta"]))
        story.append(Spacer(1, 2 * mm))
        for sec in self.form["sections"]:
            if not self.visible(sec.get("show_if")):
                continue
            flows = self.section_flows(sec)
            # Überschrift nicht allein am Seitenende stehen lassen.
            story.append(KeepTogether(flows[:4]))
            story += flows[4:]
        doc.build(story, onFirstPage=self.on_page, onLaterPages=self.on_page)
        return buf.getvalue()


def render(form: dict[str, Any], data: dict[str, Any] | None = None, *, blank: bool = False,
           fillable: bool = False, meta: dict[str, Any] | None = None,
           settings: dict[str, Any] | None = None) -> bytes:
    """blank=leere Vorlage, fillable=mit AcroForm-Feldern (auch vorbefüllt mit ``data``)."""
    return _Doc(form, data or {}, blank, settings or branding.load(), meta or {},
                fillable).build()


def filename(form: dict[str, Any], kunde: str = "") -> str:
    base = f"{form['nr']:02d}_{form['short']}"
    if kunde:
        base += f"_{kunde}"
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in base)
    return f"{safe.strip('_')}.pdf"
