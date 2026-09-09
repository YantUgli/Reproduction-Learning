"use client";

import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AuthoringJob,
  type AuthoringJobDetail,
  type Hypothesis,
  type IntegrationStatus,
  type JobRole,
  type NodeSummary,
} from "../../../lib/api";
import Container from "../../components/ui/Container";
import PageHeader from "../../components/ui/PageHeader";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";
import Badge, { type BadgeTone } from "../../components/ui/Badge";
import { IconCheck, IconX } from "../../components/ui/Icon";
import AuthoringNav from "../AuthoringNav";

/**
 * AI queue (M5, sekunder) — picu peran Claude Code lalu, saat `CLAUDE_AUTO_PROMOTE=0`,
 * approve/reject artifact.
 *
 * Sejak 2026-08-31 approve BUKAN gerbang blokir default: gerbang mesin (triad, probe
 * dieksekusi, kutipan verbatim) + promosi otomatis yang memutuskan. Halaman ini tetap
 * ada karena `CLAUDE_AUTO_PROMOTE=0` mengembalikan alur berhenti-di-`ready`.
 *
 * Bukan halaman untuk Bryant — ini meja kerja Isyah (§4).
 */
export default function AuthoringQueuePage() {
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

  // Reason kini lewat field in-UI (brief §7.7 / §9.1): `window.prompt` mentah memutus
  // konsistensi & suara antarmuka.
  const reject = async (id: string, reason: string) => {
    setError(null);
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
        title="Authoring · AI queue"
        subtitle="AI mengUSULkan; gerbang MESIN yang memutuskan. Approve manusia di sini hanya berlaku saat CLAUDE_AUTO_PROMOTE=0 — jika tidak, artifact yang lolos gerbang dipromosikan otomatis."
        back={null}
      />
      <AuthoringNav />

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
          onReject={(reason) => reject(selected.id, reason)}
        />
      )}

      <HypothesisTable rows={hypotheses} />
    </Container>
  );
}

function StatusBar({ status }: { status: IntegrationStatus }) {
  return (
    <Card className={`grid gap-2 p-4 text-13 ${status.enabled ? "" : "border-l-4 border-l-warning"}`}>
      <div>
        Integrasi:{" "}
        <strong className={status.enabled ? "text-success" : "text-warning"}>
          {status.enabled ? "aktif" : "dimatikan (kill switch)"}
        </strong>{" "}
        · CLI {status.cli_available ? "terdeteksi" : "tidak ditemukan"} ·{" "}
        {Object.entries(status.counts)
          .map(([k, v]) => `${k}: ${v}`)
          .join(" · ") || "belum ada job"}
      </div>
      {!status.enabled && (
        <div className="text-muted">
          Integrasi mati — pemicu di bawah dinonaktifkan. <strong className="text-fg">Loop inti
          Bryant tetap jalan penuh tanpa ini</strong> (PRD §10: AI akselerator, bukan fondasi).
        </div>
      )}
      {/* "Never does" — kejujuran yang membuat integrasi AI ini bisa diterima (§7.7). */}
      <div className="rounded-md border border-border-muted bg-surface-muted px-3 py-2">
        <span className="font-mono text-[11px] font-semibold uppercase tracking-wide text-subtle">
          Yang tak pernah dilakukan AI di sini
        </span>
        <ul className="mt-1 grid gap-0.5">
          {status.never_does.map((n) => (
            <li key={n} className="text-muted">
              · {n}
            </li>
          ))}
        </ul>
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

  // L4 — kelahiran node dari peta Library (R4 mode `node`).
  const [nf, setNf] = useState({
    library_file: "",
    slug: "",
    domain_id: "",
    concept: "",
    source_ref_id: "",
    prereq_node_id: "",
  });
  const nodeReady =
    nf.library_file && nf.slug && nf.domain_id && nf.concept && nf.source_ref_id;

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
          <p className="text-13 text-muted">
            R3 hanya bisa dipicu untuk node yang{" "}
            <strong className="font-semibold text-fg">punya attempt gagal</strong> — materi
            lahir dari kegagalan nyata, bukan dibaca lebih dulu.
          </p>
        </div>

        {/* node (L4) — dari peta Library */}
        <div className="grid gap-2 border-t border-border-muted pt-4">
          <label className="text-xs font-medium uppercase tracking-wide text-muted">
            Node baru dari peta Library (L4 · R4 mode node)
          </label>
          <div className="grid gap-2 sm:grid-cols-2">
            <input placeholder="library_file (mis. fastapi-produksi/01-.../x.md)" value={nf.library_file} onChange={(e) => setNf({ ...nf, library_file: e.target.value })} className={inputCls} />
            <input placeholder="slug (mis. query_params)" value={nf.slug} onChange={(e) => setNf({ ...nf, slug: e.target.value })} className={inputCls} />
            <input placeholder="domain_id (mis. fastapi)" value={nf.domain_id} onChange={(e) => setNf({ ...nf, domain_id: e.target.value })} className={inputCls} />
            <input placeholder="source_ref_id (mis. fastapi_docs_query)" value={nf.source_ref_id} onChange={(e) => setNf({ ...nf, source_ref_id: e.target.value })} className={inputCls} />
            <input placeholder="concept (judul manusia)" value={nf.concept} onChange={(e) => setNf({ ...nf, concept: e.target.value })} className={`${inputCls} sm:col-span-2`} />
            <input placeholder="prereq_node_id (opsional — edge SOFT)" value={nf.prereq_node_id} onChange={(e) => setNf({ ...nf, prereq_node_id: e.target.value })} className={`${inputCls} sm:col-span-2`} />
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              disabled={disabled || !nodeReady}
              onClick={() =>
                onTrigger(() =>
                  api.triggerNode({
                    library_file: nf.library_file,
                    slug: nf.slug,
                    domain_id: nf.domain_id,
                    concept: nf.concept,
                    source_ref_id: nf.source_ref_id,
                    prereq_node_id: nf.prereq_node_id || undefined,
                  }),
                )
              }
            >
              node · lahirkan node baru
            </Button>
            <p className="text-13 text-muted">
              Identitas (id, grader, probe id) ditetapkan server, bukan model; edge yang lahir
              selalu <code className="font-mono">soft</code>.
            </p>
          </div>
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

/** Ringkas request job jadi satu baris — beda per peran (node role tak punya node_id). */
function jobTarget(job: AuthoringJob): string {
  const r = job.request;
  if (job.role === "node") return String(r.slug ?? r.concept ?? r.library_file ?? "");
  return String(r.node_id ?? r.repo_path ?? "");
}

const ROLE_LABEL: Record<JobRole, string> = {
  r2: "R2",
  r3: "R3",
  r4: "R4",
  node: "NODE",
};

/** Titik status: berdenyut saat job masih bekerja di latar (pending/running). */
function StatusDot({ status }: { status: string }) {
  const color: Record<string, string> = {
    pending: "bg-subtle",
    running: "bg-accent",
    ready: "bg-success",
    failed: "bg-danger",
    approved: "bg-accent",
    rejected: "bg-warning",
  };
  const working = status === "pending" || status === "running";
  return (
    <span
      aria-hidden="true"
      className={`h-2.5 w-2.5 shrink-0 rounded-full ${color[status] ?? "bg-subtle"} ${
        working ? "animate-pulse" : ""
      }`}
    />
  );
}

/** Baris ringkas gerbang MESIN — check hijau kalau lolos, silang merah kalau gagal.
 *  Menampilkan HASIL gerbang yang sebenarnya (`gate.reason`), bukan daftar cek yang
 *  dikarang: gerbang backend memutuskan satu verdict per job, dan itu yang dijujurkan. */
function GateRow({ gate }: { gate: NonNullable<AuthoringJob["gate"]> }) {
  return (
    <div className="flex items-start gap-2 border-t border-border-muted bg-surface-muted px-3.5 py-2.5">
      <span
        className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${
          gate.passed ? "bg-success text-accent-fg" : "bg-danger text-accent-fg"
        }`}
        aria-hidden="true"
      >
        {gate.passed ? <IconCheck size={11} /> : <IconX size={11} />}
      </span>
      <div className="min-w-0 font-mono text-12">
        <span className={gate.passed ? "text-success" : "text-danger"}>
          {gate.passed ? "gerbang mesin lolos" : "gerbang mesin gagal"}
        </span>
        <span className="text-muted"> · {gate.reason}</span>
      </div>
    </div>
  );
}

function JobRow({ job, onOpen }: { job: AuthoringJob; onOpen: () => void }) {
  const working = job.status === "pending" || job.status === "running";
  return (
    <button onClick={onOpen} className="w-full text-left">
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <div className="flex items-center justify-between gap-3 p-3.5">
          <div className="flex min-w-0 items-center gap-3">
            <StatusDot status={job.status} />
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <strong>{ROLE_LABEL[job.role] ?? job.role}</strong>
                <span className="font-mono text-xs text-subtle">{job.id}</span>
              </div>
              <div className="truncate text-13 text-muted">
                {jobTarget(job) || "—"}
                {working && <span className="text-subtle"> · polling tiap 4s</span>}
                {job.error && !job.gate && (
                  <span className="text-danger"> · {job.error}</span>
                )}
              </div>
            </div>
          </div>
          <Badge tone={STATUS_TONE[job.status] ?? "neutral"}>{job.status}</Badge>
        </div>
        {job.gate && <GateRow gate={job.gate} />}
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
  onReject: (reason: string) => void;
}) {
  const reviewable = job.status === "ready";
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");

  return (
    <Card className="mt-6 p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold">
          {ROLE_LABEL[job.role] ?? job.role}
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
        <div className="mt-3 overflow-hidden rounded-md border border-border">
          <GateRow gate={job.gate} />
        </div>
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

      {rejecting ? (
        <div className="mt-4 grid gap-2 rounded-md border border-border bg-surface-muted p-3">
          <label htmlFor="reject-reason" className="text-13 font-semibold text-fg">
            Alasan menolak (tercatat di job.json)
          </label>
          <textarea
            id="reject-reason"
            autoFocus
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="mis. probe kedua duplikat pertanyaan node lain"
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm focus:border-accent focus:outline-none"
          />
          <div className="flex flex-wrap gap-2">
            <Button variant="danger" onClick={() => onReject(reason)}>
              Tolak job
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setRejecting(false)}>
              Batal
            </Button>
          </div>
        </div>
      ) : (
        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            variant="primary"
            onClick={onApprove}
            disabled={!reviewable}
            title={reviewable ? "" : "hanya job `ready` yang bisa masuk sistem"}
          >
            Approve → promosikan ke data/
          </Button>
          <Button
            variant="danger"
            onClick={() => setRejecting(true)}
            disabled={job.status === "approved"}
          >
            Tolak
          </Button>
        </div>
      )}
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
      <p className="mt-0.5 text-13 text-muted">
        Hipotesis <strong className="font-semibold text-fg">tidak pernah</strong> jadi
        verdict: berapa pun confidence-nya, statusnya hanya berubah lewat attempt
        reproduksi. Ia boleh mengusulkan urutan, tak boleh menyatakan mastery.
      </p>
      <Card className="mt-3 overflow-x-auto">
        <table className="w-full border-collapse text-13">
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
      className={`mt-3 rounded-md border px-4 py-2.5 text-13 ${
        tone === "ok" ? "border-success bg-success-bg text-success" : "border-danger bg-danger-bg text-danger"
      }`}
    >
      {children}
    </p>
  );
}
