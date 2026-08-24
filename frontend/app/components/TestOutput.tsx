"use client";

import { IconCheck, IconX } from "./ui/Icon";

/**
 * Hasil eksekusi hidden test. Kegagalan DITAMPILKAN, tidak disembunyikan —
 * produk ini cermin (§7.6): Bryant perlu melihat kenapa gagal.
 * Verdict pakai ikon garis + warna token (bukan emoji, §4b).
 */
export default function TestOutput({
  passed,
  output,
  timedOut = false,
}: {
  passed: boolean;
  output: string;
  timedOut?: boolean;
}) {
  return (
    <div className="mt-4">
      <div
        className={`mb-2 inline-flex items-center gap-1.5 text-sm font-bold ${
          passed ? "text-success" : "text-danger"
        }`}
      >
        {passed ? <IconCheck size={16} /> : <IconX size={16} />}
        {passed ? "TEST PASS" : "TEST FAIL"}
        {timedOut && (
          <span className="font-normal text-muted">(timeout eksekusi)</span>
        )}
      </div>
      <pre className="max-h-[260px] overflow-x-auto rounded-md bg-code-bg p-4 text-[13px] leading-relaxed text-code-fg">
        {output || "(tanpa output)"}
      </pre>
    </div>
  );
}
