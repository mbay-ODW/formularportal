import type { Cond, Data, Field, FormDef, Missing } from "../types";
import SignaturePad from "./SignaturePad";

export function condOk(c: Cond | undefined, data: Data): boolean {
  if (!c) return true;
  const v = data[c.field];
  if ("equals" in c) return v === c.equals;
  if (c.in) return c.in.includes(v);
  if (c.contains !== undefined) return Array.isArray(v) && v.includes(c.contains);
  return Boolean(v);
}

interface Props {
  form: FormDef;
  data: Data;
  onChange: (key: string, value: unknown) => void;
  readOnly?: boolean;
  missing?: Missing[];
  showMissing?: boolean;
}

type Row = Record<string, string | number>;

function TableField({ f, value, onChange, readOnly }: {
  f: Field; value: unknown; onChange: (v: Row[]) => void; readOnly?: boolean;
}) {
  const cols = f.columns ?? [];
  const rows: Row[] = Array.isArray(value) && value.length ? (value as Row[])
    : Array.from({ length: f.min_rows ?? 1 }, () => ({}));
  const set = (i: number, k: string, v: string) => {
    const next = rows.map((r, j) => (j === i ? { ...r, [k]: v } : r));
    onChange(next);
  };
  return (
    <div className="table-wrap">
      <table className="ftable">
        <thead>
          <tr>
            {cols.map((c) => <th key={c.key}>{c.label}{c.unit ? ` [${c.unit}]` : ""}</th>)}
            {!readOnly && <th />}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c.key} data-label={c.label}>
                  {c.type === "select" && c.options ? (
                    <select disabled={readOnly} value={String(r[c.key] ?? "")}
                      onChange={(e) => set(i, c.key, e.target.value)}>
                      <option value="">–</option>
                      {c.options.map((o) => <option key={o}>{o}</option>)}
                    </select>
                  ) : (
                    <input type={c.type === "number" ? "number" : "text"} step="any"
                      inputMode={c.type === "number" ? "decimal" : undefined}
                      readOnly={readOnly} value={String(r[c.key] ?? "")}
                      onChange={(e) => set(i, c.key, e.target.value)} />
                  )}
                </td>
              ))}
              {!readOnly && (
                <td className="row-del">
                  <button type="button" className="link" title="Zeile entfernen"
                    onClick={() => onChange(rows.filter((_, j) => j !== i))}>×</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {!readOnly && (
        <button type="button" className="ghost small"
          onClick={() => onChange([...rows, {}])}>+ Zeile</button>
      )}
    </div>
  );
}

function Input({ f, value, onChange, readOnly }: {
  f: Field; value: unknown; onChange: (v: unknown) => void; readOnly?: boolean;
}) {
  const str = value === null || value === undefined ? "" : String(value);
  switch (f.type) {
    case "textarea":
      return <textarea rows={3} readOnly={readOnly} value={str}
        onChange={(e) => onChange(e.target.value)} />;
    case "number":
      return (
        <div className="with-unit">
          <input type="number" step="any" inputMode="decimal" readOnly={readOnly} value={str}
            onChange={(e) => onChange(e.target.value === "" ? null : e.target.value)} />
          {f.unit && <span className="unit">{f.unit}</span>}
        </div>
      );
    case "date":
      return <input type="date" readOnly={readOnly} value={str.slice(0, 10)}
        onChange={(e) => onChange(e.target.value)} />;
    case "email":
    case "tel":
      return <input type={f.type} readOnly={readOnly} value={str}
        autoComplete={f.type === "email" ? "email" : "tel"}
        onChange={(e) => onChange(e.target.value)} />;
    case "select":
      return (
        <select disabled={readOnly} value={str} onChange={(e) => onChange(e.target.value || null)}>
          <option value="">Bitte wählen …</option>
          {f.options!.map((o) => <option key={o}>{o}</option>)}
        </select>
      );
    case "radio":
    case "yesno": {
      const opts = f.type === "yesno" ? ["ja", "nein"] : f.options!;
      return (
        <div className={f.type === "yesno" ? "choices inline" : "choices"}>
          {opts.map((o) => (
            <label key={o} className={str === o ? "choice on" : "choice"}>
              <input type="radio" disabled={readOnly} checked={str === o}
                onChange={() => onChange(o)} />
              <span>{o}</span>
            </label>
          ))}
        </div>
      );
    }
    case "checks": {
      const arr = Array.isArray(value) ? (value as string[]) : [];
      return (
        <div className="choices">
          {f.options!.map((o) => (
            <label key={o} className={arr.includes(o) ? "choice on" : "choice"}>
              <input type="checkbox" disabled={readOnly} checked={arr.includes(o)}
                onChange={(e) => onChange(e.target.checked ? [...arr, o] : arr.filter((x) => x !== o))} />
              <span>{o}</span>
            </label>
          ))}
        </div>
      );
    }
    case "check":
      return (
        <label className={value === true ? "confirm on" : "confirm"}>
          <input type="checkbox" disabled={readOnly} checked={value === true}
            onChange={(e) => onChange(e.target.checked)} />
          <span>{f.label}{f.required && <b className="req"> *</b>}</span>
        </label>
      );
    case "signature":
      return <SignaturePad value={(value as string) || null} disabled={readOnly}
        onChange={(v) => onChange(v)} />;
    case "table":
      return <TableField f={f} value={value} readOnly={readOnly} onChange={(v) => onChange(v)} />;
    default:
      return <input type="text" readOnly={readOnly} value={str}
        onChange={(e) => onChange(e.target.value)} />;
  }
}

export default function FormRenderer({ form, data, onChange, readOnly, missing, showMissing }:
  Props) {
  const miss = new Set((showMissing ? missing ?? [] : []).map((m) => m.key));
  return (
    <div className="form-render">
      {form.sections.map((s, si) => {
        if (!condOk(s.show_if, data)) return null;
        return (
          <section key={si} className="fsection">
            <h3>{s.title}</h3>
            {s.intro && <p className="intro">{s.intro}</p>}
            <div className="fgrid">
              {s.fields.map((f) => {
                if (!condOk(f.show_if, data)) return null;
                if (f.type === "info") {
                  return <div key={f.key} className="finfo w-full">{f.text}</div>;
                }
                const wide = ["table", "checks", "radio", "textarea", "check", "signature"]
                  .includes(f.type) && !f.width;
                const w = wide ? "full" : f.width ?? "full";
                return (
                  <div key={f.key} id={`f-${f.key}`}
                    className={`field w-${w}${miss.has(f.key) ? " missing" : ""}`}>
                    {f.type !== "check" && (
                      <label className="flabel">
                        {f.label}{f.required && <b className="req"> *</b>}
                      </label>
                    )}
                    <Input f={f} value={data[f.key]} readOnly={readOnly}
                      onChange={(v) => onChange(f.key, v)} />
                    {f.hint && <div className="hint">{f.hint}</div>}
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
