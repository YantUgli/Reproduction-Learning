"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type Explanation,
  type LevelView,
  type NodeDetail,
  type Probe,
  type ProbeAnswerOut,
  type SubmitOut,
} from "../../../lib/api";
import Markdown from "../../components/Markdown";
import ProbeCard from "../../components/ProbeCard";
import Timebox from "../../components/Timebox";
import TestOutput from "../../components/TestOutput";
import Container from "../../components/ui/Container";
import Button from "../../components/ui/Button";
import { IconArrowRight, IconCheck } from "../../components/ui/Icon";
import ErrorState from "../../components/ui/ErrorState";
import { EditorSkeleton } from "../../components/ui/Skeleton";

// Monaco butuh window → jangan SSR.
const SandboxEditor = dynamic(() => import("../../components/SandboxEditor"), {
  ssr: false,
  loading: () => <p className="text-muted">Memuat editor…</p>,
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
  // Materi just-in-time (R3, M5): hanya diminta SETELAH gagal, dan backend menolak
  // (403) selama node ini belum punya attempt gagal. Bukan bab untuk dibaca dulu.
  const [explanation, setExplanation] = useState<Explanation | null>(null);
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
    setExplanation(null);
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

  // Cegah refresh/tutup tab tak sengaja saat ada kode yang belum dikirim.
  useEffect(() => {
    const dirtyNow = Boolean(level && level.editable && !grade && code !== level.code);
    if (!dirtyNow) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [level, grade, code]);

  const isLast = node && levelIndex >= node.levels.length - 1;

  // "Kotor" = ada ketikan yang belum dikirim di level yang bisa diedit & belum dinilai.
  const dirty = Boolean(level && level.editable && !grade && code !== level.code);

  const goToLevel = (idx: number) => {
    if (
      dirty &&
      idx !== levelIndex &&
      !window.confirm("Kode di editor belum dikirim dan akan hilang saat pindah level. Lanjut?")
    ) {
      return;
    }
    setLevelIndex(idx);
  };

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
        } else {
          // Baru sekarang materi boleh muncul: kegagalannya sudah terjadi.
          setExplanation(await api.getExplanation(nodeId).catch(() => null));
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
      <Container>
        <BackLink />
        <div className="mt-3">
          <ErrorState error={error} onRetry={() => location.reload()} />
        </div>
      </Container>
    );
  }
  if (!node || !level) {
    return (
      <Container>
        <BackLink />
        <div className="mt-4">
          <EditorSkeleton />
        </div>
      </Container>
    );
  }

  const isVerify = level.kind === "verify";
  const cleanPass = grade?.passed && acquired;

  return (
    <Container>
      <BackLink />
      <div className="mt-2 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight">{node.concept}</h1>
          <div className="mt-0.5 font-mono text-xs text-subtle">{node.id}</div>
        </div>
        {isVerify && (
          <div className="flex shrink-0 flex-col items-end gap-1">
            <Timebox
              seconds={level.timebox_seconds}
              running={isVerify && !grade}
              onExpire={() => submit(true)}
            />
            {!grade && (
              <span className="text-13 text-muted">
                Habis waktu = kode otomatis dikirim
              </span>
            )}
          </div>
        )}
      </div>

      {/* Peta level — user selalu tahu posisinya, dan bisa lompat bebas
          (mis. balik ke L3 melihat materi lagi). Aman untuk invariant §1:
          L3–L1 tak mengirim attempt, sinyal reproduce-without-AI dihitung dari
          attempt L0.

          PENTING: level yang sudah DILEWATI ditandai NETRAL (titik + border), BUKAN
          centang hijau. Centang hijau = "terverifikasi benar lewat eksekusi"; melewati
          scaffold hanyalah navigasi, tak ada test yang jalan. Memberi ✓ hijau di sini
          justru memproduksi illusion of competence yang ditolak invariant §1. */}
      <div className="my-4 flex flex-wrap items-center gap-1.5">
        {node.levels.map((lv, i) => {
          const active = i === levelIndex;
          const visited = i < levelIndex; // scaffold sudah dilewati (navigasi, bukan lulus test)
          return (
            <button
              key={lv}
              type="button"
              onClick={() => goToLevel(i)}
              aria-current={active ? "step" : undefined}
              title={active ? `Kamu di ${lv}` : visited ? `Kembali ke ${lv}` : `Lompat ke ${lv}`}
              className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-13 font-semibold transition-colors ${
                active
                  ? "border-accent bg-accent text-accent-fg"
                  : visited
                    ? "border-border bg-surface text-fg hover:bg-surface-muted"
                    : "border-transparent bg-neutral-bg text-muted hover:bg-border-muted"
              }`}
            >
              {visited && (
                <span
                  aria-hidden="true"
                  className="inline-block h-1.5 w-1.5 rounded-full bg-subtle"
                />
              )}
              {lv}
            </button>
          );
        })}
        <span className="ml-1 text-xs text-subtle">
          klik untuk pindah level (mis. balik ke L3 lihat materi)
        </span>
      </div>

      <h2 className="text-lg font-semibold">{level.title}</h2>
      <div className="mt-2 rounded-md border border-border bg-surface-muted px-4 py-3">
        <Markdown>{level.prompt}</Markdown>
      </div>

      {level.signature_contract && (
        <p className="mt-2 font-mono text-13 text-muted">
          contract: {level.signature_contract}
        </p>
      )}

      <div className="my-4">
        <SandboxEditor
          value={code}
          onChange={onCodeChange}
          language={level.language}
          readOnly={!level.editable || Boolean(grade)}
          onSubmit={
            isVerify && !grade && !submitting ? () => submit(false) : undefined
          }
        />
      </div>

      {/* Aksi per level */}
      {!isVerify && (
        <Button
          variant="primary"
          onClick={() => !isLast && goToLevel(levelIndex + 1)}
          disabled={Boolean(isLast)}
        >
          {level.kind === "worked_example"
            ? "Saya paham — coba reproduksi"
            : "Lanjut (pudarkan scaffold)"}
          <IconArrowRight size={15} />
        </Button>
      )}

      {isVerify && !grade && (
        <Button variant="primary" onClick={() => submit(false)} loading={submitting}>
          {submitting ? "Menjalankan…" : "Jalankan & Verifikasi"}
        </Button>
      )}

      {/* Hasil test — kegagalan DITAMPILKAN (cermin §7.6) */}
      {grade && (
        <div className="mt-4">
          <TestOutput passed={grade.passed} output={grade.test_output} timedOut={grade.timed_out} />

          {!grade.passed && (
            <div className="mt-3 flex flex-wrap gap-2">
              <Button variant="secondary" onClick={() => goToLevel(levelIndex)}>
                Coba lagi (level ini)
              </Button>
              {levelIndex > 0 && (
                <Button variant="secondary" onClick={() => goToLevel(levelIndex - 1)}>
                  Naik scaffold ({node.levels[levelIndex - 1]})
                </Button>
              )}
            </div>
          )}

          {!grade.passed && explanation && (
            <details className="mt-3 rounded-md border border-border bg-surface">
              <summary className="cursor-pointer px-4 py-2.5 font-semibold">
                Materi just-in-time untuk node ini
              </summary>
              <div className="border-t border-border px-4 py-3">
                <Markdown>{explanation.markdown}</Markdown>
                {explanation.worked_example && (
                  <pre className="mt-2 overflow-x-auto rounded-md bg-code-bg p-4 text-13 text-code-fg">
                    {explanation.worked_example}
                  </pre>
                )}
              </div>
            </details>
          )}
        </div>
      )}

      {/* Probe hanya setelah test PASS di L0 */}
      {grade?.passed && isVerify && probe && !cleanPass && (
        <div className="mt-4">
          <ProbeCard probe={probe} disabled={false} outcome={probeResult} onSubmit={answerProbe} />
          {probeResult === "incorrect" && (
            <p className="mt-2 rounded-md border border-warning bg-warning-bg px-4 py-2.5 text-13 text-warning">
              Produksimu terbukti (test hijau), tapi probe menunjukkan pemahaman masih
              rapuh — sukses berjarak <strong>belum bertambah</strong> dan interval review
              diperpendek. Jawab probe dengan benar untuk menuntaskan akuisisi.
            </p>
          )}
        </div>
      )}

      {cleanPass && (
        <div className="mt-4 rounded-md border border-success bg-success-bg px-5 py-4">
          <strong className="inline-flex items-center gap-1.5 text-success">
            <IconCheck size={16} />
            {schedule?.became_mastered
              ? "Node mastered (reproduce-without-AI terbukti berulang & berjarak)"
              : "Node acquired (reproduce-without-AI terbukti)"}
          </strong>
          <p className="mt-1.5 text-13 text-muted">
            {schedule?.became_mastered ? (
              <>
                Sukses berjarak {schedule.consecutive_success}/{schedule.successes_needed} —
                terpenuhi. Node tetap dijadwalkan; gagal di jatuh tempo mana pun
                menurunkannya jadi <code className="font-mono">lapsed</code>.
              </>
            ) : (
              <>
                Status <code className="font-mono">acquired</code> — belum{" "}
                <code className="font-mono">mastered</code>. Mastery butuh{" "}
                {schedule?.successes_needed ?? 4}× lolos <strong>berjarak</strong>; baru{" "}
                {schedule?.consecutive_success ?? 1}.
              </>
            )}
          </p>
          {schedule?.due_at && (
            <p className="mt-1.5 text-13 text-muted">
              Masuk jadwal review: ~{schedule.interval_days?.toFixed(1)} hari lagi (
              {new Date(schedule.due_at).toLocaleDateString()}).
            </p>
          )}
          <Link href="/" className="mt-2 inline-block text-sm text-accent hover:underline">
            ← Kembali ke dashboard
          </Link>
        </div>
      )}
    </Container>
  );
}

function BackLink() {
  return (
    <Link href="/" className="text-sm text-accent hover:underline">
      ← Dashboard
    </Link>
  );
}
