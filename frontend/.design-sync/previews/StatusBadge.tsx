import { StatusBadge } from "reproduction-learning-engine-frontend";

// Lima status jadwal node. Proof Law: locked/available (belum terbukti) = outline;
// acquired/mastered/lapsed (pernah direproduksi tanpa AI) = solid.
export function AllStatuses() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <StatusBadge status="locked" />
      <StatusBadge status="available" />
      <StatusBadge status="acquired" />
      <StatusBadge status="mastered" />
      <StatusBadge status="lapsed" />
    </div>
  );
}
