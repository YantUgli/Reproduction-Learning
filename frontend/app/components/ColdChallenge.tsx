"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "./Markdown";
import Timebox from "./Timebox";

const SandboxEditor = dynamic(() => import("./SandboxEditor"), {
  ssr: false,
  loading: () => <p>Memuat editor…</p>,
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
  onSubmit,
}: {
  /** Berubah saat tantangan berganti → editor & timebox direset. */
  challengeKey: string;
  prompt: string;
  signatureContract: string;
  timeboxSeconds: number;
  submitting: boolean;
  submitLabel?: string;
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
    <>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Timebox
          key={challengeKey}
          seconds={timeboxSeconds}
          running={!submitting}
          onExpire={() => submit(true)}
        />
      </div>

      <div
        style={{
          background: "#f6f8fa",
          border: "1px solid #d0d7de",
          borderRadius: 8,
          padding: "0.5rem 1rem",
        }}
      >
        <Markdown>{prompt}</Markdown>
      </div>

      {signatureContract && (
        <p style={{ fontFamily: "monospace", fontSize: 13, color: "#57606a" }}>
          contract: {signatureContract}
        </p>
      )}

      <div style={{ margin: "1rem 0" }}>
        <SandboxEditor
          value={code}
          onChange={(v) => {
            setCode(v);
            codeRef.current = v;
          }}
        />
      </div>

      <button onClick={() => submit(false)} disabled={submitting}>
        {submitting ? "Menjalankan…" : submitLabel}
      </button>
    </>
  );
}
