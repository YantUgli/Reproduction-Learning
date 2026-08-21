"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type LevelView,
  type NodeDetail,
  type Probe,
  type SubmitOut,
} from "../../../lib/api";
import ProbeCard from "../../components/ProbeCard";
import Timebox from "../../components/Timebox";

// Monaco butuh window → jangan SSR.
const SandboxEditor = dynamic(() => import("../../components/SandboxEditor"), {
  ssr: false,
  loading: () => <p>Memuat editor…</p>,
});

export default function NodeSession({ params }: { params: { id: string } }) {
  const nodeId = params.id;
  const [node, setNode] = useState<NodeDetail | null>(null);
  const [levelIndex, setLevelIndex] = useState(0);
  const [level, setLevel] = useState<LevelView | null>(null);
  const [code, setCode] = useState("");
  const codeRef = useRef("");
  const startedAt = useRef<number>(Date.now());

  const [submitting, setSubmitting] = useState(false);
  const [grade, setGrade] = useState<SubmitOut | null>(null);
  const [probe, setProbe] = useState<Probe | null>(null);
  const [probeResult, setProbeResult] = useState<"correct" | "incorrect" | null>(null);
  const [acquired, setAcquired] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getNode(nodeId).then(setNode).catch((e) => setError(String(e)));
  }, [nodeId]);

  const levelName = node?.levels[levelIndex];

  // Muat konten level saat pindah level.
  useEffect(() => {
    if (!levelName) return;
    setGrade(null);
    setProbe(null);
    setProbeResult(null);
    setAcquired(false);
    api
      .getLevel(nodeId, levelName)
      .then((lv) => {
        setLevel(lv);
        setCode(lv.code);
        codeRef.current = lv.code;
        startedAt.current = Date.now();
      })
      .catch((e) => setError(String(e)));
  }, [nodeId, levelName]);

  const onCodeChange = (v: string) => {
    setCode(v);
    codeRef.current = v;
  };

  const isLast = node && levelIndex >= node.levels.length - 1;

  const goToLevel = (idx: number) => setLevelIndex(idx);

  const submit = useCallback(
    async (timeboxExceeded: boolean) => {
      if (!level) return;
      setSubmitting(true);
      setError(null);
      try {
        const duration = Math.round((Date.now() - startedAt.current) / 1000);
        const out = await api.submitAttempt({
          node_id: nodeId,
          instance_id: level.instance_id,
          scaffold_level: level.level,
          submitted_code: codeRef.current,
          duration_seconds: duration,
          timebox_exceeded: timeboxExceeded,
        });
        setGrade(out);
        if (out.passed) {
          const p = await api.getProbe(nodeId).catch(() => null);
          setProbe(p);
        }
      } catch (e) {
        setError(String(e));
      } finally {
        setSubmitting(false);
      }
    },
    [level, nodeId],
  );

  const answerProbe = async (answer: string) => {
    if (!grade || !probe) return;
    try {
      const out = await api.answerProbe({
        attempt_id: grade.attempt_id,
        probe_id: probe.id,
        answer,
      });
      setProbeResult(out.probe_correct ? "correct" : "incorrect");
      setAcquired(out.acquired);
    } catch (e) {
      setError(String(e));
    }
  };

  if (error) {
    return (
      <main style={{ maxWidth: 820, margin: "0 auto" }}>
        <BackLink />
        <p style={{ color: "#cf222e" }}>Error: {error}</p>
      </main>
    );
  }
  if (!node || !level) {
    return (
      <main style={{ maxWidth: 820, margin: "0 auto" }}>
        <BackLink />
        <p>Memuat…</p>
      </main>
    );
  }

  const isVerify = level.kind === "verify";
  const cleanPass = grade?.passed && acquired;

  return (
    <main style={{ maxWidth: 820, margin: "0 auto" }}>
      <BackLink />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h1 style={{ marginBottom: 4 }}>{node.concept}</h1>
        {isVerify && (
          <Timebox
            seconds={level.timebox_seconds}
            running={isVerify && !grade}
            onExpire={() => submit(true)}
          />
        )}
      </div>
      <div style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>{node.id}</div>

      {/* Peta level — user selalu tahu posisinya */}
      <div style={{ display: "flex", gap: 6, margin: "1rem 0" }}>
        {node.levels.map((lv, i) => (
          <span
            key={lv}
            style={{
              padding: "3px 10px",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              background: i === levelIndex ? "#0969da" : "#eaeef2",
              color: i === levelIndex ? "#fff" : "#57606a",
            }}
          >
            {lv}
          </span>
        ))}
      </div>

      <h2 style={{ fontSize: 18 }}>{level.title}</h2>
      <div
        style={{
          background: "#f6f8fa",
          border: "1px solid #d0d7de",
          borderRadius: 8,
          padding: "0.5rem 1rem",
          whiteSpace: "pre-wrap",
        }}
      >
        {level.prompt}
      </div>

      {level.signature_contract && (
        <p style={{ fontFamily: "monospace", fontSize: 13, color: "#57606a" }}>
          contract: {level.signature_contract}
        </p>
      )}

      <div style={{ margin: "1rem 0" }}>
        <SandboxEditor
          value={code}
          onChange={onCodeChange}
          readOnly={!level.editable || Boolean(grade)}
        />
      </div>

      {/* Aksi per level */}
      {!isVerify && (
        <button onClick={() => !isLast && goToLevel(levelIndex + 1)} disabled={Boolean(isLast)}>
          {level.kind === "worked_example"
            ? "Saya paham — coba reproduksi →"
            : "Lanjut (pudarkan scaffold) →"}
        </button>
      )}

      {isVerify && !grade && (
        <button onClick={() => submit(false)} disabled={submitting}>
          {submitting ? "Menjalankan…" : "Jalankan & Verifikasi"}
        </button>
      )}

      {/* Hasil test — kegagalan DITAMPILKAN (cermin §7.6) */}
      {grade && (
        <div style={{ marginTop: 16 }}>
          <div
            style={{
              fontWeight: 700,
              color: grade.passed ? "#1a7f37" : "#cf222e",
            }}
          >
            {grade.passed ? "TEST PASS ✓" : "TEST FAIL ✗"}
            {grade.timed_out && " (timeout eksekusi)"}
          </div>
          <pre
            style={{
              background: "#0d1117",
              color: "#e6edf3",
              padding: "0.75rem 1rem",
              borderRadius: 8,
              overflowX: "auto",
              fontSize: 13,
              maxHeight: 260,
            }}
          >
            {grade.test_output || "(tanpa output)"}
          </pre>

          {!grade.passed && (
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => goToLevel(levelIndex)}>Coba lagi (level ini)</button>
              {levelIndex > 0 && (
                <button onClick={() => goToLevel(levelIndex - 1)}>
                  Naik scaffold ({node.levels[levelIndex - 1]})
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Probe hanya setelah test PASS di L0 */}
      {grade?.passed && isVerify && probe && !cleanPass && (
        <div style={{ marginTop: 16 }}>
          <ProbeCard
            probe={probe}
            disabled={false}
            outcome={probeResult}
            onSubmit={answerProbe}
          />
        </div>
      )}

      {cleanPass && (
        <div
          style={{
            marginTop: 16,
            padding: "1rem 1.25rem",
            background: "#dafbe1",
            border: "1px solid #1a7f37",
            borderRadius: 8,
          }}
        >
          <strong style={{ color: "#1a7f37" }}>
            Node acquired ✓ (reproduce-without-AI terbukti)
          </strong>
          <p style={{ margin: "6px 0 0", color: "#57606a" }}>
            Status <code>acquired</code> — belum <code>mastered</code>. Mastery butuh
            lolos berulang berjarak (FSRS, M4).
          </p>
          <Link href="/">← Kembali ke daftar node</Link>
        </div>
      )}
    </main>
  );
}

function BackLink() {
  return (
    <p>
      <Link href="/">← Daftar node</Link>
    </p>
  );
}
