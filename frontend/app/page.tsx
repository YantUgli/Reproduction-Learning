"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  api,
  type DueItem,
  type LibraryProgress,
  type NodeStat,
  type Stats,
} from "../lib/api";
import StatusBadge from "./components/StatusBadge";
import Card from "./components/ui/Card";
import Container from "./components/ui/Container";
import EmptyState from "./components/ui/EmptyState";
import ErrorState from "./components/ui/ErrorState";
import { KpiRowSkeleton } from "./components/ui/Skeleton";
import { IconArrowRight, IconInbox, IconLock } from "./components/ui/Icon";

/**
 * Dashboard penuh (M4): KPI inti · review jatuh tempo hari ini · peta progres.
 *
 * Peta progres adalah **DAFTAR LINEAR** (dikelompokkan per domain) — bukan graf/DAG
 * explorer. Itu bukan kekurangan yang menunggu diperbaiki; §8 PRD menyebut DAG visual
 * sebagai "versi builder dari avoidance trap". Yang ditutup produk ini jurang produksi,
 * bukan rasa puas melihat peta.
 */
export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [due, setDue] = useState<DueItem[] | null>(null);
  const [lib, setLib] = useState<LibraryProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    // KPI Library boleh kosong tanpa merobohkan dashboard: lajur Library adalah
    // pendamping, bukan sumber KPI inti (`/stats`).
    Promise.all([api.getStats(), api.listDue(), api.getLibraryProgress().catch(() => null)])
      .then(([s, d, l]) => {
        setStats(s);
        setDue(d);
        setLib(l);
      })
      .catch((e) => setError(String(e)));
  };

  useEffect(load, []);

  return (
    <Container>
      <header className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Reproduction Learning Engine</h1>
        <p className="mt-1 max-w-2xl text-muted">
          Ukuran satu-satunya: <strong className="font-semibold text-fg">reproduce-without-AI</strong>.
          Buka node, pudarkan scaffold, lalu buktikan kamu bisa memproduksinya dari nol.
        </p>
      </header>

      {error && <ErrorState error={error} onRetry={load} />}
      {!stats && !error && <KpiRowSkeleton />}

      {stats && (
        <>
          <KpiRow stats={stats} lib={lib} />
          <DueSection due={due ?? []} />
          <ProgressMap stats={stats} />
        </>
      )}
    </Container>
  );
}

/** KPI inti PRD §9: pass rate reproduce-without-AI & jumlah node mastered. */
function KpiRow({ stats, lib }: { stats: Stats; lib: LibraryProgress | null }) {
  const rate =
    stats.reproduce_pass_rate === null
      ? "—"
      : `${Math.round(stats.reproduce_pass_rate * 100)}%`;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Kpi
        label="reproduce-without-AI"
        value={rate}
        hint={`${stats.reproduce_passed}/${stats.reproduce_attempts} attempt tanpa bantuan`}
      />
      <Kpi
        label="mastered"
        value={`${stats.mastered_count}`}
        hint={`dari ${stats.total_nodes} node · butuh ${stats.successes_needed}× sukses berjarak`}
      />
      <Kpi
        label="jatuh tempo"
        value={`${stats.due_count}`}
        hint={stats.due_count > 0 ? "perlu direview hari ini" : "tak ada yang menunggu"}
      />
      {/* L5 — "% direproduksi", bukan "% dibaca". Satu angka saja di dashboard;
          daftar course-nya tinggal di /library (Forge yang harus terasa utama). */}
      <Kpi
        label="materi direproduksi"
        value={libPct(lib)}
        hint={
          lib && lib.total > 0
            ? `${lib.reproduced}/${lib.total} materi Library terbukti`
            : "library/ kosong"
        }
      />
    </div>
  );
}

/** Sama seperti di /library: jangan pernah menampilkan 100% selama masih ada materi
 *  yang belum terbukti — pembulatan yang berbohong ke atas adalah persis jenis
 *  kenyamanan yang lajur ini dibangun untuk melawan. */
function libPct(lib: LibraryProgress | null): string {
  if (!lib || lib.reproduced_pct === null) return "—";
  let p = Math.round(lib.reproduced_pct * 100);
  if (lib.reproduced < lib.total && p >= 100) p = 99;
  if (lib.reproduced > 0 && p <= 0) p = 1;
  return `${p}%`;
}

function Kpi({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <Card className="p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-0.5 text-3xl font-bold leading-tight tabular-nums">{value}</div>
      <div className="mt-0.5 text-xs text-muted">{hint}</div>
    </Card>
  );
}

function DueSection({ due }: { due: DueItem[] }) {
  return (
    <section className="mt-8">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-lg font-semibold">Review jatuh tempo hari ini</h2>
        <span className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <Link href="/placement" className="inline-flex items-center gap-1 text-accent hover:underline">
            Jalankan placement <IconArrowRight size={14} />
          </Link>
          <Link href="/library" className="inline-flex items-center gap-1 text-accent hover:underline">
            Library <IconArrowRight size={14} />
          </Link>
          {/* Role bleed dihapus (brief §4): tautan "Review authoring" adalah meja
              Isyah, bukan jalur Bryant. Authoring kini hidup di frame area-switch
              (§5), dan disembunyikan saat kill switch mati. */}
        </span>
      </div>

      {due.length === 0 ? (
        <div className="mt-3">
          <EmptyState
            icon={<IconInbox />}
            title="Tak ada yang jatuh tempo"
          >
            Ambil node <code className="rounded bg-neutral-bg px-1 py-0.5 font-mono text-[0.85em]">tersedia</code> di
            bawah, atau jalankan placement kalau belum pernah menemukan lantai awal.
          </EmptyState>
        </div>
      ) : (
        <ul className="mt-3 grid gap-2">
          {due.map((d) => (
            <li key={d.node_id}>
              <Link href={`/review?node=${d.node_id}`} className="block">
                <Card className="flex items-center justify-between gap-3 border-l-4 border-l-warning p-3 transition-shadow hover:shadow-md">
                  <div>
                    <div className="font-semibold">{d.concept}</div>
                    <div className="text-13 text-muted">
                      telat {d.overdue_days.toFixed(1)} hari · sukses berjarak{" "}
                      {d.consecutive_success}/{d.successes_needed}
                    </div>
                  </div>
                  <StatusBadge status={d.status} />
                </Card>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

const DOMAINS: { prefix: string; label: string }[] = [
  { prefix: "n", label: "FastAPI" },
  { prefix: "r", label: "React" },
  { prefix: "m", label: "ML" },
];

function domainOf(nodeId: string): string {
  return DOMAINS.find((d) => nodeId.startsWith(d.prefix))?.label ?? "Lainnya";
}

function ProgressMap({ stats }: { stats: Stats }) {
  // Kelompokkan per domain, urut FastAPI → React → ML, pertahankan urutan dalam grup.
  const order = [...DOMAINS.map((d) => d.label), "Lainnya"];
  const groups = new Map<string, NodeStat[]>();
  for (const n of stats.nodes) {
    const key = domainOf(n.node_id);
    (groups.get(key) ?? groups.set(key, []).get(key)!).push(n);
  }

  // "Berikutnya" = node tersedia pertama yang belum tersentuh. Sistem sudah tahu ke
  // mana user harus melangkah; sebelumnya tak ada satu pun afordansi yang menunjukkannya.
  const nextNode =
    stats.nodes.find((n) => n.status === "available" && n.attempts === 0)?.node_id ??
    stats.nodes.find((n) => n.status === "available")?.node_id ??
    null;

  return (
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Peta progres</h2>
      {stats.placement_floor_node_id && (
        <p className="mt-0.5 text-13 text-muted">
          Lantai dari placement terakhir:{" "}
          <code className="font-mono">{stats.placement_floor_node_id}</code>
        </p>
      )}
      {order
        .filter((label) => groups.has(label))
        .map((label) => (
          <div key={label} className="mt-6">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-subtle">
              {label}
            </h3>
            <ol className="grid gap-2">
              {groups.get(label)!.map((n) => (
                <li key={n.node_id}>
                  {n.status === "locked" ? (
                    <LockedRow node={n} />
                  ) : (
                    <NodeRow
                      node={n}
                      successesNeeded={stats.successes_needed}
                      isNext={n.node_id === nextNode}
                    />
                  )}
                </li>
              ))}
            </ol>
          </div>
        ))}
    </section>
  );
}

/** Node terkunci: baris rapat satu-baris, bukan Card penuh. Menghemat berat visual
 *  (mayoritas layar terkunci) & memberi penjelasan yang TERLIHAT, bukan tooltip hover
 *  (yang tak terjangkau keyboard/sentuh). */
function LockedRow({ node }: { node: NodeStat }) {
  return (
    <div className="flex items-center gap-2.5 rounded-md border border-border-muted bg-surface-muted px-4 py-2.5">
      <IconLock className="shrink-0 text-fg-disabled" />
      <div className="min-w-0 flex-1">
        <span className="text-sm font-medium text-fg-disabled">{node.concept}</span>
        <span className="ml-2 text-13 text-fg-disabled">
          terkunci — selesaikan prasyaratnya dulu
        </span>
      </div>
    </div>
  );
}

function NodeRow({
  node,
  successesNeeded,
  isNext,
}: {
  node: NodeStat;
  successesNeeded: number;
  isNext: boolean;
}) {
  // Tampilkan metadata HANYA bila bermakna — jangan ulang "belum diuji · 0/4" 19×
  // (noise yang menenggelamkan baris yang benar-benar punya progres).
  const hasSignal = node.attempts > 0 || node.consecutive_success > 0 || node.is_due;
  const rate = node.pass_rate === null ? null : `${Math.round(node.pass_rate * 100)}%`;

  const href = node.is_due ? `/review?node=${node.node_id}` : `/node/${node.node_id}`;
  return (
    <Link href={href} className="block">
      <Card
        className={`flex items-center justify-between gap-3 p-4 transition-shadow hover:shadow-md ${
          isNext ? "border-l-4 border-l-accent" : ""
        }`}
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{node.concept}</span>
            {isNext && (
              <span className="inline-flex items-center gap-1 rounded-full bg-info-bg px-2 py-0.5 text-xs font-semibold text-info">
                Mulai di sini <IconArrowRight size={12} />
              </span>
            )}
          </div>
          <div className="mt-0.5 font-mono text-xs text-subtle">{node.node_id}</div>
          {hasSignal && (
            <div className="mt-0.5 text-13 text-muted">
              {rate && (
                <>
                  pass rate {rate}
                  {node.attempts > 0 && ` (${node.passed}/${node.attempts})`} ·{" "}
                </>
              )}
              sukses berjarak {node.consecutive_success}/{successesNeeded}
              {node.due_at && ` · due ${new Date(node.due_at).toLocaleDateString()}`}
            </div>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {node.is_due && <span className="text-13 font-semibold text-warning">due</span>}
          <StatusBadge status={node.status} />
        </div>
      </Card>
    </Link>
  );
}
