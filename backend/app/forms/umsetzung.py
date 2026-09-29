"""Formulare 16–20: Abschluss iSFP, Eigenleistung, Baubegleitung, Lüftung, Energieausweis."""
from app.forms._bausteine import eigentuemer_kurz, objekt_kurz
from app.forms._dsl import (area, check, checks, col, date, info, num, ort_datum, radio, sec,
                            select, sign, table, text, when, yesno)

ABSCHLUSS_ISFP = {
    "key": "abschluss_isfp",
    "nr": 16,
    "title": "Übergabe- und Abschlussprotokoll Sanierungsfahrplan",
    "short": "Abschluss iSFP",
    "audience": "kunde",
    "category": "Förderung",
    "version": "2026-09",
    "description": "Bestätigt die Übergabe und Erläuterung des Sanierungsfahrplans im "
                   "Abschlussgespräch – Dokumentation für Verwendungsnachweis und Rückfragen.",
    "sections": [
        sec("Beratungsempfänger/in", *eigentuemer_kurz(required=False)),
        sec("Objekt", *objekt_kurz(required=False)),
        sec("Abschlussgespräch",
            date("ai_datum", "Datum des Abschlussgesprächs", required=True, width="half"),
            radio("ai_art", "Form", ["vor Ort", "in unseren Büroräumen", "per Video"],
                  required=True, width="half"),
            text("ai_teilnehmer", "Teilnehmende"),
            checks("ai_unterlagen", "Übergebene Unterlagen", [
                "Sanierungsfahrplan (Übersicht)", "Umsetzungshilfe für die Maßnahmen",
                "Energieberatungsbericht", "Übersicht Fördermöglichkeiten",
                "Kostenschätzung / Wirtschaftlichkeit", "Lüftungs- und "
                "Feuchteschutzhinweise"], required=True),
            radio("ai_uebergabe", "Übergabe als", ["Papier", "PDF per E-Mail", "beides"]),
            area("ai_fragen", "Besprochene Fragen / nächste Schritte")),
        sec("Bestätigung",
            check("ai_erhalten", "Ich habe den Sanierungsfahrplan und die genannten Unterlagen "
                  "erhalten; sie wurden mir erläutert und meine Fragen beantwortet.",
                  required=True),
            check("ai_bonus_info", "Ich wurde über die Voraussetzungen des iSFP-Bonus bei "
                  "späteren Einzelmaßnahmen (u. a. Mindestinvestition, Gültigkeitsdauer, "
                  "Umsetzung laut Fahrplan) informiert."),
            *ort_datum(),
            sign("unterschrift", "Unterschrift Beratungsempfänger/in", required=True),
            sign("unterschrift_berater", "Unterschrift Energieberater/in")),
    ],
}

EIGENLEISTUNG = {
    "key": "erklaerung_eigenleistung",
    "nr": 17,
    "title": "Erklärung und Bestätigung Eigenleistung",
    "short": "Eigenleistung",
    "audience": "kunde",
    "category": "Nachweise",
    "version": "2026-09",
    "description": "Für Maßnahmen, die ganz oder teilweise in Eigenleistung ausgeführt werden: "
                   "Materialnachweis durch den Antragsteller und Bestätigung der fachgerechten "
                   "Ausführung durch den Energieeffizienz-Experten.",
    "sections": [
        sec("Antragsteller/in", *eigentuemer_kurz()),
        sec("Objekt und Förderung", *objekt_kurz(),
            text("el_foerder_id", "Kennung Förderantrag (z. B. TPB-ID)", width="half"),
            text("el_massnahme", "Maßnahme", width="half", required=True)),
        sec("Erklärung Antragsteller/in",
            table("el_material", "Eingesetztes Material", [
                col("produkt", "Produkt / Material"), col("menge", "Menge"),
                col("lieferant", "Lieferant"), col("rechnung", "Rechnung Nr./Datum"),
                col("kosten", "Kosten brutto", "number", unit="€")], min_rows=3, required=True),
            date("el_zeitraum_von", "Ausführung von", width="half"),
            date("el_zeitraum_bis", "bis", width="half"),
            info("el_hinweis", "In Eigenleistung sind in der Regel nur die Materialkosten "
                 "förderfähig, nicht die eigene Arbeitszeit. Rechnungen müssen auf den "
                 "Antragsteller ausgestellt und unbar bezahlt sein."),
            check("el_versicherung", "Ich versichere, dass das aufgeführte Material für die "
                  "geförderte Maßnahme an diesem Objekt verwendet wurde.", required=True),
            sign("unterschrift", "Unterschrift Antragsteller/in", required=True)),
        sec("Bestätigung Energieeffizienz-Experte/in",
            date("el_begehung", "Datum der Inaugenscheinnahme", width="half"),
            check("el_fotos", "Ausführung ist mit Fotos dokumentiert."),
            check("el_fachgerecht", "Die Maßnahme wurde nach Inaugenscheinnahme fachgerecht und "
                  "entsprechend der technischen Mindestanforderungen ausgeführt."),
            area("el_bemerkung", "Bemerkungen"),
            sign("unterschrift_eee", "Unterschrift Energieeffizienz-Experte/in")),
    ],
}

BAUBEGLEITUNG = {
    "key": "protokoll_baubegleitung",
    "nr": 18,
    "title": "Protokoll Baubegleitung",
    "short": "Baubegleitung",
    "audience": "berater",
    "category": "Nachweise",
    "version": "2026-09",
    "description": "Dokumentation eines Baustellentermins: geprüfte Punkte, Abweichungen und "
                   "Mängel – Nachweis für geförderte Baubegleitung.",
    "sections": [
        sec("Termin", *objekt_kurz(required=False),
            date("bb_datum", "Datum", required=True, width="third"),
            text("bb_gewerk", "Gewerk / Maßnahme", required=True, width="two-thirds"),
            text("fu_firma", "Ausführendes Fachunternehmen", width="half"),
            text("bb_anwesend", "Anwesend", width="half"),
            select("bb_bauphase", "Bauphase", ["vor Beginn / Einweisung", "während der "
                   "Ausführung", "vor dem Verschließen", "Abnahme"], width="half")),
        sec("Geprüfte Punkte",
            checks("bb_geprueft", "Geprüft und in Ordnung", [
                "Material / Dämmstoff entspricht der Planung (Produkt, Dicke, WLS)",
                "Lieferscheine bzw. Produktdatenblätter liegen vor",
                "Anschlüsse gemäß Wärmebrückenkonzept", "Luftdichtheitsebene lückenlos und "
                "verklebt", "Fenstereinbau nach Montageleitfaden (innen dicht, außen offen)",
                "Durchdringungen abgedichtet", "Sommerlicher Wärmeschutz / Verschattung",
                "Hydraulischer Abgleich / Einstellwerte dokumentiert"]),
            table("bb_maengel", "Abweichungen und Mängel", [
                col("punkt", "Feststellung"), col("massnahme", "Erforderliche Maßnahme"),
                col("frist", "Frist"), col("erledigt", "Erledigt", "select", ["offen", "ja"])],
                min_rows=2),
            check("bb_fotos", "Fotodokumentation erstellt"),
            date("bb_folgetermin", "Folgetermin", width="half"),
            area("bb_notizen", "Weitere Notizen")),
        sec("Unterschriften", *ort_datum(),
            sign("unterschrift", "Unterschrift Energieberater/in", required=True),
            sign("unterschrift_fu", "Kenntnisnahme Fachunternehmen")),
    ],
}

LUEFTUNG = {
    "key": "kenntnisnahme_lueftung",
    "nr": 19,
    "title": "Nutzerinformation und Kenntnisnahme Lüftungskonzept",
    "short": "Lüftung Kenntnisnahme",
    "audience": "kunde",
    "category": "Förderung",
    "version": "2026-09",
    "description": "Bei Fenstertausch oder Dachsanierung: Ergebnis des Lüftungskonzepts nach "
                   "DIN 1946-6, Ihre Entscheidung und Hinweise zum richtigen Lüften.",
    "sections": [
        sec("Eigentümer/in", *eigentuemer_kurz(required=False)),
        sec("Objekt und Anlass", *objekt_kurz(required=False),
            checks("lk_anlass", "Anlass", ["Fenstertausch", "Dachsanierung / -dämmung",
                                           "Fassadendämmung", "Sonstige Abdichtung"])),
        sec("Ergebnis des Lüftungskonzepts",
            radio("lk_ergebnis", "Ergebnis", [
                "Lüftung zum Feuchteschutz ist ohne lüftungstechnische Maßnahmen sichergestellt",
                "Lüftungstechnische Maßnahmen sind erforderlich"], required=True),
            text("lk_empfehlung", "Empfohlene Lösung (z. B. Außenluftdurchlässe, Abluftanlage, "
                 "dezentrale Geräte mit WRG)",
                 show_if=when("lk_ergebnis", equals="Lüftungstechnische Maßnahmen sind "
                                                   "erforderlich")),
            radio("lk_entscheidung", "Meine Entscheidung", [
                "Die empfohlene Lösung wird umgesetzt",
                "Die empfohlene Lösung wird vorerst nicht umgesetzt"],
                show_if=when("lk_ergebnis", equals="Lüftungstechnische Maßnahmen sind "
                                                   "erforderlich"), required=True)),
        sec("Hinweise zum Lüften",
            info("lk_hinweise",
                 "Nach der Sanierung ist das Gebäude dichter; Feuchte aus Kochen, Duschen und "
                 "Atmen muss aktiv abgeführt werden. Mehrmals täglich 5–10 Minuten stoßlüften "
                 "(Fenster ganz öffnen, möglichst Querlüftung), nach dem Duschen und Kochen "
                 "sofort lüften, Räume nicht dauerhaft unter 16 °C auskühlen lassen und Möbel "
                 "mit Abstand zu Außenwänden stellen. Ein Hygrometer hilft: dauerhaft über 60 % "
                 "relative Feuchte ist ein Warnzeichen."),
            check("lk_kenntnis", "Ich habe das Ergebnis des Lüftungskonzepts und die Hinweise "
                  "zum Lüften zur Kenntnis genommen.", required=True),
            check("lk_verantwortung", "Mir ist bekannt, dass ich ohne die empfohlenen "
                  "lüftungstechnischen Maßnahmen selbst für einen ausreichenden Luftwechsel "
                  "sorgen muss, um Feuchte- und Schimmelschäden zu vermeiden.",
                  show_if=when("lk_entscheidung", equals="Die empfohlene Lösung wird vorerst "
                                                         "nicht umgesetzt"), required=True)),
        sec("Unterschrift", *ort_datum(),
            sign("unterschrift", "Unterschrift Eigentümer/in", required=True)),
    ],
}

ENERGIEAUSWEIS = {
    "key": "datenerhebung_energieausweis",
    "nr": 20,
    "title": "Datenerhebung Energieausweis",
    "short": "Energieausweis",
    "audience": "kunde",
    "category": "Energieausweis",
    "version": "2026-09",
    "description": "Angaben für den Bedarfs- oder Verbrauchsausweis und Bestätigung der "
                   "Richtigkeit der vom Eigentümer bereitgestellten Daten.",
    "sections": [
        sec("Eigentümer/in", *eigentuemer_kurz()),
        sec("Gebäude", *objekt_kurz(),
            num("obj_baujahr", "Baujahr Gebäude", required=True, width="third"),
            num("obj_heizung_baujahr", "Baujahr Heizung", width="third"),
            num("obj_anzahl_we", "Wohneinheiten", required=True, width="third"),
            num("obj_wohnflaeche", "Wohnfläche", unit="m²", width="half"),
            select("obj_heizung_art", "Heizungsart", [
                "Gas-Brennwert", "Gas-Niedertemperatur/Konstanttemperatur", "Öl-Brennwert",
                "Öl-Niedertemperatur/Konstanttemperatur", "Wärmepumpe", "Pelletkessel",
                "Fern-/Nahwärme", "Nachtspeicher/Stromdirekt", "Sonstige"], width="half")),
        sec("Art und Anlass",
            radio("ea_art", "Gewünschter Ausweis", ["Bedarfsausweis", "Verbrauchsausweis",
                                                    "Beratung gewünscht"], required=True),
            radio("ea_anlass", "Anlass", ["Verkauf", "Vermietung / Verpachtung",
                                          "Aushangpflicht", "Modernisierung", "freiwillig"],
                  required=True)),
        sec("Verbrauchsdaten (für Verbrauchsausweis)",
            table("ea_verbrauch", "Verbräuche der letzten drei Abrechnungsjahre", [
                col("von", "Zeitraum von"), col("bis", "bis"),
                col("traeger", "Energieträger"), col("menge", "Menge", "number"),
                col("einheit", "Einheit"), col("ww", "inkl. Warmwasser", "select", ["ja", "nein"])],
                min_rows=3, show_if=when("ea_art", equals="Verbrauchsausweis")),
            num("ea_leerstand", "Leerstand im Zeitraum", unit="%", width="half",
                show_if=when("ea_art", equals="Verbrauchsausweis")),
            yesno("ea_kuehlung", "Gibt es eine Klimaanlage / Kühlung?", width="half")),
        sec("Sanierungen seit Baujahr",
            table("ea_sanierungen", "Durchgeführte Modernisierungen", [
                col("bauteil", "Bauteil"), col("jahr", "Jahr"), col("beschreibung",
                                                                    "Beschreibung")],
                min_rows=3),
            checks("ea_unterlagen", "Beigefügt", ["Grundrisse / Schnitte", "Wohnflächenberechnung",
                                                  "Verbrauchsabrechnungen", "Fotos",
                                                  "Alter Energieausweis"])),
        sec("Bestätigung",
            check("ea_richtig", "Ich versichere, dass die von mir bereitgestellten Daten richtig "
                  "und vollständig sind. Mir ist bekannt, dass der Aussteller auf dieser "
                  "Grundlage arbeitet.", required=True),
            *ort_datum(),
            sign("unterschrift", "Unterschrift Eigentümer/in", required=True)),
    ],
}

FORMS = [ABSCHLUSS_ISFP, EIGENLEISTUNG, BAUBEGLEITUNG, LUEFTUNG, ENERGIEAUSWEIS]
