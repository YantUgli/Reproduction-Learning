"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { api, type PlacementState, type PlacementSubmitOut } from "../../lib/api";
import ColdChallenge from "../components/ColdChallenge";
import TestOutput from "../components/TestOutput";
import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Button from "../components/ui/Button";
import ErrorState from "../components/ui/ErrorState";
import Card from "../components/ui/Card";
import { IconCheck, IconX } from "../components/ui/Icon";

/**
 * Sesi placement (M4).
 *
 * Lantai awal **ditemukan**, tidak ditanyakan. Halaman ini sengaja tak punya satu pun
 * pertanyaan "kamu sudah bisa apa" — self-report tidak reliabel (§1 PRD, illusion of
 * competence). Yang ada cuma rangkaian tantangan reproduksi yang menurun, berhenti di
 * node pertama yang berhasil diproduksi.
 */
export default function PlacementPage() {
  const [state, setState] = useState<PlacementState | null>(null);
  const [last, setLast] = useState<PlacementSubmitOut | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const start = async () => {
    setError(null);
    setLast(null);
    try {
      setState(await api.startPlacement());
    } catch (e) {
      setError(String(e));
    }
  };

  const submit = useCallback(
    async (code: string, duration: number, exceeded: boolean) => {
      if (!state) return;
      setSubmitting(true);
      setError(null);
      try {
        const out = await api.submitPlacement(state.session_id, {
          submitted_code: code,
          duration_seconds: duration,
          timebox_exceeded: exceeded,
        });
        setLast(out);
        setState(out.state);
      } catch (e) {
        setError(String(e));
      } finally {
        setSubmitting(false);
      }
    },
    [state],
  );

  return (
    <Container>
      <PageHeader
        backLabel="Forge"
        title="Placement — menemukan lantai"
        subtitle="Tantangan turun dari yang paling jauh di hilir ke yang paling primitif. Sesi berhenti di node pertama yang berhasil kamu produksi — itulah lantai awalmu. Gagal di sini bukan kegagalan; justru itu cara lantainya ketemu."
      />

      {error && <ErrorState error={error} onRetry={start} />}

      {!state && !error && (
        <Card className="p-5">
          <h2 className="text-lg font-semibold">Yang akan terjadi</h2>
          <ol className="mt-2 grid gap-1.5 text-sm text-muted">
            <li>
              <strong className="font-semibold text-fg">1.</strong> Kamu diberi tantangan
              reproduksi, dari yang paling jauh di hilir ke yang paling primitif.
            </li>
            <li>
              <strong className="font-semibold text-fg">2.</strong> Tiap tantangan ada
              timebox. Habis waktu = kode otomatis dikirim &amp; dinilai eksekusi.
            </li>
            <li>
              <strong className="font-semibold text-fg">3.</strong> Sesi berhenti di node
              pertama yang berhasil kamu produksi — itulah lantai awalmu.
            </li>
          </ol>
          <p className="mt-3 text-13 text-muted">
            Tak ada pertanyaan &quot;kamu sudah bisa apa&quot;: lantai ditemukan lewat
            eksekusi, bukan self-report.
          </p>
          <Button variant="primary" className="mt-4" onClick={start}>
            Mulai sesi placement
          </Button>
        </Card>
      )}

      {state && (
        <>
          <Progress state={state} />

          {last && <TestOutput passed={last.passed} output={last.test_output} />}

          {!state.finished && state.current && (
            <div className="mt-4">
              <h2 className="text-lg font-semibold">
                Tantangan {state.current.position}/{state.max_nodes} · {state.current.concept}
              </h2>
              <ColdChallenge
                challengeKey={state.current.instance_id}
                prompt={state.current.prompt}
                signatureContract={state.current.signature_contract}
                timeboxSeconds={state.current.timebox_seconds}
                submitting={submitting}
                language={state.current.language}
                onSubmit={submit}
              />
            </div>
          )}

          {state.finished && <Finished state={state} last={last} onRestart={start} />}
        </>
      )}
    </Container>
  );
}

function Progress({ state }: { state: PlacementState }) {
  if (state.tested.length === 0) return null;
  return (
    <div className="my-4 flex flex-wrap gap-1.5">
      {state.tested.map((t) => {
        const pass = t.result === "pass";
        return (
          <span
            key={t.node_id}
            title={t.node_id}
            className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 font-mono text-13 font-semibold ${
              pass ? "bg-success-bg text-success" : "bg-danger-bg text-danger"
            }`}
          >
            {t.node_id}
            {pass ? <IconCheck size={13} /> : <IconX size={13} />}
          </span>
        );
      })}
    </div>
  );
}

function Finished({
  state,
  last,
  onRestart,
}: {
  state: PlacementState;
  last: PlacementSubmitOut | null;
  onRestart: () => void;
}) {
  if (state.exhausted) {
    return (
      <div className="mt-4 rounded-md border border-warning bg-warning-bg px-5 py-4">
        <strong className="text-warning">Lantai belum ketemu.</strong>
        <p className="mt-1 text-13 text-muted">
          Batas {state.max_nodes} node tercapai tanpa satu pun lolos — sesi dihentikan
          supaya tidak melelahkan. Itu sendiri informasi: mulai dari node paling
          primitif yang tersedia, atau kurikulumnya butuh node yang lebih dasar lagi.
          Tak ada status yang diberikan; tak ada yang diasumsikan.
        </p>
        <Link href="/" className="mt-2 inline-block text-sm text-accent hover:underline">
          ← Kembali ke dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="mt-4 rounded-md border border-success bg-success-bg px-5 py-4">
      <strong className="inline-flex items-center gap-1.5 text-success">
        <IconCheck size={16} />
        Lantai ditemukan: <code className="font-mono">{state.floor_node_id}</code>
      </strong>
      <p className="mt-1.5 text-13 text-muted">
        Kamu memproduksinya dari nol tanpa scaffold apa pun, jadi node ini langsung{" "}
        <code className="font-mono">acquired</code> dan masuk jadwal review
        {last?.floor_outcome?.interval_days != null && (
          <> (~{last.floor_outcome.interval_days.toFixed(1)} hari lagi)</>
        )}
        .
      </p>
      {last && last.unlocked.length > 0 && (
        <p className="mt-1.5 text-13 text-muted">
          Prasyaratnya <strong>dibuka</strong> jadi <code className="font-mono">tersedia</code>:{" "}
          {last.unlocked.map((n) => (
            <code key={n} className="mr-1.5 font-mono">
              {n}
            </code>
          ))}
          — dibuka, bukan diklaim dikuasai: tak ada eksekusi yang membuktikannya.
        </p>
      )}
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Link href="/" className="text-sm text-accent hover:underline">
          ← Kembali ke dashboard
        </Link>
        <Button variant="secondary" size="sm" onClick={onRestart}>
          Ulangi placement
        </Button>
      </div>
    </div>
  );
}
