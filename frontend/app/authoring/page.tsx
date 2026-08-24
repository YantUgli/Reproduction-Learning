"use client";

import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AuthoringJob,
  type AuthoringJobDetail,
  type Hypothesis,
  type IntegrationStatus,
  type NodeSummary,
} from "../../lib/api";
import Container from "../components/ui/Container";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import Badge, { type BadgeTone } from "../components/ui/Badge";

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
    <Container wide>
      <PageHeader
        title="Authoring · review artifact Claude Code"
        subtitle="AI mengUSULkan; kamu yang memutuskan. Tak ada artifact yang masuk sistem tanpa Approve di halaman ini."
      />

      {status && <StatusBar status={status} />}
      {note && <Banner tone="ok">{note}</Banner>}
      {error && <Banner tone="bad">{error}</Banner>}

      <TriggerPanel nodes={nodes} disabled={!status?.enabled} onTrigger={trigger} />

      <h2 className="mt-8 text-lg font-semibold">Antrean</h2>
      {!jobs && <p className="mt-2 text-muted">Memuat…</p>}
      {jobs?.length === 0 && (
        <p className="mt-2 text-muted">Belum ada job. Picu satu peran di atas.</p>
      )}
      <ul className="mt-3 grid gap-2">
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
    </Container>
  );
}

function StatusBar({ status }: { status: IntegrationStatus }) {
  return (
    <Card className="grid gap-1 p-4 text-[13px]">
      <div>
        Integrasi:{" "}
        <strong className={status.enabled ? "text-success" : "text-danger"}>
          {status.enabled ? "aktif" : "dimatikan"}
        </strong>{" "}
        · CLI {status.cli_available ? "terdeteksi" : "tidak ditemukan"} ·{" "}
        {Object.entries(status.counts)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ") || "belum ada job"}
      </div>
      <div className="text-muted">
        Yang tak pernah dilakukan AI di sini: {status.never_does.join(" · ")}.
      </div>
    </Card>
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

  const inputCls =
    "rounded-md border border-border bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none";

  return (
    <section className="mt-6">
      <h2 className="text-lg font-semibold">Picu peran</h2>

      <Card className="mt-3 grid gap-4 p-4">
        {/* R3 / R4 — per node */}
        <div className="grid gap-2">
          <label className="text-xs font-medium uppercase tracking-wide text-muted">
            Node sasaran (R3 · R4)
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={node}
              onChange={(e) => setNodeId(e.target.value)}
              className={`${inputCls} min-w-[280px] flex-1`}
            >
              {nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.id} · {n.concept}
                </option>
              ))}
            </select>
            <Button
              variant="secondary"
              disabled={disabled || !node}
              onClick={() => onTrigger(() => api.triggerR3({ node_id: node }))}
            >
              R3 · materi just-in-time
            </Button>
            <Button
              variant="secondary"
              disabled={disabled || !node}
              onClick={() => onTrigger(() => api.triggerR4({ node_id: node }))}
            >
              R4 · varian soal baru
            </Button>
          </div>
          <p className="text-[13px] text-muted">
            R3 hanya bisa dipicu untuk node yang{" "}
            <strong className="font-semibold text-fg">punya attempt gagal</strong> — materi
            lahir dari kegagalan nyata, bukan dibaca lebih dulu.
          </p>
        </div>

        {/* R2 — dari repo */}
        <div className="grid gap-2 border-t border-border-muted pt-4">
          <label className="text-xs font-medium uppercase tracking-wide text-muted">
            Repo untuk bukti codebase (R2)
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <input
              placeholder="path repo untuk R2 (mis. C:\project\repo-bryant)"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              className={`${inputCls} min-w-[340px] flex-1`}
            />
            <Button
              variant="secondary"
              disabled={disabled || !repoPath}
              onClick={() => onTrigger(() => api.triggerR2({ repo_path: repoPath }))}
            >
              R2 · bukti codebase (jadi hipotesis)
            </Button>
          </div>
        </div>
      </Card>
    </section>
  );
}

const STATUS_TONE: Record<string, BadgeTone> = {
  pending: "neutral",
  running: "info",
  ready: "success",
  failed: "danger",
  approved: "info",
  rejected: "warning",
};

function JobRow({ job, onOpen }: { job: AuthoringJob; onOpen: () => void }) {
  return (
    <button onClick={onOpen} className="w-full text-left">
      <Card className="grid gap-1.5 p-3.5 transition-shadow hover:shadow-md">
        <div className="flex items-center gap-2">
          <strong className="uppercase">{job.role}</strong>
          <Badge tone={STATUS_TONE[job.status] ?? "neutral"}>{job.status}</Badge>
          <span className="font-mono text-xs text-subtle">{job.id}</span>
        </div>
        <div className="text-[13px] text-muted">
          {String(job.request.node_id ?? job.request.repo_path ?? "")}
          {job.gate && !job.gate.passed && ` · gate: ${job.gate.reason}`}
          {job.error && ` · ${job.error}`}
        </div>
      </Card>
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
    <Card className="mt-6 p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          {job.role.toUpperCase()}
          <Badge tone={STATUS_TONE[job.status] ?? "neutral"}>{job.status}</Badge>
        </h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          tutup
        </Button>
      </div>
      <div className="mt-1 font-mono text-xs text-subtle">
        {job.id} · prompt {job.prompt_version} · percobaan {job.attempts}
      </div>

      {job.gate && (
        <p className={`mt-2 text-[13px] ${job.gate.passed ? "text-success" : "text-danger"}`}>
          Gate otomatis: {job.gate.reason}
        </p>
      )}
      {job.error && <Banner tone="bad">{job.error}</Banner>}

      {Object.entries(job.existing).length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer font-medium">
            Yang sudah ada di data/ (pembanding)
          </summary>
          {Object.entries(job.existing).map(([name, content]) => (
            <FileBlock key={name} name={name} content={content} />
          ))}
        </details>
      )}

      <h3 className="mb-1 mt-4 font-semibold">Artifact</h3>
      {Object.entries(job.files).map(([name, content]) => (
        <FileBlock key={name} name={name} content={content} />
      ))}

      <details className="mt-3">
        <summary className="cursor-pointer font-medium">Prompt yang dikirim</summary>
        <FileBlock name="prompt.md" content={job.prompt} />
      </details>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button
          variant="primary"
          onClick={onApprove}
          disabled={!reviewable}
          title={reviewable ? "" : "hanya job `ready` yang bisa masuk sistem"}
        >
          Approve → promosikan ke data/
        </Button>
        <Button variant="danger" onClick={onReject} disabled={job.status === "approved"}>
          Tolak
        </Button>
      </div>
    </Card>
  );
}

function FileBlock({ name, content }: { name: string; content: string }) {
  return (
    <div className="mt-2">
      <div className="font-mono text-xs text-subtle">{name}</div>
      <pre className="mt-1 max-h-[320px] overflow-x-auto rounded-md bg-code-bg p-3.5 text-[12.5px] text-code-fg">
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
    <section className="mt-10">
      <h2 className="text-lg font-semibold">Hipotesis codebase (R2)</h2>
      <p className="mt-0.5 text-[13px] text-muted">
        Hipotesis <strong className="font-semibold text-fg">tidak pernah</strong> jadi
        verdict: berapa pun confidence-nya, statusnya hanya berubah lewat attempt
        reproduksi. Ia boleh mengusulkan urutan, tak boleh menyatakan mastery.
      </p>
      <Card className="mt-3 overflow-x-auto">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="px-3 py-2 font-medium">node</th>
              <th className="px-3 py-2 font-medium">conf.</th>
              <th className="px-3 py-2 font-medium">status</th>
              <th className="px-3 py-2 font-medium">bukti</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <tr key={h.id} className="border-b border-border-muted last:border-0">
                <td className="px-3 py-2 font-mono">{h.node_id}</td>
                <td className="px-3 py-2 tabular-nums">{h.confidence.toFixed(2)}</td>
                <td className="px-3 py-2">{HYPOTHESIS_LABEL[h.status] ?? h.status}</td>
                <td className="px-3 py-2 font-mono text-xs">{h.evidence_locator}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </section>
  );
}

function Banner({ tone, children }: { tone: "ok" | "bad"; children: React.ReactNode }) {
  return (
    <p
      className={`mt-3 rounded-md border px-4 py-2.5 text-[13px] ${
        tone === "ok" ? "border-success bg-success-bg text-success" : "border-danger bg-danger-bg text-danger"
      }`}
    >
      {children}
    </p>
  );
}
