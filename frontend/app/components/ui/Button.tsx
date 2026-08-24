import type { ButtonHTMLAttributes } from "react";

/**
 * Tombol dengan varian eksplisit. `primary` (biru solid) SATU per layar untuk aksi
 * terpenting — di produk ini "Jalankan & Verifikasi". Sebelumnya semua tombol default
 * browser, jadi aksi inti tak terbedakan dari aksi pendamping (masalah UX #1).
 */
type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const VARIANT: Record<Variant, string> = {
  primary: "bg-accent text-accent-fg border border-transparent hover:bg-accent-hover shadow-sm",
  secondary: "bg-surface text-fg border border-border hover:bg-surface-muted",
  ghost: "bg-transparent text-accent border border-transparent hover:bg-info-bg",
  danger: "bg-surface text-danger border border-border hover:bg-danger-bg",
};

const SIZE: Record<Size, string> = {
  sm: "text-13 px-3 py-1.5",
  md: "text-sm px-4 py-2",
};

export default function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  className = "",
  children,
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-md font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT[variant]} ${SIZE[size]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
