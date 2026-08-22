"use client";

import type { NodeStatus } from "../../lib/api";

export const STATUS_STYLE: Record<NodeStatus, { label: string; bg: string; fg: string }> = {
  locked: { label: "terkunci", bg: "#eaeef2", fg: "#57606a" },
  available: { label: "tersedia", bg: "#ddf4ff", fg: "#0969da" },
  acquired: { label: "acquired", bg: "#dafbe1", fg: "#1a7f37" },
  mastered: { label: "mastered", bg: "#fff8c5", fg: "#9a6700" },
  lapsed: { label: "lapsed", bg: "#ffebe9", fg: "#cf222e" },
};

export default function StatusBadge({ status }: { status: NodeStatus }) {
  const s = STATUS_STYLE[status] ?? STATUS_STYLE.locked;
  return (
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
  );
}
