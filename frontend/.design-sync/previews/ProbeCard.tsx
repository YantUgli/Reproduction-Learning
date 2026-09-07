import { ProbeCard } from "reproduction-learning-engine-frontend";

// Comprehension probe deterministik (predict_output | spot_bug | trace).
// Jawaban benar TIDAK ada di klien — dicek server. onSubmit di-noop untuk preview.
const PROBE = {
  id: "n003_probe_01",
  node_id: "n003_path_param_404",
  type: "predict_output",
  question: "Status code apa yang dibalas saat item_id tidak ada di penyimpanan?",
  options: ["200 OK", "404 Not Found", "422 Unprocessable", "500 Internal"],
};

export function Unanswered() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ProbeCard probe={PROBE} disabled={false} onSubmit={() => {}} outcome={null} />
    </div>
  );
}

export function AfterIncorrect() {
  return (
    <div style={{ maxWidth: 560 }}>
      <ProbeCard probe={PROBE} disabled onSubmit={() => {}} outcome="incorrect" />
    </div>
  );
}
