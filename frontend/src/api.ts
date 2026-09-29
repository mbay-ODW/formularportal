import type {
  Branding, CatalogEntry, Data, Ereignis, FormDef, FormularSummary, FormularView, HeroProject,
  Me, Missing, PublicForm, Vorgang,
} from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string, public fehlend?: Missing[]) {
    super(message);
  }
}

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const init: RequestInit = { method, headers: {} };
  if (body instanceof FormData) {
    init.body = body;
  } else if (body !== undefined) {
    init.body = JSON.stringify(body);
    (init.headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  const r = await fetch(url, init);
  if (!r.ok) {
    let msg = `Fehler ${r.status}`;
    let fehlend: Missing[] | undefined;
    try {
      const j = await r.json();
      msg = typeof j.detail === "string" ? j.detail : msg;
      fehlend = j.fehlend ?? undefined;
    } catch { /* keine JSON-Antwort */ }
    throw new ApiError(r.status, msg, fehlend);
  }
  if (r.status === 204) return undefined as T;
  return r.json() as Promise<T>;
}

export const api = {
  // Verwaltung
  me: () => req<Me>("GET", "/api/me"),
  catalog: () => req<{ formulare: CatalogEntry[]; pakete: Record<string, string[]> }>(
    "GET", "/api/forms"),
  formDef: (key: string) => req<FormDef>("GET", `/api/forms/${key}`),
  vorgaenge: (q = "", archiviert = false) =>
    req<Vorgang[]>("GET", `/api/vorgaenge?q=${encodeURIComponent(q)}&archiviert=${archiviert}`),
  vorgang: (id: number) => req<Vorgang>("GET", `/api/vorgaenge/${id}`),
  vorgangNeu: (body: Record<string, unknown>) => req<Vorgang>("POST", "/api/vorgaenge", body),
  vorgangPatch: (id: number, body: Record<string, unknown>) =>
    req<Vorgang>("PATCH", `/api/vorgaenge/${id}`, body),
  vorgangLoeschen: (id: number) => req<void>("DELETE", `/api/vorgaenge/${id}`),
  vorgangFormulare: (id: number, keys: string[]) =>
    req<Vorgang>("POST", `/api/vorgaenge/${id}/formulare`, { keys }),
  vorgangEreignisse: (id: number) => req<Ereignis[]>("GET", `/api/vorgaenge/${id}/ereignisse`),
  vorgangHeroSync: (id: number, overwrite = false) =>
    req<{ uebernommen: string[] }>("POST", `/api/vorgaenge/${id}/hero-sync?overwrite=${overwrite}`),
  vorgangLinkSenden: (id: number, email = "", nachricht = "") =>
    req<{ gesendet_an: string }>("POST", `/api/vorgaenge/${id}/link-senden`, { email, nachricht }),
  vorgangNeuerLink: (id: number) => req<Vorgang>("POST", `/api/vorgaenge/${id}/neuer-link`),
  formular: (id: number) => req<FormularView>("GET", `/api/formulare/${id}`),
  formularSpeichern: (id: number, data: Data) =>
    req<FormularView>("PUT", `/api/formulare/${id}`, { data }),
  formularEinreichen: (id: number) => req<FormularView>("POST", `/api/formulare/${id}/einreichen`),
  formularStatus: (id: number, status: string) =>
    req<FormularView>("POST", `/api/formulare/${id}/status`, { status }),
  formularFreigabe: (id: number, freigegeben: boolean) =>
    req<FormularSummary>("PATCH", `/api/formulare/${id}`, { freigegeben }),
  formularNeuerLink: (id: number) => req<FormularSummary>("POST", `/api/formulare/${id}/neuer-link`),
  formularLinkSenden: (id: number, email = "", nachricht = "") =>
    req<{ gesendet_an: string }>("POST", `/api/formulare/${id}/link-senden`, { email, nachricht }),
  formularHeroUpload: (id: number) =>
    req<{ dateiname: string }>("POST", `/api/formulare/${id}/hero-upload`),
  formularLoeschen: (id: number) => req<void>("DELETE", `/api/formulare/${id}`),
  heroProjekte: (q: string) =>
    req<HeroProject[]>("GET", `/api/hero/projekte?q=${encodeURIComponent(q)}`),
  einstellungen: () => req<Record<string, string | boolean>>("GET", "/api/einstellungen"),
  einstellungenSpeichern: (body: Record<string, unknown>) =>
    req<Record<string, string | boolean>>("PUT", "/api/einstellungen", body),
  logoHochladen: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req<{ ok: boolean }>("POST", "/api/einstellungen/logo", fd);
  },
  logoLoeschen: () => req<{ ok: boolean }>("DELETE", "/api/einstellungen/logo"),
  testmail: () => req<{ gesendet_an: string }>("POST", "/api/einstellungen/testmail"),

  // Kundenportal
  branding: () => req<Branding>("GET", "/api/public/branding"),
  portal: (token: string) => req<{
    kunde: string; objekt: string; titel: string; branding: Branding;
    formulare: { token: string; title: string; nr: number; description: string;
                 status: string; audience: string; updated_at: string }[];
  }>("GET", `/api/public/p/${token}`),
  publicForm: (token: string) => req<PublicForm>("GET", `/api/public/f/${token}`),
  publicSave: (token: string, data: Data) =>
    req<{ status: string; fehlend: Missing[]; gespeichert: string }>(
      "PUT", `/api/public/f/${token}`, { data }),
  publicSubmit: (token: string, data: Data) =>
    req<PublicForm>("POST", `/api/public/f/${token}/submit`, { data }),
};

export const STATUS_LABEL: Record<string, string> = {
  entwurf: "Offen",
  in_bearbeitung: "In Bearbeitung",
  eingereicht: "Eingereicht",
  geprueft: "Geprüft",
};

export function fmtDate(iso?: string | null): string {
  if (!iso) return "–";
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString("de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit",
  });
}
