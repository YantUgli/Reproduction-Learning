"use client";

import { useState } from "react";
import type { Probe } from "../../lib/api";
import Button from "./ui/Button";
import { IconCheck, IconX } from "./ui/Icon";

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
    <div className="rounded-md border border-border bg-surface-muted p-5">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">
        Comprehension probe · {probe.type}
      </div>
      <p className="mt-2 font-semibold text-fg">{probe.question}</p>
      <div className="mt-3 flex flex-col gap-2">
        {probe.options.map((opt) => {
          const active = selected === opt;
          return (
            <label
              key={opt}
              className={`flex items-center gap-2.5 rounded-md border px-3 py-2 transition-colors ${
                disabled ? "cursor-default" : "cursor-pointer hover:border-accent"
              } ${active ? "border-accent bg-info-bg" : "border-border bg-surface"}`}
            >
              <input
                type="radio"
                name={`probe-${probe.id}`}
                value={opt}
                checked={active}
                disabled={disabled}
                onChange={() => setSelected(opt)}
                className="accent-accent"
              />
              <code className="font-mono text-sm">{opt}</code>
            </label>
          );
        })}
      </div>
      <Button
        variant="primary"
        size="sm"
        className="mt-3"
        disabled={disabled || selected === null}
        onClick={() => selected && onSubmit(selected)}
      >
        Kirim jawaban probe
      </Button>
      {outcome === "correct" && (
        <p className="mt-2 inline-flex items-center gap-1.5 font-semibold text-success">
          <IconCheck size={15} /> Probe benar
        </p>
      )}
      {outcome === "incorrect" && (
        <p className="mt-2 inline-flex items-center gap-1.5 font-semibold text-danger">
          <IconX size={15} /> Probe salah — coba lagi.
        </p>
      )}
    </div>
  );
}
