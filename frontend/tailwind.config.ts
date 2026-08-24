import type { Config } from "tailwindcss";

/**
 * Konfigurasi Tailwind (M-UI).
 *
 * Warna TIDAK di-hardcode di sini — semuanya menunjuk CSS variable di
 * `app/globals.css` (`:root`). Itu satu sumber kebenaran warna, dan jalur murah
 * untuk dark mode nanti (cukup tambah blok `.dark { ... }`, tanpa menyentuh config
 * atau komponen). Palet dasarnya = GitHub Primer yang sudah dipakai sejak M3–M6,
 * kini diberi nama SEMANTIK (`accent`, `success`, dst.) alih-alih hex telanjang.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--canvas)",
        surface: "var(--surface)",
        "surface-muted": "var(--surface-muted)",
        border: "var(--border)",
        "border-muted": "var(--border-muted)",
        fg: "var(--fg)",
        muted: "var(--muted)",
        subtle: "var(--subtle)",
        "fg-disabled": "var(--fg-disabled)",
        accent: {
          DEFAULT: "var(--accent)",
          hover: "var(--accent-hover)",
          fg: "var(--accent-fg)",
        },
        neutral: { DEFAULT: "var(--neutral)", bg: "var(--neutral-bg)" },
        success: { DEFAULT: "var(--success)", bg: "var(--success-bg)" },
        danger: { DEFAULT: "var(--danger)", bg: "var(--danger-bg)" },
        warning: { DEFAULT: "var(--warning)", bg: "var(--warning-bg)" },
        info: { DEFAULT: "var(--info)", bg: "var(--info-bg)" },
        code: { bg: "var(--code-bg)", fg: "var(--code-fg)" },
      },
      // 13px dulu ditulis ad-hoc `text-[13px]` ~30 kali (di luar skala). Kini token
      // bernama supaya jadi bagian skala tipografi, bukan escape hatch.
      fontSize: { "13": ["13px", { lineHeight: "1.45" }] },
      borderRadius: { md: "8px", lg: "12px" },
      boxShadow: {
        sm: "0 1px 2px rgba(31,35,40,.06), 0 1px 1px rgba(31,35,40,.04)",
        md: "0 3px 8px rgba(31,35,40,.10)",
      },
      maxWidth: { content: "820px", wide: "980px" },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
