"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AuthoringJob,
  type AuthoringJobDetail,
  type Hypothesis,
  type IntegrationStatus,
  type NodeSummary,
} from "../../lib/api";

/**
 * Review authoring (M5) — antrean artifact Claude Code menunggu keputusan Isyah.
 *
 * Halaman ini adalah **gerbang manusia**, lapis terakhir setelah skema & gate
 * otomatis. Tak ada artifact yang masuk `data/`/DB tanpa tombol Approve di sini.
 * Yang di-review adalah KONTEN; format sudah dijamin backend (`contracts.py`).
 *
 * Bukan halaman untuk Bryant — ini meja kerja Isyah.
 */
export default function AuthoringPage() {
  const [status, setStatus] = useState<IntegrationStatus | null>(null);
  const [jobs, setJobs] = useState<AuthoringJob[] | null>(null);
  const [nodes, setNodes] = useState<NodeSummary[]>([]);
  const [selected, setSelected] = useState<AuthoringJobDetail | null>(null);
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, j, h] = await Promise.all([
        api.getIntegrationStatus(),
        api.listJobs(),
        api.listHypotheses(),
      ]);
      setStatus(s);
      setJobs(j);
      setHypotheses(h);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    api.listNodes().then(setNodes).catch(() => undefined);
  }, [refresh]);

  // Job `pending`/`running` berubah di latar (Claude Code masih jalan) — polling
  // ringan supaya antrean tak perlu di-refresh manual.
  useEffect(() => {
    const working = jobs?.some((j) => j.status === "pending" || j.status === "running");
    if (!working) return;
    const t = setTimeout(refresh, 4000);
    return () => clearTimeout(t);
  }, [jobs, refresh]);

  const open = async (id: string) => {
    setNote(null);
    try {
      setSelected(await api.getJob(id));
    } catch (e) {
      setError(String(e));
    }
  };

  const trigger = async (fn: () => Promise<AuthoringJob>) => {
    setError(null);
    setNote(null);
    try {
      const job = await fn();
      setNote(`Job ${job.id} dibuat — Claude Code jalan di latar.`);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const approve = async (id: string) => {
    setError(null);
    try {
      const out = await api.approveJob(id);
      setNote(
        out.written_paths.length
          ? `Approved. File ditulis: ${out.written_paths.join(", ")}`
          : `Approved. Efek DB: ${JSON.stringify(out.db_effect)}`,
      );
      setSelected(null);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  const reject = async (id: string) => {
    const reason = window.prompt("Alasan menolak (tercatat di job.json):") ?? "";
    try {
      await api.rejectJob(id, reason);
      setSelected(null);
      refresh();
    } catch (e) {
      setError(String(e));
    }
  };

  return (
    <main style={{ maxWidth: 980, margin: "0 auto" }}>
      <p>
        <Link href="/">← Dashboard</Link>
      </p>
      <h1 style={{ marginBottom: 4 }}>Authoring · review artifact Claude Code</h1>
      <p style={{ color: "#57606a", marginTop: 0 }}>
        AI mengUSULkan; kamu yang memutuskan. Tak ada artifact yang masuk sistem tanpa
        Approve di halaman ini.
      </p>

      {status && <StatusBar status={status} />}
      {note && <Banner tone="ok">{note}</Banner>}
      {error && <Banner tone="bad">{error}</Banner>}

      <TriggerPanel nodes={nodes} disabled={!status?.enabled} onTrigger={trigger} />

      <h2 style={{ marginTop: 28 }}>Antrean</h2>
      {!jobs && <p>Memuat…</p>}
      {jobs?.length === 0 && (
        <p style={{ color: "#57606a" }}>Belum ada job. Picu satu peran di atas.</p>
      )}
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: 8 }}>
        {jobs?.map((job) => (
          <li key={job.id}>
            <JobRow job={job} onOpen={() => open(job.id)} />
          </li>
        ))}
      </ul>

      {selected && (
        <JobPanel
          job={selected}
          onClose={() => setSelected(null)}
          onApprove={() => approve(selected.id)}
          onReject={() => reject(selected.id)}
        />
      )}

      <HypothesisTable rows={hypotheses} />
    </main>
  );
}

function StatusBar({ status }: { status: IntegrationStatus }) {
  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: 8,
        padding: "0.7rem 1rem",
        fontSize: 13,
        display: "grid",
        gap: 4,
      }}
    >
      <div>
        Integrasi:{" "}
        <strong style={{ color: status.enabled ? "#1a7f37" : "#cf222e" }}>
          {status.enabled ? "aktif" : "dimatikan"}
        </strong>{" "}
        · CLI {status.cli_available ? "terdeteksi" : "tidak ditemukan"} ·{" "}
        {Object.entries(status.counts)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ") || "belum ada job"}
      </div>
      <div style={{ color: "#57606a" }}>
        Yang tak pernah dilakukan AI di sini: {status.never_does.join(" · ")}.
      </div>
    </div>
  );
}

function TriggerPanel({
  nodes,
  disabled,
  onTrigger,
}: {
  nodes: NodeSummary[];
  disabled: boolean;
  onTrigger: (fn: () => Promise<AuthoringJob>) => void;
}) {
  const [nodeId, setNodeId] = useState("");
  const [repoPath, setRepoPath] = useState("");
  const node = nodeId || nodes[0]?.id || "";

  return (
    <section style={{ marginTop: 20, display: "grid", gap: 10 }}>
      <h2 style={{ margin: 0 }}>Picu peran</h2>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <select value={node} onChange={(e) => setNodeId(e.target.value)} style={{ padding: 6 }}>
          {nodes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.id} · {n.concept}
            </option>
          ))}
        </select>
        <button disabled={disabled || !node} onClick={() => onTrigger(() => api.triggerR3({ node_id: node }))}>
          R3 · materi just-in-time
        </button>
        <button disabled={disabled || !node} onClick={() => onTrigger(() => api.triggerR4({ node_id: node }))}>
          R4 · varian soal baru
        </button>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <input
          placeholder="path repo untuk R2 (mis. C:\\project\\repo-bryant)"
          value={repoPath}
          onChange={(e) => setRepoPath(e.target.value)}
          style={{ padding: 6, minWidth: 340 }}
        />
        <button
          disabled={disabled || !repoPath}
          onClick={() => onTrigger(() => api.triggerR2({ repo_path: repoPath }))}
        >
          R2 · bukti codebase (jadi hipotesis)
        </button>
      </div>
      <p style={{ color: "#57606a", fontSize: 13, margin: 0 }}>
        R3 hanya bisa dipicu untuk node yang <strong>punya attempt gagal</strong> — materi
        lahir dari kegagalan nyata, bukan dibaca lebih dulu.
      </p>
    </section>
  );
}

const STATUS_COLOR: Record<string, string> = {
  pending: "#57606a",
  running: "#0969da",
  ready: "#1a7f37",
  failed: "#cf222e",
  approved: "#8250df",
  rejected: "#9a6700",
};

function JobRow({ job, onOpen }: { job: AuthoringJob; onOpen: () => void }) {
  return (
    <button
      onClick={onOpen}
      style={{
        width: "100%",
        textAlign: "left",
        padding: "0.6rem 0.9rem",
        display: "grid",
        gap: 2,
      }}
    >
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <strong style={{ textTransform: "uppercase" }}>{job.role}</strong>
        <span style={{ color: STATUS_COLOR[job.status], fontWeight: 600 }}>{job.status}</span>
        <span style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>{job.id}</span>
      </div>
      <div style={{ fontSize: 13, color: "#57606a" }}>
        {String(job.request.node_id ?? job.request.repo_path ?? "")}
        {job.gate && !job.gate.passed && ` · gate: ${job.gate.reason}`}
        {job.error && ` · ${job.error}`}
      </div>
    </button>
  );
}

function JobPanel({
  job,
  onClose,
  onApprove,
  onReject,
}: {
  job: AuthoringJobDetail;
  onClose: () => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  const reviewable = job.status === "ready";
  return (
    <section
      style={{
        marginTop: 20,
        border: "1px solid #d0d7de",
        borderRadius: 8,
        padding: "1rem 1.25rem",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>
          {job.role.toUpperCase()} · <span style={{ color: STATUS_COLOR[job.status] }}>{job.status}</span>
        </h2>
        <button onClick={onClose}>tutup</button>
      </div>
      <div style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>
        {job.id} · prompt {job.prompt_version} · percobaan {job.attempts}
      </div>

      {job.gate && (
        <p style={{ color: job.gate.passed ? "#1a7f37" : "#cf222e", fontSize: 13 }}>
          Gate otomatis: {job.gate.reason}
        </p>
      )}
      {job.error && <Banner tone="bad">{job.error}</Banner>}

      {Object.entries(job.existing).length > 0 && (
        <details style={{ marginTop: 8 }}>
          <summary>Yang sudah ada di data/ (pembanding)</summary>
          {Object.entries(job.existing).map(([name, content]) => (
            <FileBlock key={name} name={name} content={content} />
          ))}
        </details>
      )}

      <h3 style={{ marginBottom: 4 }}>Artifact</h3>
      {Object.entries(job.files).map(([name, content]) => (
        <FileBlock key={name} name={name} content={content} />
      ))}

      <details style={{ marginTop: 8 }}>
        <summary>Prompt yang dikirim</summary>
        <FileBlock name="prompt.md" content={job.prompt} />
      </details>

      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button
          onClick={onApprove}
          disabled={!reviewable}
          title={reviewable ? "" : "hanya job `ready` yang bisa masuk sistem"}
          style={{ padding: "0.5rem 1rem", fontWeight: 600 }}
        >
          Approve → promosikan ke data/
        </button>
        <button onClick={onReject} disabled={job.status === "approved"} style={{ padding: "0.5rem 1rem" }}>
          Tolak
        </button>
      </div>
    </section>
  );
}

function FileBlock({ name, content }: { name: string; content: string }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontFamily: "monospace", fontSize: 12, color: "#57606a" }}>{name}</div>
      <pre
        style={{
          background: "#0d1117",
          color: "#e6edf3",
          padding: "0.7rem 0.9rem",
          borderRadius: 8,
          overflowX: "auto",
          fontSize: 12.5,
          maxHeight: 320,
        }}
      >
        {content}
      </pre>
    </div>
  );
}

const HYPOTHESIS_LABEL: Record<string, string> = {
  unverified: "belum diverifikasi",
  confirmed_by_attempt: "dikonfirmasi eksekusi",
  refuted_by_attempt: "dibantah eksekusi",
};

function HypothesisTable({ rows }: { rows: Hypothesis[] }) {
  if (rows.length === 0) return null;
  return (
    <section style={{ marginTop: 28 }}>
      <h2 style={{ marginBottom: 4 }}>Hipotesis codebase (R2)</h2>
      <p style={{ color: "#57606a", marginTop: 0, fontSize: 13 }}>
        Hipotesis <strong>tidak pernah</strong> jadi verdict: berapa pun confidence-nya,
        statusnya hanya berubah lewat attempt reproduksi. Ia boleh mengusulkan urutan,
        tak boleh menyatakan mastery.
      </p>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #d0d7de" }}>
            <th style={{ padding: "6px 4px" }}>node</th>
            <th style={{ padding: "6px 4px" }}>conf.</th>
            <th style={{ padding: "6px 4px" }}>status</th>
            <th style={{ padding: "6px 4px" }}>bukti</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((h) => (
            <tr key={h.id} style={{ borderBottom: "1px solid #eaeef2" }}>
              <td style={{ padding: "6px 4px", fontFamily: "monospace" }}>{h.node_id}</td>
              <td style={{ padding: "6px 4px" }}>{h.confidence.toFixed(2)}</td>
              <td style={{ padding: "6px 4px" }}>{HYPOTHESIS_LABEL[h.status] ?? h.status}</td>
              <td style={{ padding: "6px 4px", fontFamily: "monospace", fontSize: 12 }}>
                {h.evidence_locator}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Banner({ tone, children }: { tone: "ok" | "bad"; children: React.ReactNode }) {
  return (
    <p
      style={{
        marginTop: 12,
        padding: "0.6rem 0.9rem",
        borderRadius: 8,
        background: tone === "ok" ? "#dafbe1" : "#ffebe9",
        border: `1px solid ${tone === "ok" ? "#1a7f37" : "#cf222e"}`,
        fontSize: 13,
      }}
    >
      {children}
    </p>
  );
}
