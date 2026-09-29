import { useEffect, useState } from "react";
import { api, ApiError, STATUS_LABEL } from "../api";
import { applyBranding } from "../hooks";
import { linkProps } from "../router";
import BrandHeader from "./BrandHeader";

type Portal = Awaited<ReturnType<typeof api.portal>>;

export default function PublicPortal({ token }: { token: string }) {
  const [p, setP] = useState<Portal | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.portal(token).then((r) => { setP(r); applyBranding(r.branding); })
      .catch((e: ApiError) => setErr(e.message));
  }, [token]);

  if (err) {
    return (
      <div className="public"><BrandHeader />
        <main className="narrow"><div className="card"><h2>Link ungültig</h2><p>{err}</p></div></main>
      </div>
    );
  }
  if (!p) return <div className="public"><main className="narrow"><p>Lädt …</p></main></div>;
  const offen = p.formulare.filter((f) => f.status === "entwurf" || f.status === "in_bearbeitung");

  return (
    <div className="public">
      <BrandHeader branding={p.branding} />
      <main className="narrow">
        <div className="card head-card">
          <h1>{p.kunde ? `Willkommen, ${p.kunde}` : "Ihre Formulare"}</h1>
          {p.objekt && <p className="meta">Objekt: {p.objekt}</p>}
          <p>{p.branding.portal_begruessung}</p>
          <p className="muted">{offen.length === 0 ? "Alle Formulare sind erledigt – vielen Dank!"
            : `${offen.length} von ${p.formulare.length} Formularen sind noch offen.`}</p>
        </div>
        <div className="portal-list">
          {p.formulare.map((f) => (
            <a key={f.token} className={`portal-item status-${f.status}`}
              {...linkProps(`/f/${f.token}`)}>
              <span className="nr">{f.nr}</span>
              <span className="pi-body">
                <b>{f.title}</b>
                <span className="muted">{f.description}</span>
              </span>
              <span className={`badge ${f.status}`}>{STATUS_LABEL[f.status]}</span>
            </a>
          ))}
        </div>
        <p className="footnote">Ihre Eingaben werden automatisch gespeichert. Sie können jederzeit
          unterbrechen und später über diesen Link weitermachen.</p>
        <div className="card">
          <h3>Lieber auf Papier oder am PC?</h3>
          <p className="muted small">Jedes Formular gibt es auch als beschreibbares PDF – am
            Computer ausfüllen oder ausdrucken und an {p.branding.email || "uns"} zurücksenden.</p>
          <ul className="pdf-list">
            {p.formulare.filter((f) => f.status === "entwurf" || f.status === "in_bearbeitung")
              .map((f) => (
                <li key={f.token}><a href={`/api/public/f/${f.token}/pdf?ausfuellbar=true`}>
                  {f.nr}. {f.title} (PDF)</a></li>
              ))}
          </ul>
        </div>
      </main>
    </div>
  );
}
