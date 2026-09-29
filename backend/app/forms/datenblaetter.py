"""Formulare 3–5: Datenblätter Teil A (Nutzerverhalten), B (Aufnahme), C (MFH)."""
from app.forms._bausteine import objekt_kurz
from app.forms._dsl import (area, check, checks, col, date, info, num, ort_datum, radio, sec,
                            select, sign, table, text, when, yesno)

ENERGIETRAEGER = ["Erdgas", "Heizöl", "Flüssiggas", "Strom (Heizung/WP)", "Strom (Haushalt)",
                  "Pellets", "Scheitholz", "Fern-/Nahwärme", "Sonstiges"]

DATENBLATT_A = {
    "key": "datenblatt_a",
    "nr": 3,
    "title": "Datenblatt Teil A – Nutzerverhalten EFH/ZFH",
    "short": "Teil A Nutzerverhalten",
    "audience": "kunde",
    "category": "Datenblätter",
    "version": "2026-09",
    "description": "Füllen Sie dieses Blatt vor dem Vor-Ort-Termin aus: Nutzung, Verbräuche "
                   "und Behaglichkeit. So können wir den Termin gezielt vorbereiten.",
    "sections": [
        sec("Objekt", *objekt_kurz(required=False),
            intro="Die Adresse ist bereits vorbelegt, wenn Sie das Stammdatenblatt ausgefüllt "
                  "haben."),
        sec("Bewohner und Nutzung",
            num("a_personen", "Personen im Haushalt", required=True, width="third"),
            num("a_kinder", "davon Kinder", width="third"),
            yesno("a_homeoffice", "Regelmäßig Homeoffice?", width="third"),
            radio("a_anwesenheit", "Wann ist das Haus überwiegend bewohnt?", [
                "ganztags", "morgens und abends", "überwiegend abends / am Wochenende",
                "unregelmäßig"]),
            area("a_ungenutzt", "Gibt es ungenutzte oder nur selten genutzte Räume/Etagen?")),
        sec("Heizen und Lüften",
            num("a_temp_wohnen", "Raumtemperatur Wohnräume", unit="°C", width="third"),
            num("a_temp_schlafen", "Raumtemperatur Schlafräume", unit="°C", width="third"),
            num("a_temp_bad", "Raumtemperatur Bad", unit="°C", width="third"),
            yesno("a_nachtabsenkung", "Wird nachts abgesenkt?", width="half"),
            radio("a_heizperiode", "Wie heizen Sie?", [
                "alle Räume gleichmäßig", "nur genutzte Räume", "stark schwankend"], width="half"),
            area("a_unbeheizt", "Welche Räume bleiben unbeheizt?"),
            radio("a_lueften", "Wie lüften Sie überwiegend?", [
                "Stoßlüften (mehrmals täglich)", "Dauerhaft gekippte Fenster",
                "Lüftungsanlage", "selten"]),
            radio("a_warmwasser", "Warmwasserverbrauch", ["gering", "durchschnittlich", "hoch"],
                  hint="z. B. hoch bei täglichem Baden oder vielen Personen.")),
        sec("Verbräuche der letzten Jahre",
            table("a_verbrauch", "Heizenergie / Brennstoff", [
                col("jahr", "Jahr / Zeitraum"),
                col("traeger", "Energieträger", "select", ENERGIETRAEGER),
                col("menge", "Menge", "number"),
                col("einheit", "Einheit", "select", ["kWh", "Liter", "m³", "kg", "Raummeter",
                                                     "Tonnen"]),
                col("kosten", "Kosten", "number", unit="€")], min_rows=3, required=True,
                hint="Aus Jahresabrechnungen, Tankrechnungen oder Zählerständen. Bitte "
                     "möglichst 3 Jahre."),
            table("a_strom", "Haushaltsstrom", [
                col("jahr", "Jahr"), col("kwh", "Verbrauch", "number", unit="kWh"),
                col("kosten", "Kosten", "number", unit="€")], min_rows=2)),
        sec("Behaglichkeit und Zustand",
            yesno("a_zugluft", "Spüren Sie Zugluft?", width="half"),
            text("a_zugluft_wo", "Wo?", width="half", show_if=when("a_zugluft", equals="ja")),
            yesno("a_kalte_waende", "Kalte Wände oder Fußböden?", width="half"),
            text("a_kalte_waende_wo", "Wo?", width="half",
                 show_if=when("a_kalte_waende", equals="ja")),
            yesno("a_schimmel", "Schimmel oder Feuchtigkeit?", width="half"),
            text("a_schimmel_wo", "Wo?", width="half", show_if=when("a_schimmel", equals="ja")),
            yesno("a_ueberhitzung", "Überhitzung im Sommer?", width="half"),
            yesno("a_heizung_probleme", "Probleme mit der Heizung (laut, ungleichmäßig warm)?",
                  width="half"),
            area("a_maengel", "Sonstige Mängel, Schäden oder Beobachtungen")),
        sec("Ihre Ziele",
            checks("a_ziele", "Was ist Ihnen besonders wichtig?", [
                "Energiekosten senken", "Wohnkomfort verbessern", "Unabhängigkeit von fossilen "
                "Energien", "Wertsteigerung der Immobilie", "Klimaschutz", "Gesetzliche Pflichten "
                "erfüllen", "Fördermittel optimal nutzen", "Barrierefreiheit"]),
            area("a_wuensche", "Weitere Wünsche oder Fragen an uns")),
        sec("Abschluss", *ort_datum(), sign("unterschrift", "Unterschrift")),
    ],
}

BAUTEIL_ZUSTAND = ["gut", "mittel", "schlecht", "unbekannt"]

DATENBLATT_B = {
    "key": "datenblatt_b",
    "nr": 4,
    "title": "Datenblatt Teil B – Technische Gebäudeaufnahme",
    "short": "Teil B Gebäudeaufnahme",
    "audience": "berater",
    "category": "Datenblätter",
    "version": "2026-09",
    "description": "Strukturierte Vorlage für den Vor-Ort-Termin: Gebäudehülle, Anlagentechnik, "
                   "Wärmebrücken und Luftdichtheit – nichts vergessen.",
    "sections": [
        sec("Termin",
            *objekt_kurz(required=False),
            date("b_datum", "Datum der Begehung", required=True, width="third"),
            text("b_teilnehmer", "Teilnehmer/innen", width="two-thirds"),
            num("b_aussentemp", "Außentemperatur", unit="°C", width="third"),
            text("b_wetter", "Witterung", width="two-thirds")),
        sec("Dach / oberste Geschossdecke",
            radio("b_dach_form", "Dachform", ["Satteldach", "Walmdach", "Pultdach", "Flachdach",
                                              "Mansarddach", "Sonstige"]),
            radio("b_dach_grenze", "Thermische Hülle oben", [
                "Dachschrägen (beheiztes DG)", "oberste Geschossdecke", "gemischt"]),
            text("b_dach_aufbau", "Aufbau / Konstruktion (z. B. Sparren 16 cm, Zwischensparren)"),
            num("b_dach_daemmung", "Vorhandene Dämmung", unit="cm", width="third"),
            text("b_dach_material", "Dämmstoff", width="third"),
            select("b_dach_zustand", "Zustand", BAUTEIL_ZUSTAND, width="third"),
            num("b_dach_flaeche", "Fläche (ca.)", unit="m²", width="third"),
            text("b_dach_eindeckung", "Eindeckung / Alter", width="two-thirds")),
        sec("Außenwände",
            select("b_aw_konstruktion", "Konstruktion", [
                "Mauerwerk einschalig", "Mauerwerk zweischalig mit Luftschicht",
                "Mauerwerk mit Kerndämmung", "Fachwerk", "Holzständer / Fertighaus", "Beton",
                "Sonstige"], width="half"),
            text("b_aw_material", "Material (z. B. Hochlochziegel, Bims, KS)", width="half"),
            num("b_aw_dicke", "Wanddicke", unit="cm", width="third"),
            num("b_aw_daemmung", "Vorhandene Dämmung", unit="cm", width="third"),
            select("b_aw_zustand", "Zustand", BAUTEIL_ZUSTAND, width="third"),
            text("b_aw_oberflaeche", "Oberfläche außen (Putz, Klinker, Verkleidung)"),
            num("b_aw_flaeche", "Fläche (ca., abzgl. Fenster)", unit="m²", width="third")),
        sec("Fenster und Außentüren",
            table("b_fenster", "Fenster", [
                col("lage", "Lage/Raum"), col("anzahl", "Anz.", "number"),
                col("rahmen", "Rahmen", "select", ["Holz", "Kunststoff", "Alu", "Holz-Alu"]),
                col("verglasung", "Verglasung", "select", ["1-fach", "2-fach Iso",
                                                           "2-fach WSV", "3-fach WSV"]),
                col("baujahr", "Baujahr"), col("masse", "B × H (m)")], min_rows=4),
            text("b_rolllaeden", "Rollläden / Rollladenkästen (Art, gedämmt?)"),
            table("b_tueren", "Außentüren", [
                col("lage", "Lage"), col("material", "Material"), col("baujahr", "Baujahr"),
                col("zustand", "Zustand", "select", BAUTEIL_ZUSTAND)], min_rows=1)),
        sec("Unterer Gebäudeabschluss",
            radio("b_unten", "Unterer Abschluss", [
                "Kellerdecke gegen unbeheizten Keller", "Bodenplatte gegen Erdreich",
                "gemischt", "Decke über Außenluft (Durchfahrt)"]),
            text("b_unten_aufbau", "Aufbau (z. B. Stahlbeton 16 cm, Estrich)"),
            num("b_unten_daemmung", "Vorhandene Dämmung", unit="cm", width="third"),
            num("b_unten_hoehe", "Lichte Kellerhöhe", unit="m", width="third"),
            num("b_unten_flaeche", "Fläche (ca.)", unit="m²", width="third")),
        sec("Wärmeerzeugung",
            text("b_wez_hersteller", "Hersteller / Typ", width="two-thirds"),
            num("b_wez_baujahr", "Baujahr", width="third"),
            select("b_wez_traeger", "Energieträger", ENERGIETRAEGER, width="third"),
            num("b_wez_leistung", "Nennleistung", unit="kW", width="third"),
            text("b_wez_aufstellort", "Aufstellort", width="third"),
            text("b_abgas", "Abgasführung / Schornstein (Zustand, Querschnitt)"),
            text("b_tank", "Brennstofflager (Tank, Volumen, Lage)")),
        sec("Wärmeverteilung und -übergabe",
            radio("b_uebergabe", "Übergabe", ["Heizkörper", "Fußbodenheizung", "gemischt",
                                              "Einzelöfen"]),
            num("b_vorlauf", "Vorlauftemperatur (Auslegung / beobachtet)", unit="°C",
                width="third"),
            radio("b_pumpe", "Heizungspumpe", ["ungeregelt", "Hocheffizienzpumpe", "unbekannt"],
                  width="two-thirds"),
            yesno("b_abgleich", "Hydraulischer Abgleich dokumentiert?", width="half"),
            yesno("b_thermostat", "Voreinstellbare Thermostatventile?", width="half"),
            radio("b_leitungen", "Dämmung der Leitungen im unbeheizten Bereich", [
                "vollständig", "teilweise", "keine"])),
        sec("Warmwasser, Lüftung, Erneuerbare",
            radio("b_ww", "Warmwasserbereitung", ["zentral mit Speicher", "zentral Durchlauf",
                                                  "dezentral elektrisch", "Wärmepumpe"]),
            num("b_ww_speicher", "Speichervolumen", unit="l", width="third"),
            yesno("b_zirkulation", "Zirkulation vorhanden?", width="third"),
            text("b_zirk_zeit", "Zeitsteuerung Zirkulation", width="third",
                 show_if=when("b_zirkulation", equals="ja")),
            radio("b_lueftung", "Lüftung", ["Fensterlüftung", "Abluftanlage (Bad/Küche)",
                                            "zentrale Anlage mit WRG", "dezentrale Geräte mit WRG"]),
            text("b_solar", "Solarthermie / PV (Fläche, kWp, Ausrichtung, Baujahr)"),
            text("b_elektro", "Zählerschrank / Hausanschluss (Platz für WP, Wallbox?)")),
        sec("Wärmebrücken und Luftdichtheit",
            checks("b_wb", "Auffällige Wärmebrücken", [
                "Balkonplatten auskragend", "Rollladenkästen", "Fensteranschlüsse",
                "Sockel / Perimeter", "Attika / Traufe", "Heizkörpernischen", "Deckenauflager"]),
            checks("b_luftdicht", "Undichtigkeiten", [
                "Bodentreppe / Dachluke", "Fensterfugen", "Rollladengurt", "Steckdosen "
                "Außenwand", "Dachanschlüsse", "Durchdringungen (Rohre, Kabel)"]),
            check("b_fotos", "Fotodokumentation erstellt"),
            check("b_thermografie", "Thermografie durchgeführt")),
        sec("Notizen und Empfehlungen",
            area("b_notizen", "Notizen zur Begehung"),
            area("b_sofortmassnahmen", "Geringinvestive Sofortmaßnahmen"),
            area("b_empfehlungen", "Erste Maßnahmenideen / Varianten"),
            table("b_pakete", "Erste Maßnahmenpakete (Grobplanung)", [
                col("paket", "Paket"), col("massnahmen", "Maßnahmen"),
                col("prioritaet", "Priorität", "select", ["hoch", "mittel", "niedrig"]),
                col("zeitraum", "Zeitraum"), col("kosten", "Kosten grob", "number", unit="€")],
                min_rows=3)),
        sec("Bestätigung", *ort_datum(), sign("unterschrift", "Unterschrift Energieberater/in")),
    ],
}

DATENBLATT_C = {
    "key": "datenblatt_c",
    "nr": 5,
    "title": "Datenblatt Teil C – Objekt- und Belegungsstruktur MFH",
    "short": "Teil C MFH-Struktur",
    "audience": "kunde",
    "category": "Datenblätter",
    "version": "2026-09",
    "description": "Ergänzung für Mehrfamilienhäuser und WEG: Wohneinheiten, Belegung, "
                   "Eigentumsstruktur und Abrechnung.",
    "sections": [
        sec("Objekt", *objekt_kurz(required=False)),
        sec("Eigentum und Verwaltung",
            radio("c_eigentumsform", "Eigentumsform", [
                "ein Eigentümer (Mietshaus)", "Wohnungseigentümergemeinschaft (WEG)",
                "Genossenschaft", "gemischt / Sonstiges"], required=True),
            text("c_verwaltung", "Hausverwaltung (Firma, Ansprechpartner, Kontakt)"),
            yesno("c_beschluss", "Liegt ein Beschluss der Eigentümerversammlung zur Beratung / "
                  "Sanierung vor?", show_if=when("c_eigentumsform",
                                                 equals="Wohnungseigentümergemeinschaft (WEG)")),
            date("c_beschluss_datum", "Datum des Beschlusses",
                 show_if=when("c_beschluss", equals="ja"))),
        sec("Wohn- und Gewerbeeinheiten",
            num("c_anzahl_we", "Anzahl Wohneinheiten", required=True, width="half"),
            num("c_anzahl_ge", "Anzahl Gewerbeeinheiten", width="half"),
            table("c_einheiten", "Einheiten", [
                col("nr", "Nr."), col("lage", "Geschoss/Lage"),
                col("flaeche", "Fläche", "number", unit="m²"),
                col("art", "Art", "select", ["Wohnung", "Gewerbe", "Einliegerwohnung"]),
                col("nutzung", "Nutzung", "select", ["selbstgenutzt", "vermietet", "leer"]),
                col("personen", "Pers.", "number"), col("eigentuemer", "Eigentümer/in")],
                min_rows=3, required=True,
                hint="Einliegerwohnung ohne eigene Küche, Bad und eigenen Zugang zählt "
                     "förderrechtlich meist nicht als eigene Wohneinheit – bitte trotzdem "
                     "eintragen."),
            yesno("c_treppenhaus_beheizt", "Ist das Treppenhaus beheizt?", width="half"),
            yesno("c_dg_ausbau", "Ist ein Dachgeschossausbau geplant?", width="half")),
        sec("Energieversorgung und Abrechnung",
            radio("c_versorgung", "Wärmeversorgung", [
                "zentrale Heizung für alle Einheiten", "Etagenheizungen", "gemischt",
                "Fern-/Nahwärme"]),
            text("c_abrechnung", "Abrechnungsdienstleister (z. B. Heizkostenverteiler)"),
            table("c_verbrauch", "Gesamtverbrauch Heizung/Warmwasser", [
                col("jahr", "Jahr"), col("traeger", "Energieträger", "select", ENERGIETRAEGER),
                col("menge", "Menge", "number"), col("einheit", "Einheit"),
                col("kosten", "Kosten", "number", unit="€")], min_rows=3),
            checks("c_gemeinschaft", "Gemeinschaftsanlagen", [
                "zentrale Heizungsanlage", "zentrale Warmwasserbereitung", "Aufzug",
                "Lüftungsanlage", "Photovoltaik / Mieterstrom", "Tiefgarage / Stellplätze mit "
                "Lademöglichkeit", "Gemeinschaftsräume beheizt", "Waschküche / Trockenraum"]),
            info("c_hinweis",
                 "Die Förderhöchstgrenzen in der BEG richten sich nach der Zahl der "
                 "Wohneinheiten des Gebäudes – vollständige Angaben sichern die maximale "
                 "Förderung.")),
        sec("Sanierungsplanung auf Objektebene",
            num("c_ruecklage", "Erhaltungsrücklage (aktueller Stand)", unit="€", width="half"),
            select("c_beschlusslage", "Beschlusslage zur Sanierung", [
                "noch nicht besprochen", "in Diskussion", "Grundsatzbeschluss liegt vor",
                "Maßnahmen beschlossen"], width="half"),
            table("c_geplant", "Geplante oder notwendige Maßnahmen", [
                col("massnahme", "Maßnahme"), col("anlass", "Anlass (Schaden, Pflicht, Wunsch)"),
                col("zeitraum", "Zeitraum"), col("budget", "Budget", "number", unit="€")],
                min_rows=3),
            area("c_hemmnisse", "Besonderheiten (z. B. vermietete Einheiten, Finanzierung, "
                 "Denkmalschutz, Uneinigkeit in der Gemeinschaft)")),
        sec("Abschluss", *ort_datum(), sign("unterschrift", "Unterschrift Eigentümer/in bzw. "
                                           "Verwaltung")),
    ],
}

FORMS = [DATENBLATT_A, DATENBLATT_B, DATENBLATT_C]
