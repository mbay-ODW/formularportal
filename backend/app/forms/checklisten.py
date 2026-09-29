"""Formulare 6, 7, 9: Checklisten EBW, BEG EM und Heizungstausch.

Förderrechtliche Hinweise sind bewusst allgemein formuliert; Beträge und Sätze
ändern sich mit den Richtlinien und werden im Beratungsgespräch konkretisiert.
"""
from app.forms._bausteine import eigentuemer_kurz, objekt_kurz
from app.forms._dsl import (area, check, checks, col, date, info, num, ort_datum, radio, sec,
                            select, sign, table, text, when, yesno)

CHECKLISTE_EBW = {
    "key": "checkliste_ebw",
    "nr": 6,
    "title": "Checkliste EBW – Antragstellung in Vollmacht",
    "short": "Checkliste EBW (iSFP)",
    "audience": "kunde",
    "category": "Förderung",
    "version": "2026-09",
    "description": "Alle Erklärungen, die Sie für die geförderte Energieberatung für "
                   "Wohngebäude (iSFP) abgeben – aufbereitet für die Antragstellung durch Ihren "
                   "Energieberater in Vollmacht.",
    "sections": [
        sec("Antragsteller/in", *eigentuemer_kurz()),
        sec("Beratungsobjekt", *objekt_kurz(),
            num("obj_baujahr", "Baujahr", width="third"),
            num("obj_anzahl_we", "Wohneinheiten", width="third"),
            date("obj_bauantrag", "Bauantrag / Bauanzeige", width="third")),
        sec("Art des Antragstellers",
            radio("ebw_antragsteller", "Sie stellen den Antrag als …", [
                "Privatperson (Eigentümer/in)", "Wohnungseigentümergemeinschaft",
                "Unternehmen / Freiberufler/in", "gemeinnützige Organisation",
                "sonstige juristische Person"], required=True),
            check("ebw_deminimis",
                  "Ich lege eine De-minimis-Erklärung über erhaltene Beihilfen der letzten "
                  "drei Jahre vor.",
                  show_if=when("ebw_antragsteller", in_=["Unternehmen / Freiberufler/in",
                                                         "sonstige juristische Person"]),
                  required=True)),
        sec("Erklärungen",
            info("ebw_info",
                 "Den Förderantrag stellt Ihr Energieberater in Ihrem Namen beim BAFA. Der "
                 "Zuschuss wird an den Energieberater ausgezahlt und mit dem Honorar "
                 "verrechnet; Sie zahlen nur den Eigenanteil."),
            check("ebw_e_eigentum", "Ich bin Eigentümer/in des Gebäudes oder handle mit "
                  "Zustimmung aller Eigentümer/innen.", required=True),
            check("ebw_e_wohngebaeude", "Das Gebäude ist ein Wohngebäude, dessen Bauantrag bzw. "
                  "Bauanzeige zum Zeitpunkt der Antragstellung mindestens zehn Jahre "
                  "zurückliegt.", required=True),
            check("ebw_e_beginn", "Mir ist bekannt, dass mit der Beratung erst nach Eingang des "
                  "Förderantrags beim BAFA begonnen werden darf.", required=True),
            check("ebw_e_vollmacht", "Ich bevollmächtige den Energieberater, den Antrag in "
                  "meinem Namen zu stellen und das Verfahren abzuwickeln (gesondertes "
                  "Vollmachtsformular des BAFA).", required=True),
            check("ebw_e_auszahlung", "Ich bin damit einverstanden, dass der Zuschuss an den "
                  "Energieberater ausgezahlt und mit seinem Honorar verrechnet wird.",
                  required=True),
            check("ebw_e_subvention", "Ich wurde darauf hingewiesen, dass meine Angaben "
                  "subventionserhebliche Tatsachen im Sinne von § 264 StGB sind.", required=True),
            check("ebw_e_datenweitergabe", "Ich bin einverstanden, dass die Beratungsergebnisse "
                  "zu Kontroll- und Evaluationszwecken an das BAFA bzw. beauftragte Stellen "
                  "übermittelt werden.", required=True),
            check("ebw_e_keine_doppel", "Für diese Beratung beantrage ich keine weiteren "
                  "öffentlichen Fördermittel.", required=True)),
        sec("Honorar und Eigenanteil",
            num("ebw_honorar", "Beratungshonorar (brutto)", unit="€", width="third"),
            num("ebw_zuschuss", "voraussichtlicher Zuschuss", unit="€", width="third"),
            num("ebw_eigenanteil", "Ihr Eigenanteil", unit="€", width="third"),
            yesno("ebw_umsetzung", "Wünschen Sie ein zusätzliches Gespräch zur Umsetzung "
                  "(Umsetzungsberatung)?"),
            intro="Wird vom Energieberater vorbelegt."),
        sec("Unterlagen",
            checks("ebw_unterlagen", "Folgende Unterlagen liegen vor bzw. werden nachgereicht", [
                "Stammdatenblatt Eigentümer", "Stammdatenblatt Gebäude",
                "Datenblatt Teil A", "Vollmacht BAFA unterschrieben",
                "Verbrauchsabrechnungen", "Grundrisse / Pläne",
                "De-minimis-Erklärung (nur Unternehmen)"])),
        sec("Unterschrift", *ort_datum(),
            sign("unterschrift", "Unterschrift Antragsteller/in", required=True)),
    ],
}

MASSNAHMEN_HUELLE = ["Außenwand", "Dach / Dachschräge", "Oberste Geschossdecke", "Flachdach",
                     "Kellerdecke / Bodenplatte", "Fenster / Fenstertüren",
                     "Dachflächenfenster", "Außentüren", "Sommerlicher Wärmeschutz"]
MASSNAHMEN_ANLAGE = ["Lüftungsanlage", "Heizungsoptimierung (hydraulischer Abgleich, Pumpe)",
                     "Gebäudeautomation / Mess-, Steuer- und Regeltechnik",
                     "Fachplanung und Baubegleitung"]

CHECKLISTE_BEG_EM = {
    "key": "checkliste_beg_em",
    "nr": 7,
    "title": "Checkliste BEG EM – Einzelmaßnahmen",
    "short": "Checkliste BEG EM",
    "audience": "kunde",
    "category": "Förderung",
    "version": "2026-09",
    "description": "Geplante Sanierungsmaßnahmen an Gebäudehülle und Anlagentechnik, "
                   "Voraussetzungen und wichtige Hinweise zu Investition und Förderumfang.",
    "sections": [
        sec("Antragsteller/in", *eigentuemer_kurz()),
        sec("Objekt", *objekt_kurz(),
            num("obj_anzahl_we", "Wohneinheiten", width="half", required=True),
            yesno("obj_isfp", "Liegt ein iSFP vor?", width="half")),
        sec("Geplante Maßnahmen",
            checks("em_huelle", "Gebäudehülle", MASSNAHMEN_HUELLE),
            checks("em_anlage", "Anlagentechnik (außer Heizung)", MASSNAHMEN_ANLAGE),
            table("em_angebote", "Angebote und Kosten", [
                col("massnahme", "Maßnahme"), col("unternehmen", "Fachunternehmen"),
                col("angebot_datum", "Angebot vom"),
                col("kosten", "Kosten brutto", "number", unit="€")], min_rows=2,
                hint="Förderfähig sind auch Nebenarbeiten (z. B. Gerüst, Entsorgung, "
                     "Anpassungsarbeiten)."),
            select("em_zeitraum", "Geplanter Beginn", [
                "sofort nach Förderzusage", "in 3–6 Monaten", "in 6–12 Monaten",
                "später"], width="half"),
            yesno("em_eigenleistung", "Planen Sie Eigenleistungen?", width="half",
                  hint="In Eigenleistung sind in der Regel nur Materialkosten förderfähig; "
                       "die fachgerechte Ausführung muss bestätigt werden.")),
        sec("Voraussetzungen – bitte bestätigen",
            check("em_v_kein_vertrag", "Ich habe noch keinen Liefer- oder Leistungsvertrag "
                  "abgeschlossen – oder nur einen Vertrag mit auflösender bzw. aufschiebender "
                  "Bedingung der Förderzusage.", required=True),
            check("em_v_kein_beginn", "Mit der Ausführung wurde noch nicht begonnen. "
                  "Planungs- und Beratungsleistungen sind davon ausgenommen.", required=True),
            check("em_v_alter", "Der Bauantrag bzw. die Bauanzeige des Gebäudes liegt "
                  "mindestens fünf Jahre zurück.", required=True),
            check("em_v_fachunternehmen", "Die Maßnahmen werden von Fachunternehmen "
                  "ausgeführt, soweit keine Eigenleistung vereinbart ist.", required=True),
            check("em_v_frist", "Mir ist bekannt, dass die Maßnahmen innerhalb des "
                  "Bewilligungszeitraums umgesetzt und nachgewiesen werden müssen.",
                  required=True),
            check("em_v_zahlung", "Rechnungen werden unbar bezahlt; Barzahlungen sind nicht "
                  "förderfähig.", required=True),
            check("em_v_35c", "Mir ist bekannt, dass für dieselbe Maßnahme nicht zusätzlich die "
                  "Steuerermäßigung nach § 35c EStG in Anspruch genommen werden kann.",
                  required=True)),
        sec("Wichtige Hinweise zur Förderung",
            info("em_h_satz",
                 "Einzelmaßnahmen an der Gebäudehülle und der Anlagentechnik werden mit einem "
                 "Grundfördersatz bezuschusst, Fachplanung und Baubegleitung gesondert. Die "
                 "förderfähigen Ausgaben sind je Gebäude und Kalenderjahr gedeckelt; die "
                 "Höchstgrenze richtet sich nach der Zahl der Wohneinheiten."),
            info("em_h_isfp",
                 "Mit einem individuellen Sanierungsfahrplan (iSFP) erhöhen sich Fördersatz "
                 "und Höchstgrenze unter bestimmten Voraussetzungen (u. a. Mindestinvestition). "
                 "Ob sich das Bündeln von Maßnahmen lohnt, rechnen wir gemeinsam durch."),
            info("em_h_ablauf",
                 "Ablauf: Technische Projektbeschreibung (TPB) durch den Energieberater → "
                 "Antrag beim BAFA vor Vorhabenbeginn → Umsetzung → Technischer "
                 "Projektnachweis (TPN) und Verwendungsnachweis mit Rechnungen → "
                 "Auszahlung."),
            yesno("em_vorsteuer", "Sind Sie vorsteuerabzugsberechtigt?", width="half"),
            yesno("em_weitere_foerderung", "Beantragen Sie weitere Förderungen (z. B. "
                  "Land, Kommune) für diese Maßnahmen?", width="half"),
            text("em_weitere_foerderung_welche", "Welche?",
                 show_if=when("em_weitere_foerderung", equals="ja"))),
        sec("Unterschrift", *ort_datum(),
            sign("unterschrift", "Unterschrift Antragsteller/in", required=True)),
    ],
}

CHECKLISTE_HEIZUNG = {
    "key": "checkliste_heizungstausch",
    "nr": 9,
    "title": "Checkliste Heizungstausch",
    "short": "Checkliste Heizung",
    "audience": "kunde",
    "category": "Förderung",
    "version": "2026-09",
    "description": "Bestandsheizung, geplante Anlage, Umfeldmaßnahmen und Ablauf der "
                   "Heizungsförderung inklusive Angaben für mögliche Boni.",
    "sections": [
        sec("Antragsteller/in", *eigentuemer_kurz(),
            yesno("eig_selbstnutzung", "Bewohnen Sie das Gebäude selbst?", required=True)),
        sec("Objekt", *objekt_kurz(),
            num("obj_anzahl_we", "Wohneinheiten", required=True, width="half"),
            num("obj_wohnflaeche", "Wohnfläche", unit="m²", width="half")),
        sec("Bestehende Heizung",
            select("obj_heizung_art", "Heizungsart", [
                "Gas-Brennwert", "Gas-Niedertemperatur/Konstanttemperatur", "Öl-Brennwert",
                "Öl-Niedertemperatur/Konstanttemperatur", "Gasetagenheizung",
                "Nachtspeicher/Stromdirekt", "Kohle", "Biomasse", "Sonstige"],
                required=True, width="half"),
            num("obj_heizung_baujahr", "Baujahr / Inbetriebnahme", required=True,
                width="quarter"),
            num("obj_heizung_leistung", "Leistung", unit="kW", width="quarter"),
            yesno("h_funktionstuechtig", "Ist die Heizung noch funktionstüchtig?", width="half"),
            yesno("h_tank", "Ist ein Öltank vorhanden?", width="half"),
            info("h_bonus_info",
                 "Für den Austausch alter fossiler Heizungen durch Selbstnutzer kann ein "
                 "zeitlich gestaffelter Geschwindigkeitsbonus hinzukommen – deshalb sind Art "
                 "und Alter der Bestandsanlage wichtig.")),
        sec("Geplante neue Heizung",
            radio("h_neu", "Welche Anlage ist geplant?", [
                "Luft/Wasser-Wärmepumpe", "Sole/Wasser-Wärmepumpe (Erdwärme)",
                "Wasser/Wasser-Wärmepumpe", "Biomasse (Pellets/Hackschnitzel)",
                "Anschluss an ein Wärmenetz", "Solarthermie", "Hybridheizung",
                "noch offen"], required=True),
            text("h_fachbetrieb", "Beauftragter Fachbetrieb (falls bekannt)"),
            num("h_kosten", "Kosten laut Angebot (brutto)", unit="€", width="half"),
            date("h_angebot_datum", "Angebotsdatum", width="half"),
            checks("h_umfeld", "Geplante Umfeldmaßnahmen", [
                "Heizkörpertausch", "Flächenheizung", "hydraulischer Abgleich",
                "Elektroarbeiten / Zählerschrank", "Fundament / Aufstellung",
                "Schornsteinanpassung", "Demontage und Entsorgung Altanlage / Tank",
                "Pufferspeicher / Warmwasserspeicher"],
                hint="Umfeldmaßnahmen sind in der Regel mitförderfähig.")),
        sec("Angaben für Boni (nur Selbstnutzer)",
            num("eig_hh_personen", "Personen im Haushalt", width="third"),
            num("eig_hh_kinder", "davon Kinder", width="third"),
            num("eig_hh_einkommen", "Zu versteuerndes Haushaltseinkommen (Ø)", unit="€/Jahr",
                width="third"),
            info("h_einkommen_info",
                 "Einkommensabhängige Zuschläge werden über die Einkommensteuerbescheide "
                 "nachgewiesen. Die Angabe ist freiwillig.")),
        sec("Ablauf – bitte bestätigen",
            check("h_v_vertrag", "Ich schließe den Liefer- und Leistungsvertrag mit "
                  "auflösender oder aufschiebender Bedingung der Förderzusage und mit dem "
                  "voraussichtlichen Umsetzungsdatum.", required=True),
            check("h_v_bza", "Das Fachunternehmen bzw. der Energieeffizienz-Experte erstellt "
                  "vor Antragstellung die Bestätigung zum Antrag (BzA).", required=True),
            check("h_v_antrag", "Ich stelle den Antrag im Kundenportal der Förderbank vor "
                  "Beginn der Arbeiten (bzw. mein Energieberater unterstützt mich dabei).",
                  required=True),
            check("h_v_bnd", "Nach Fertigstellung reiche ich Bestätigung nach Durchführung "
                  "(BnD) und Rechnungen fristgerecht ein.", required=True),
            check("h_v_abgleich", "Mir ist bekannt, dass ein hydraulischer Abgleich "
                  "durchzuführen ist.", required=True)),
        sec("Unterschrift", *ort_datum(),
            sign("unterschrift", "Unterschrift Antragsteller/in", required=True)),
    ],
}

FORMS = [CHECKLISTE_EBW, CHECKLISTE_BEG_EM, CHECKLISTE_HEIZUNG]
