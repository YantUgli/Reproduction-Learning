"use client";

import Editor from "@monaco-editor/react";

/**
 * Editor sandbox berbasis Monaco.
 *
 * INVARIANT §2 (ditegakkan di UI): SEMUA saran cerdas / AI-assist / autocomplete
 * berbasis kata DIMATIKAN. Highlight sintaks dasar boleh; saran solusi TIDAK.
 * Kalau editor menyarankan solusi, itu melanggar "reproduce-without-AI".
 */
export default function SandboxEditor({
  value,
  onChange,
  readOnly = false,
  height = "340px",
  language = "plaintext",
}: {
  value: string;
  onChange?: (v: string) => void;
  readOnly?: boolean;
  height?: string;
  /** Mode highlight dari backend (diturunkan dari berkas node, bukan dari domain). */
  language?: string;
}) {
  // Hint muncul hanya saat editor benar-benar kosong & bisa diedit — bukan placeholder
  // yang menyarankan solusi (§2), cuma pengingat aturan main. pointer-events-none supaya
  // klik tetap sampai ke Monaco.
  const showHint = !readOnly && value.trim() === "";

  return (
    <div className="relative overflow-hidden rounded-md border border-border">
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={(v) => onChange?.(v ?? "")}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          scrollBeyondLastLine: false,
          // --- matikan semua bantuan cerdas / AI ---
          quickSuggestions: false,
          suggestOnTriggerCharacters: false,
          wordBasedSuggestions: "off",
          parameterHints: { enabled: false },
          inlineSuggest: { enabled: false },
          tabCompletion: "off",
          acceptSuggestionOnEnter: "off",
          hover: { enabled: "off" },
          codeLens: false,
          suggest: { showWords: false },
        }}
      />
      {showHint && (
        <div className="pointer-events-none absolute left-[62px] top-[9px] select-none font-mono text-sm text-subtle">
          Tulis dari nol — tanpa contoh, tanpa AI.
        </div>
      )}
    </div>
  );
}
