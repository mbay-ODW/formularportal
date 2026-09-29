#!/usr/bin/env python3
"""Baut die Images auf dem Docker-Host und legt den Portainer-Stack an bzw. aktualisiert ihn.

Alles über die Portainer-API – kein SSH nötig:
  1. POST /api/endpoints/{id}/docker/build?remote=<git>#<ref>:<kontext>  (Docker baut direkt
     aus dem Git-Repo auf dem Host; bei privatem Repo GIT_TOKEN setzen)
  2. Stack "formularportal" mit deploy/docker-compose.prod.yml anlegen oder aktualisieren.
     Bestehende Stack-Variablen bleiben erhalten; fehlende Secrets werden einmalig erzeugt.

Umgebung:
  PORTAINER_URL      z. B. https://portainer.example.com
  PORTAINER_TOKEN    API-Key (X-API-Key)
  PORTAINER_ENDPOINT Environment-ID (Default 1)
  GIT_URL            Default https://github.com/<owner>/formularportal.git
  GIT_REF            Default main
  GIT_TOKEN          nur bei privatem Repo (Fine-grained PAT, read-only Contents)
  FP_HOST, FP_MCP_HOST, FP_HERO_TOKEN … werden beim ersten Anlegen als Stack-Env übernommen.

Nutzung:  ./scripts/portainer_deploy.py [--nur-stack] [--nur-images]
"""
from __future__ import annotations

import json
import os
import secrets
import ssl
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STACK_NAME = os.environ.get("STACK_NAME", "formularportal")
IMAGES = [  # (Tag, Kontext im Repo, Dockerfile relativ zum Kontext)
    ("formularportal-backend:latest", "backend", "Dockerfile"),
    ("formularportal-frontend:latest", "frontend", "Dockerfile"),
    ("formularportal-mcp:latest", "", "Dockerfile.mcp"),
]
SECRET_KEYS = ("FP_INTERNAL_API_KEY", "MCP_API_KEY", "OIDC_CLIENT_SECRET")
PASS_KEYS = ("FP_HOST", "FP_MCP_HOST", "TRAEFIK_CERTRESOLVER", "FP_HERO_TOKEN",
             "FP_HERO_AUTO_UPLOAD", "FP_LINK_TTL_DAYS", "FP_SMTP_HOST", "FP_SMTP_PORT",
             "FP_SMTP_USER", "FP_SMTP_PASSWORD", "FP_SMTP_FROM", "FP_SMTP_SECURITY",
             "FP_NTFY_URL", "FP_NTFY_TOPIC", "FP_NTFY_TOKEN", "OIDC_CLIENT_ID")


def env(name: str, default: str | None = None) -> str:
    v = os.environ.get(name, default)
    if v is None:
        sys.exit(f"Umgebungsvariable {name} fehlt")
    return v


BASE = env("PORTAINER_URL").rstrip("/")
TOKEN = env("PORTAINER_TOKEN")
EID = int(env("PORTAINER_ENDPOINT", "1"))
CTX = ssl.create_default_context()


def call(method: str, path: str, body=None, raw: bool = False, timeout: int = 60):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method,
                                 headers={"X-API-Key": TOKEN,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
        out = r.read()
    return out if raw else (json.loads(out) if out else None)


def git_remote(context: str) -> str:
    url = env("GIT_URL", "https://github.com/mbay-ODW/formularportal.git")
    tok = os.environ.get("GIT_TOKEN")
    if tok:
        p = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit((p.scheme, f"x-access-token:{tok}@{p.netloc}", p.path,
                                       "", ""))
    ref = env("GIT_REF", "main")
    return f"{url}#{ref}" + (f":{context}" if context else "")


def build_images() -> None:
    for tag, context, dockerfile in IMAGES:
        q = urllib.parse.urlencode({"t": tag, "remote": git_remote(context),
                                    "dockerfile": dockerfile, "rm": "1", "forcerm": "1",
                                    "pull": "1"})
        print(f"→ baue {tag} …", flush=True)
        out = call("POST", f"/api/endpoints/{EID}/docker/build?{q}", raw=True, timeout=1800)
        errors = []
        for line in out.decode("utf-8", "replace").splitlines():
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if "error" in msg:
                errors.append(msg["error"])
        if errors:
            sys.exit(f"Build {tag} fehlgeschlagen: {errors[-1]}")
        print(f"  ✓ {tag}")


def deploy_stack() -> None:
    compose = (ROOT / "deploy" / "docker-compose.prod.yml").read_text(encoding="utf-8")
    stacks = call("GET", "/api/stacks") or []
    stack = next((s for s in stacks if s.get("Name") == STACK_NAME
                  and s.get("EndpointId") == EID), None)
    current = {e["name"]: e["value"] for e in (stack or {}).get("Env") or []}
    envs = dict(current)
    for k in PASS_KEYS:
        if os.environ.get(k):
            envs[k] = os.environ[k]
    for k in SECRET_KEYS:
        if not envs.get(k):
            envs[k] = secrets.token_urlsafe(36)
            print(f"  neues Secret erzeugt: {k} (steht im Stack-Env)")
    for k in ("FP_HOST", "FP_MCP_HOST"):
        if not envs.get(k):
            sys.exit(f"{k} fehlt (als Umgebungsvariable setzen)")
    env_list = [{"name": k, "value": v} for k, v in sorted(envs.items())]
    if stack:
        print(f"→ aktualisiere Stack {STACK_NAME} (id {stack['Id']}) …")
        call("PUT", f"/api/stacks/{stack['Id']}?endpointId={EID}",
             {"stackFileContent": compose, "env": env_list, "prune": True, "pullImage": False},
             timeout=300)
    else:
        print(f"→ lege Stack {STACK_NAME} an …")
        call("POST", f"/api/stacks/create/standalone/string?endpointId={EID}",
             {"name": STACK_NAME, "stackFileContent": compose, "env": env_list}, timeout=300)
    print("  ✓ Stack deployed")


if __name__ == "__main__":
    args = set(sys.argv[1:])
    if "--nur-stack" not in args:
        build_images()
    if "--nur-images" not in args:
        deploy_stack()
