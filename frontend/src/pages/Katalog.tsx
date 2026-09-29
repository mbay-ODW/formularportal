import { useEffect, useState } from "react";
import { api } from "../api";
import FormRenderer from "../components/FormRenderer";
import { linkProps } from "../router";
import type { CatalogEntry, Data, FormDef } from "../types";

export default function Katalog({ formKey }: { formKey?: string }) {
  const [items, setItems] = useState<CatalogEntry[]>([]);
  const [def, setDef] = useState<FormDef | null>(null);
  const [data, setData] = useState<Data>({});

  useEffect(() => { api.catalog().then((r) => setItems(r.formulare)); }, []);
  useEffect(() => {
    setDef(null);
    setData({});
    if (formKey) api.formDef(formKey).then(setDef);
  }, [formKey]);

  if (formKey) {
    return (
      <>
        <a className="back" {...linkProps("/katalog")}>← Alle Formulare</a>
        {def && (
          <>
            <div className="vorgang-head">
              <div><h2>{def.title}</h2><p className="muted">{def.description}</p></div>
              <div className="head-actions">
                <a className="button ghost small" href={`/api/forms/${def.key}/pdf`}
                  target="_blank" rel="noreferrer">Druckvorlage (PDF)</a>
              </div>
            </div>
            <p className="muted">Vorschau – Eingaben hier werden nicht gespeichert.</p>
            <div className="card">
              <FormRenderer form={def} data={data}
                onChange={(k, v) => setData((d) => ({ ...d, [k]: v }))} />
            </div>
          </>
        )}
      </>
    );
  }

  const groups = [...new Set(items.map((i) => i.category))];
  return (
    <>
      <p className="muted">Zwölf Formulare für den gesamten Beratungs- und Förderprozess –
        online ausfüllbar und als gebrandete Druckvorlage.</p>
      {groups.map((g) => (
        <div key={g} className="card">
          <h3>{g}</h3>
          <div className="catalog">
            {items.filter((i) => i.category === g).map((i) => (
              <div key={i.key} className="cat-item">
                <span className="nr">{i.nr}</span>
                <div>
                  <a {...linkProps(`/katalog/${i.key}`)}><b>{i.title}</b></a>
                  <p className="muted small">{i.description}</p>
                  <p className="small">
                    <span className="pill">{i.audience_label}</span>{" "}
                    <span className="muted">{i.anzahl_felder} Felder · Stand {i.version}</span>
                    {" · "}<a href={`/api/forms/${i.key}/pdf`} target="_blank"
                      rel="noreferrer">PDF-Vorlage</a>
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </>
  );
}
