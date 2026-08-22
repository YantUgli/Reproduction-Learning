"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type DueItem, type NodeStat, type Stats } from "../lib/api";
import StatusBadge from "./components/StatusBadge";

/**
 * Dashboard penuh (M4): KPI inti · review jatuh tempo hari ini · peta progres.
 *
 * Peta progres adalah **DAFTAR LINEAR** — bukan graf/DAG explorer. Itu bukan
 * kekurangan yang menunggu diperbaiki; §8 PRD menyebut DAG visual sebagai "versi
 * builder dari avoidance trap". Yang ditutup produk ini jurang produksi, bukan rasa
 * puas melihat peta.
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
    <main style={{ maxWidth: 820, margin: "0 auto" }}>
      <h1 style={{ marginBottom: 4 }}>Reproduction Learning Engine</h1>
      <p style={{ color: "#57606a", marginTop: 0 }}>
        Ukuran satu-satunya: <strong>reproduce-without-AI</strong>. Buka node,
        pudarkan scaffold, lalu buktikan kamu bisa memproduksinya dari nol.
      </p>

      {error && <p style={{ color: "#cf222e" }}>Gagal memuat: {error}</p>}
      {!stats && !error && <p>Memuat…</p>}

      {stats && (
        <>
          <KpiRow stats={stats} />
          <DueSection due={due ?? []} />
          <ProgressMap stats={stats} />
        </>
      )}
    </main>
  );
}

/** KPI inti PRD §9: pass rate reproduce-without-AI & jumlah node mastered. */
function KpiRow({ stats }: { stats: Stats }) {
  const rate =
    stats.reproduce_pass_rate === null
      ? "—"
      : `${Math.round(stats.reproduce_pass_rate * 100)}%`;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
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
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: 8,
        padding: "0.75rem 1rem",
        background: "#fff",
      }}
    >
      <div style={{ fontSize: 12, textTransform: "uppercase", color: "#57606a" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, lineHeight: 1.2 }}>{value}</div>
      <div style={{ fontSize: 12, color: "#57606a" }}>{hint}</div>
    </div>
  );
}

function DueSection({ due }: { due: DueItem[] }) {
  return (
    <section style={{ marginTop: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h2 style={{ fontSize: 18 }}>Review jatuh tempo hari ini</h2>
        <span style={{ display: "flex", gap: 14 }}>
          <Link href="/placement">Jalankan placement →</Link>
          {/* Meja kerja Isyah (M5), bukan jalur belajar Bryant. */}
          <Link href="/authoring">Review authoring →</Link>
        </span>
      </div>

      {due.length === 0 ? (
        <p style={{ color: "#57606a" }}>
          Tak ada yang jatuh tempo. Ambil node <code>tersedia</code> di bawah, atau
          jalankan placement kalau belum pernah menemukan lantai awal.
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
          {due.map((d) => (
            <li key={d.node_id}>
              <Link
                href={`/review?node=${d.node_id}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    border: "1px solid #d0d7de",
                    borderLeft: "4px solid #9a6700",
                    borderRadius: 8,
                    padding: "0.7rem 1rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    background: "#fff",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{d.concept}</div>
                    <div style={{ fontSize: 13, color: "#57606a" }}>
                      telat {d.overdue_days.toFixed(1)} hari · sukses berjarak{" "}
                      {d.consecutive_success}/{d.successes_needed}
                    </div>
                  </div>
                  <StatusBadge status={d.status} />
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function ProgressMap({ stats }: { stats: Stats }) {
  return (
    <section style={{ marginTop: 28 }}>
      <h2 style={{ fontSize: 18 }}>Peta progres</h2>
      {stats.placement_floor_node_id && (
        <p style={{ fontSize: 13, color: "#57606a" }}>
          Lantai dari placement terakhir: <code>{stats.placement_floor_node_id}</code>
        </p>
      )}
      <ol style={{ listStyle: "none", padding: 0, display: "grid", gap: 10 }}>
        {stats.nodes.map((n) => (
          <li key={n.node_id}>
            <NodeRow node={n} successesNeeded={stats.successes_needed} />
          </li>
        ))}
      </ol>
    </section>
  );
}

function NodeRow({ node, successesNeeded }: { node: NodeStat; successesNeeded: number }) {
  const locked = node.status === "locked";
  const rate = node.pass_rate === null ? "belum diuji" : `${Math.round(node.pass_rate * 100)}%`;

  const inner = (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: 8,
        padding: "0.85rem 1rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        background: locked ? "#f6f8fa" : "#fff",
        opacity: locked ? 0.7 : 1,
      }}
    >
      <div>
        <div style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>
          {node.node_id}
        </div>
        <div style={{ fontWeight: 600 }}>{node.concept}</div>
        <div style={{ fontSize: 13, color: "#57606a" }}>
          pass rate {rate}
          {node.attempts > 0 && ` (${node.passed}/${node.attempts})`} · sukses berjarak{" "}
          {node.consecutive_success}/{successesNeeded}
          {node.due_at && ` · due ${new Date(node.due_at).toLocaleDateString()}`}
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        {node.is_due && (
          <span style={{ fontSize: 13, fontWeight: 600, color: "#9a6700" }}>due</span>
        )}
        <StatusBadge status={node.status} />
      </div>
    </div>
  );

  if (locked) {
    return <div title="Terkunci sampai prasyarat (hard edge) terbukti">{inner}</div>;
  }
  const href = node.is_due ? `/review?node=${node.node_id}` : `/node/${node.node_id}`;
  return (
    <Link href={href} style={{ textDecoration: "none", color: "inherit" }}>
      {inner}
    </Link>
  );
}
