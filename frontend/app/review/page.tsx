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
import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import { IconCheck, IconInbox } from "../components/ui/Icon";

/**
 * Sesi review harian (M4).
 *
 * Yang direview adalah **reproduksi node**, bukan kartu untuk dikenali — dan selalu
 * pada **instance berbeda** dari yang terakhir dipakai (backend yang memilih). Kalau
 * instance-nya diulang, review berubah jadi hafalan jawaban.
 */
export default function ReviewPage() {
  return (
    <Suspense fallback={<Shell><p className="text-muted">Memuat…</p></Shell>}>
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
        <p className="rounded-md border border-danger bg-danger-bg px-4 py-3 text-danger">
          Error: {error}
        </p>
      </Shell>
    );
  }

  if (!nodeId) {
    return (
      <Shell>
        <h1 className="text-2xl font-bold tracking-tight">Review harian</h1>
        {!due && <p className="mt-3 text-muted">Memuat…</p>}
        {due?.length === 0 && (
          <div className="mt-4">
            <EmptyState icon={<IconInbox />} title="Tak ada node yang jatuh tempo">
              Spaced repetition cuma bekerja kalau jaraknya dihormati — kembali lagi nanti.
            </EmptyState>
          </div>
        )}
        {due && due.length > 0 && (
          <ul className="mt-4 grid gap-2">
            {due.map((d) => (
              <li key={d.node_id}>
                <button onClick={() => setNodeId(d.node_id)} className="w-full text-left">
                  <Card className="p-3.5 transition-shadow hover:shadow-md">
                    <div className="font-semibold">{d.concept}</div>
                    <div className="text-[13px] text-muted">
                      telat {d.overdue_days.toFixed(1)} hari · sukses berjarak{" "}
                      {d.consecutive_success}/{d.successes_needed}
                    </div>
                  </Card>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Shell>
    );
  }

  if (!challenge) {
    return (
      <Shell>
        <p className="text-muted">Memuat…</p>
      </Shell>
    );
  }

  return (
    <Shell>
      <h1 className="text-2xl font-bold tracking-tight">{challenge.concept}</h1>
      <div className="mt-0.5 font-mono text-xs text-subtle">
        review · {challenge.node_id} · varian {challenge.variant_label}
      </div>
      <p className="mt-2 text-muted">
        Instance ini <strong className="font-semibold text-fg">berbeda</strong> dari yang
        terakhir kamu kerjakan. Tanpa contoh, tanpa kerangka, tanpa AI — produksi dari nol.
      </p>
      {challenge.needs_more_variants && (
        <p className="mt-2 rounded-md border border-warning bg-warning-bg px-4 py-2.5 text-[13px] text-warning">
          Varian node ini menipis — rotasi akan mulai berulang. Itu sinyal untuk
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
          language={challenge.language}
          onSubmit={submit}
        />
      )}

      {grade && (
        <TestOutput passed={grade.passed} output={grade.test_output} timedOut={grade.timed_out} />
      )}

      {grade?.passed && probe && !outcome && (
        <div className="mt-4">
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
      className={`mt-4 rounded-md border px-5 py-4 ${
        bad ? "border-danger bg-danger-bg" : "border-success bg-success-bg"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <StatusBadge status={outcome.status} />
        {outcome.became_mastered && (
          <strong className="inline-flex items-center gap-1.5 text-warning">
            <IconCheck size={15} /> MASTERED
          </strong>
        )}
        {outcome.became_lapsed && (
          <strong className="text-danger">Lapsed — interval direset</strong>
        )}
      </div>
      <p className="mt-2 text-[13px] text-muted">
        Rating FSRS: <code className="font-mono">{outcome.rating}</code>
        {outcome.interval_days !== null && (
          <> · jadwal berikutnya ~{outcome.interval_days.toFixed(1)} hari lagi</>
        )}
        {outcome.due_at && <> ({new Date(outcome.due_at).toLocaleDateString()})</>}
      </p>
      <p className="mt-1 text-[13px] text-muted">
        Sukses berjarak {outcome.consecutive_success}/{outcome.successes_needed} menuju{" "}
        <code className="font-mono">mastered</code>
        {!outcome.spaced && " · attempt ini belum jatuh tempo, jadi tidak dihitung"}
        {!outcome.clean &&
          outcome.rating === "Hard" &&
          " · probe salah: produksi terbukti, pemahaman masih rapuh"}
      </p>
      <Link href="/" className="mt-2 inline-block text-sm text-accent hover:underline">
        ← Kembali ke dashboard
      </Link>
    </div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <Container>
      <Link href="/" className="text-sm text-accent hover:underline">
        ← Dashboard
      </Link>
      <div className="mt-3">{children}</div>
    </Container>
  );
}
