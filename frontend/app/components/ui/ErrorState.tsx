"use client";

import Button from "./Button";

/**
 * Error state yang bisa ditindaklanjuti — bukan `String(e)` mentah di ruang kosong
 * (brief §9.2). Kegagalan `fetch` (backend :8000 mati) adalah kasus paling umum di dev
 * local, jadi dideteksi & diberi diagnosis + tombol coba lagi. Untuk error ber-status
 * HTTP (`"500: ..."`, `"403: ..."`) kita tampilkan **kalimat manusia** di atas dan
 * simpan detail teknisnya di disclosure — bukan status telanjang.
 */

/** Klien `api` melempar `Error("<status>: <body>")`; `String(e)` = `"Error: 500: …"`. */
function parseHttp(raw: string): { status: number; body: string } | null {
  const m = /(?:error:\s*)?(\d{3}):\s*([\s\S]*)/i.exec(raw.trim());
  if (!m) return null;
  return { status: Number(m[1]), body: m[2].trim() };
}

const SENTENCE: Record<number, string> = {
  400: "Permintaan tidak bisa diproses — kemungkinan datanya tidak lengkap.",
  403: "Belum boleh dibuka — gerbang produk ini menahannya sampai syaratnya terpenuhi.",
  404: "Yang kamu cari tidak ditemukan.",
  409: "Ada bentrokan status — coba muat ulang lalu ulangi.",
  500: "Backend mengalami kesalahan saat memproses permintaan ini.",
  503: "Layanan ini sedang dimatikan (kemungkinan kill switch integrasi).",
};

export default function ErrorState({
  error,
  onRetry,
}: {
  error: string;
  onRetry?: () => void;
}) {
  const isFetch = /failed to fetch|networkerror|load failed/i.test(error);
  const http = isFetch ? null : parseHttp(error);

  let title = "Terjadi kesalahan";
  if (isFetch) title = "Tidak bisa menghubungi backend";
  else if (http) title = SENTENCE[http.status] ?? `Backend membalas ${http.status}.`;

  return (
    <div className="rounded-md border border-danger bg-danger-bg px-4 py-3">
      <p className="font-semibold text-danger">{title}</p>

      {isFetch ? (
        <p className="mt-1 text-13 text-fg">
          Backend di <code className="font-mono">localhost:8000</code> tidak merespons.
          Pastikan ia berjalan (<code className="font-mono">uvicorn app.main:app</code>),
          lalu coba lagi.
        </p>
      ) : http ? (
        // Kalimat sudah di judul; detail teknis (kode + body) di disclosure.
        http.body && (
          <details className="mt-1.5">
            <summary className="cursor-pointer text-13 text-muted hover:text-fg">
              Detail teknis
            </summary>
            <pre className="mt-1.5 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded bg-surface-muted px-3 py-2 font-mono text-xs text-fg">
              {http.status}: {http.body}
            </pre>
          </details>
        )
      ) : (
        <p className="mt-1 break-words font-mono text-13 text-fg">{error}</p>
      )}

      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>
          Coba lagi
        </Button>
      )}
    </div>
  );
}
