import { useEffect, useMemo, useState } from "react";
import { api, ApiError, fmtDate } from "../api";
import FormRenderer, { condOk } from "../components/FormRenderer";
import { applyBranding, SAVE_LABEL, useAutosave } from "../hooks";
import { linkProps } from "../router";
import type { Data, Missing, PublicForm as PF } from "../types";
import BrandHeader from "./BrandHeader";

const BACKUP = (t: string) => `fp-entwurf-${t}`;

export default function PublicForm({ token }: { token: string }) {
  const [pf, setPf] = useState<PF | null>(null);
  const [data, setData] = useState<Data>({});
  const [missing, setMissing] = useState<Missing[]>([]);
  const [showMissing, setShowMissing] = useState(false);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.publicForm(token).then((r) => {
      setPf(r);
      applyBranding(r.branding);
      let d = r.data;
      if (!r.locked) {
        try {
          const b = localStorage.getItem(BACKUP(token));
          if (b) d = { ...d, ...JSON.parse(b) };
        } catch { /* kein lokaler Entwurf */ }
      }
      setData(d);
      setMissing(r.fehlend);
    }).catch((e: ApiError) => setErr(e.message));
  }, [token]);

  const auto = useAutosave(async () => {
    const r = await api.publicSave(token, data);
    setMissing(r.fehlend);
    try { localStorage.removeItem(BACKUP(token)); } catch { /* egal */ }
  });

  const change = (k: string, v: unknown) => {
    setData((d) => {
      const next = { ...d, [k]: v };
      try { localStorage.setItem(BACKUP(token), JSON.stringify(next)); } catch { /* voll */ }
      return next;
    });
    auto.mark();
  };

  const progress = useMemo(() => {
    if (!pf) return { done: 0, total: 0 };
    let total = 0, done = 0;
    for (const s of pf.form.sections) {
      if (!condOk(s.show_if, data)) continue;
      for (const f of s.fields) {
        if (!f.required || !condOk(f.show_if, data)) continue;
        total++;
        const v = data[f.key];
        const empty = v === null || v === undefined || v === "" || v === false ||
          (Array.isArray(v) && v.length === 0);
        if (!empty) done++;
      }
    }
    return { done, total };
  }, [pf, data]);

  const submit = async () => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.publicSubmit(token, data);
      try { localStorage.removeItem(BACKUP(token)); } catch { /* egal */ }
      setPf(r);
      setData(r.data);
      window.scrollTo(0, 0);
    } catch (e) {
      const ae = e as ApiError;
      if (ae.fehlend) {
        setMissing(ae.fehlend);
        setShowMissing(true);
        const first = ae.fehlend[0];
        if (first) document.getElementById(`f-${first.key}`)?.scrollIntoView({
          behavior: "smooth", block: "center" });
      }
      setErr(ae.message);
    } finally {
      setBusy(false);
    }
  };

  if (err && !pf) {
    return (
      <div className="public">
        <BrandHeader />
        <main className="narrow"><div className="card"><h2>Formular nicht verfügbar</h2>
          <p>{err}</p></div></main>
      </div>
    );
  }
  if (!pf) return <div className="public"><main className="narrow"><p>Lädt …</p></main></div>;

  return (
    <div className="public">
      <BrandHeader branding={pf.branding} />
      <main className="narrow">
        {pf.portal_token && (
          <a className="back" {...linkProps(`/p/${pf.portal_token}`)}>← Alle Formulare</a>
        )}
        <div className="card head-card">
          <h1>{pf.form.title}</h1>
          <p className="muted">{pf.form.description}</p>
          {(pf.kunde || pf.objekt) && (
            <p className="meta">{[pf.kunde, pf.objekt].filter(Boolean).join(" · ")}</p>
          )}
          {!pf.locked && progress.total > 0 && (
            <div className="progress" title="Pflichtangaben">
              <div style={{ width: `${(progress.done / progress.total) * 100}%` }} />
              <span>{progress.done} von {progress.total} Pflichtangaben</span>
            </div>
          )}
        </div>

        {pf.locked ? (
          <div className="card success">
            <h2>Vielen Dank!</h2>
            <p>Das Formular wurde am {fmtDate(pf.submitted_at)} übermittelt. Ihre Angaben
              können nicht mehr geändert werden – bei Korrekturen melden Sie sich bitte bei uns.</p>
            <a className="button" href={`/api/public/f/${token}/pdf`} target="_blank"
              rel="noreferrer">PDF herunterladen</a>
          </div>
        ) : null}

        <div className="card">
          <FormRenderer form={pf.form} data={data} onChange={change} readOnly={pf.locked}
            missing={missing} showMissing={showMissing} />
        </div>

        {!pf.locked && (
          <div className="submit-bar">
            <span className={`save-state ${auto.state}`}>{SAVE_LABEL[auto.state]}</span>
            {err && <span className="error">{err}</span>}
            {showMissing && missing.length > 0 && (
              <span className="error">Es fehlen noch {missing.length} Pflichtangaben.</span>
            )}
            <button className="primary" disabled={busy} onClick={submit}>
              {busy ? "Wird übermittelt …" : "Verbindlich absenden"}</button>
          </div>
        )}
      </main>
    </div>
  );
}
