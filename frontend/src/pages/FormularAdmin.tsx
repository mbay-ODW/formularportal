import { useEffect, useState } from "react";
import { api, ApiError, STATUS_LABEL } from "../api";
import FormRenderer from "../components/FormRenderer";
import { copy, SAVE_LABEL, useAutosave } from "../hooks";
import { linkProps } from "../router";
import type { Data, FormularView, Me } from "../types";

export default function FormularAdmin({ id }: { id: number }) {
  const [fv, setFv] = useState<FormularView | null>(null);
  const [data, setData] = useState<Data>({});
  const [me, setMe] = useState<Me | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [showMissing, setShowMissing] = useState(false);

  useEffect(() => {
    api.formular(id).then((r) => { setFv(r); setData(r.data); }).catch((e) => setErr(e.message));
    api.me().then(setMe).catch(() => undefined);
  }, [id]);

  const auto = useAutosave(async () => {
    const r = await api.formularSpeichern(id, data);
    setFv((old) => (old ? { ...old, fehlend: r.fehlend, status: r.status } : r));
  });

  const change = (k: string, v: unknown) => { setData((d) => ({ ...d, [k]: v })); auto.mark(); };

  const act = async (fn: () => Promise<FormularView | unknown>, ok: string) => {
    setErr(""); setMsg("");
    try {
      await auto.flush();
      const r = await fn();
      if (r && typeof r === "object" && "form" in (r as FormularView)) {
        setFv(r as FormularView);
        setData((r as FormularView).data);
      }
      setMsg(ok);
    } catch (e) {
      const ae = e as ApiError;
      if (ae.fehlend) { setShowMissing(true); setFv((o) => o && { ...o, fehlend: ae.fehlend! }); }
      setErr(ae.message);
    }
  };

  if (err && !fv) return <div className="card"><p className="error">{err}</p></div>;
  if (!fv) return <p>Lädt …</p>;

  return (
    <>
      <a className="back" {...linkProps(`/vorgang/${fv.vorgang.id}`)}>← {fv.vorgang.titel}</a>
      <div className="vorgang-head sticky">
        <div>
          <h2>{fv.form.title}</h2>
          <p className="muted">{[fv.vorgang.kunde, fv.vorgang.objekt].filter(Boolean).join(" · ")}
            {" · "}<span className={`badge ${fv.status}`}>{STATUS_LABEL[fv.status]}</span>
            {fv.fehlend.length > 0 && <> · <button className="link" onClick={() =>
              setShowMissing((s) => !s)}>{fv.fehlend.length} Pflichtangaben offen</button></>}
          </p>
        </div>
        <div className="head-actions">
          <span className={`save-state ${auto.state}`}>{SAVE_LABEL[auto.state]}</span>
          <button className="ghost small" onClick={() => copy(fv.link).then(() =>
            setMsg("Formular-Link kopiert"))}>Link kopieren</button>
          <a className="button ghost small" href={`/api/formulare/${id}/pdf`} target="_blank"
            rel="noreferrer" onClick={() => auto.flush()}>PDF</a>
          {me?.hero && fv.vorgang.hero_project_id && (
            <button className="ghost small" onClick={() => act(() => api.formularHeroUpload(id),
              "PDF in HERO abgelegt")}>→ HERO</button>
          )}
          {fv.status === "eingereicht" ? (
            <button className="primary auto" onClick={() => act(() => api.formularStatus(id,
              "geprueft"), "Als geprüft markiert")}>Als geprüft markieren</button>
          ) : fv.status !== "geprueft" ? (
            <button className="primary auto" onClick={() => act(() => api.formularEinreichen(id),
              "Formular abgeschlossen")}>Abschließen</button>
          ) : (
            <button className="ghost small" onClick={() => act(() => api.formularStatus(id,
              "in_bearbeitung"), "Für Kunden wieder geöffnet")}>Wieder öffnen</button>
          )}
        </div>
      </div>
      {msg && <p className="ok-note">{msg}</p>}
      {err && <p className="error">{err}</p>}
      {showMissing && fv.fehlend.length > 0 && (
        <div className="card warn">
          <b>Offene Pflichtangaben:</b>{" "}
          {fv.fehlend.map((m) => (
            <button key={m.key} className="link" onClick={() => document.getElementById(
              `f-${m.key}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}>
              {m.label}</button>
          ))}
        </div>
      )}
      <div className="card">
        <FormRenderer form={fv.form} data={data} onChange={change} missing={fv.fehlend}
          showMissing={showMissing} />
      </div>
    </>
  );
}
