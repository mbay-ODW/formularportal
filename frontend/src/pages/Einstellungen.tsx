import { useEffect, useState } from "react";
import { api, ApiError } from "../api";
import { applyBranding } from "../hooks";
import type { Me } from "../types";

const FELDER: [string, string, string?][] = [
  ["firma", "Firmenname"], ["inhaber", "Inhaber/in bzw. Ansprechpartner/in"],
  ["zusatz", "Zusatzzeile (z. B. Qualifikation)"], ["strasse", "Straße, Hausnr."],
  ["plz_ort", "PLZ, Ort"], ["telefon", "Telefon"], ["email", "E-Mail (öffentlich)"],
  ["website", "Website"],
  ["benachrichtigung_email", "Benachrichtigung bei Einreichung an", "Leer = öffentliche E-Mail"],
  ["fusszeile", "Fußzeile in PDFs (z. B. USt-ID, Bank)"],
];
const FARBEN: [string, string][] = [["farbe_primaer", "Primärfarbe"], ["farbe_akzent",
  "Akzentfarbe"], ["farbe_text", "Textfarbe"]];

export default function Einstellungen() {
  const [s, setS] = useState<Record<string, string | boolean> | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [logoV, setLogoV] = useState(Date.now());

  useEffect(() => {
    api.einstellungen().then(setS);
    api.me().then(setMe);
  }, []);

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    setMsg(""); setErr("");
    try { await fn(); setMsg(ok); } catch (e) { setErr((e as ApiError).message); }
  };

  if (!s) return <p>Lädt …</p>;
  const set = (k: string, v: string) => setS({ ...s, [k]: v });

  return (
    <>
      {msg && <p className="ok-note">{msg}</p>}
      {err && <p className="error">{err}</p>}
      <div className="grid-2">
        <div className="card">
          <h3>Firmenkopf</h3>
          <p className="muted small">Erscheint im Kundenportal und im Kopf jedes PDFs.</p>
          <div className="fgrid">
            {FELDER.map(([k, l, hint]) => (
              <div key={k} className="field w-full">
                <label className="flabel">{l}</label>
                <input value={String(s[k] ?? "")} onChange={(e) => set(k, e.target.value)} />
                {hint && <div className="hint">{hint}</div>}
              </div>
            ))}
            <div className="field w-full">
              <label className="flabel">Begrüßungstext im Kundenportal</label>
              <textarea rows={3} value={String(s.portal_begruessung ?? "")}
                onChange={(e) => set("portal_begruessung", e.target.value)} />
            </div>
            <div className="field w-full">
              <label className="confirm">
                <input type="checkbox" checked={s.kopie_an_kunde === "ja"}
                  onChange={(e) => set("kopie_an_kunde", e.target.checked ? "ja" : "nein")} />
                <span>Nach dem Absenden eine Kopie (PDF) an den Kunden bzw. das
                  Fachunternehmen senden</span>
              </label>
            </div>
            {FARBEN.map(([k, l]) => (
              <div key={k} className="field w-third">
                <label className="flabel">{l}</label>
                <input type="color" value={String(s[k])} onChange={(e) => set(k, e.target.value)} />
              </div>
            ))}
          </div>
          <button className="primary" onClick={() => run(async () => {
            const r = await api.einstellungenSpeichern(s);
            setS(r);
            applyBranding(r as never);
          }, "Gespeichert")}>Speichern</button>
        </div>
        <div>
          <div className="card">
            <h3>Logo</h3>
            <img src={`/api/public/logo?v=${logoV}`} alt="Logo" className="logo-preview" />
            <p className="muted small">PNG oder JPG, max. 2 MB. Ohne eigenes Logo wird das
              Standardlogo verwendet.</p>
            <input type="file" accept="image/png,image/jpeg" onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) run(async () => { await api.logoHochladen(f); setLogoV(Date.now()); },
                "Logo hochgeladen");
            }} />
            {s.eigenes_logo && <button className="link" onClick={() => run(async () => {
              await api.logoLoeschen(); setLogoV(Date.now());
              setS({ ...s, eigenes_logo: false });
            }, "Logo entfernt")}>Eigenes Logo entfernen</button>}
          </div>
          <div className="card">
            <h3>Anbindungen</h3>
            <ul className="status-list">
              <li><span className={me?.hero ? "dot on" : "dot"} /> HERO {me?.hero ? "verbunden"
                : "nicht konfiguriert (FP_HERO_TOKEN)"}
                {me?.hero_auto_upload ? " · Auto-Upload aktiv" : ""}</li>
              <li><span className={me?.smtp ? "dot on" : "dot"} /> Mailversand {me?.smtp
                ? "aktiv" : "nicht konfiguriert (FP_SMTP_*)"}</li>
              <li><span className={me?.ntfy ? "dot on" : "dot"} /> Push (ntfy) {me?.ntfy
                ? "aktiv" : "aus"}</li>
              <li className="muted small">Öffentliche Adresse: {me?.public_base_url}</li>
            </ul>
            {me?.smtp && <button className="ghost small" onClick={() => run(async () => {
              const r = await api.testmail(); setMsg(`Testmail an ${r.gesendet_an} gesendet`);
            }, "Testmail gesendet")}>Testmail senden</button>}
          </div>
        </div>
      </div>
    </>
  );
}
