"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "./Markdown";
import Timebox from "./Timebox";
import Button from "./ui/Button";

const SandboxEditor = dynamic(() => import("./SandboxEditor"), {
  ssr: false,
  loading: () => <p className="text-muted">Memuat editor…</p>,
});

/**
 * Tantangan reproduksi DINGIN: prompt + kontrak signature + editor kosong + timebox.
 * Dipakai review harian dan placement — dua-duanya tanpa scaffold sama sekali
 * (tak ada worked example, tak ada starter code). Editor-nya SandboxEditor yang sama,
 * jadi jaminan "tanpa AI-assist" (§2) berlaku di semua jalur, bukan cuma di sesi node.
 */
export default function ColdChallenge({
  challengeKey,
  prompt,
  signatureContract,
  timeboxSeconds,
  submitting,
  submitLabel = "Jalankan & Verifikasi",
  language = "plaintext",
  onSubmit,
}: {
  /** Berubah saat tantangan berganti → editor & timebox direset. */
  challengeKey: string;
  prompt: string;
  signatureContract: string;
  timeboxSeconds: number;
  submitting: boolean;
  submitLabel?: string;
  language?: string;
  onSubmit: (code: string, durationSeconds: number, timeboxExceeded: boolean) => void;
}) {
  const [code, setCode] = useState("");
  const codeRef = useRef("");
  const startedAt = useRef(Date.now());

  useEffect(() => {
    setCode("");
    codeRef.current = "";
    startedAt.current = Date.now();
  }, [challengeKey]);

  const submit = useCallback(
    (timeboxExceeded: boolean) => {
      const duration = Math.round((Date.now() - startedAt.current) / 1000);
      onSubmit(codeRef.current, duration, timeboxExceeded);
    },
    [onSubmit],
  );

  return (
    <div className="mt-4">
      <div className="mb-2 flex justify-end">
        <Timebox
          key={challengeKey}
          seconds={timeboxSeconds}
          running={!submitting}
          onExpire={() => submit(true)}
        />
      </div>

      <div className="rounded-md border border-border bg-surface-muted px-4 py-3">
        <Markdown>{prompt}</Markdown>
      </div>

      {signatureContract && (
        <p className="mt-2 font-mono text-[13px] text-muted">
          contract: {signatureContract}
        </p>
      )}

      <div className="my-4">
        <SandboxEditor
          value={code}
          language={language}
          onChange={(v) => {
            setCode(v);
            codeRef.current = v;
          }}
        />
      </div>

      <Button variant="primary" onClick={() => submit(false)} loading={submitting}>
        {submitting ? "Menjalankan…" : submitLabel}
      </Button>
    </div>
  );
}
