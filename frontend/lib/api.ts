// Klien tipis ke backend FastAPI. State server via fetch (v1, tanpa state mgmt berat).

export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type NodeStatus = "locked" | "available" | "acquired" | "mastered" | "lapsed";

export interface NodeSummary {
  id: string;
  concept: string;
  description: string;
  grader_type: string;
  estimated_minutes: number;
  timebox_seconds: number;
  status: NodeStatus;
}

export interface NodeDetail extends NodeSummary {
  levels: string[];
}

export interface LevelView {
  level: string;
  kind: "worked_example" | "faded" | "signature" | "verify";
  title: string;
  prompt: string;
  code: string;
  signature_contract: string;
  instance_id: string;
  editable: boolean;
  show_timebox: boolean;
  timebox_seconds: number;
  /** Mode highlight editor — diturunkan backend dari berkas node (M6). */
  language: string;
}

export interface SubmitOut {
  attempt_id: number;
  passed: boolean;
  result: string;
  test_output: string;
  timed_out: boolean;
  duration_seconds: number;
  mode: string;
  scaffold_level: string;
}

export interface Probe {
  id: string;
  node_id: string;
  type: string;
  question: string;
  options: string[];
}

export interface ProbeAnswerOut {
  probe_correct: boolean;
  acquired: boolean;
  // M4 — node masuk jadwal FSRS setelah lolos bersih.
  status: NodeStatus | null;
  due_at: string | null;
  interval_days: number | null;
  consecutive_success: number | null;
  successes_needed: number | null;
  became_mastered: boolean;
}

// --- M4: statistik dashboard (KPI PRD §9) ---
export interface NodeStat {
  node_id: string;
  concept: string;
  status: NodeStatus;
  attempts: number;
  passed: number;
  pass_rate: number | null;
  review_count: number;
  consecutive_success: number;
  due_at: string | null;
  is_due: boolean;
}

export interface Stats {
  total_nodes: number;
  by_status: Record<string, number>;
  mastered_count: number;
  due_count: number;
  reproduce_attempts: number;
  reproduce_passed: number;
  reproduce_pass_rate: number | null;
  successes_needed: number;
  placement_floor_node_id: string | null;
  nodes: NodeStat[];
}

// --- M4: review harian ---
export interface DueItem {
  node_id: string;
  concept: string;
  status: NodeStatus;
  due_at: string | null;
  overdue_days: number;
  review_count: number;
  consecutive_success: number;
  successes_needed: number;
}

export interface ReviewChallenge {
  node_id: string;
  concept: string;
  instance_id: string;
  variant_label: string;
  prompt: string;
  signature_contract: string;
  timebox_seconds: number;
  previous_instance_id: string | null;
  needs_more_variants: boolean;
  language: string;
}

export interface Outcome {
  node_id: string;
  previous_status: NodeStatus;
  status: NodeStatus;
  rating: string;
  clean: boolean;
  spaced: boolean;
  consecutive_success: number;
  successes_needed: number;
  due_at: string | null;
  interval_days: number | null;
  became_acquired: boolean;
  became_mastered: boolean;
  became_lapsed: boolean;
}

export interface ReviewSubmitOut {
  attempt_id: number;
  passed: boolean;
  test_output: string;
  timed_out: boolean;
  probe: Probe | null;
  outcome: Outcome | null;
}

export interface ReviewProbeOut {
  probe_correct: boolean;
  outcome: Outcome;
}

// --- M4: placement ---
export interface PlacementChallenge {
  node_id: string;
  concept: string;
  instance_id: string;
  prompt: string;
  signature_contract: string;
  timebox_seconds: number;
  position: number;
  language: string;
}

export interface PlacementState {
  session_id: number;
  max_nodes: number;
  tested: { node_id: string; result: string | null; attempt_id: number | null }[];
  finished: boolean;
  exhausted: boolean;
  floor_node_id: string | null;
  current: PlacementChallenge | null;
}

export interface PlacementSubmitOut {
  passed: boolean;
  test_output: string;
  attempt_id: number;
  state: PlacementState;
  floor_outcome: Outcome | null;
  unlocked: string[];
}

// --- M5: integrasi Claude Code (async via artifact + review Isyah) ---
// `node` (L4) ditambahkan backend sebagai R4 mode kelahiran node — brief §7.7 minta
// tipe & UI direkonsiliasi supaya job node-birth ikut ter-render.
export type JobRole = "r2" | "r3" | "r4" | "node";
export type JobStatus =
  | "pending"
  | "running"
  | "ready"
  | "failed"
  | "approved"
  | "rejected";

export interface IntegrationStatus {
  enabled: boolean;
  cli_available: boolean;
  counts: Record<string, number>;
  never_does: string[];
}

export interface AuthoringJob {
  id: string;
  role: JobRole;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  prompt_version: string;
  request: Record<string, unknown>;
  summary: Record<string, unknown>;
  gate: { passed: boolean; reason: string; output?: string } | null;
  error: string;
  attempts: number;
}

export interface AuthoringJobDetail extends AuthoringJob {
  prompt: string;
  files: Record<string, string>;
  existing: Record<string, string>;
}

export interface ApproveOut {
  job_id: string;
  role: JobRole;
  node_id: string;
  written_paths: string[];
  db_effect: Record<string, unknown>;
}

export interface Hypothesis {
  id: number;
  node_id: string;
  source: string;
  confidence: number;
  rationale: string;
  evidence_locator: string;
  status: "unverified" | "confirmed_by_attempt" | "refuted_by_attempt";
  created_at: string;
}

export interface Explanation {
  node_id: string;
  markdown: string;
  worked_example: string;
}

// --- M7: meja audit (telemetri kurikulum, bukan gerbang manusia) ---
// Sinyal per node: never-fails=trivia, never-passes=broken, low-discrimination.
export interface AuditSignal {
  node_id: string;
  kind: string;
  detail: string;
  samples: number;
}

// Edge yang BELUM terkukuhkan (bukti konstruk hulu tak terlihat di hilir). Laporan,
// bukan gerbang (§7 2026-09-01): ketiadaan bukti tak membuktikan edge itu salah.
export interface AuditEdge {
  from_node_id: string;
  to_node_id: string;
  kind: string;
  reason: string;
}

// Seberapa banyak kurikulum yang PUNYA data — tanpa ini, "tak ada temuan" mudah
// terbaca "semuanya sehat", padahal dengan n=1 hampir selalu "belum ada datanya".
export interface AuditCoverage {
  nodes: number;
  nodes_with_cold_data: number;
  nodes_assessable: number;
  min_attempts: number;
  lapsed_now: number;
}

export interface AuditOut {
  coverage: AuditCoverage;
  node_signals: AuditSignal[];
  edge_findings: AuditEdge[];
  domains_without_destination: string[];
}

// --- L5: lajur Library ("% direproduksi", bukan "% dibaca") ---
export type MaterialState = "unmapped" | "mapped_unproven" | "reproduced";

export interface LibraryMaterial {
  path: string;
  title: string;
  type: string;
  /** Status CATATAN (outline/captured) - label, BUKAN kemajuan. Jangan diakumulasi. */
  note_status: string;
  node_ids: string[];
  missing_node_ids: string[];
  state: MaterialState;
  mastered: boolean;
  decayed: boolean;
}

export interface LibraryModule {
  module: string;
  title: string;
  materials: LibraryMaterial[];
}

export interface LibraryCourse {
  course: string;
  title: string;
  total: number;
  unmapped: number;
  mapped_unproven: number;
  reproduced: number;
  mastered: number;
  decayed: number;
  reproduced_pct: number | null;
  modules: LibraryModule[];
}

export interface LibraryProgress {
  total: number;
  reproduced: number;
  reproduced_pct: number | null;
  courses: LibraryCourse[];
}

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listNodes: () => fetch(`${BACKEND_URL}/nodes`).then(j<NodeSummary[]>),
  getNode: (id: string) => fetch(`${BACKEND_URL}/nodes/${id}`).then(j<NodeDetail>),
  getLevel: (id: string, level: string) =>
    fetch(`${BACKEND_URL}/nodes/${id}/level/${level}`).then(j<LevelView>),
  getProbe: (id: string) => fetch(`${BACKEND_URL}/nodes/${id}/probe`).then(j<Probe>),
  submitAttempt: (body: {
    node_id: string;
    instance_id: string;
    scaffold_level: string;
    submitted_code: string;
    duration_seconds: number;
    timebox_exceeded?: boolean;
  }) =>
    fetch(`${BACKEND_URL}/attempts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<SubmitOut>),
  answerProbe: (body: { attempt_id: number; probe_id: string; answer: string }) =>
    fetch(`${BACKEND_URL}/probes/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<ProbeAnswerOut>),

  // --- M4 ---
  getStats: () => fetch(`${BACKEND_URL}/stats`).then(j<Stats>),

  listDue: () => fetch(`${BACKEND_URL}/review/due`).then(j<DueItem[]>),
  getReviewChallenge: (nodeId: string) =>
    fetch(`${BACKEND_URL}/review/${nodeId}/challenge`).then(j<ReviewChallenge>),
  submitReview: (body: {
    node_id: string;
    instance_id: string;
    submitted_code: string;
    duration_seconds: number;
    timebox_exceeded?: boolean;
  }) =>
    fetch(`${BACKEND_URL}/review/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<ReviewSubmitOut>),
  submitReviewProbe: (body: { attempt_id: number; probe_id: string; answer: string }) =>
    fetch(`${BACKEND_URL}/review/probe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<ReviewProbeOut>),

  startPlacement: () =>
    fetch(`${BACKEND_URL}/placement/start`, { method: "POST" }).then(j<PlacementState>),
  getPlacement: (sessionId: number) =>
    fetch(`${BACKEND_URL}/placement/${sessionId}`).then(j<PlacementState>),
  submitPlacement: (
    sessionId: number,
    body: { submitted_code: string; duration_seconds: number; timebox_exceeded?: boolean },
  ) =>
    fetch(`${BACKEND_URL}/placement/${sessionId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<PlacementSubmitOut>),

  // --- L5: lajur Library. READ-ONLY; penulis `library/` tetap scripts/ (L1-L4). ---
  getLibraryProgress: () =>
    fetch(`${BACKEND_URL}/library/progress`).then(j<LibraryProgress>),

  // --- M5 ---
  // Materi just-in-time: backend menolak (403) selama node belum punya attempt gagal.
  getExplanation: (nodeId: string) =>
    fetch(`${BACKEND_URL}/nodes/${nodeId}/explanation`).then(j<Explanation>),

  getIntegrationStatus: () =>
    fetch(`${BACKEND_URL}/authoring/status`).then(j<IntegrationStatus>),
  listJobs: (params?: { role?: JobRole; status?: JobStatus }) => {
    const q = new URLSearchParams();
    if (params?.role) q.set("role", params.role);
    if (params?.status) q.set("status", params.status);
    const suffix = q.toString() ? `?${q}` : "";
    return fetch(`${BACKEND_URL}/authoring/jobs${suffix}`).then(j<AuthoringJob[]>);
  },
  getJob: (jobId: string) =>
    fetch(`${BACKEND_URL}/authoring/jobs/${jobId}`).then(j<AuthoringJobDetail>),
  triggerR3: (body: { node_id: string; attempt_id?: number }) =>
    fetch(`${BACKEND_URL}/authoring/r3`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<AuthoringJob>),
  triggerR4: (body: { node_id: string; variant_label?: string }) =>
    fetch(`${BACKEND_URL}/authoring/r4`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<AuthoringJob>),
  // L4 — satu entri peta Library → satu node Forge (R4 mode `node`).
  triggerNode: (body: {
    library_file: string;
    slug: string;
    domain_id: string;
    concept: string;
    source_ref_id: string;
    prereq_node_id?: string;
  }) =>
    fetch(`${BACKEND_URL}/authoring/node`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<AuthoringJob>),
  triggerR2: (body: { repo_path: string; node_ids?: string[] }) =>
    fetch(`${BACKEND_URL}/authoring/r2`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(j<AuthoringJob>),
  approveJob: (jobId: string) =>
    fetch(`${BACKEND_URL}/authoring/jobs/${jobId}/approve`, { method: "POST" }).then(
      j<ApproveOut>,
    ),
  rejectJob: (jobId: string, reason: string) =>
    fetch(`${BACKEND_URL}/authoring/jobs/${jobId}/reject`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    }).then(j<AuthoringJob>),
  listHypotheses: (nodeId?: string) =>
    fetch(`${BACKEND_URL}/authoring/hypotheses${nodeId ? `?node_id=${nodeId}` : ""}`).then(
      j<Hypothesis[]>,
    ),

  // M7 — meja audit: telemetri MENANDAI node curiga; pencabutan tetap satu klik manusia
  // (belum ada endpoint — lihat kontrol pending di /authoring).
  getAudit: () => fetch(`${BACKEND_URL}/authoring/audit`).then(j<AuditOut>),
};
