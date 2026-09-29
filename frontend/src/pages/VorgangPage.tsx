import { useCallback, useEffect, useState } from "react";
import { api, ApiError, fmtDate, STATUS_LABEL } from "../api";
import { copy } from "../hooks";
import { linkProps, navigate } from "../router";
import type { CatalogEntry, Ereignis, FormularSummary, Me, Vorgang } from "../types";

const SD_LABELS: [string, string][] = [
  ["eig_vorname", "Vorname"], ["eig_nachname", "Nachname"], ["eig_firma", "Firma"],
  ["eig_strasse", "Straße"], ["eig_hausnr", "Nr."], ["eig_plz", "PLZ"], ["eig_ort", "Ort"],
  ["eig_email", "E-Mail"], ["eig_telefon", "Telefon"], ["eig_mobil", "Mobil"],
  ["obj_strasse", "Objekt Straße"], ["obj_hausnr", "Objekt Nr."], ["obj_plz", "Objekt PLZ"],
  ["obj_ort", "Objekt Ort"], ["obj_baujahr", "Baujahr"], ["obj_anzahl_we", "Wohneinheiten"],
  ["fu_firma", "Fachunternehmen"],
];

export default function VorgangPage({ id }: { id: number }) {
  const [v, setV] = useState<Vorgang | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [catalog, setCatalog] = useState<CatalogEntry[]>([]);
  const [events, setEvents] = useState<Ereignis[]>([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [add, setAdd] = useState("");
  const [notiz, setNotiz] = useState("");

  const load = useCallback(async () => {
    const r = await api.vorgang(id);
    setV(r);
    setNotiz(r.notiz);
    setEvents(await api.vorgangEreignisse(id));
  }, [id]);

  useEffect(() => {
    load().catch((e) => setErr(e.message));
    api.me().then(setMe).catch(() => undefined);
    api.catalog().then((r) => setCatalog(r.formulare));
  }, [load]);

  const run = async (fn: () => Promise<unknown>, ok?: string) => {
    setErr(""); setMsg("");
    try {
      await fn();
      if (ok) setMsg(ok);
      await load();
    } catch (e) { setErr((e as ApiError).message); }
  };

  if (err && !v) return <div className="card"><p className="error">{err}</p></div>;
  if (!v) return <p>Lädt …</p>;
  const vorhanden = new Set(v.formulare?.map((f) => f.form_key));

  const formRow = (f: FormularSummary) => (
    <tr key={f.id}>
      <td><span className="nr">{f.nr}</span></td>
      <td>
        <a {...linkProps(`/formular/${f.id}`)}><b>{f.title}</b></a>
        <div className="muted small">
          {f.audience === "berater" ? "Berater" : f.audience === "fachunternehmen"
            ? "Fachunternehmen" : "Kunde"}
          {f.pflicht_gesamt ? ` · Pflichtangaben ${f.pflicht_gesamt - (f.pflicht_offen ?? 0)}/`
            + `${f.pflicht_gesamt}` : ""}
          {f.abgelaufen ? " · Link abgelaufen" : ""}
          {f.hero_document_id ? ` · in HERO (${f.hero_document_id})` : ""}
        </div>
      </td>
      <td>
        <select value={f.status} onChange={(e) => run(() => api.formularStatus(f.id,
          e.target.value))} className={`badge-select ${f.status}`}>
          {Object.entries(STATUS_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
        </select>
        {f.submitted_at && <div className="muted small">{fmtDate(f.submitted_at)}</div>}
      </td>
      <td>
        <label className="inline-check" title="Im Kundenportal sichtbar">
          <input type="checkbox" checked={f.freigegeben}
            onChange={(e) => run(() => api.formularFreigabe(f.id, e.target.checked))} /> Portal
        </label>
      </td>
      <td className="actions">
        <button className="ghost small" onClick={() => navigate(`/formular/${f.id}`)}>
          Bearbeiten</button>
        <a className="button ghost small" href={`/api/formulare/${f.id}/pdf`} target="_blank"
          rel="noreferrer">PDF</a>
        <button className="ghost small" onClick={() => copy(f.link).then(() =>
          setMsg(`Link für „${f.title}“ kopiert`))}>Link</button>
        {me?.smtp && <button className="ghost small" onClick={() => {
          const to = window.prompt("Link per Mail senden an (leer = hinterlegte Adresse):", "");
          if (to !== null) run(() => api.formularLinkSenden(f.id, to), "Link gesendet");
        }}>Mail</button>}
        {me?.hero && v.hero_project_id && (
          <button className="ghost small" onClick={() => run(() => api.formularHeroUpload(f.id),
            "PDF in HERO abgelegt")}>→ HERO</button>
        )}
        <button className="link danger" title="Entfernen" onClick={() => {
          if (window.confirm(`„${f.title}“ aus dem Vorgang entfernen? Eingaben gehen verloren.`))
            run(() => api.formularLoeschen(f.id));
        }}>×</button>
      </td>
    </tr>
  );

  return (
    <>
      <a className="back" {...linkProps("/")}>← Vorgänge</a>
      <div className="vorgang-head">
        <div>
          <h2>{v.titel}</h2>
          <p className="muted">{[v.kunde, v.objekt].filter(Boolean).join(" · ") || "–"}</p>
        </div>
        <div className="head-actions">
          <button className="ghost small" onClick={() => {
            const t = window.prompt("Titel", v.titel);
            if (t) run(() => api.vorgangPatch(v.id, { titel: t }));
          }}>Umbenennen</button>
          <button className="ghost small" onClick={() => run(() => api.vorgangPatch(v.id,
            { archiviert: !v.archiviert }), v.archiviert ? "Wiederhergestellt" : "Archiviert")}>
            {v.archiviert ? "Aus Archiv holen" : "Archivieren"}</button>
          <button className="link danger" onClick={() => {
            if (window.confirm("Vorgang mit allen Formularen endgültig löschen?"))
              api.vorgangLoeschen(v.id).then(() => navigate("/"));
          }}>Löschen</button>
        </div>
      </div>

      {msg && <p className="ok-note">{msg}</p>}
      {err && <p className="error">{err}</p>}

      <div className="grid-2">
        <div className="card">
          <h3>Kundenportal</h3>
          <p className="muted">Ein Link für alle freigegebenen Formulare dieses Vorgangs.</p>
          <div className="linkbox">
            <input readOnly value={v.portal_link} onFocus={(e) => e.target.select()} />
            <button className="ghost small" onClick={() => copy(v.portal_link!).then(() =>
              setMsg("Portal-Link kopiert"))}>Kopieren</button>
          </div>
          <div className="row-actions">
            <a className="button ghost small" href={v.portal_link} target="_blank"
              rel="noreferrer">Als Kunde ansehen</a>
            {me?.smtp && <button className="ghost small" onClick={() => {
              const to = window.prompt("An (leer = " + (v.kunde_email || "hinterlegte Adresse") +
                "):", "");
              if (to !== null) run(() => api.vorgangLinkSenden(v.id, to), "Link gesendet");
            }}>Per Mail senden</button>}
            <button className="link" onClick={() => {
              if (window.confirm("Neuen Portal-Link erzeugen? Der alte Link funktioniert danach "
                + "nicht mehr.")) run(() => api.vorgangNeuerLink(v.id), "Neuer Link erzeugt");
            }}>Link erneuern</button>
          </div>
        </div>
        <div className="card">
          <h3>HERO</h3>
          {v.hero_project_id ? (
            <>
              <p>Verknüpft mit <b>{v.hero_ref || v.hero_project_id}</b></p>
              <div className="row-actions">
                <button className="ghost small" disabled={!me?.hero}
                  onClick={() => run(async () => {
                    const r = await api.vorgangHeroSync(v.id);
                    setMsg(r.uebernommen.length ? `Aus HERO übernommen: ${r.uebernommen.length}`
                      + " Felder" : "Keine neuen Daten in HERO");
                  })}>Leere Felder aus HERO füllen</button>
                <button className="link" disabled={!me?.hero} onClick={() => {
                  if (window.confirm("Stammdaten mit HERO überschreiben?"))
                    run(() => api.vorgangHeroSync(v.id, true), "Stammdaten aus HERO aktualisiert");
                }}>alles überschreiben</button>
              </div>
            </>
          ) : (
            <p className="muted">Nicht mit HERO verknüpft. Beim Anlegen „Aus HERO übernehmen“
              wählen oder die Projekt-ID hier setzen:{" "}
              <button className="link" onClick={() => {
                const pid = window.prompt("HERO-Projekt-ID (numerisch)");
                if (pid && /^\d+$/.test(pid)) run(() => api.vorgangPatch(v.id,
                  { hero_project_id: Number(pid) }), "Verknüpft");
              }}>verknüpfen</button></p>
          )}
        </div>
      </div>

      <div className="card flush">
        <div className="card-head">
          <h3>Formulare</h3>
          <div className="add-form">
            <select value={add} onChange={(e) => setAdd(e.target.value)}>
              <option value="">Formular hinzufügen …</option>
              {catalog.filter((c) => !vorhanden.has(c.key)).map((c) =>
                <option key={c.key} value={c.key}>{c.nr}. {c.title}</option>)}
            </select>
            <button className="ghost small" disabled={!add} onClick={() => run(async () => {
              await api.vorgangFormulare(v.id, [add]); setAdd("");
            })}>Hinzufügen</button>
          </div>
        </div>
        <table className="list forms">
          <tbody>{v.formulare?.map(formRow)}</tbody>
        </table>
      </div>

      <div className="grid-2">
        <div className="card">
          <h3>Stammdaten (vorgangsweit)</h3>
          <dl className="sd">
            {SD_LABELS.filter(([k]) => v.stammdaten[k]).map(([k, l]) => (
              <div key={k}><dt>{l}</dt><dd>{String(v.stammdaten[k])}</dd></div>
            ))}
          </dl>
          <p className="muted small">Werden in allen Formularen des Vorgangs vorbelegt und bei
            jeder Eingabe aktualisiert.</p>
        </div>
        <div className="card">
          <h3>Notiz</h3>
          <textarea rows={4} value={notiz} onChange={(e) => setNotiz(e.target.value)}
            onBlur={() => notiz !== v.notiz && run(() => api.vorgangPatch(v.id, { notiz }))} />
          <h3>Verlauf</h3>
          <ul className="events">
            {events.slice(0, 15).map((e) => (
              <li key={e.id}><span className="muted">{fmtDate(e.ts)}</span> {e.aktion.replace(/_/g,
                " ")} <span className="muted">{e.details} · {e.akteur}</span></li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}
