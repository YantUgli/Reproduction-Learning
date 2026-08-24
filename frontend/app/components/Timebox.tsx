"use client";

import { useEffect, useRef, useState } from "react";
import { IconClock } from "./ui/Icon";

/**
 * Hitung mundur timebox_seconds (§7.6 — bagian desain integritas, bukan hiasan).
 * Saat habis memanggil onExpire SEKALI (parent lalu auto-submit).
 *
 * Slot lebar TETAP + tabular-nums: kemunculan/tik timer tak lagi menggeser layout
 * (masalah UX #2 — judul node bergeser saat timer muncul di L0).
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
  const warn = !danger && left <= 120;

  const tone = danger
    ? "bg-danger-bg text-danger"
    : warn
      ? "bg-warning-bg text-warning"
      : "bg-neutral-bg text-fg";

  return (
    <span
      className={`inline-flex w-[84px] items-center justify-center gap-1.5 rounded-md px-2 py-1 text-sm font-semibold tabular-nums ${tone}`}
      title="Timebox — batas waktu berpikir"
    >
      <IconClock size={14} />
      {m}:{String(s).padStart(2, "0")}
    </span>
  );
}
