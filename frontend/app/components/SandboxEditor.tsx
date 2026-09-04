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

  // Matikan layanan bahasa JS/TS SUNGGUHAN, bukan cuma di UI. Untuk node React (`.jsx`
  // → mode `javascript`) Monaco menyalakan layanan bahasa TypeScript-nya yang berjalan
  // di WORKER TERPISAH (`ts.worker`) — bukan `editor.worker` yang kita sediakan. Efeknya
  // dua-duanya buruk: (1) melanggar §2 karena menghidupkan validasi/saran cerdas untuk JS,
  // dan (2) memanggil `ts.worker` yang tak pernah kita bundel → "Missing requestHandler or
  // method: getSyntacticDiagnostics". Python tak punya layanan seperti ini (highlight-nya
  // Monarch di main-thread), makanya bug ini baru muncul begitu node React masuk kurikulum.
  // Mematikan diagnostics + seluruh fitur mode membuat JS/TS berperilaku seperti Python:
  // highlight sintaks tetap (tokenizer main-thread), tapi tak ada worker bahasa yang
  // dipanggil. §2 aman, error hilang.
  for (const d of [
    monaco.languages.typescript.javascriptDefaults,
    monaco.languages.typescript.typescriptDefaults,
  ]) {
    d.setDiagnosticsOptions({
      noSemanticValidation: true,
      noSyntacticValidation: true,
      noSuggestionDiagnostics: true,
    });
    d.setModeConfiguration({
      completionItems: false,
      hovers: false,
      documentSymbols: false,
      definitions: false,
      references: false,
      documentHighlights: false,
      rename: false,
      diagnostics: false,
      documentRangeFormattingEdits: false,
      signatureHelp: false,
      onTypeFormattingEdits: false,
      codeActions: false,
      inlayHints: false,
    });
  }
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
            // Indentasi otomatis ala IDE (indent setelah `def …:`, pertahankan indent
            // baris sebelumnya) memakai onEnterRules bawaan Monaco per-bahasa — Python
            // & JS/TS (React `.jsx`). Deterministik, bukan saran solusi → §2 aman.
            // `"advanced"` (bukan `"full"`) sengaja dipilih: ia TIDAK me-reindent baris
            // yang sudah ada saat mengetik, jadi `starter_code` scaffold L2 tak teracak.
            // Penggandaan indent lama (`def f():`⏎`    x` → 8 spasi) hanya terjadi bila
            // user mengetik spasi manual di atas indent otomatis — sama seperti di IDE.
            autoIndent: "advanced",
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
