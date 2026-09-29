import { useEffect, useRef } from "react";

interface Props {
  value: string | null;
  onChange: (dataUrl: string | null) => void;
  disabled?: boolean;
}

// Unterschriftenfeld (Maus, Finger, Stift) – liefert ein PNG als Data-URL.
export default function SignaturePad({ value, onChange, disabled }: Props) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const last = useRef<{ x: number; y: number } | null>(null);
  const dirty = useRef(false);

  useEffect(() => {
    const c = canvas.current;
    if (!c) return;
    const ratio = window.devicePixelRatio || 1;
    const w = c.clientWidth, h = c.clientHeight;
    c.width = w * ratio;
    c.height = h * ratio;
    const ctx = c.getContext("2d")!;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, w, h);
    if (value) {
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, w, h);
      img.src = value;
    }
    dirty.current = false;
    // nur beim Laden / Zurücksetzen neu zeichnen
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value === null]);

  const pos = (e: React.PointerEvent) => {
    const r = canvas.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top };
  };

  const down = (e: React.PointerEvent) => {
    if (disabled) return;
    canvas.current!.setPointerCapture(e.pointerId);
    drawing.current = true;
    last.current = pos(e);
  };

  const move = (e: React.PointerEvent) => {
    if (!drawing.current || disabled) return;
    const ctx = canvas.current!.getContext("2d")!;
    const p = pos(e);
    ctx.strokeStyle = "#0e2a40";
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(last.current!.x, last.current!.y);
    ctx.lineTo(p.x, p.y);
    ctx.stroke();
    last.current = p;
    dirty.current = true;
  };

  const up = () => {
    if (!drawing.current) return;
    drawing.current = false;
    if (dirty.current) onChange(canvas.current!.toDataURL("image/png"));
  };

  return (
    <div className="sig">
      <canvas ref={canvas} className={disabled ? "sig-canvas disabled" : "sig-canvas"}
        onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerLeave={up} />
      {!disabled && (
        <div className="sig-actions">
          <span className="muted">{value ? "Unterschrift erfasst" : "Hier unterschreiben"}</span>
          {value && <button type="button" className="link" onClick={() => onChange(null)}>
            Löschen</button>}
        </div>
      )}
    </div>
  );
}
