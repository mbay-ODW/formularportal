"""Formulare 8 und 10: Fachunternehmererklärungen Gebäudehülle und Heizungstechnik."""
from app.forms._bausteine import fachunternehmen, objekt_kurz
from app.forms._dsl import (area, check, checks, col, date, info, num, ort_datum, radio, sec,
                            select, sign, table, text, when, yesno)

PROGRAMME = ["BAFA – BEG Einzelmaßnahmen", "KfW – Heizungsförderung",
             "KfW – Effizienzhaus", "Steuerermäßigung § 35c EStG", "Landes-/Kommunalprogramm"]

FUE_HUELLE = {
    "key": "fue_gebaeudehuelle",
    "nr": 8,
    "title": "Fachunternehmererklärung Gebäudehülle",
    "short": "FUE Gebäudehülle",
    "audience": "fachunternehmen",
    "category": "Nachweise",
    "version": "2026-09",
    "description": "Bestätigung des ausführenden Fachunternehmens: erreichte U-Werte, "
                   "eingesetzte Produkte und fachgerechte Ausführung nach BEG und GEG.",
    "sections": [
        sec("Ausführendes Fachunternehmen", *fachunternehmen()),
        sec("Bauherr/in und Objekt",
            text("eig_vorname", "Vorname", width="half"),
            text("eig_nachname", "Nachname", required=True, width="half"),
            *objekt_kurz()),
        sec("Förderprogramm",
            radio("fue_programm", "Förderprogramm", PROGRAMME, required=True),
            text("fue_foerder_id", "Kennung (z. B. TPB-ID, Vorgangs- oder Antragsnummer)",
                 width="half"),
            text("fue_eee", "Energieeffizienz-Experte/in", width="half")),
        sec("Ausgeführte Maßnahmen",
            checks("fue_massnahmen", "Maßnahmen", [
                "Außenwand", "Dach / Dachschräge", "Oberste Geschossdecke", "Flachdach",
                "Kellerdecke / Bodenplatte", "Wände gegen Erdreich / unbeheizt",
                "Fenster / Fenstertüren", "Dachflächenfenster", "Außentüren",
                "Vorhangfassade", "Sommerlicher Wärmeschutz"], required=True),
            table("fue_bauteile", "Bauteile, Produkte und erreichte Werte", [
                col("bauteil", "Bauteil"), col("produkt", "Dämmstoff / Produkt"),
                col("dicke", "Dicke", "number", unit="mm"),
                col("lambda", "λ bzw. WLS", "number", unit="W/(mK)"),
                col("u_ist", "U erreicht", "number", unit="W/(m²K)"),
                col("u_max", "U Anforderung", "number", unit="W/(m²K)"),
                col("flaeche", "Fläche", "number", unit="m²")], min_rows=2, required=True),
            info("fue_anforderungen",
                 "Orientierung BEG-Anforderungen (U-Wert max., W/(m²K)): Außenwand 0,20 · "
                 "Dach/Schrägdach, oberste Geschossdecke, Flachdach 0,14 · Kellerdecke, "
                 "Bodenplatte, Wände gegen Erdreich/unbeheizt 0,25 · Fenster 0,95 · "
                 "Dachflächenfenster 1,0 · Außentüren 1,3. Maßgeblich sind die zum "
                 "Antragszeitpunkt gültigen technischen Mindestanforderungen und die Vorgaben "
                 "des Energieeffizienz-Experten.")),
        sec("Bestätigungen des Fachunternehmens",
            check("fue_b_wb", "Das Wärmebrückenkonzept nach Vorgabe des Energieeffizienz-"
                  "Experten wurde umgesetzt.", default=True),
            check("fue_b_luftdicht", "Das Luftdichtheitskonzept nach Vorgabe des "
                  "Energieeffizienz-Experten wurde umgesetzt.", default=True),
            check("fue_b_regeln", "Die Arbeiten wurden fachgerecht nach den allgemein "
                  "anerkannten Regeln der Technik und den Herstellervorgaben ausgeführt.",
                  required=True),
            check("fue_b_werte", "Die angegebenen Werte wurden mit den eingebauten Produkten "
                  "erreicht; Produktdatenblätter bzw. Nachweise liegen vor.", required=True),
            check("fue_b_geg", "Die Anforderungen des Gebäudeenergiegesetzes an die geänderten "
                  "Bauteile sind eingehalten.", required=True),
            check("fue_b_subvention", "Mir ist bekannt, dass die Angaben subventionserheblich "
                  "sind (§ 264 StGB).", required=True)),
        sec("Ausführung und Rechnung",
            date("fue_beginn", "Beginn der Arbeiten", width="third"),
            date("fue_fertig", "Fertigstellung", required=True, width="third"),
            text("fue_rechnung_nr", "Rechnungsnummer", width="third"),
            date("fue_rechnung_datum", "Rechnungsdatum", width="half"),
            num("fue_kosten", "Rechnungsbetrag brutto", unit="€", width="half"),
            area("fue_bemerkung", "Bemerkungen (Abweichungen, Denkmalschutz o. Ä.)")),
        sec("Unterschrift Fachunternehmen", *ort_datum(),
            text("fue_unterzeichner", "Name der unterzeichnenden Person", required=True),
            sign("unterschrift", "Unterschrift / Stempel Fachunternehmen", required=True)),
    ],
}

FUE_HEIZUNG = {
    "key": "fue_heizungstechnik",
    "nr": 10,
    "title": "Fachunternehmererklärung Heizungstechnik",
    "short": "FUE Heizungstechnik",
    "audience": "fachunternehmen",
    "category": "Nachweise",
    "version": "2026-09",
    "description": "Bestätigung des Heizungsbauers: installierte Anlage, hydraulischer "
                   "Abgleich, Inbetriebnahme und Stilllegung der Altanlage.",
    "sections": [
        sec("Ausführendes Fachunternehmen", *fachunternehmen()),
        sec("Bauherr/in und Objekt",
            text("eig_vorname", "Vorname", width="half"),
            text("eig_nachname", "Nachname", required=True, width="half"),
            *objekt_kurz()),
        sec("Förderprogramm",
            radio("fuh_programm", "Förderprogramm", PROGRAMME, required=True),
            text("fuh_foerder_id", "Antrags- bzw. Zusagenummer", width="half"),
            text("fuh_bza_id", "ID der Bestätigung zum Antrag (BzA)", width="half")),
        sec("Installierte Anlage",
            select("fuh_art", "Anlagenart", [
                "Luft/Wasser-Wärmepumpe", "Sole/Wasser-Wärmepumpe", "Wasser/Wasser-Wärmepumpe",
                "Biomassekessel", "Wärmenetzanschluss / Übergabestation", "Solarthermie",
                "Hybridheizung", "Sonstige"], required=True, width="half"),
            text("fuh_hersteller", "Hersteller", required=True, width="half"),
            text("fuh_modell", "Modell / Typ", required=True, width="half"),
            text("fuh_seriennr", "Seriennummer", width="half"),
            num("fuh_leistung", "Nennwärmeleistung", unit="kW", required=True, width="third"),
            num("fuh_jaz", "Jahresarbeitszahl (berechnet)", width="third",
                show_if=when("fuh_art", in_=["Luft/Wasser-Wärmepumpe", "Sole/Wasser-Wärmepumpe",
                                             "Wasser/Wasser-Wärmepumpe", "Hybridheizung"])),
            text("fuh_kaeltemittel", "Kältemittel", width="third",
                 show_if=when("fuh_art", in_=["Luft/Wasser-Wärmepumpe", "Sole/Wasser-Wärmepumpe",
                                              "Wasser/Wasser-Wärmepumpe", "Hybridheizung"])),
            text("fuh_anlagennr", "Anlagen- bzw. Listennummer (falls gefordert)", width="half"),
            num("fuh_speicher", "Speichervolumen", unit="l", width="half"),
            date("fuh_inbetriebnahme", "Inbetriebnahme", required=True, width="half")),
        sec("Auslegung und Abgleich",
            yesno("fuh_heizlast", "Raumweise Heizlastberechnung durchgeführt?", required=True,
                  width="half"),
            radio("fuh_abgleich_verfahren", "Hydraulischer Abgleich", [
                "Verfahren B (raumweise Heizlast)", "Verfahren A", "noch ausstehend"],
                required=True, width="half"),
            date("fuh_abgleich_datum", "Datum des Abgleichs", width="half"),
            check("fuh_abgleich_nachweis", "Bestätigungsformular zum hydraulischen Abgleich "
                  "liegt bei."),
            num("fuh_vorlauf", "Auslegungs-Vorlauftemperatur", unit="°C", width="half")),
        sec("Bestätigungen",
            check("fuh_b_fachgerecht", "Die Anlage wurde fachgerecht nach Herstellervorgaben "
                  "installiert und in Betrieb genommen.", required=True),
            check("fuh_b_einweisung", "Der Betreiber wurde in die Bedienung eingewiesen; "
                  "Unterlagen wurden übergeben.", required=True),
            check("fuh_b_zaehler", "Bei Wärmepumpen: Strom- und Wärmemengenzähler sind "
                  "installiert bzw. eine Verbrauchserfassung ist möglich."),
            check("fuh_b_altanlage", "Die fossile Altanlage wurde außer Betrieb genommen bzw. "
                  "demontiert und fachgerecht entsorgt."),
            check("fuh_b_subvention", "Mir ist bekannt, dass die Angaben subventionserheblich "
                  "sind (§ 264 StGB).", required=True)),
        sec("Rechnung",
            text("fuh_rechnung_nr", "Rechnungsnummer", width="third"),
            date("fuh_rechnung_datum", "Rechnungsdatum", width="third"),
            num("fuh_kosten", "Rechnungsbetrag brutto", unit="€", width="third"),
            area("fuh_bemerkung", "Bemerkungen")),
        sec("Unterschrift Fachunternehmen", *ort_datum(),
            text("fuh_unterzeichner", "Name der unterzeichnenden Person", required=True),
            sign("unterschrift", "Unterschrift / Stempel Fachunternehmen", required=True)),
    ],
}

FORMS = [FUE_HUELLE, FUE_HEIZUNG]
