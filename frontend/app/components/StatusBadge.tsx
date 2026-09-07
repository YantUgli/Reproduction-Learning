"use client";

import type { NodeStatus } from "../../lib/api";
import Badge, { type BadgeTone, type BadgeVariant } from "./ui/Badge";

/**
 * Proof Law (brief §8): status yang DITEGAKKAN eksikusi tampil `solid`; status yang
 * belum pernah dibuktikan tampil `outline`. `locked`/`available` = belum ada satu pun
 * attempt lolos → garis. `acquired`/`mastered`/`lapsed` = PERNAH direproduksi tanpa AI
 * → terisi (lapsed memorinya meluruh, buktinya tidak — §7 2026-08-21 Q3).
 */
const STATUS: Record<NodeStatus, { label: string; tone: BadgeTone; variant: BadgeVariant }> = {
  locked: { label: "terkunci", tone: "neutral", variant: "outline" },
  available: { label: "tersedia", tone: "info", variant: "outline" },
  acquired: { label: "acquired", tone: "success", variant: "solid" },
  mastered: { label: "mastered", tone: "warning", variant: "solid" },
  lapsed: { label: "lapsed", tone: "danger", variant: "solid" },
};

export default function StatusBadge({ status }: { status: NodeStatus }) {
  const s = STATUS[status] ?? STATUS.locked;
  return (
    <Badge tone={s.tone} variant={s.variant}>
      {s.label}
    </Badge>
  );
}
