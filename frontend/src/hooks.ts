import { useCallback, useEffect, useRef, useState } from "react";
import type { Branding } from "./types";

export type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";

/** Debounced Autospeichern: `mark()` nach jeder Änderung, speichert nach `delay` ms Ruhe. */
export function useAutosave(save: () => Promise<void>, delay = 1200) {
  const [state, setState] = useState<SaveState>("idle");
  const timer = useRef<number>();
  const saveRef = useRef(save);
  saveRef.current = save;

  const flush = useCallback(async () => {
    window.clearTimeout(timer.current);
    setState("saving");
    try {
      await saveRef.current();
      setState("saved");
    } catch {
      setState("error");
    }
  }, []);

  const mark = useCallback(() => {
    setState("dirty");
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(flush, delay);
  }, [delay, flush]);

  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (state === "dirty" || state === "saving") e.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [state]);

  useEffect(() => () => window.clearTimeout(timer.current), []);
  return { state, mark, flush };
}

export const SAVE_LABEL: Record<SaveState, string> = {
  idle: "",
  dirty: "Ungespeicherte Änderungen …",
  saving: "Speichert …",
  saved: "Automatisch gespeichert",
  error: "Speichern fehlgeschlagen – Verbindung prüfen",
};

export function applyBranding(b?: Partial<Branding> | null) {
  if (!b) return;
  const root = document.documentElement.style;
  if (b.farbe_primaer) root.setProperty("--primary", b.farbe_primaer);
  if (b.farbe_akzent) root.setProperty("--accent", b.farbe_akzent);
  if (b.farbe_text) root.setProperty("--ink", b.farbe_text);
}

export async function copy(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    window.prompt("Link kopieren:", text);
    return false;
  }
}
