"use client";

import Button from "./Button";

/**
 * Error state yang bisa ditindaklanjuti — bukan `String(e)` mentah di ruang kosong.
 * Kegagalan `fetch` (backend :8000 mati) adalah kasus paling umum di dev local, jadi
 * dideteksi & diberi diagnosis + tombol coba lagi.
 */
export default function ErrorState({
  error,
  onRetry,
}: {
  error: string;
  onRetry?: () => void;
}) {
  const isFetch = /failed to fetch|networkerror|load failed/i.test(error);
  return (
    <div className="rounded-md border border-danger bg-danger-bg px-4 py-3">
      <p className="font-semibold text-danger">
        {isFetch ? "Tidak bisa menghubungi backend" : "Terjadi kesalahan"}
      </p>
      <p className="mt-1 text-13 text-fg">
        {isFetch ? (
          <>
            Backend di <code className="font-mono">localhost:8000</code> tidak merespons.
            Pastikan ia berjalan (<code className="font-mono">uvicorn app.main:app</code>),
            lalu coba lagi.
          </>
        ) : (
          <span className="break-words font-mono">{error}</span>
        )}
      </p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>
          Coba lagi
        </Button>
      )}
    </div>
  );
}
