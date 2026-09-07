import { Card, StatusBadge } from "reproduction-learning-engine-frontend";

// Permukaan dasar (surface + border + radius + shadow). Isi bebas.
export function NodeRow() {
  return (
    <div style={{ maxWidth: 460 }}>
      <Card className="flex items-center justify-between gap-3 p-4">
        <div>
          <div style={{ fontWeight: 600 }}>Path parameter dengan 404</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--subtle)" }}>
            n003_path_param_404
          </div>
        </div>
        <StatusBadge status="mastered" />
      </Card>
    </div>
  );
}

export function NextNode() {
  return (
    <div style={{ maxWidth: 460 }}>
      <Card className="flex items-center justify-between gap-3 border-l-4 border-l-accent p-4">
        <div>
          <div style={{ fontWeight: 600 }}>Paginasi query</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--subtle)" }}>
            n001_paginate · mulai di sini
          </div>
        </div>
        <StatusBadge status="available" />
      </Card>
    </div>
  );
}
