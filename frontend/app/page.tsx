"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type NodeStatus, type NodeSummary } from "../lib/api";

const STATUS_STYLE: Record<NodeStatus, { label: string; bg: string; fg: string }> = {
  locked: { label: "terkunci", bg: "#eaeef2", fg: "#57606a" },
  available: { label: "tersedia", bg: "#ddf4ff", fg: "#0969da" },
  acquired: { label: "acquired", bg: "#dafbe1", fg: "#1a7f37" },
  mastered: { label: "mastered", bg: "#fff8c5", fg: "#9a6700" },
  lapsed: { label: "lapsed", bg: "#ffebe9", fg: "#cf222e" },
};

export default function Dashboard() {
  const [nodes, setNodes] = useState<NodeSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listNodes().then(setNodes).catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ maxWidth: 780, margin: "0 auto" }}>
      <h1>Reproduction Learning Engine</h1>
      <p style={{ color: "#57606a" }}>
        Ukuran satu-satunya: <strong>reproduce-without-AI</strong>. Buka node,
        pudarkan scaffold, lalu buktikan kamu bisa memproduksinya dari nol.
      </p>

      {error && <p style={{ color: "#cf222e" }}>Gagal memuat: {error}</p>}
      {!nodes && !error && <p>Memuat…</p>}

      <ol style={{ listStyle: "none", padding: 0, display: "grid", gap: 10 }}>
        {nodes?.map((n) => {
          const s = STATUS_STYLE[n.status];
          const locked = n.status === "locked";
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
                  {n.id}
                </div>
                <div style={{ fontWeight: 600 }}>{n.concept}</div>
                <div style={{ fontSize: 13, color: "#57606a" }}>
                  ~{n.estimated_minutes} mnt · {n.grader_type}
                </div>
              </div>
              <span
                style={{
                  background: s.bg,
                  color: s.fg,
                  padding: "3px 10px",
                  borderRadius: 999,
                  fontSize: 13,
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                }}
              >
                {s.label}
              </span>
            </div>
          );
          return (
            <li key={n.id}>
              {locked ? (
                <div title="Terkunci sampai prasyarat (hard edge) acquired">{inner}</div>
              ) : (
                <Link href={`/node/${n.id}`} style={{ textDecoration: "none", color: "inherit" }}>
                  {inner}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </main>
  );
}
