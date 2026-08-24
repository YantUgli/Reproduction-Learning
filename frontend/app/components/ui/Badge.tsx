import type { ReactNode } from "react";

/** Pill token generik. StatusBadge & label kecil lain memakai ini. */
export type BadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

const TONE: Record<BadgeTone, string> = {
  neutral: "bg-neutral-bg text-neutral",
  info: "bg-info-bg text-info",
  success: "bg-success-bg text-success",
  warning: "bg-warning-bg text-warning",
  danger: "bg-danger-bg text-danger",
};

export default function Badge({
  tone = "neutral",
  className = "",
  children,
}: {
  tone?: BadgeTone;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-13 font-semibold ${TONE[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
