import { useEffect, useState } from "react";
import { api } from "../api";
import { applyBranding } from "../hooks";
import type { Branding } from "../types";

// Firmenkopf für das Kundenportal (Logo, Name, Kontakt aus den Einstellungen).
export default function BrandHeader({ branding }: { branding?: Branding }) {
  const [b, setB] = useState<Branding | undefined>(branding);
  useEffect(() => {
    if (branding) { setB(branding); return; }
    api.branding().then((r) => { setB(r); applyBranding(r); }).catch(() => undefined);
  }, [branding]);
  if (!b) return <header className="brand" />;
  return (
    <header className="brand">
      <div className="brand-inner">
        <img src={b.logo_url} alt="" className="brand-logo" />
        <div>
          <div className="brand-name">{b.firma}</div>
          <div className="brand-sub">
            {[b.inhaber, b.zusatz].filter(Boolean).join(" · ")}
          </div>
        </div>
        <div className="brand-contact">
          {b.telefon && <a href={`tel:${b.telefon}`}>{b.telefon}</a>}
          {b.email && <a href={`mailto:${b.email}`}>{b.email}</a>}
          {b.website && <a href={b.website.startsWith("http") ? b.website : `https://${b.website}`}
            target="_blank" rel="noreferrer">{b.website.replace(/^https?:\/\//, "")}</a>}
        </div>
      </div>
    </header>
  );
}
