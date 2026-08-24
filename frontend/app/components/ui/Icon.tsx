/**
 * Ikon garis (stroke) minimal, inline — TANPA dependency icon-pack dan TANPA emoji
 * (§4b rencana UI: emoji bikin tampilan terasa "AI slop"). Dipakai hemat.
 * Semua memakai `currentColor` supaya mewarisi warna teks/token induknya.
 */
type IconProps = { className?: string; size?: number };

function svg(path: React.ReactNode, size: number, className?: string) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {path}
    </svg>
  );
}

export function IconClock({ className, size = 16 }: IconProps) {
  return svg(
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>,
    size,
    className,
  );
}

export function IconCheck({ className, size = 16 }: IconProps) {
  return svg(<path d="M20 6 9 17l-5-5" />, size, className);
}

/** Stopwatch — untuk timebox (hitung mundur), sengaja BUKAN jam dinding supaya
 * `17:53` tak terbaca sebagai "pukul 17:53". */
export function IconStopwatch({ className, size = 14 }: IconProps) {
  return svg(
    <>
      <path d="M9 2h6" />
      <path d="M12 2v2" />
      <circle cx="12" cy="14" r="8" />
      <path d="M12 14V10" />
    </>,
    size,
    className,
  );
}

export function IconX({ className, size = 16 }: IconProps) {
  return svg(<path d="M18 6 6 18M6 6l12 12" />, size, className);
}

export function IconArrowRight({ className, size = 16 }: IconProps) {
  return svg(<path d="M5 12h14M13 6l6 6-6 6" />, size, className);
}

export function IconInbox({ className, size = 28 }: IconProps) {
  return svg(
    <>
      <path d="M22 12h-6l-2 3h-4l-2-3H2" />
      <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
    </>,
    size,
    className,
  );
}

export function IconLock({ className, size = 14 }: IconProps) {
  return svg(
    <>
      <rect x="4" y="11" width="16" height="10" rx="2" />
      <path d="M8 11V7a4 4 0 0 1 8 0v4" />
    </>,
    size,
    className,
  );
}

export function IconTarget({ className, size = 28 }: IconProps) {
  return svg(
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </>,
    size,
    className,
  );
}
