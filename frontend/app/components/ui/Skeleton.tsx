/**
 * Placeholder memuat. Menggantikan teks "Memuat…" telanjang di halaman kosong —
 * dengan Monaco & fetch backend, jendela memuat bisa terasa lama, jadi bentuk konten
 * yang akan datang mengurangi kesan "aplikasi menggantung".
 */
export default function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`animate-pulse rounded-md bg-neutral-bg ${className}`}
    />
  );
}

/** Skeleton baris kartu KPI (4 kolom) untuk dashboard. */
export function KpiRowSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-busy="true" aria-label="Memuat statistik">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="rounded-md border border-border bg-surface p-4 shadow-sm">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="mt-2 h-8 w-16" />
          <Skeleton className="mt-2 h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton blok prompt + editor untuk halaman node/challenge. */
export function EditorSkeleton() {
  return (
    <div aria-busy="true" aria-label="Memuat tantangan">
      <Skeleton className="h-6 w-2/3" />
      <Skeleton className="mt-3 h-24 w-full" />
      <Skeleton className="mt-4 h-[320px] w-full" />
    </div>
  );
}
