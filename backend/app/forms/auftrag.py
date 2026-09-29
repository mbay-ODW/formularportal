"""Formulare 13–15: Beratungsauftrag, Datenschutz/Einwilligungen, Vollmacht Datenabfrage.

Platzhalter {{firma}}, {{inhaber}}, {{anschrift}}, {{telefon}}, {{email}}, {{website}}
in Info-Texten werden beim Ausliefern mit dem Firmenkopf aus den Einstellungen ersetzt.
Die Texte sind Vorlagen – vor dem Einsatz rechtlich prüfen lassen.
"""
from app.forms._bausteine import eigentuemer_kurz, objekt_kurz
from app.forms._dsl import (area, check, checks, col, date, info, num, radio, sec, sign, table,
                            text, when)

LEISTUNGEN = [
    "Energieberatung für Wohngebäude mit individuellem Sanierungsfahrplan (iSFP)",
    "Energieausweis (Bedarfs- oder Verbrauchsausweis)",
    "Technische Projektbeschreibung / Antrag BEG Einzelmaßnahmen",
    "Technischer Projektnachweis / Verwendungsnachweis BEG EM",
    "Fachplanung und Baubegleitung",
    "Bestätigung zum Antrag / nach Durchführung Heizungsförderung",
    "Heizlastberechnung und hydraulischer Abgleich",
    "Lüftungskonzept nach DIN 1946-6",
    "Wärmebrücken- und Luftdichtheitskonzept",
    "Begleitung Sanierung zum Effizienzhaus",
    "Bescheinigung für die Steuerermäßigung (§ 35c EStG)",
]

WIDERRUFSBELEHRUNG = (
    "Widerrufsbelehrung – Widerrufsrecht: Sie haben das Recht, binnen vierzehn Tagen ohne "
    "Angabe von Gründen diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage "
    "ab dem Tag des Vertragsabschlusses. Um Ihr Widerrufsrecht auszuüben, müssen Sie uns "
    "({{firma}}, {{anschrift}}, Telefon {{telefon}}, E-Mail {{email}}) mittels einer eindeutigen "
    "Erklärung (z. B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, "
    "diesen Vertrag zu widerrufen, informieren. Sie können dafür das beigefügte "
    "Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist. Zur Wahrung der "
    "Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des "
    "Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.\n\n"
    "Folgen des Widerrufs: Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, "
    "die wir von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem "
    "Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns "
    "eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei "
    "der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich "
    "etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte "
    "berechnet. Haben Sie verlangt, dass die Dienstleistungen während der Widerrufsfrist "
    "beginnen sollen, so haben Sie uns einen angemessenen Betrag zu zahlen, der dem Anteil der "
    "bis zu dem Zeitpunkt, zu dem Sie uns von der Ausübung des Widerrufsrechts hinsichtlich "
    "dieses Vertrags unterrichten, bereits erbrachten Dienstleistungen im Vergleich zum "
    "Gesamtumfang der im Vertrag vorgesehenen Dienstleistungen entspricht."
)

MUSTER_WIDERRUF = (
    "Muster-Widerrufsformular (Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte "
    "dieses Formular aus und senden Sie es zurück.) – An {{firma}}, {{anschrift}}, "
    "E-Mail {{email}}: Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen "
    "Vertrag über die Erbringung der folgenden Dienstleistung (*) – Bestellt am (*)/erhalten "
    "am (*) – Name des/der Verbraucher(s) – Anschrift des/der Verbraucher(s) – Unterschrift "
    "des/der Verbraucher(s) (nur bei Mitteilung auf Papier) – Datum. (*) Unzutreffendes "
    "streichen."
)

BERATUNGSVERTRAG = {
    "key": "beratungsvertrag",
    "nr": 13,
    "title": "Auftrag Energieberatung mit Honorarvereinbarung",
    "short": "Beratungsauftrag",
    "audience": "kunde",
    "category": "Auftrag & Datenschutz",
    "version": "2026-09",
    "description": "Beauftragung der Energieberatungsleistungen mit Honorar, Förderverrechnung, "
                   "Mitwirkungspflichten und – bei Verbrauchern – Widerrufsbelehrung.",
    "sections": [
        sec("Auftraggeber/in", *eigentuemer_kurz()),
        sec("Objekt", *objekt_kurz()),
        sec("Auftragnehmer",
            info("bv_an", "{{firma}} · {{inhaber}} · {{anschrift}} · {{telefon}} · {{email}}")),
        sec("Beauftragte Leistungen",
            checks("bv_leistungen", "Leistungen", LEISTUNGEN, required=True),
            area("bv_leistung_details", "Ergänzende Leistungsbeschreibung / Angebot vom")),
        sec("Honorar",
            table("bv_honorar", "Honorarpositionen", [
                col("leistung", "Leistung"), col("betrag", "Betrag brutto", "number", unit="€")],
                min_rows=2),
            num("bv_summe", "Gesamthonorar brutto", unit="€", width="third"),
            num("bv_zuschuss", "davon voraussichtlicher Zuschuss", unit="€", width="third",
                hint="z. B. Zuschuss zur Energieberatung, der mit dem Honorar verrechnet wird"),
            num("bv_eigenanteil", "Eigenanteil", unit="€", width="third"),
            radio("bv_zuschuss_regelung", "Wird der Zuschuss nicht oder nur teilweise gewährt …", [
                "trägt der Auftraggeber den Differenzbetrag",
                "reduziert sich das Honorar um den Differenzbetrag"], required=True),
            text("bv_zahlung", "Zahlungsbedingungen", width="half",
                 default="14 Tage nach Rechnungsstellung ohne Abzug"),
            date("bv_termin", "Geplanter Termin Vor-Ort-Begehung", width="half")),
        sec("Mitwirkung und Hinweise",
            info("bv_mitwirkung",
                 "Der Auftraggeber stellt die für die Beratung erforderlichen Unterlagen "
                 "(z. B. Pläne, Verbrauchsabrechnungen, Angebote) vollständig und wahrheitsgemäß "
                 "zur Verfügung und ermöglicht den Zugang zum Objekt. Förderentscheidungen trifft "
                 "allein der Fördermittelgeber; ein bestimmter Förderbetrag wird nicht geschuldet. "
                 "Maßnahmen, Verträge mit Fachunternehmen oder Bestellungen dürfen erst nach "
                 "Rücksprache begonnen werden, wenn eine Förderung beantragt werden soll."),
            check("bv_mitwirkung_ok", "Ich habe die Hinweise zur Mitwirkung und zum Förderablauf "
                  "zur Kenntnis genommen.", required=True)),
        sec("Widerrufsrecht für Verbraucher",
            radio("bv_verbraucher", "Der Auftrag wird erteilt als …", [
                "Verbraucher/in (privat)", "Unternehmer/in, WEG-Verwaltung oder öffentliche "
                "Stelle"], required=True),
            info("bv_widerruf", WIDERRUFSBELEHRUNG,
                 show_if=when("bv_verbraucher", equals="Verbraucher/in (privat)")),
            info("bv_muster", MUSTER_WIDERRUF,
                 show_if=when("bv_verbraucher", equals="Verbraucher/in (privat)")),
            check("bv_belehrung", "Ich habe die Widerrufsbelehrung und das "
                  "Muster-Widerrufsformular erhalten.", required=True,
                  show_if=when("bv_verbraucher", equals="Verbraucher/in (privat)")),
            check("bv_vorzeitig", "Ich verlange ausdrücklich, dass mit der Leistung vor Ablauf der "
                  "Widerrufsfrist begonnen wird. Mir ist bekannt, dass ich bei einem Widerruf "
                  "Wertersatz für bereits erbrachte Leistungen schulde und mein Widerrufsrecht "
                  "bei vollständiger Vertragserfüllung erlischt.",
                  show_if=when("bv_verbraucher", equals="Verbraucher/in (privat)"))),
        sec("Unterschriften",
            text("ort_unterschrift", "Ort", width="half"),
            date("datum_unterschrift", "Datum", width="half"),
            sign("unterschrift_ag", "Unterschrift Auftraggeber/in", required=True),
            sign("unterschrift_an", "Unterschrift Auftragnehmer")),
    ],
}

DATENSCHUTZ = {
    "key": "datenschutz_einwilligung",
    "nr": 14,
    "title": "Datenschutzhinweise und Einwilligungen",
    "short": "Datenschutz",
    "audience": "kunde",
    "category": "Auftrag & Datenschutz",
    "version": "2026-09",
    "description": "Informationen nach Art. 13 DSGVO zur Verarbeitung Ihrer Daten und freiwillige "
                   "Einwilligungen (z. B. Messenger, Fotos, Referenzen).",
    "sections": [
        sec("Betroffene Person",
            text("eig_vorname", "Vorname", width="half", required=True),
            text("eig_nachname", "Nachname", width="half", required=True)),
        sec("Informationen nach Art. 13 DSGVO",
            info("ds_verantwortlich", "Verantwortlich: {{firma}}, {{inhaber}}, {{anschrift}}, "
                 "E-Mail {{email}}, Telefon {{telefon}}."),
            info("ds_zwecke",
                 "Zwecke und Rechtsgrundlagen: Wir verarbeiten Ihre Angaben zur Durchführung der "
                 "Energieberatung, zur Beantragung, Abwicklung und zum Nachweis von Fördermitteln "
                 "sowie zur Abrechnung (Art. 6 Abs. 1 lit. b DSGVO), zur Erfüllung gesetzlicher "
                 "und förderrechtlicher Aufbewahrungs- und Nachweispflichten (Art. 6 Abs. 1 lit. c "
                 "DSGVO) und – soweit Sie unten einwilligen – für die dort genannten Zwecke "
                 "(Art. 6 Abs. 1 lit. a DSGVO)."),
            info("ds_empfaenger",
                 "Empfänger: Fördermittelgeber und deren Prüfstellen (z. B. BAFA, KfW, dena), von "
                 "Ihnen beauftragte Fachunternehmen, soweit für die Maßnahme erforderlich, "
                 "Steuerberatung sowie technische Dienstleister (Hosting, E-Mail, Software), die "
                 "wir vertraglich zur Vertraulichkeit verpflichtet haben. Eine Übermittlung in "
                 "Drittländer findet nicht statt."),
            info("ds_dauer",
                 "Speicherdauer: Solange es für die genannten Zwecke erforderlich ist; danach "
                 "bis zum Ablauf gesetzlicher und förderrechtlicher Aufbewahrungsfristen (in der "
                 "Regel bis zu zehn Jahre)."),
            info("ds_rechte",
                 "Ihre Rechte: Auskunft (Art. 15), Berichtigung (Art. 16), Löschung (Art. 17), "
                 "Einschränkung (Art. 18), Datenübertragbarkeit (Art. 20) und Widerspruch "
                 "(Art. 21 DSGVO). Einwilligungen können Sie jederzeit mit Wirkung für die "
                 "Zukunft widerrufen. Sie haben das Recht, sich bei einer Aufsichtsbehörde zu "
                 "beschweren, in Hessen beim Hessischen Beauftragten für Datenschutz und "
                 "Informationsfreiheit."),
            check("ds_kenntnis", "Ich habe die Datenschutzhinweise zur Kenntnis genommen.",
                  required=True)),
        sec("Freiwillige Einwilligungen",
            info("ds_freiwillig", "Die folgenden Einwilligungen sind freiwillig und für die "
                 "Beratung nicht erforderlich."),
            check("ds_messenger", "Kommunikation und Dateiaustausch auch per Messenger "
                  "(z. B. WhatsApp, Signal) an meine Mobilnummer."),
            check("ds_fotos_intern", "Fotos des Gebäudes (innen und außen) dürfen zur "
                  "Dokumentation angefertigt und an Fördermittelgeber übermittelt werden."),
            check("ds_referenz", "Anonymisierte Fotos und Eckdaten des Projekts dürfen als "
                  "Referenz (Website, soziale Medien) verwendet werden – ohne Namen und Adresse."),
            check("ds_news", "Ich möchte gelegentlich Informationen zu Förderänderungen per "
                  "E-Mail erhalten.")),
        sec("Unterschrift",
            text("ort_unterschrift", "Ort", width="half"),
            date("datum_unterschrift", "Datum", width="half"),
            sign("unterschrift", "Unterschrift", required=True)),
    ],
}

VOLLMACHT_DATEN = {
    "key": "vollmacht_datenabfrage",
    "nr": 15,
    "title": "Vollmacht zur Einholung von Unterlagen und Verbrauchsdaten",
    "short": "Vollmacht Datenabfrage",
    "audience": "kunde",
    "category": "Auftrag & Datenschutz",
    "version": "2026-09",
    "description": "Erlaubt dem Energieberater, Verbrauchsdaten, Bauakten und Protokolle direkt "
                   "bei Versorgern, Behörden, Schornsteinfeger oder Verwaltung anzufordern. Die "
                   "amtlichen Vollmachten der Fördermittelgeber ersetzt sie nicht.",
    "sections": [
        sec("Vollmachtgeber/in", *eigentuemer_kurz()),
        sec("Objekt", *objekt_kurz()),
        sec("Bevollmächtigt wird",
            info("vd_bevollmaechtigter", "{{inhaber}}, {{firma}}, {{anschrift}}")),
        sec("Umfang der Vollmacht",
            checks("vd_umfang", "Der Bevollmächtigte darf in meinem Namen …", [
                "Verbrauchs- und Abrechnungsdaten bei Energieversorger, Netzbetreiber bzw. "
                "Messstellenbetreiber anfordern",
                "Feuerstättenbescheid, Messprotokolle und Kehrbuchdaten beim "
                "Bezirksschornsteinfeger anfordern",
                "Einsicht in die Bauakte nehmen und Kopien bei Bauaufsicht bzw. Bauarchiv "
                "anfordern",
                "Unterlagen, Beschlüsse und Abrechnungen bei der Hausverwaltung anfordern",
                "Auskünfte bei Fachunternehmen zu Angeboten, Ausführung und Rechnungen einholen",
                "einen Grundbuchauszug anfordern"], required=True),
            table("vd_stellen", "Betroffene Stellen (falls bekannt)", [
                col("stelle", "Stelle / Unternehmen"), col("kundennr", "Kunden-/Zählernummer"),
                col("bemerkung", "Bemerkung")], min_rows=2),
            date("vd_gueltig_bis", "Gültig bis (leer = bis Abschluss des Auftrags)", width="half"),
            info("vd_hinweis", "Die Vollmacht kann jederzeit widerrufen werden. Für Förderanträge "
                 "gelten zusätzlich die Vollmachtsformulare der jeweiligen Förderstelle.")),
        sec("Unterschrift",
            text("ort_unterschrift", "Ort", width="half"),
            date("datum_unterschrift", "Datum", width="half"),
            sign("unterschrift", "Unterschrift Vollmachtgeber/in", required=True)),
    ],
}

FORMS = [BERATUNGSVERTRAG, DATENSCHUTZ, VOLLMACHT_DATEN]
