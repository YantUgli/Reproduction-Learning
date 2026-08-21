"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Hitung mundur timebox_seconds (§7.6 — bagian desain integritas, bukan hiasan).
 * Saat habis memanggil onExpire SEKALI (parent lalu auto-submit).
 */
export default function Timebox({
  seconds,
  running,
  onExpire,
}: {
  seconds: number;
  running: boolean;
  onExpire: () => void;
}) {
  const [left, setLeft] = useState(seconds);
  const fired = useRef(false);
  // Simpan onExpire di ref supaya re-render parent (mis. mengetik) tak mereset timer.
  const onExpireRef = useRef(onExpire);
  onExpireRef.current = onExpire;

  useEffect(() => {
    setLeft(seconds);
    fired.current = false;
  }, [seconds]);

  useEffect(() => {
    if (!running) return;
    if (left <= 0) {
      if (!fired.current) {
        fired.current = true;
        onExpireRef.current();
      }
      return;
    }
    const t = setTimeout(() => setLeft((l) => l - 1), 1000);
    return () => clearTimeout(t);
  }, [left, running]);

  const m = Math.floor(Math.max(left, 0) / 60);
  const s = Math.max(left, 0) % 60;
  const danger = left <= 30;
  return (
    <span
      style={{
        fontVariantNumeric: "tabular-nums",
        fontWeight: 600,
        color: danger ? "#cf222e" : "#1f2328",
        background: danger ? "#ffebe9" : "#eaeef2",
        padding: "2px 8px",
        borderRadius: 6,
      }}
      title="Timebox — batas waktu berpikir"
    >
      ⏱ {m}:{String(s).padStart(2, "0")}
    </span>
  );
}
