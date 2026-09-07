import {
  Skeleton,
  KpiRowSkeleton,
  EditorSkeleton,
} from "reproduction-learning-engine-frontend";

// Placeholder loading. Skeleton = bar dasar; komposisi KPI & editor memakainya.
export function Base() {
  // Kelas ukuran yang PASTI ada di compiled.css (dipakai KpiRow/EditorSkeleton) —
  // Tailwind JIT hanya meng-emit utilitas yang dipakai di app/.
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 360 }}>
      <Skeleton className="h-6 w-2/3" />
      <Skeleton className="h-3 w-32" />
      <Skeleton className="h-3 w-24" />
    </div>
  );
}

export function KpiRow() {
  return (
    <div style={{ maxWidth: 720 }}>
      <KpiRowSkeleton />
    </div>
  );
}

export function Editor() {
  return (
    <div style={{ maxWidth: 640 }}>
      <EditorSkeleton />
    </div>
  );
}
