import { defineConfig } from "vitest/config";

/**
 * Konfigurasi eksekusi hidden test React (M6).
 *
 * - `environment: jsdom` → DOM sungguhan tanpa browser. Ini yang membuat
 *   `dom_behavior` bisa meng-assert PERILAKU (teks muncul, state berubah setelah
 *   klik), bukan struktur JSX.
 * - `esbuild.jsx: automatic` → submisi boleh menulis JSX tanpa `import React`,
 *   persis seperti proyek Next.js yang dipelajari Bryant.
 * - `include` menunjuk pola file yang dirakit executor di direktori kerja sementara.
 */
export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["**/*.test.jsx"],
    globals: false,
    setupFiles: ["./vitest.setup.js"],
    reporters: ["basic"],
    // Satu berkas test per grading; fork tunggal lebih cepat daripada pool worker.
    pool: "forks",
    poolOptions: { forks: { singleFork: true } },
  },
  esbuild: { jsx: "automatic" },
});
