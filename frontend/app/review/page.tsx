"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import {
  api,
  type DueItem,
  type Outcome,
  type Probe,
  type ReviewChallenge,
  type ReviewSubmitOut,
} from "../../lib/api";
import ColdChallenge from "../components/ColdChallenge";
import ProbeCard from "../components/ProbeCard";
import StatusBadge from "../components/StatusBadge";
import TestOutput from "../components/TestOutput";

/**
 * Sesi review harian (M4).
 *
 * Yang direview adalah **reproduksi node**, bukan kartu untuk dikenali — dan selalu
 * pada **instance berbeda** dari yang terakhir dipakai (backend yang memilih). Kalau
 * instance-nya diulang, review berubah jadi hafalan jawaban.
 */
export default function ReviewPage() {
  return (
    <Suspense fallback={<Shell><p>Memuat…</p></Shell>}>
      <ReviewSession />
    </Suspense>
  );
}

function ReviewSession() {
  const params = useSearchParams();
  const nodeParam = params.get("node");

  const [due, setDue] = useState<DueItem[] | null>(null);
  const [nodeId, setNodeId] = useState<string | null>(nodeParam);
  const [challenge, setChallenge] = useState<ReviewChallenge | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [grade, setGrade] = useState<ReviewSubmitOut | null>(null);
  const [probe, setProbe] = useState<Probe | null>(null);
  const [probeResult, setProbeResult] = useState<"correct" | "incorrect" | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listDue().then(setDue).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!nodeId) return;
    setGrade(null);
    setProbe(null);
    setProbeResult(null);
    setOutcome(null);
    api.getReviewChallenge(nodeId).then(setChallenge).catch((e) => setError(String(e)));
  }, [nodeId]);

  const submit = useCallback(
    async (code: string, duration: number, exceeded: boolean) => {
      if (!challenge) return;
      setSubmitting(true);
      setError(null);
      try {
        const out = await api.submitReview({
          node_id: challenge.node_id,
          instance_id: challenge.instance_id,
          submitted_code: code,
          duration_seconds: duration,
          timebox_exceeded: exceeded,
        });
        setGrade(out);
        setProbe(out.probe);
        if (out.outcome) setOutcome(out.outcome); // gagal → hasil sudah final
      } catch (e) {
        setError(String(e));
      } finally {
        setSubmitting(false);
      }
    },
    [challenge],
  );

  const answerProbe = async (answer: string) => {
    if (!grade || !probe) return;
    try {
      const out = await api.submitReviewProbe({
        attempt_id: grade.attempt_id,
        probe_id: probe.id,
        answer,
      });
      setProbeResult(out.probe_correct ? "correct" : "incorrect");
      setOutcome(out.outcome);
    } catch (e) {
      setError(String(e));
    }
  };

  if (error) {
    return (
      <Shell>
        <p style={{ color: "#cf222e" }}>Error: {error}</p>
      </Shell>
    );
  }

  if (!nodeId) {
    return (
      <Shell>
        <h1>Review harian</h1>
        {!due && <p>Memuat…</p>}
        {due?.length === 0 && (
          <p style={{ color: "#57606a" }}>
            Tak ada node yang jatuh tempo. Spaced repetition cuma bekerja kalau
            jaraknya dihormati — kembali lagi nanti.
          </p>
        )}
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {due?.map((d) => (
            <li key={d.node_id}>
              <button
                onClick={() => setNodeId(d.node_id)}
                style={{ width: "100%", textAlign: "left", padding: "0.7rem 1rem" }}
              >
                <strong>{d.concept}</strong> · telat {d.overdue_days.toFixed(1)} hari ·
                sukses berjarak {d.consecutive_success}/{d.successes_needed}
              </button>
            </li>
          ))}
        </ul>
      </Shell>
    );
  }

  if (!challenge) {
    return (
      <Shell>
        <p>Memuat…</p>
      </Shell>
    );
  }

  return (
    <Shell>
      <h1 style={{ marginBottom: 0 }}>{challenge.concept}</h1>
      <div style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>
        review · {challenge.node_id} · varian {challenge.variant_label}
      </div>
      <p style={{ color: "#57606a" }}>
        Instance ini <strong>berbeda</strong> dari yang terakhir kamu kerjakan. Tanpa
        contoh, tanpa kerangka, tanpa AI — produksi dari nol.
      </p>
      {challenge.needs_more_variants && (
        <p style={{ fontSize: 13, color: "#9a6700" }}>
          ⚠ Varian node ini menipis — rotasi akan mulai berulang. Itu sinyal untuk
          mengarang varian baru (authoring), bukan alasan berhenti review.
        </p>
      )}

      {!grade && (
        <ColdChallenge
          challengeKey={challenge.instance_id}
          prompt={challenge.prompt}
          signatureContract={challenge.signature_contract}
          timeboxSeconds={challenge.timebox_seconds}
          submitting={submitting}
          onSubmit={submit}
        />
      )}

      {grade && (
        <TestOutput passed={grade.passed} output={grade.test_output} timedOut={grade.timed_out} />
      )}

      {grade?.passed && probe && !outcome && (
        <div style={{ marginTop: 16 }}>
          <ProbeCard probe={probe} disabled={false} outcome={probeResult} onSubmit={answerProbe} />
        </div>
      )}

      {outcome && <OutcomePanel outcome={outcome} />}
    </Shell>
  );
}

function OutcomePanel({ outcome }: { outcome: Outcome }) {
  const bad = outcome.became_lapsed;
  return (
    <div
      style={{
        marginTop: 16,
        padding: "1rem 1.25rem",
        background: bad ? "#ffebe9" : "#dafbe1",
        border: `1px solid ${bad ? "#cf222e" : "#1a7f37"}`,
        borderRadius: 8,
      }}
    >
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <StatusBadge status={outcome.status} />
        {outcome.became_mastered && <strong style={{ color: "#9a6700" }}>MASTERED 🎉</strong>}
        {outcome.became_lapsed && (
          <strong style={{ color: "#cf222e" }}>Lapsed — interval direset</strong>
        )}
      </div>
      <p style={{ margin: "8px 0 0", color: "#57606a" }}>
        Rating FSRS: <code>{outcome.rating}</code>
        {outcome.interval_days !== null && (
          <> · jadwal berikutnya ~{outcome.interval_days.toFixed(1)} hari lagi</>
        )}
        {outcome.due_at && <> ({new Date(outcome.due_at).toLocaleDateString()})</>}
      </p>
      <p style={{ margin: "4px 0 8px", color: "#57606a" }}>
        Sukses berjarak {outcome.consecutive_success}/{outcome.successes_needed} menuju{" "}
        <code>mastered</code>
        {!outcome.spaced && " · attempt ini belum jatuh tempo, jadi tidak dihitung"}
        {!outcome.clean &&
          outcome.rating === "Hard" &&
          " · probe salah: produksi terbukti, pemahaman masih rapuh"}
      </p>
      <Link href="/">← Kembali ke dashboard</Link>
    </div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main style={{ maxWidth: 820, margin: "0 auto" }}>
      <p>
        <Link href="/">← Dashboard</Link>
      </p>
      {children}
    </main>
  );
}
