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
};
