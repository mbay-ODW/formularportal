# Formularportal

Online-Formulare für den kompletten Energieberatungs- und Förderprozess, mit eigenem
Branding, Kundenportal, PDF-Export, HERO-Anbindung und MCP-Server für Agenten.

## Funktionen

- **20 Formulare** entlang des Beratungsablaufs (Katalog unter *Formulare*):

  | Nr. | Formular | füllt aus |
  |---|---|---|
  | 1 | Stammdatenblatt Eigentümer / Antragsteller | Kunde |
  | 2 | Stammdatenblatt Gebäude / Objekt | Kunde |
  | 3 | Datenblatt Teil A – Nutzerverhalten EFH/ZFH | Kunde |
  | 4 | Datenblatt Teil B – Technische Gebäudeaufnahme | Energieberater |
  | 5 | Datenblatt Teil C – Objekt- und Belegungsstruktur MFH | Kunde / Verwaltung |
  | 6 | Checkliste EBW – Antragstellung in Vollmacht | Kunde |
  | 7 | Checkliste BEG EM – Einzelmaßnahmen | Kunde |
  | 8 | Fachunternehmererklärung Gebäudehülle | Fachunternehmen |
  | 9 | Checkliste Heizungstausch | Kunde |
  | 10 | Fachunternehmererklärung Heizungstechnik | Fachunternehmen |
  | 11 | Liefer- und Leistungsvertrag BEG EM (mit Förderbedingung) | Kunde + Fachunternehmen |
  | 12 | Liefer- und Leistungsvertrag Heizung (mit Förderbedingung) | Kunde + Fachunternehmen |
  | 13 | Auftrag Energieberatung mit Honorarvereinbarung und Widerrufsbelehrung | Kunde + Berater |
  | 14 | Datenschutzhinweise (Art. 13 DSGVO) und Einwilligungen | Kunde |
  | 15 | Vollmacht zur Einholung von Unterlagen und Verbrauchsdaten | Kunde |
  | 16 | Übergabe- und Abschlussprotokoll Sanierungsfahrplan | Kunde + Berater |
  | 17 | Erklärung und Bestätigung Eigenleistung | Kunde + Berater |
  | 18 | Protokoll Baubegleitung | Berater (+ Fachunternehmen) |
  | 19 | Nutzerinformation und Kenntnisnahme Lüftungskonzept | Kunde |
  | 20 | Datenerhebung Energieausweis | Kunde |

  Info-Texte mit `{{firma}}`, `{{anschrift}}`, `{{telefon}}`, `{{email}}` … werden aus dem
  Firmenkopf befüllt (z. B. in der Widerrufsbelehrung). Vertrags-, Widerrufs- und
  Datenschutztexte sind Vorlagen und vor dem Einsatz rechtlich zu prüfen.
- **Vorgänge** je Kunde/Objekt, wahlweise aus einem **HERO-Projekt** angelegt (Kunde, Anschrift,
  Kontaktdaten und Objektadresse werden übernommen), mit Formular-Paketen
  (iSFP, BEG EM Gebäudehülle, Heizungstausch, MFH/WEG).
- **Keine doppelten Abfragen:** Felder mit `eig_`/`obj_`/`fu_` gelten vorgangsweit und sind in
  allen Formularen vorbelegt. Unterschriften und Einzelbestätigungen werden nie übertragen.
- **Kundenportal** ohne Login über geheime Links (`/p/<token>` für alle freigegebenen
  Formulare, `/f/<token>` für ein einzelnes, z. B. für das Fachunternehmen): responsiv,
  **Autospeichern**, Pflichtfeldprüfung, **digitale Unterschrift**, Sperre nach dem Absenden,
  Ablaufdatum für Links.
- **Gebrandete PDFs:** Logo, Firmenname, Anschrift und Website im Kopf jeder Seite – ausgefüllt,
  als Druckvorlage oder als **beschreibbares PDF** (Formularfelder, optional mit den bekannten
  Daten vorbefüllt) für den Mailversand.
- **Sprungmarken** mit Erledigt-Status je Abschnitt und Fortschrittsanzeige in langen
  Formularen.
- **Benachrichtigung** bei Einreichung per Mail (mit PDF-Anhang), Kopie an den Kunden bzw. das
  Fachunternehmen und optional ntfy-Push;
  Link-Versand an Kunden per Mail.
- **HERO:** Projekte/Kontakte suchen, Stammdaten übernehmen oder abgleichen, fertige PDFs ins
  Projekt hochladen (manuell, per Agent oder automatisch nach Einreichung) inkl.
  Logbucheintrag.
- **MCP-Server** (eigener Container) mit 19 Tools, damit Agenten Vorgänge anlegen,
  Formulare aus Unterlagen vorbefüllen, prüfen, abschließen und in HERO ablegen können.

## Architektur

| Service | Basis | Aufgabe | Port |
|---|---|---|---|
| `backend` | python:3.12-slim | FastAPI, SQLite, PDF (ReportLab), HERO, SMTP | 8000 (intern) |
| `frontend` | nginx:1.27-alpine | React-SPA (Verwaltung + Kundenportal), proxyt `/api` | 80 |
| `mcp` | python:3.12-slim | MCP über Streamable HTTP, spricht die interne API | 3000 |

Sicherheit: Die Verwaltung liegt hinter Authelia. Das Kundenportal hat einen eigenen
Traefik-Router ohne Login, der nur die Kundenpfade freigibt. Traefik setzt je Router den Header
`X-Portal-Zone`, und das Backend beantwortet Verwaltungs-Endpunkte nur mit Zone `admin` oder dem
internen API-Key des MCP-Containers. Kundentoken sind 192 Bit zufällig, laufen ab und lassen sich
erneuern.

## Entwicklung

```bash
# Backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
FP_DATA_DIR=./data uvicorn app.main:app --reload       # :8000
pytest -q

# Frontend (proxyt /api auf :8000)
cd frontend && npm install && npm run dev               # :5173
```

Lokal komplett per Docker: `cp .env.example .env && docker compose up -d --build`
(Verwaltung und Portal unter http://localhost:8090, MCP unter http://localhost:8091/mcp).

## Deployment

Siehe [DEPLOYMENT.md](DEPLOYMENT.md): Portainer-Stack hinter Traefik + Authelia, Images
werden per Portainer-API direkt aus dem Git-Repo gebaut.

## MCP verbinden

- **Claude Code / Desktop:** `https://<FP_MCP_HOST>/mcp` mit Header
  `Authorization: Bearer <MCP_API_KEY>`.
- **claude.ai-Connector:** URL `https://<FP_MCP_HOST>/mcp`; der Login läuft über Authelia (OIDC,
  siehe `deploy/`).

Typischer Agenten-Ablauf: `hero_projekte_suchen` → `vorgang_anlegen(hero_project_id, paket)` →
`formular_schema` → `formular_ausfuellen` → `formular_lesen` (offene Pflichtfelder) →
`kundenlink` bzw. `link_per_mail_senden` für Unterschriften → `hero_pdf_hochladen`.

## Formulare anpassen

Die Definitionen liegen als Python-Daten unter `backend/app/forms/` (kleine DSL in `_dsl.py`).
Neue Felder brauchen keine Datenbankänderung. Förderrechtliche Hinweise sind bewusst allgemein
gehalten und bei Richtlinienänderungen dort anzupassen (Feld `version` hochzählen).
