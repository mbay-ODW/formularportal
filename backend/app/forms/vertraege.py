"""Formulare 11–12: Liefer-/Leistungsverträge mit Förderbedingung."""
from app.forms._bausteine import eigentuemer_kurz, fachunternehmen, objekt_kurz
from app.forms._dsl import (area, check, date, info, num, ort_datum, radio, sec, sign, text,
                            when)

BEDINGUNG = ["aufschiebend", "auflösend"]

KLAUSEL_AUFSCHIEBEND = (
    "Dieser Vertrag wird erst wirksam, wenn dem Auftraggeber für das Vorhaben eine "
    "Förderzusage (Zuwendungsbescheid bzw. Zusage) erteilt wurde. Der Auftraggeber teilt dem "
    "Auftragnehmer den Eingang der Zusage unverzüglich mit. Wird die Förderung abgelehnt oder "
    "ist bis zum unten genannten Datum keine Zusage erteilt, wird der Vertrag nicht wirksam; "
    "gegenseitige Ansprüche bestehen dann nicht.")
KLAUSEL_AUFLOESEND = (
    "Dieser Vertrag steht unter der auflösenden Bedingung, dass die beantragte Förderung "
    "abgelehnt wird. Tritt die Bedingung ein, entfällt der Vertrag; bereits erbrachte "
    "Leistungen werden nicht vergütet, soweit nichts anderes vereinbart ist. Der Auftraggeber "
    "teilt dem Auftragnehmer die Entscheidung über den Förderantrag unverzüglich mit.")


def _vertrag(key, nr, title, short, programm_optionen, programm_hint, extra_fields):
    return {
        "key": key,
        "nr": nr,
        "title": title,
        "short": short,
        "audience": "kunde",
        "category": "Verträge",
        "version": "2026-09",
        "description": "Vertragsvorlage zwischen Eigentümer/in und Fachunternehmen, die den "
                       "Vorhabenbeginn förderunschädlich an die Förderzusage knüpft.",
        "sections": [
            sec("Auftraggeber/in", *eigentuemer_kurz()),
            sec("Auftragnehmer/in (Fachunternehmen)", *fachunternehmen()),
            sec("Bauvorhaben", *objekt_kurz()),
            sec("Vertragsgegenstand",
                text("v_angebot_nr", "Angebot Nr.", width="half"),
                date("v_angebot_datum", "vom", width="half"),
                area("v_leistung", "Leistungsbeschreibung (Kurzfassung, Details laut Angebot)",
                     required=True),
                num("v_verguetung", "Vergütung brutto", unit="€", required=True, width="half"),
                text("v_zahlung", "Zahlungsbedingungen", width="half"),
                *extra_fields),
            sec("Förderbedingung",
                radio("v_programm", "Förderprogramm", programm_optionen, required=True,
                      hint=programm_hint),
                radio("v_bedingung", "Art der Bedingung", BEDINGUNG, required=True,
                      default="aufschiebend"),
                info("v_klausel_aufschiebend", KLAUSEL_AUFSCHIEBEND,
                     show_if=when("v_bedingung", equals="aufschiebend")),
                info("v_klausel_aufloesend", KLAUSEL_AUFLOESEND,
                     show_if=when("v_bedingung", equals="auflösend")),
                date("v_frist_zusage", "Bedingung gilt bis spätestens", width="half",
                     hint="Datum, bis zu dem die Förderentscheidung vorliegen soll."),
                check("v_kenntnis", "Beiden Parteien ist bekannt, dass ohne diese Bedingung der "
                      "Vertragsabschluss als förderschädlicher Vorhabenbeginn gilt.",
                      required=True)),
            sec("Sonstige Vereinbarungen",
                area("v_sonstiges", "Weitere Vereinbarungen"),
                info("v_vob", "Im Übrigen gelten das Angebot des Auftragnehmers und die "
                     "gesetzlichen Bestimmungen.")),
            sec("Unterschriften",
                text("ort_unterschrift", "Ort", width="half"),
                date("datum_unterschrift", "Datum", width="half"),
                sign("unterschrift_ag", "Unterschrift Auftraggeber/in", required=True),
                sign("unterschrift_an", "Unterschrift Auftragnehmer/in (Fachunternehmen)",
                     required=True)),
        ],
    }


VERTRAG_BEG_EM = _vertrag(
    "vertrag_beg_em", 11,
    "Liefer- und Leistungsvertrag BEG EM (mit Förderbedingung)", "Vertrag BEG EM",
    ["BAFA – BEG Einzelmaßnahmen (Gebäudehülle / Anlagentechnik)",
     "BAFA – BEG Einzelmaßnahmen (Heizungsoptimierung)"],
    "Der Vertrag darf vor Antragstellung geschlossen werden, wenn er diese Bedingung enthält.",
    [date("v_ausfuehrung_von", "Ausführung voraussichtlich ab", width="half"),
     date("v_ausfuehrung_bis", "bis", width="half")],
)

VERTRAG_HEIZUNG = _vertrag(
    "vertrag_heizung", 12,
    "Liefer- und Leistungsvertrag Heizung (mit Förderbedingung)", "Vertrag Heizung",
    ["KfW – Heizungsförderung für Privatpersonen (Wohngebäude)",
     "KfW – Heizungsförderung für Unternehmen / WEG / Kommunen"],
    "Für die Heizungsförderung muss der Vertrag die Bedingung und das voraussichtliche "
    "Umsetzungsdatum enthalten und bei Antragstellung vorliegen.",
    [text("v_anlage", "Wärmeerzeuger (Art, Hersteller, Modell)", required=True),
     date("v_umsetzung", "Voraussichtliches Umsetzungsdatum", required=True, width="half"),
     num("v_leistung_kw", "Nennleistung", unit="kW", width="half")],
)

FORMS = [VERTRAG_BEG_EM, VERTRAG_HEIZUNG]
