"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { api, type PlacementState, type PlacementSubmitOut } from "../../lib/api";
import ColdChallenge from "../components/ColdChallenge";
import TestOutput from "../components/TestOutput";

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
    <main style={{ maxWidth: 820, margin: "0 auto" }}>
      <p>
        <Link href="/">← Dashboard</Link>
      </p>
      <h1 style={{ marginBottom: 4 }}>Placement — menemukan lantai</h1>
      <p style={{ color: "#57606a", marginTop: 0 }}>
        Tantangan turun dari yang paling jauh di hilir ke yang paling primitif. Sesi
        berhenti di node pertama yang berhasil kamu produksi — itulah lantai awalmu.
        Gagal di sini bukan kegagalan; justru itu cara lantainya ketemu.
      </p>

      {error && <p style={{ color: "#cf222e" }}>Error: {error}</p>}

      {!state && <button onClick={start}>Mulai sesi placement</button>}

      {state && (
        <>
          <Progress state={state} />

          {last && (
            <TestOutput passed={last.passed} output={last.test_output} />
          )}

          {!state.finished && state.current && (
            <div style={{ marginTop: 16 }}>
              <h2 style={{ fontSize: 18 }}>
                Tantangan {state.current.position}/{state.max_nodes} · {state.current.concept}
              </h2>
              <ColdChallenge
                challengeKey={state.current.instance_id}
                prompt={state.current.prompt}
                signatureContract={state.current.signature_contract}
                timeboxSeconds={state.current.timebox_seconds}
                submitting={submitting}
                onSubmit={submit}
              />
            </div>
          )}

          {state.finished && <Finished state={state} last={last} onRestart={start} />}
        </>
      )}
    </main>
  );
}

function Progress({ state }: { state: PlacementState }) {
  return (
    <div style={{ display: "flex", gap: 6, margin: "1rem 0", flexWrap: "wrap" }}>
      {state.tested.map((t) => (
        <span
          key={t.node_id}
          title={t.node_id}
          style={{
            padding: "3px 10px",
            borderRadius: 6,
            fontSize: 13,
            fontWeight: 600,
            background: t.result === "pass" ? "#dafbe1" : "#ffebe9",
            color: t.result === "pass" ? "#1a7f37" : "#cf222e",
          }}
        >
          {t.node_id} {t.result === "pass" ? "✓" : "✗"}
        </span>
      ))}
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
      <div
        style={{
          marginTop: 16,
          padding: "1rem 1.25rem",
          background: "#fff8c5",
          border: "1px solid #9a6700",
          borderRadius: 8,
        }}
      >
        <strong>Lantai belum ketemu.</strong>
        <p style={{ color: "#57606a" }}>
          Batas {state.max_nodes} node tercapai tanpa satu pun lolos — sesi dihentikan
          supaya tidak melelahkan. Itu sendiri informasi: mulai dari node paling
          primitif yang tersedia, atau kurikulumnya butuh node yang lebih dasar lagi.
          Tak ada status yang diberikan; tak ada yang diasumsikan.
        </p>
        <Link href="/">← Kembali ke dashboard</Link>
      </div>
    );
  }

  return (
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
        Lantai ditemukan: <code>{state.floor_node_id}</code>
      </strong>
      <p style={{ margin: "6px 0", color: "#57606a" }}>
        Kamu memproduksinya dari nol tanpa scaffold apa pun, jadi node ini langsung{" "}
        <code>acquired</code> dan masuk jadwal review
        {last?.floor_outcome?.interval_days != null && (
          <> (~{last.floor_outcome.interval_days.toFixed(1)} hari lagi)</>
        )}
        .
      </p>
      {last && last.unlocked.length > 0 && (
        <p style={{ margin: "6px 0", color: "#57606a" }}>
          Prasyaratnya <strong>dibuka</strong> jadi <code>tersedia</code>:{" "}
          {last.unlocked.map((n) => (
            <code key={n} style={{ marginRight: 6 }}>
              {n}
            </code>
          ))}
          — dibuka, bukan diklaim dikuasai: tak ada eksekusi yang membuktikannya.
        </p>
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <Link href="/">← Kembali ke dashboard</Link>
        <button onClick={onRestart}>Ulangi placement</button>
      </div>
    </div>
  );
}
