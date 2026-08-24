"use client";

import type { NodeStatus } from "../../lib/api";
import Badge, { type BadgeTone } from "./ui/Badge";

const STATUS: Record<NodeStatus, { label: string; tone: BadgeTone }> = {
  locked: { label: "terkunci", tone: "neutral" },
  available: { label: "tersedia", tone: "info" },
  acquired: { label: "acquired", tone: "success" },
  mastered: { label: "mastered", tone: "warning" },
  lapsed: { label: "lapsed", tone: "danger" },
};

export default function StatusBadge({ status }: { status: NodeStatus }) {
  const s = STATUS[status] ?? STATUS.locked;
  return <Badge tone={s.tone}>{s.label}</Badge>;
}
