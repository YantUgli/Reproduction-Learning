"use client";

import Editor, { loader } from "@monaco-editor/react";
import type { editor } from "monaco-editor";
import * as monaco from "monaco-editor";
import { useRef } from "react";

/**
 * Editor sandbox berbasis Monaco.
 *
 * INVARIANT §2 (ditegakkan di UI): SEMUA saran cerdas / AI-assist / autocomplete
 * berbasis kata DIMATIKAN. Highlight sintaks dasar boleh; saran solusi TIDAK.
 * Kalau editor menyarankan solusi, itu melanggar "reproduce-without-AI".
 *
 * SELF-HOSTED (bukan CDN): Monaco di-bundle lokal via paket `monaco-editor`, jadi
 * aplikasi tetap jalan tanpa internet (klaim local-first) dan versinya ter-pin —
 * tak ada varians "editor beda perilaku hari ini" dari cdn.jsdelivr.
 */

// Konfigurasi sekali, hanya di browser (komponen ini di-mount dynamic ssr:false).
if (typeof window !== "undefined") {
  // Worker editor lokal. Hanya editor.worker yang dibutuhkan: seluruh layanan bahasa
  // (saran/hover/validasi) sudah dimatikan, dan highlight Python berbasis Monarch
  // jalan di main-thread.
  (self as unknown as { MonacoEnvironment: monaco.Environment }).MonacoEnvironment = {
    getWorker() {
      return new Worker(
        new URL("monaco-editor/esm/vs/editor/editor.worker.js", import.meta.url),
      );
    },
  };
  loader.config({ monaco });
}

export default function SandboxEditor({
  value,
  onChange,
  onSubmit,
  readOnly = false,
  height = "320px",
  language = "plaintext",
}: {
  value: string;
  onChange?: (v: string) => void;
  /** Dipanggil saat Ctrl/Cmd+Enter di dalam editor — jalankan & verifikasi. */
  onSubmit?: () => void;
  readOnly?: boolean;
  height?: string;
  /** Mode highlight dari backend (diturunkan dari berkas node, bukan dari domain). */
  language?: string;
}) {
  const showHint = !readOnly && value.trim() === "";

  // Ref supaya command Monaco (didaftar sekali saat mount) selalu memanggil onSubmit
  // terbaru, bukan yang ter-capture di render pertama (hindari stale closure).
  const onSubmitRef = useRef(onSubmit);
  onSubmitRef.current = onSubmit;

  const handleMount = (ed: editor.IStandaloneCodeEditor, m: typeof monaco) => {
    // Ctrl/Cmd+Enter menjalankan test — shortcut yang paling diharapkan di editor
    // coding, dan menutup loop tulis→jalankan tanpa pindah ke mouse tiap iterasi.
    ed.addCommand(m.KeyMod.CtrlCmd | m.KeyCode.Enter, () => onSubmitRef.current?.());
  };

  return (
    <div>
      <div className="overflow-hidden rounded-md border border-border">
        <Editor
          height={height}
          language={language}
          value={value}
          onChange={(v) => onChange?.(v ?? "")}
          onMount={handleMount}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            scrollBeyondLastLine: false,
            // Wrap: di layar sempit (mobile) baris kode tak lagi terpotong horizontal.
            wordWrap: "on",
            // Indentasi: user yang mengetik spasinya sendiri. `none` mematikan
            // auto-indent supaya spasi ketikan tak menumpuk di atas indent otomatis
            // (dulu `def f():`⏎`    x` jadi 8 spasi → IndentationError palsu).
            autoIndent: "none",
            detectIndentation: false,
            insertSpaces: true,
            tabSize: 4,
            formatOnPaste: false,
            formatOnType: false,
            // --- matikan semua bantuan cerdas / AI ---
            quickSuggestions: false,
            suggestOnTriggerCharacters: false,
            wordBasedSuggestions: "off",
            parameterHints: { enabled: false },
            inlineSuggest: { enabled: false },
            tabCompletion: "off",
            acceptSuggestionOnEnter: "off",
            hover: { enabled: false },
            codeLens: false,
            suggest: { showWords: false },
          }}
        />
      </div>
      {/* Caption di bawah editor — menggantikan overlay placeholder yang dipaku ke
          offset ajaib (meleset saat zoom / nomor baris ≥ 3 digit). */}
      {showHint && (
        <p className="mt-1.5 font-mono text-13 text-subtle">
          Tulis dari nol — tanpa contoh, tanpa AI.
        </p>
      )}
      {!readOnly && (
        <p className="mt-1 text-13 text-subtle">
          <Kbd>Ctrl</Kbd>+<Kbd>Enter</Kbd> menjalankan · <Kbd>Ctrl</Kbd>+<Kbd>M</Kbd> lalu{" "}
          <Kbd>Tab</Kbd> keluar dari editor (pengguna keyboard)
        </p>
      )}
    </div>
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd className="rounded border border-border bg-surface px-1 font-mono text-[0.9em]">
      {children}
    </kbd>
  );
}
