import Link from "next/link";
import type { ReactNode } from "react";

/**
 * Header halaman konsisten: link balik + judul + subjudul + slot aksi kanan.
 * Menggantikan pola "← Dashboard" yang berbeda-beda tiap halaman.
 */
export default function PageHeader({
  title,
  subtitle,
  back = "/",
  backLabel = "Dashboard",
  actions,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  back?: string | null;
  backLabel?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="mb-6">
      {back && (
        <Link
          href={back}
          className="text-sm text-accent hover:underline"
        >
          ← {backLabel}
        </Link>
      )}
      <div className="mt-2 flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-fg">{title}</h1>
          {subtitle && <p className="mt-1 max-w-2xl text-muted">{subtitle}</p>}
        </div>
        {actions && (
          <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1">
            {actions}
          </div>
        )}
      </div>
    </header>
  );
}
