"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AuditEdge,
  type AuditOut,
  type AuditSignal,
  type PendingEdgeOut,
} from "../../lib/api";
import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge, { type BadgeTone } from "../components/ui/Badge";
import EmptyState from "../components/ui/EmptyState";
import ErrorState from "../components/ui/ErrorState";
import { IconAlert, IconArrowRight, IconClock } from "../components/ui/Icon";
import AuthoringNav from "./AuthoringNav";

// Hatch "belum ada data" — bagian kurikulum yang belum diuji dingin. Sama pola dengan
// bar Library: yang belum terbukti bergaris, bukan solid.
const HATCH =
  "repeating-linear-gradient(45deg, var(--neutral-bg) 0 4px, var(--surface) 4px 8px)";

/**
 * MEJA AUDIT (M7, primer) — brief §7.6.
 *
 * Sejak 2026-08-31 peran Isyah bukan lagi gerbang blokir: gerbang mesin + promosi
 * otomatis yang memutuskan, dan mata Isyah di level kurikulum diganti **telemetri**.
 * Halaman ini menampilkan node yang telemetri-nya curiga — dengan ALASAN & ANGKA —
 * supaya keputusan pensiun bisa diambil dalam hitungan detik.
 *
 * BUKAN dashboard, bukan graf (§8 tolak DAG explorer): daftar bertanda + alasan.
 *
 * Batas jujur (§7.6): dengan **n=1** telemetri hanya MENANDAI; tak ada pensiun
 * otomatis. Dan aksi **retire** + **set-destination** BELUM punya endpoint — dirender
 * sebagai kontrol pending, bukan tombol yang berpura-pura bekerja.
 */
export default function AuditDeskPage() {
  const [audit, setAudit] = useState<AuditOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    api.getAudit().then(setAudit).catch((e) => setError(String(e)));
  }, []);

  useEffect(load, [load]);

  return (
    <Container wide>
      <PageHeader
        title="Authoring · Audit desk"
        subtitle="Node yang telemetri-nya distrust — dengan alasan dan angkanya. Kurasi pindah ke belakang: gerbang mesin yang memutuskan konten masuk; ini tempat menandai mana yang ternyata tak layak."
        back={null}
      />
      <AuthoringNav />

      {error && <ErrorState error={error} onRetry={load} />}
      {!audit && !error && <p className="text-muted">Memuat telemetri…</p>}

      {audit && (
        <>
          <CoveragePanel audit={audit} />
          <SignalsSection signals={audit.node_signals} />
          <EdgesSection edges={audit.edge_findings} />
          <PendingEdgesSection
            edges={audit.pending_edges}
            readyToPromote={audit.ready_to_promote}
          />
          <DestinationsSection domains={audit.domains_without_destination} />
        </>
      )}
    </Container>
  );
}

/** Coverage prominan (§7.6): tanpa ini "tak ada temuan" salah terbaca "semuanya sehat",
 *  padahal dengan n=1 hampir selalu "belum ada datanya". */
function CoveragePanel({ audit }: { audit: AuditOut }) {
  const c = audit.coverage;
  const pctData = c.nodes > 0 ? Math.round((c.nodes_with_cold_data / c.nodes) * 100) : 0;
  return (
    <Card className="mt-2 p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-semibold">Cakupan data</h2>
        <span className="font-mono text-[11px] text-subtle">
          n=1 · telemetri MENANDAI, tak mencabut
        </span>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-3">
        <div>
          <div className="font-mono text-[11px] font-semibold uppercase tracking-wide text-muted">
            punya data
          </div>
          <div className="mt-1 font-mono text-4xl font-bold tabular-nums">
            {pctData}% <span className="text-base font-normal text-subtle">ada data</span>
          </div>
        </div>
        <div className="min-w-[240px] flex-1">
          {/* Bar cakupan: porsi solid = sudah punya data dingin; sisanya bergaris =
              belum diuji (belum ada datanya, bukan "sehat"). */}
          <div className="flex h-2.5 overflow-hidden rounded-md border border-border-muted bg-surface-muted">
            {pctData > 0 && (
              <div className="h-full bg-neutral" style={{ width: `${pctData}%` }} />
            )}
            <div className="h-full flex-1" style={{ background: HATCH }} />
          </div>
          <p className="mt-2 text-13 text-muted">
            Baru <strong className="text-fg tabular-nums">{c.nodes_assessable}</strong> dari{" "}
            <strong className="text-fg tabular-nums">{c.nodes}</strong> node punya cukup
            attempt dingin (≥{c.min_attempts}) untuk dinilai. Sisanya bukan
            &quot;sehat&quot; — cuma <strong className="text-fg">belum ada datanya</strong>.
          </p>
        </div>
      </div>

      <div className="mt-3 border-t border-border-muted pt-2.5 font-mono text-[11px] text-subtle tabular-nums">
        node total {c.nodes} · punya data dingin {c.nodes_with_cold_data} · bisa dinilai{" "}
        {c.nodes_assessable} · lapsed sekarang {c.lapsed_now}
      </div>
    </Card>
  );
}

const SIGNAL_META: Record<
  string,
  { label: string; tone: BadgeTone; border: string; tint: string }
> = {
  trivia: {
    label: "trivia (lolos-100%-tak-pernah-gagal)",
    tone: "warning",
    border: "border-l-warning",
    tint: "text-warning",
  },
  rusak: {
    label: "rusak (tak pernah lolos)",
    tone: "danger",
    border: "border-l-danger",
    tint: "text-danger",
  },
  salah_kalibrasi: {
    label: "salah kalibrasi (waktu vs estimasi)",
    tone: "warning",
    border: "border-l-warning",
    tint: "text-warning",
  },
  probe_mati: {
    label: "probe mati (daya beda rendah)",
    tone: "warning",
    border: "border-l-subtle",
    tint: "text-subtle",
  },
};

function SignalsSection({ signals }: { signals: AuditSignal[] }) {
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">Node bertanda</h2>
      {signals.length === 0 ? (
        <div className="mt-3">
          {/* Empty ≠ healthy (§7.6 / §9.5). */}
          <EmptyState icon={<IconAlert size={26} />} title="Belum ada tanda">
            Dengan satu pelajar ini biasanya berarti <strong className="text-fg">belum cukup
            data</strong>, bukan <em>semuanya baik</em>. Lihat panel cakupan di atas: node
            baru bisa dinilai setelah beberapa attempt dingin.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-3 grid gap-2">
          {signals.map((s) => (
            <li key={`${s.node_id}-${s.kind}`}>
              <SignalRow signal={s} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function SignalRow({ signal }: { signal: AuditSignal }) {
  const meta =
    SIGNAL_META[signal.kind] ??
    ({ label: signal.kind, tone: "neutral", border: "border-l-subtle", tint: "text-subtle" } as const);
  return (
    <Card className={`border-l-4 p-3.5 ${meta.border}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <IconAlert size={18} className={`mt-0.5 shrink-0 ${meta.tint}`} />
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <code className="font-mono text-sm font-semibold">{signal.node_id}</code>
              <Badge tone={meta.tone} variant="outline">
                {meta.label}
              </Badge>
              <span className="font-mono text-xs text-subtle tabular-nums">
                n={signal.samples}
              </span>
            </div>
            <div className={`mt-1 font-mono text-13 ${meta.tint}`}>{signal.detail}</div>
          </div>
        </div>
        <Link
          href={`/node/${signal.node_id}`}
          className="inline-flex shrink-0 items-center gap-1 text-13 font-semibold text-accent hover:underline"
        >
          Inspeksi <IconArrowRight size={13} />
        </Link>
      </div>
      {/* Retire di bawah pemisah putus-putus — pending (§7.6). */}
      <div className="mt-3 flex justify-end border-t border-dashed border-border-muted pt-3">
        <RetireControl nodeId={signal.node_id} />
      </div>
    </Card>
  );
}

/** ⚠ GAP (§7.6): retire BELUM punya endpoint. Dirancang, ditandai pending — bukan
 *  tombol yang berpura-pura bekerja (§9.6 "fiction removed"). */
function RetireControl({ nodeId }: { nodeId: string }) {
  return (
    <div className="flex shrink-0 flex-col items-end gap-1">
      <Button
        variant="danger"
        size="sm"
        disabled
        title="Butuh kapabilitas backend baru: POST /authoring/nodes/{id}/retire"
      >
        Pensiunkan node
      </Button>
      <span className="font-mono text-[10px] text-subtle" aria-hidden="true">
        pending · butuh endpoint baru
      </span>
      <span className="sr-only">
        Aksi pensiun untuk {nodeId} belum tersedia — memerlukan endpoint backend baru.
      </span>
    </div>
  );
}

const EDGE_META: Record<string, { label: string; tone: BadgeTone }> = {
  uncorroborated: { label: "belum terkukuhkan", tone: "warning" },
  predictive: { label: "prediktif lemah", tone: "warning" },
};

function EdgesSection({ edges }: { edges: AuditEdge[] }) {
  if (edges.length === 0) return null;
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">Edge belum terkukuhkan</h2>
      <p className="mt-0.5 max-w-2xl text-13 text-muted">
        Laporan, <strong className="text-fg">bukan gerbang</strong> (§7 2026-09-01):
        ketiadaan bukti konstruk hulu di hilir tak membuktikan edge itu salah. Yang
        menopang tetap pembatasan akibat — edge usulan AI selalu <code className="font-mono">soft</code>.
      </p>
      <ul className="mt-3 grid gap-2">
        {edges.map((e) => {
          const meta = EDGE_META[e.kind] ?? { label: e.kind, tone: "neutral" as BadgeTone };
          return (
            <li key={`${e.from_node_id}-${e.to_node_id}-${e.kind}`}>
              <Card className="flex flex-wrap items-center gap-2 p-3">
                <code className="font-mono text-13">{e.from_node_id}</code>
                <span className="text-subtle" aria-hidden="true">→</span>
                <code className="font-mono text-13">{e.to_node_id}</code>
                <Badge tone={meta.tone} variant="outline">
                  {meta.label}
                </Badge>
                <span className="text-13 text-muted">{e.reason}</span>
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

const PENDING_STATE_META: Record<
  PendingEdgeOut["state"],
  { label: string; tone: BadgeTone }
> = {
  menunggu: { label: "menunggu", tone: "neutral" },
  matang: { label: "matang · siap promosi", tone: "warning" },
  diveto: { label: "diveto", tone: "danger" },
};

/** Hitung mundur jatuh tempo (statis — halaman ini load-sekali, tak live-ticking). */
function maturityLabel(edge: PendingEdgeOut): string {
  if (edge.state === "diveto") return "diveto — tak akan dipromosikan";
  const ms = new Date(edge.matures_at).getTime() - Date.now();
  const days = Math.round(ms / 86_400_000);
  if (ms <= 0) return `matang sejak ${Math.abs(days)} hari lalu`;
  return `matang dalam ${days} hari`;
}

/**
 * Edge `hard` menunggu veto (Amandemen C). Sengaja BUKAN gerbang blokir: usulan hidup di
 * `edges.pending.yaml` (bukan `edges.yaml`), jadi loop tak pernah membacanya dan node tak
 * pernah terkunci selama menunggu. Veto & promosi keduanya lewat script manual — halaman
 * ini read-only, memberi perintah tempel (pola retire/set-destination yang sudah ada).
 */
function PendingEdgesSection({
  edges,
  readyToPromote,
}: {
  edges: PendingEdgeOut[];
  readyToPromote: number;
}) {
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">Edge hard menunggu veto</h2>
      <p className="mt-0.5 max-w-2xl text-13 text-muted">
        Usulan edge <code className="font-mono">hard</code> dari AI (Amandemen B) tak
        langsung mengunci urutan: ia menunggu <strong className="text-fg">7 hari</strong> di{" "}
        <code className="font-mono">edges.pending.yaml</code>, dan Isyah bisa memveto kapan
        saja. Loop <strong className="text-fg">tak pernah</strong> membaca antrian ini —
        node tetap <code className="font-mono">available</code> selama edge menunggu.
      </p>

      {readyToPromote > 0 && <PromoteReminder count={readyToPromote} />}

      {edges.length === 0 ? (
        <div className="mt-3">
          <EmptyState icon={<IconClock size={26} />} title="Antrian kosong">
            Ini <strong className="text-fg">normal</strong>: sampai Amandemen B diaktifkan,
            usulan AI selalu <code className="font-mono">soft</code> dan mendarat langsung di{" "}
            <code className="font-mono">edges.yaml</code> — tak ada yang lewat antrian veto.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-3 grid gap-2">
          {edges.map((e) => (
            <li key={`${e.from_node_id}-${e.to_node_id}`}>
              <PendingEdgeRow edge={e} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Pengingat "X siap promosi" — hanya saat ada yang matang. `--dry-run` duluan (pratinjau
 *  sebelum gerbang, pola `verify_library.py --candidates`). */
function PromoteReminder({ count }: { count: number }) {
  return (
    <Card className="mt-3 border-l-4 border-l-warning p-3.5">
      <div className="flex items-start gap-3">
        <IconClock size={18} className="mt-0.5 shrink-0 text-warning" />
        <div className="min-w-0">
          <div className="text-13 font-semibold text-fg">
            {count} edge siap dipromosikan{" "}
            <span className="font-normal text-muted">(matang, tak diveto)</span>
          </div>
          <p className="mt-0.5 text-13 text-muted">
            Pratinjau dulu, lalu jalankan. Promosi ini menulis <code className="font-mono">hard</code>{" "}
            ke <code className="font-mono">edges.yaml</code> — jalankan di terminal:
          </p>
          <pre className="mt-2 overflow-x-auto rounded-md bg-code-bg p-3 text-[12.5px] text-code-fg">
            python scripts/promote_pending_edges.py --dry-run{"\n"}
            python scripts/promote_pending_edges.py
          </pre>
        </div>
      </div>
    </Card>
  );
}

function PendingEdgeRow({ edge }: { edge: PendingEdgeOut }) {
  const meta = PENDING_STATE_META[edge.state];
  const vetoCmd = `python scripts/promote_pending_edges.py --veto ${edge.from_node_id}__${edge.to_node_id} --reason "..."`;
  return (
    <Card className="p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <code className="font-mono text-13">{edge.from_node_id}</code>
        <span className="text-subtle" aria-hidden="true">→</span>
        <code className="font-mono text-13">{edge.to_node_id}</code>
        <Badge tone={meta.tone} variant="outline">
          {meta.label}
        </Badge>
        <span className="font-mono text-xs text-subtle tabular-nums">{maturityLabel(edge)}</span>
        <span className="ml-auto font-mono text-[11px] text-subtle">{edge.domain_id}</span>
      </div>
      <div className="mt-1.5 truncate text-13 text-muted" title={edge.library_file}>
        {edge.library_file}
      </div>
      {edge.state === "diveto" && edge.veto_reason && (
        <div className="mt-1 text-13 text-danger">alasan veto: {edge.veto_reason}</div>
      )}
      {edge.state !== "diveto" && (
        <div className="mt-3 border-t border-dashed border-border-muted pt-3">
          <div className="font-mono text-[10px] uppercase tracking-wide text-subtle">
            veto (isi alasan, lalu jalankan di terminal)
          </div>
          <pre className="mt-1 overflow-x-auto rounded-md bg-code-bg p-3 text-[12.5px] text-code-fg">
            {vetoCmd}
          </pre>
        </div>
      )}
    </Card>
  );
}

function DestinationsSection({ domains }: { domains: string[] }) {
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold">Arah domain (destination)</h2>
      <p className="mt-0.5 max-w-2xl text-13 text-muted">
        Satu-satunya keputusan yang <strong className="text-fg">tak bisa</strong> diserahkan
        ke mesin: &quot;mau jadi apa&quot;. Ditetapkan manusia sekali per domain — bukan per node.
      </p>
      {domains.length === 0 ? (
        <p className="mt-3 text-13 text-muted">Semua domain sudah punya destination.</p>
      ) : (
        <ul className="mt-3 grid gap-2">
          {domains.map((d) => (
            <li key={d}>
              <Card className="flex flex-wrap items-center justify-between gap-3 p-3.5">
                <div className="flex items-center gap-2">
                  <code className="font-mono text-sm font-semibold">{d}</code>
                  <Badge tone="warning" variant="outline">
                    tanpa destination
                  </Badge>
                </div>
                {/* ⚠ GAP (§7.6): set-destination belum punya endpoint. */}
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled
                    title="Butuh kapabilitas backend baru: PUT /domains/{id}/destination"
                  >
                    Tetapkan destination
                  </Button>
                  <span className="font-mono text-[10px] text-subtle" aria-hidden="true">
                    pending · butuh endpoint baru
                  </span>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
