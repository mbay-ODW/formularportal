"""Formulare 1–2: Stammdatenblätter Eigentümer und Gebäude."""
from app.forms._bausteine import ANREDEN
from app.forms._dsl import (area, check, checks, date, email, info, num, ort_datum, radio,
                            sec, select, sign, table, col, tel, text, when, yesno)

STAMMDATEN_EIGENTUEMER = {
    "key": "stammdaten_eigentuemer",
    "nr": 1,
    "title": "Stammdatenblatt Eigentümer / Antragsteller",
    "short": "Stammdaten Eigentümer",
    "audience": "kunde",
    "category": "Stammdaten",
    "version": "2026-09",
    "description": "Persönliche Daten, Eigentumsverhältnisse und Bankverbindung – einmal "
                   "erfasst, für alle Förderprogramme verwendbar.",
    "sections": [
        sec("Antragsteller/in",
            select("eig_anrede", "Anrede", ANREDEN, width="third"),
            text("eig_titel", "Titel", width="third"),
            date("eig_geburtsdatum", "Geburtsdatum", width="third",
                 hint="Wird für die Heizungsförderung (KfW-Kundenportal) benötigt."),
            text("eig_vorname", "Vorname", required=True, width="half"),
            text("eig_nachname", "Nachname", required=True, width="half"),
            text("eig_firma", "Firma / WEG / Gemeinschaft (falls zutreffend)"),
            text("eig_strasse", "Straße", required=True, width="two-thirds"),
            text("eig_hausnr", "Hausnr.", required=True, width="third"),
            text("eig_plz", "PLZ", required=True, width="third"),
            text("eig_ort", "Ort", required=True, width="two-thirds"),
            tel("eig_telefon", "Telefon", width="half"),
            tel("eig_mobil", "Mobil", width="half"),
            email("eig_email", "E-Mail", required=True,
                  hint="An diese Adresse gehen Unterlagen und Rückfragen."),
            intro="Bitte tragen Sie die Daten der Person ein, die den Förderantrag stellt "
                  "(in der Regel die Eigentümerin bzw. der Eigentümer)."),
        sec("Eigentumsverhältnisse",
            radio("eig_rolle", "Sie sind …", [
                "Alleineigentümer/in", "Miteigentümer/in", "Wohnungseigentümergemeinschaft (WEG)",
                "Erbbauberechtigte/r", "Mieter/in bzw. Pächter/in (mit Zustimmung Eigentümer)",
                "Unternehmen / Gewerbe", "Sonstiges"], required=True),
            table("eig_miteigentuemer", "Weitere Miteigentümer/innen", [
                col("name", "Name"), col("anschrift", "Anschrift"), col("anteil", "Anteil")],
                show_if=when("eig_rolle", equals="Miteigentümer/in"),
                hint="Für den Antrag benötigen wir die Zustimmung aller Miteigentümer."),
            text("eig_verwalter", "Hausverwaltung (Name, Kontakt)",
                 show_if=when("eig_rolle", equals="Wohnungseigentümergemeinschaft (WEG)")),
            yesno("eig_selbstnutzung", "Nutzen Sie das Gebäude selbst zu Wohnzwecken?",
                  required=True,
                  hint="Relevant u. a. für Einkommens- und Geschwindigkeitsbonus der "
                       "Heizungsförderung sowie für die Steuerermäßigung nach § 35c EStG."),
            yesno("eig_unternehmen", "Stellen Sie den Antrag als Unternehmen bzw. im Rahmen einer "
                  "wirtschaftlichen Tätigkeit (z. B. Vermietung über GmbH)?",
                  hint="Dann ist in der Regel eine De-minimis-Erklärung erforderlich."),
            yesno("eig_vorsteuer", "Sind Sie zum Vorsteuerabzug berechtigt?",
                  hint="Wenn ja, sind nur die Nettokosten förderfähig.")),
        sec("Steuerangaben",
            text("eig_steuer_id", "Steuerliche Identifikationsnummer", width="half",
                 hint="Für Nachweise zu einkommensabhängigen Zuschüssen und für die "
                      "Steuerermäßigung nach § 35c EStG."),
            text("eig_finanzamt", "Zuständiges Finanzamt", width="half"),
            text("eig_steuernummer", "Steuernummer (Unternehmen)", width="half",
                 show_if=when("eig_unternehmen", equals="ja")),
            text("eig_ust_id", "USt-IdNr.", width="half",
                 show_if=when("eig_unternehmen", equals="ja")),
            radio("eig_unternehmensgroesse", "Unternehmensgröße", [
                "Kleinstunternehmen", "kleines Unternehmen", "mittleres Unternehmen",
                "großes Unternehmen"], show_if=when("eig_unternehmen", equals="ja"))),
        sec("Einkommen und Haushalt (optional)",
            info("eig_einkommen_info",
                 "Bei der Heizungsförderung hängen Zuschläge vom zu versteuernden "
                 "Haushaltseinkommen und der Haushaltsgröße ab. Die Angaben helfen uns, die "
                 "für Sie beste Förderung zu ermitteln. Der Nachweis erfolgt später über die "
                 "Einkommensteuerbescheide."),
            num("eig_hh_personen", "Personen im Haushalt", width="third"),
            num("eig_hh_kinder", "davon Kinder", width="third"),
            num("eig_hh_einkommen", "Zu versteuerndes Haushaltseinkommen (Ø)", unit="€/Jahr",
                width="third")),
        sec("Bankverbindung für Förderauszahlungen",
            text("eig_kontoinhaber", "Kontoinhaber/in", width="half"),
            text("eig_bank", "Kreditinstitut", width="half"),
            text("eig_iban", "IBAN", width="two-thirds"),
            text("eig_bic", "BIC", width="third"),
            intro="Die Auszahlung von BAFA- und KfW-Zuschüssen erfolgt auf dieses Konto."),
        sec("Kommunikation und Einwilligung",
            radio("eig_kontaktweg", "Bevorzugter Kontaktweg", ["E-Mail", "Telefon", "Post"]),
            check("eig_datenschutz",
                  "Ich willige ein, dass meine Angaben zur Durchführung der Energieberatung, "
                  "zur Beantragung und Abwicklung von Fördermitteln verarbeitet und hierfür an "
                  "Fördermittelgeber (z. B. BAFA, KfW) sowie beauftragte Fachunternehmen "
                  "übermittelt werden. Die Einwilligung kann ich jederzeit widerrufen.",
                  required=True),
            check("eig_richtigkeit",
                  "Ich versichere, dass die Angaben vollständig und richtig sind.",
                  required=True)),
        sec("Unterschrift",
            *ort_datum(),
            sign("unterschrift", "Unterschrift Antragsteller/in", required=True)),
    ],
}

STAMMDATEN_GEBAEUDE = {
    "key": "stammdaten_gebaeude",
    "nr": 2,
    "title": "Stammdatenblatt Gebäude / Objekt",
    "short": "Stammdaten Gebäude",
    "audience": "kunde",
    "category": "Stammdaten",
    "version": "2026-09",
    "description": "Zentrale Objektdaten: Lage, Baujahr, Wohneinheiten, Heizung und "
                   "vorhandene Unterlagen.",
    "sections": [
        sec("Lage des Gebäudes",
            yesno("obj_gleich_wohnadresse", "Entspricht die Objektadresse Ihrer Wohnadresse?"),
            text("obj_strasse", "Straße", required=True, width="two-thirds"),
            text("obj_hausnr", "Hausnr.", required=True, width="third"),
            text("obj_plz", "PLZ", required=True, width="third"),
            text("obj_ort", "Ort", required=True, width="two-thirds"),
            text("obj_gemarkung", "Gemarkung", width="third"),
            text("obj_flur", "Flur", width="third"),
            text("obj_flurstueck", "Flurstück", width="third")),
        sec("Gebäudedaten",
            select("obj_gebaeudeart", "Gebäudeart", [
                "Einfamilienhaus", "Zweifamilienhaus", "Doppelhaushälfte", "Reihenendhaus",
                "Reihenmittelhaus", "Mehrfamilienhaus", "Wohn- und Geschäftshaus",
                "Nichtwohngebäude"], required=True, width="half"),
            num("obj_baujahr", "Baujahr", required=True, width="quarter"),
            num("obj_anzahl_we", "Wohneinheiten", required=True, width="quarter"),
            date("obj_bauantrag", "Datum Bauantrag / Bauanzeige (falls bekannt)", width="half",
                 hint="Förderprogramme setzen ein Mindestalter des Gebäudes voraus."),
            num("obj_wohnflaeche", "Wohnfläche gesamt", unit="m²", width="quarter"),
            num("obj_gewerbeflaeche", "Gewerbefläche", unit="m²", width="quarter"),
            num("obj_vollgeschosse", "Vollgeschosse", width="third"),
            radio("obj_keller", "Keller", ["kein Keller", "unbeheizt", "teilweise beheizt",
                                           "beheizt"], width="two-thirds"),
            radio("obj_dachgeschoss", "Dachgeschoss", ["Flachdach", "unbeheizter Dachboden",
                                                       "ausgebaut / beheizt", "teilweise ausgebaut"]),
            yesno("obj_denkmal", "Steht das Gebäude unter Denkmalschutz?", width="half"),
            yesno("obj_erhaltenswert", "Besonders erhaltenswerte Bausubstanz?", width="half")),
        sec("Heizung und Energie heute",
            select("obj_heizung_art", "Heizungsart", [
                "Gas-Brennwert", "Gas-Niedertemperatur/Konstanttemperatur", "Öl-Brennwert",
                "Öl-Niedertemperatur/Konstanttemperatur", "Wärmepumpe", "Pelletkessel",
                "Scheitholz/Kaminofen", "Fern-/Nahwärme", "Nachtspeicher/Stromdirekt",
                "Gasetagenheizung", "Sonstige"], required=True, width="half"),
            num("obj_heizung_baujahr", "Baujahr Heizung", width="quarter"),
            num("obj_heizung_leistung", "Nennleistung", unit="kW", width="quarter"),
            radio("obj_warmwasser", "Warmwasser", [
                "zentral über Heizung", "dezentral elektrisch (Durchlauferhitzer/Boiler)",
                "mit Solarthermie", "Wärmepumpe separat"]),
            yesno("obj_pv", "Photovoltaik vorhanden?", width="half"),
            num("obj_pv_kwp", "Leistung PV", unit="kWp", width="half",
                show_if=when("obj_pv", equals="ja")),
            yesno("obj_energieausweis", "Energieausweis vorhanden?", width="half"),
            yesno("obj_isfp", "Individueller Sanierungsfahrplan (iSFP) vorhanden?", width="half"),
            date("obj_isfp_datum", "Datum iSFP", show_if=when("obj_isfp", equals="ja"))),
        sec("Vorhandene Unterlagen",
            checks("obj_unterlagen", "Welche Unterlagen können Sie bereitstellen?", [
                "Grundrisse", "Schnitte", "Ansichten", "Baubeschreibung",
                "Energieausweis", "Schornsteinfegerprotokoll", "Heizkosten-/Verbrauchsabrechnungen "
                "(3 Jahre)", "Rechnungen früherer Sanierungen", "Fotos", "Lageplan"]),
            info("obj_unterlagen_info",
                 "Pläne und Abrechnungen können Sie uns gern per E-Mail oder beim "
                 "Vor-Ort-Termin übergeben.")),
        sec("Ihre Vorhaben",
            checks("obj_vorhaben", "Was planen Sie?", [
                "Energieberatung / iSFP", "Dach bzw. oberste Geschossdecke dämmen",
                "Fassade dämmen", "Fenster / Türen erneuern", "Kellerdecke dämmen",
                "Heizung erneuern", "Lüftungsanlage", "Photovoltaik / Speicher",
                "Sanierung zum Effizienzhaus", "Noch offen"]),
            select("obj_zeitraum", "Geplanter Umsetzungszeitraum", [
                "sofort", "innerhalb von 12 Monaten", "in 1–3 Jahren", "später / schrittweise"]),
            area("obj_anmerkungen", "Anmerkungen, bekannte Probleme, Wünsche")),
        sec("Unterschrift",
            *ort_datum(),
            sign("unterschrift", "Unterschrift Eigentümer/in")),
    ],
}

FORMS = [STAMMDATEN_EIGENTUEMER, STAMMDATEN_GEBAEUDE]
