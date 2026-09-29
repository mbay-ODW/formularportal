# Deployment

Produktion als Portainer-Stack hinter Traefik + Authelia, mit drei Containern
(`backend`, `frontend`, `mcp`). Vorlage: `deploy/docker-compose.prod.yml`.

## Voraussetzungen

- Traefik mit externem Netzwerk `traefik`, einem DNS-Challenge-CertResolver und den
  File-Provider-Middlewares `middlewares-authelia@file`, `middlewares-rate-limit@file`,
  `middlewares-secure-headers@file`.
- Authelia als forward-auth und OIDC-Provider.
- DNS-Einträge für `FP_HOST` (Verwaltung + Kundenportal) und `FP_MCP_HOST` (MCP).

## 1. Images bauen und Stack anlegen (Portainer-API)

```bash
export PORTAINER_URL=https://portainer.example.com
export PORTAINER_TOKEN=ptr_…            # Portainer → My account → Access tokens
export PORTAINER_ENDPOINT=1
export FP_HOST=formulare.example.com
export FP_MCP_HOST=formulare-mcp.example.com
export FP_HERO_TOKEN=…                  # optional
export GIT_TOKEN=…                      # nur bei privatem Repo (read-only PAT)
./scripts/portainer_deploy.py
```

Das Skript lässt Docker die drei Images direkt aus dem Git-Repo bauen
(`POST /endpoints/{id}/docker/build?remote=…`) und legt den Stack `formularportal` an bzw.
aktualisiert ihn. Fehlende Secrets (`FP_INTERNAL_API_KEY`, `MCP_API_KEY`, `OIDC_CLIENT_SECRET`)
erzeugt es einmalig; sie stehen danach im Stack-Env in Portainer und bleiben bei Updates erhalten.

Update nach neuen Commits: dasselbe Skript erneut ausführen. Nur den Stack neu schreiben:
`--nur-stack`; nur Images bauen: `--nur-images`.

Manuell geht es auch: Images auf dem Host bauen
(`docker build -t formularportal-backend:latest backend/`,
`docker build -t formularportal-frontend:latest frontend/`,
`docker build -t formularportal-mcp:latest -f Dockerfile.mcp .`) und den Inhalt von
`deploy/docker-compose.prod.yml` in Portainer als Stack (Web-Editor) mit den Variablen aus
`.env.example` anlegen.

## 2. Routing und Login

- **Verwaltung** (`https://FP_HOST/`): Router `formulare-admin` mit Authelia.
- **Kundenportal** (`/p/…`, `/f/…`, `/api/public/…`, `/assets/…`): Router `formulare-public` mit
  höherer Priorität, ohne Login, mit Rate-Limit.
- Authelia braucht eine Zugriffsregel für `FP_HOST` (eine vorhandene Wildcard-Regel genügt), siehe
  `deploy/authelia-oidc-client.yml`.

## 3. MCP-Connector (optional für claude.ai)

1. In Authelia den OIDC-Client `formularportal-mcp` anlegen (`deploy/authelia-oidc-client.yml`);
   als Secret den bcrypt-Hash von `OIDC_CLIENT_SECRET` aus dem Stack-Env eintragen.
2. `deploy/traefik-formulare-mcp-oauth.yml` anpassen (`mcp.example.com` → `FP_MCP_HOST`) und in
   das rules-Verzeichnis des Traefik-File-Providers legen.
3. Für Claude Desktop/Code reicht `MCP_API_KEY` als Bearer. Dafür sind die Schritte 1–2 nicht
   nötig.

## 4. Einrichtung in der Oberfläche

*Einstellungen*: Firmenkopf, Logo, Farben, Benachrichtigungsadresse und Begrüßungstext.
Mailversand wird über die `FP_SMTP_*`-Variablen aktiviert, der Status steht in den
Einstellungen, dort gibt es auch eine Testmail.

## Daten und Backup

Alle veränderlichen Daten liegen im Volume `formularportal_data`: SQLite-Datenbank,
`einstellungen.json` und das Logo.

```bash
docker run --rm -v formularportal_formularportal_data:/data -v "$PWD":/backup alpine \
  tar czf /backup/formularportal-$(date +%F).tar.gz -C /data .
```

## Health

- Backend: `GET /api/health`, Compose-Healthcheck im Image.
- MCP: `GET /health`.
