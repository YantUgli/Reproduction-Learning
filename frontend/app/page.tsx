"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type DueItem, type NodeStat, type Stats } from "../lib/api";
import StatusBadge from "./components/StatusBadge";
import Card from "./components/ui/Card";
import Container from "./components/ui/Container";
import EmptyState from "./components/ui/EmptyState";
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getStats(), api.listDue()])
      .then(([s, d]) => {
        setStats(s);
        setDue(d);
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <Container>
      <header className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Reproduction Learning Engine</h1>
        <p className="mt-1 max-w-2xl text-muted">
          Ukuran satu-satunya: <strong className="font-semibold text-fg">reproduce-without-AI</strong>.
          Buka node, pudarkan scaffold, lalu buktikan kamu bisa memproduksinya dari nol.
        </p>
      </header>

      {error && (
        <p className="rounded-md border border-danger bg-danger-bg px-4 py-3 text-danger">
          Gagal memuat: {error}
        </p>
      )}
      {!stats && !error && <p className="text-muted">Memuat…</p>}

      {stats && (
        <>
          <KpiRow stats={stats} />
          <DueSection due={due ?? []} />
          <ProgressMap stats={stats} />
        </>
      )}
    </Container>
  );
}

/** KPI inti PRD §9: pass rate reproduce-without-AI & jumlah node mastered. */
function KpiRow({ stats }: { stats: Stats }) {
  const rate =
    stats.reproduce_pass_rate === null
      ? "—"
      : `${Math.round(stats.reproduce_pass_rate * 100)}%`;
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
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
    </div>
  );
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
          {/* Meja kerja Isyah (M5), bukan jalur belajar Bryant. */}
          <Link href="/authoring" className="inline-flex items-center gap-1 text-accent hover:underline">
            Review authoring <IconArrowRight size={14} />
          </Link>
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
                    <div className="text-[13px] text-muted">
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

  return (
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Peta progres</h2>
      {stats.placement_floor_node_id && (
        <p className="mt-0.5 text-[13px] text-muted">
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
            <ol className="grid gap-2.5">
              {groups.get(label)!.map((n) => (
                <li key={n.node_id}>
                  <NodeRow node={n} successesNeeded={stats.successes_needed} />
                </li>
              ))}
            </ol>
          </div>
        ))}
    </section>
  );
}

function NodeRow({ node, successesNeeded }: { node: NodeStat; successesNeeded: number }) {
  const locked = node.status === "locked";
  const rate = node.pass_rate === null ? "belum diuji" : `${Math.round(node.pass_rate * 100)}%`;

  const inner = (
    <Card
      className={`flex items-center justify-between gap-3 p-4 ${
        locked ? "bg-surface-muted opacity-70" : "transition-shadow hover:shadow-md"
      }`}
    >
      <div className="min-w-0">
        <div className="font-mono text-xs text-subtle">{node.node_id}</div>
        <div className="font-semibold">{node.concept}</div>
        <div className="text-[13px] text-muted">
          pass rate {rate}
          {node.attempts > 0 && ` (${node.passed}/${node.attempts})`} · sukses berjarak{" "}
          {node.consecutive_success}/{successesNeeded}
          {node.due_at && ` · due ${new Date(node.due_at).toLocaleDateString()}`}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {node.is_due && <span className="text-[13px] font-semibold text-warning">due</span>}
        {locked && <IconLock className="text-subtle" />}
        <StatusBadge status={node.status} />
      </div>
    </Card>
  );

  if (locked) {
    return <div title="Terkunci sampai prasyarat (hard edge) terbukti">{inner}</div>;
  }
  const href = node.is_due ? `/review?node=${node.node_id}` : `/node/${node.node_id}`;
  return (
    <Link href={href} className="block">
      {inner}
    </Link>
  );
}
