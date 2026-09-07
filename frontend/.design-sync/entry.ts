// Entry buatan-tangan untuk design-sync (bukan build app).
//
// App ini memakai `export default` untuk komponen + named export untuk helper.
// Synth-entry converter memakai `export *` yang MENJATUHKAN default export, jadi
// `window.RLE.Button` akan undefined. Entry ini menamai-ulang default → named
// supaya setiap komponen muncul di `window.<globalName>`. Isi komponen tetap kode
// asli repo (di-bundle dari sumbernya), bukan reimplementasi.

// -- Primitif ui/ (default export → named) --
export { default as Button } from "../app/components/ui/Button";
export { default as Card } from "../app/components/ui/Card";
export { default as Badge } from "../app/components/ui/Badge";
export { default as Container } from "../app/components/ui/Container";
export { default as EmptyState } from "../app/components/ui/EmptyState";
export { default as ErrorState } from "../app/components/ui/ErrorState";
export { default as PageHeader } from "../app/components/ui/PageHeader";
export { default as ConfirmDialog } from "../app/components/ui/ConfirmDialog";
export { default as Skeleton } from "../app/components/ui/Skeleton";

// -- Komponen komposit components/ --
export { default as StatusBadge } from "../app/components/StatusBadge";
export { default as ProbeCard } from "../app/components/ProbeCard";
export { default as TestOutput } from "../app/components/TestOutput";
export { default as Timebox } from "../app/components/Timebox";
export { default as Markdown } from "../app/components/Markdown";

// -- Helper & provider (di-bundle, dipakai preview; tak semua jadi kartu) --
export { KpiRowSkeleton, EditorSkeleton } from "../app/components/ui/Skeleton";
export { ConfirmProvider, useConfirm } from "../app/components/ui/ConfirmProvider";

// -- Ikon garis SVG (dipakai banyak komponen; ship ke bundle) --
export {
  IconClock,
  IconCheck,
  IconStopwatch,
  IconX,
  IconArrowRight,
  IconInbox,
  IconLock,
  IconTarget,
} from "../app/components/ui/Icon";
