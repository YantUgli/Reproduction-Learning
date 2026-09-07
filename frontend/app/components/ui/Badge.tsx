import type { ReactNode } from "react";

/** Pill token generik. StatusBadge & label kecil lain memakai ini. */
export type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger" | "ember";

/**
 * Proof Law (brief §8): apa yang DIBUKTIKAN eksekusi tampil `solid` (terisi); apa yang
 * belum terbukti tampil `outline` (garis, transparan). Sebuah pill terisi = sesuatu yang
 * dijalankan kodenya, bukan sekadar dilihat/dibaca. Default `solid` supaya pemanggil lama
 * tak berubah; pemanggil yang menandai keadaan BELUM-terbukti memilih `outline`.
 */
export type BadgeVariant = "solid" | "outline";

const SOLID: Record<BadgeTone, string> = {
  neutral: "bg-neutral-bg text-neutral",
  info: "bg-info-bg text-info",
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
  ember: "bg-ember-bg text-ember",
};

const OUTLINE: Record<BadgeTone, string> = {
  neutral: "bg-transparent text-neutral border border-border",
  info: "bg-transparent text-info border border-info",
  success: "bg-transparent text-success border border-success",
  warning: "bg-transparent text-warning border border-warning",
  danger: "bg-transparent text-danger border border-danger",
  ember: "bg-transparent text-ember border border-ember",
};

export default function Badge({
  tone = "neutral",
  variant = "solid",
  className = "",
  children,
}: {
  tone?: BadgeTone;
  variant?: BadgeVariant;
  className?: string;
  children: ReactNode;
}) {
  const style = variant === "outline" ? OUTLINE[tone] : SOLID[tone];
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-13 font-semibold ${style} ${className}`}
    >
      {children}
    </span>
  );
}
