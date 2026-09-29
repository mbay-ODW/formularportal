export type FieldType =
  | "text" | "textarea" | "number" | "date" | "email" | "tel" | "select" | "radio"
  | "checks" | "yesno" | "check" | "table" | "signature" | "info";

export interface Cond { field: string; equals?: unknown; in?: unknown[]; contains?: string }

export interface Column { key: string; label: string; type?: string; options?: string[]; unit?: string }

export interface Field {
  key: string;
  type: FieldType;
  label: string;
  required?: boolean;
  options?: string[];
  hint?: string;
  unit?: string;
  width?: "full" | "half" | "third" | "two-thirds" | "quarter";
  show_if?: Cond;
  columns?: Column[];
  min_rows?: number;
  default?: unknown;
  text?: string;
}

export interface Section { title: string; intro?: string; show_if?: Cond; fields: Field[] }

export interface FormDef {
  key: string; nr: number; title: string; short: string;
  audience: "kunde" | "berater" | "fachunternehmen";
  category: string; description: string; version: string;
  sections: Section[];
}

export type Data = Record<string, unknown>;

export interface Missing { key: string; label: string; abschnitt: string }

export interface Branding {
  firma: string; inhaber: string; zusatz: string; strasse: string; plz_ort: string;
  telefon: string; email: string; website: string; farbe_primaer: string;
  farbe_akzent: string; farbe_text: string; portal_begruessung: string; fusszeile: string;
  logo_url: string;
}

export interface CatalogEntry {
  key: string; nr: number; title: string; short: string; audience: string;
  audience_label: string; category: string; description: string; version: string;
  anzahl_felder: number;
}

export interface FormularSummary {
  id: number; vorgang_id: number; form_key: string; status: string; freigegeben: boolean;
  created_at: string; updated_at: string; submitted_at: string | null;
  expires_at: string | null; abgelaufen: boolean; hero_document_id: string | null;
  title: string; nr: number; audience: string; link: string;
  pflicht_offen?: number; pflicht_gesamt?: number;
}

export interface Vorgang {
  id: number; titel: string; kunde_name: string; kunde_email: string; token: string;
  hero_project_id: number | null; hero_ref: string; hero_contact_id: number | null;
  stammdaten: Data; notiz: string; archiviert: boolean; created_at: string; updated_at: string;
  kunde: string; objekt: string; portal_link?: string; formulare?: FormularSummary[];
  anzahl_formulare?: number; anzahl_eingereicht?: number; anzahl_geprueft?: number;
}

export interface FormularView extends FormularSummary {
  form: FormDef; data: Data; locked: boolean; fehlend: Missing[];
  vorgang: { id: number; titel: string; kunde: string; objekt: string;
             hero_project_id: number | null; hero_ref: string };
}

export interface PublicForm {
  token: string; status: string; locked: boolean; form: FormDef; data: Data;
  fehlend: Missing[]; submitted_at: string | null; portal_token: string | null;
  kunde: string; objekt: string; branding: Branding;
}

export interface HeroProject {
  project_id: number; hero_ref: string; name: string; measure: string; status: string;
  kunde: string; kunde_email: string; contact_id: number | null; adresse: string;
}

export interface Me {
  user: string; hero: boolean; smtp: boolean; ntfy: boolean; hero_auto_upload: boolean;
  public_base_url: string;
}

export interface Ereignis { id: number; ts: string; akteur: string; aktion: string; details: string }
