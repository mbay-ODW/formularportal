import { useEffect, useRef, useState } from "react";
import { api, ApiError, fmtDate } from "../api";
import { linkProps, navigate } from "../router";
import type { CatalogEntry, HeroProject, Vorgang } from "../types";

function NeuerVorgang({ onClose }: { onClose: () => void }) {
  const [mode, setMode] = useState<"hero" | "manuell">("hero");
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [pakete, setPakete] = useState<Record<string, string[]>>({});
  const [paket, setPaket] = useState("");
  const [keys, setKeys] = useState<string[]>([]);
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<HeroProject[]>([]);
  const [heroSel, setHeroSel] = useState<HeroProject | null>(null);
  const [loading, setLoading] = useState(false);
  const [f, setF] = useState({ titel: "", vorname: "", nachname: "", email: "" });
  const [err, setErr] = useState("");
  const timer = useRef<number>();

  useEffect(() => {
    api.catalog().then((r) => {
      setCatalog(r.formulare);
      setPakete(r.pakete);
      const first = Object.keys(r.pakete)[0];
      setPaket(first);
      setKeys(r.pakete[first]);
    });
  }, []);

  useEffect(() => {
    window.clearTimeout(timer.current);
    if (mode !== "hero" || q.trim().length < 2) { setHits([]); return; }
    timer.current = window.setTimeout(async () => {
      setLoading(true);
      try { setHits(await api.heroProjekte(q)); } catch (e) { setErr((e as Error).message); }
      setLoading(false);
    }, 350);
  }, [q, mode]);

  const pickPaket = (p: string) => { setPaket(p); if (p) setKeys(pakete[p]); };
  const toggle = (k: string) => { setPaket(""); setKeys((ks) => ks.includes(k) ? ks.filter((x) =>
    x !== k) : [...ks, k]); };

  const create = async () => {
    setErr("");
    try {
      const body: Record<string, unknown> = { formulare: keys, titel: f.titel };
      if (mode === "hero") {
        if (!heroSel) { setErr("Bitte ein HERO-Projekt auswählen."); return; }
        body.hero_project_id = heroSel.project_id;
      } else {
        body.kunde_email = f.email;
        body.stammdaten = { eig_vorname: f.vorname || null, eig_nachname: f.nachname || null,
                            eig_email: f.email || null };
      }
      const v = await api.vorgangNeu(body);
      navigate(`/vorgang/${v.id}`);
    } catch (e) { setErr((e as ApiError).message); }
  };

  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Neuer Vorgang</h2>
        <div className="tabs">
          <button className={mode === "hero" ? "on" : ""} onClick={() => setMode("hero")}>
            Aus HERO übernehmen</button>
          <button className={mode === "manuell" ? "on" : ""} onClick={() => setMode("manuell")}>
            Manuell</button>
        </div>
        {mode === "hero" ? (
          <div>
            <input autoFocus placeholder="HERO-Projekt suchen (Nr., Name, Kunde, Ort) …"
              value={q} onChange={(e) => setQ(e.target.value)} />
            {loading && <p className="muted">suche in HERO …</p>}
            <div className="hero-hits">
              {hits.map((h) => (
                <button key={h.project_id} type="button"
                  className={heroSel?.project_id === h.project_id ? "hit on" : "hit"}
                  onClick={() => setHeroSel(h)}>
                  <b>{h.hero_ref} · {h.name}</b>
                  <span className="muted">{[h.kunde, h.adresse].filter(Boolean).join(" — ")}
                    {h.measure ? ` · ${h.measure}` : ""}{h.status ? ` · ${h.status}` : ""}</span>
                </button>
              ))}
            </div>
            {heroSel && <p className="ok-note">Übernommen werden Kunde, Anschrift, Kontaktdaten
              und Objektadresse aus {heroSel.hero_ref}.</p>}
          </div>
        ) : (
          <div className="fgrid">
            <div className="field w-half"><label className="flabel">Vorname</label>
              <input value={f.vorname} onChange={(e) => setF({ ...f, vorname: e.target.value })} /></div>
            <div className="field w-half"><label className="flabel">Nachname</label>
              <input value={f.nachname} onChange={(e) => setF({ ...f, nachname: e.target.value })} /></div>
            <div className="field w-full"><label className="flabel">E-Mail</label>
              <input type="email" value={f.email}
                onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
          </div>
        )}
        <div className="field w-full"><label className="flabel">Titel (optional)</label>
          <input value={f.titel} placeholder="z. B. iSFP Musterstraße 1"
            onChange={(e) => setF({ ...f, titel: e.target.value })} /></div>
        <h3>Formulare</h3>
        <select value={paket} onChange={(e) => pickPaket(e.target.value)}>
          <option value="">Individuelle Auswahl</option>
          {Object.keys(pakete).map((p) => <option key={p}>{p}</option>)}
        </select>
        <div className="choices cols">
          {catalog.map((c) => (
            <label key={c.key} className={keys.includes(c.key) ? "choice on" : "choice"}>
              <input type="checkbox" checked={keys.includes(c.key)} onChange={() => toggle(c.key)} />
              <span>{c.nr}. {c.short} <span className="muted">({c.audience_label})</span></span>
            </label>
          ))}
        </div>
        {err && <p className="error">{err}</p>}
        <div className="modal-actions">
          <button className="ghost" onClick={onClose}>Abbrechen</button>
          <button className="primary" onClick={create}>Vorgang anlegen</button>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [items, setItems] = useState<Vorgang[] | null>(null);
  const [q, setQ] = useState("");
  const [archiv, setArchiv] = useState(false);
  const [neu, setNeu] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => api.vorgaenge(q, archiv).then(setItems), 250);
    return () => window.clearTimeout(t);
  }, [q, archiv]);

  return (
    <>
      <div className="toolbar">
        <input className="search" placeholder="Suchen (Kunde, Titel, HERO-Nr., E-Mail) …" value={q}
          onChange={(e) => setQ(e.target.value)} />
        <label className="inline-check"><input type="checkbox" checked={archiv}
          onChange={(e) => setArchiv(e.target.checked)} /> Archiv</label>
        <button className="primary auto" onClick={() => setNeu(true)}>+ Neuer Vorgang</button>
      </div>
      {items === null ? <p>Lädt …</p> : items.length === 0 ? (
        <div className="card empty">
          <p>Noch keine Vorgänge. Lege einen Vorgang an – am schnellsten direkt aus einem
            HERO-Projekt.</p>
        </div>
      ) : (
        <div className="card flush">
          <table className="list">
            <thead><tr><th>Vorgang</th><th>Kunde</th><th>Objekt</th><th>Formulare</th>
              <th>HERO</th><th>Aktualisiert</th></tr></thead>
            <tbody>
              {items.map((v) => (
                <tr key={v.id} onClick={() => navigate(`/vorgang/${v.id}`)}>
                  <td><a {...linkProps(`/vorgang/${v.id}`)}><b>{v.titel}</b></a></td>
                  <td>{v.kunde || "–"}</td>
                  <td>{v.objekt || "–"}</td>
                  <td>
                    <span className="pill">{v.anzahl_formulare ?? 0}</span>
                    {(v.anzahl_eingereicht ?? 0) > 0 &&
                      <span className="badge eingereicht">{v.anzahl_eingereicht} neu</span>}
                    {(v.anzahl_geprueft ?? 0) > 0 &&
                      <span className="badge geprueft">{v.anzahl_geprueft} geprüft</span>}
                  </td>
                  <td>{v.hero_ref || "–"}</td>
                  <td className="muted">{fmtDate(v.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {neu && <NeuerVorgang onClose={() => setNeu(false)} />}
    </>
  );
}
