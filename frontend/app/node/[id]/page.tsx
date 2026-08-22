"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type LevelView,
  type NodeDetail,
  type Probe,
  type ProbeAnswerOut,
  type SubmitOut,
} from "../../../lib/api";
import Markdown from "../../components/Markdown";
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
  const [schedule, setSchedule] = useState<ProbeAnswerOut | null>(null);
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
    setSchedule(null);
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
      setSchedule(out);
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

      {/* Peta level — user selalu tahu posisinya, dan bisa lompat bebas
          (mis. balik ke L3 melihat materi lagi). Aman untuk invariant §1:
          L3–L1 tak mengirim attempt, sinyal reproduce-without-AI dihitung dari
          attempt L0. */}
      <div style={{ display: "flex", gap: 6, margin: "1rem 0", alignItems: "center" }}>
        {node.levels.map((lv, i) => (
          <button
            key={lv}
            type="button"
            onClick={() => goToLevel(i)}
            title={i === levelIndex ? `Kamu di ${lv}` : `Lompat ke ${lv}`}
            style={{
              padding: "3px 10px",
              borderRadius: 6,
              fontSize: 13,
              fontWeight: 600,
              border: "1px solid transparent",
              cursor: "pointer",
              background: i === levelIndex ? "#0969da" : "#eaeef2",
              color: i === levelIndex ? "#fff" : "#57606a",
            }}
          >
            {lv}
          </button>
        ))}
        <span style={{ fontSize: 12, color: "#8c959f", marginLeft: 4 }}>
          ← klik untuk pindah level (mis. balik ke L3 lihat materi)
        </span>
      </div>

      <h2 style={{ fontSize: 18 }}>{level.title}</h2>
      <div
        style={{
          background: "#f6f8fa",
          border: "1px solid #d0d7de",
          borderRadius: 8,
          padding: "0.5rem 1rem",
        }}
      >
        <Markdown>{level.prompt}</Markdown>
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
            {schedule?.became_mastered
              ? "Node mastered 🎉 (reproduce-without-AI terbukti berulang & berjarak)"
              : "Node acquired ✓ (reproduce-without-AI terbukti)"}
          </strong>
          <p style={{ margin: "6px 0 0", color: "#57606a" }}>
            {schedule?.became_mastered ? (
              <>
                Sukses berjarak {schedule.consecutive_success}/{schedule.successes_needed} —
                terpenuhi. Node tetap dijadwalkan; gagal di jatuh tempo mana pun
                menurunkannya jadi <code>lapsed</code>.
              </>
            ) : (
              <>
                Status <code>acquired</code> — belum <code>mastered</code>. Mastery butuh{" "}
                {schedule?.successes_needed ?? 4}× lolos <strong>berjarak</strong>; baru{" "}
                {schedule?.consecutive_success ?? 1}.
              </>
            )}
          </p>
          {schedule?.due_at && (
            <p style={{ margin: "6px 0 0", color: "#57606a" }}>
              Masuk jadwal review: ~{schedule.interval_days?.toFixed(1)} hari lagi (
              {new Date(schedule.due_at).toLocaleDateString()}).
            </p>
          )}
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
