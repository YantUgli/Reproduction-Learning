"use client";

import { useState } from "react";
import type { Probe } from "../../lib/api";

/**
 * Render comprehension probe DETERMINISTIK (predict_output | spot_bug | trace).
 * Jawaban benar TIDAK ada di klien — pengecekan dilakukan server.
 */
export default function ProbeCard({
  probe,
  disabled,
  onSubmit,
  outcome,
}: {
  probe: Probe;
  disabled: boolean;
  onSubmit: (answer: string) => void;
  outcome?: "correct" | "incorrect" | null;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: 8,
        padding: "1rem 1.25rem",
        background: "#f6f8fa",
      }}
    >
      <div style={{ fontSize: 12, textTransform: "uppercase", color: "#57606a" }}>
        Comprehension probe · {probe.type}
      </div>
      <p style={{ fontWeight: 600, marginTop: 8 }}>{probe.question}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {probe.options.map((opt) => (
          <label
            key={opt}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 10px",
              border: "1px solid #d0d7de",
              borderRadius: 6,
              background: selected === opt ? "#ddf4ff" : "#fff",
              cursor: disabled ? "default" : "pointer",
            }}
          >
            <input
              type="radio"
              name={`probe-${probe.id}`}
              value={opt}
              checked={selected === opt}
              disabled={disabled}
              onChange={() => setSelected(opt)}
            />
            <code>{opt}</code>
          </label>
        ))}
      </div>
      <button
        style={{ marginTop: 12 }}
        disabled={disabled || selected === null}
        onClick={() => selected && onSubmit(selected)}
      >
        Kirim jawaban probe
      </button>
      {outcome === "correct" && (
        <p style={{ color: "#1a7f37", fontWeight: 600 }}>Probe benar ✓</p>
      )}
      {outcome === "incorrect" && (
        <p style={{ color: "#cf222e", fontWeight: 600 }}>Probe salah — coba lagi.</p>
      )}
    </div>
  );
}
