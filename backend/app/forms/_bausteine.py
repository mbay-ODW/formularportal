"""Wiederverwendete Feldblöcke (geteilte Schlüssel eig_/obj_/fu_)."""
from app.forms._dsl import email, tel, text

ANREDEN = ["Frau", "Herr", "Divers", "Firma", "Eheleute", "Eigentümergemeinschaft"]


def eigentuemer_kurz(required: bool = True):
    return [
        text("eig_vorname", "Vorname", required=required, width="half"),
        text("eig_nachname", "Nachname", required=required, width="half"),
        text("eig_firma", "Firma / Gemeinschaft (falls zutreffend)"),
        text("eig_strasse", "Straße", required=required, width="two-thirds"),
        text("eig_hausnr", "Hausnr.", required=required, width="third"),
        text("eig_plz", "PLZ", required=required, width="third"),
        text("eig_ort", "Ort", required=required, width="two-thirds"),
        tel("eig_telefon", "Telefon", width="half"),
        email("eig_email", "E-Mail", width="half"),
    ]


def objekt_kurz(required: bool = True):
    return [
        text("obj_strasse", "Straße (Objekt)", required=required, width="two-thirds"),
        text("obj_hausnr", "Hausnr.", required=required, width="third"),
        text("obj_plz", "PLZ", required=required, width="third"),
        text("obj_ort", "Ort", required=required, width="two-thirds"),
    ]


def fachunternehmen(required: bool = True):
    return [
        text("fu_firma", "Firma", required=required),
        text("fu_ansprechpartner", "Ansprechpartner/in", width="half"),
        text("fu_gewerk", "Gewerk / Handwerksrolle", width="half"),
        text("fu_strasse", "Straße, Hausnr.", required=required, width="two-thirds"),
        text("fu_plz_ort", "PLZ, Ort", required=required, width="third"),
        tel("fu_telefon", "Telefon", width="half"),
        email("fu_email", "E-Mail", width="half"),
    ]
