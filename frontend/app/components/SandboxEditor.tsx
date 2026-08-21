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
}: {
  value: string;
  onChange?: (v: string) => void;
  readOnly?: boolean;
  height?: string;
}) {
  return (
    <div style={{ border: "1px solid #d0d7de", borderRadius: 6, overflow: "hidden" }}>
      <Editor
        height={height}
        language="python"
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
    </div>
  );
}
