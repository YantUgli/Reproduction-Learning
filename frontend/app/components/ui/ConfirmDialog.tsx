"use client";

import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import Button from "./Button";

/**
 * Dialog konfirmasi — pengganti `window.confirm` bawaan browser (tampilannya kaku,
 * tak bisa di-tema, dan memblokir thread). Presentasional murni: SEMUA state (buka/
 * tutup, teks) datang dari `ConfirmProvider`, yang memakainya lewat `useConfirm()`.
 *
 * Aksesibilitas: `role="dialog"` + `aria-modal`, judul/keterangan ter-`aria-label`/
 * `describedby`, fokus dipindah ke tombol AMAN (Batal) saat buka lalu dikembalikan ke
 * pemicu saat tutup, Tab terjebak di dalam dialog, Escape & klik backdrop = batal.
 */
export type ConfirmTone = "default" | "danger";

export type ConfirmOptions = {
  title: string;
  description?: React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: ConfirmTone;
};

export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Lanjut",
  cancelLabel = "Batal",
  tone = "default",
  onConfirm,
  onCancel,
}: ConfirmOptions & {
  open: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useId();
  const descId = useId();

  useEffect(() => {
    if (!open) return;
    // Simpan fokus & scroll-lock; pulihkan saat dialog tutup.
    const prevActive = document.activeElement as HTMLElement | null;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Fokus tombol AMAN (Batal = tombol pertama) agar Enter tak sengaja mengeksekusi
    // aksi destruktif.
    const buttons = panelRef.current?.querySelectorAll<HTMLElement>("button");
    buttons?.[0]?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key === "Tab") {
        const f = panelRef.current?.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (!f || f.length === 0) return;
        const first = f[0];
        const last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      prevActive?.focus?.();
    };
  }, [open, onCancel]);

  // Tutup saat SSR / belum dibuka: tak menyentuh `document`, cocok dengan hidrasi.
  if (!open) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop — klik = batal. */}
      <div
        className="absolute inset-0 bg-black/40"
        aria-hidden="true"
        onClick={onCancel}
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descId : undefined}
        className="relative z-10 w-full max-w-md rounded-lg border border-border bg-surface p-5 shadow-xl"
      >
        <h2 id={titleId} className="text-lg font-semibold">
          {title}
        </h2>
        {description && (
          <div id={descId} className="mt-2 text-sm text-muted">
            {description}
          </div>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button variant={tone === "danger" ? "danger" : "primary"} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
