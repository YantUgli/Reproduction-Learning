"use client";

/**
 * Hasil eksekusi hidden test. Kegagalan DITAMPILKAN, tidak disembunyikan —
 * produk ini cermin (§7.6): Bryant perlu melihat kenapa gagal.
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
    <div style={{ marginTop: 16 }}>
      <div style={{ fontWeight: 700, color: passed ? "#1a7f37" : "#cf222e" }}>
        {passed ? "TEST PASS ✓" : "TEST FAIL ✗"}
        {timedOut && " (timeout eksekusi)"}
      </div>
      <pre
        style={{
          background: "#0d1117",
          color: "#e6edf3",
          padding: "0.75rem 1rem",
          borderRadius: 8,
          overflowX: "auto",
          fontSize: 13,
          maxHeight: 260,
        }}
      >
        {output || "(tanpa output)"}
      </pre>
    </div>
  );
}
