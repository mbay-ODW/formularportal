import { useEffect, useState } from "react";
import { api } from "../api";
import { linkProps } from "../router";
import type { Me } from "../types";

export function AdminLayout({ path, children }: { path: string; children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  useEffect(() => { api.me().then(setMe).catch(() => undefined); }, []);
  const nav = [
    { to: "/", label: "Vorgänge", active: path === "/" || path.startsWith("/vorgang") ||
        path.startsWith("/formular/") },
    { to: "/katalog", label: "Formulare", active: path.startsWith("/katalog") },
    { to: "/einstellungen", label: "Einstellungen", active: path.startsWith("/einstellungen") },
  ];
  return (
    <div className="admin">
      <header className="app">
        <img src="/api/public/logo" alt="" className="brand-logo" />
        <h1>Formularportal</h1>
        <nav>
          {nav.map((n) => (
            <a key={n.to} className={n.active ? "active" : ""} {...linkProps(n.to)}>{n.label}</a>
          ))}
        </nav>
        <span className="sub">
          {me && <>
            <span className={me.hero ? "dot on" : "dot"} title="HERO" /> HERO
            <span className={me.smtp ? "dot on" : "dot"} title="Mail" /> Mail
            {me.user && <span className="user">{me.user}</span>}
          </>}
        </span>
      </header>
      <main className="wide">{children}</main>
    </div>
  );
}
