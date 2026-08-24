import type { ReactNode } from "react";

/**
 * Empty state: bukan sekadar teks abu di ruang kosong. Copy-nya (yang sudah bagus)
 * dibingkai dengan ikon garis + border putus-putus + spacing supaya terasa dirancang,
 * bukan "kosong & kaku". Tanpa emoji (§4b).
 */
export default function EmptyState({
  icon,
  title,
  children,
  action,
}: {
  icon?: ReactNode;
  title?: ReactNode;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-md border border-dashed border-border bg-surface-muted px-6 py-12 text-center">
      {icon && <div className="text-subtle">{icon}</div>}
      {title && <p className="text-base font-semibold text-fg">{title}</p>}
      {children && <div className="max-w-md text-sm leading-relaxed text-muted">{children}</div>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}
