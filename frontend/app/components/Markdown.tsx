import type { ReactNode } from "react";

/**
 * Renderer markdown minimal & tanpa dependency untuk prompt/materi node.
 *
 * Sengaja kecil: prompt ditulis Isyah di `data/` (sumber tepercaya, single-user
 * local) dan hanya memakai heading, list, paragraf, bold, dan inline code.
 * Membangun elemen React langsung — TANPA `dangerouslySetInnerHTML` — jadi tak
 * ada pintu XSS. Kalau kelak butuh tabel/code-fence/nested list, tukar dengan
 * `react-markdown` (catat di CLAUDE.md §7).
 *
 * Didukung:
 *   #, ##, ### …   → heading
 *   - / *          → unordered list
 *   ```            → code block (fence)
 *   `code`         → inline code
 *   **bold**       → bold
 *   baris kosong   → pemisah blok (paragraf)
 */
export default function Markdown({ children }: { children: string }) {
  return <div className="text-[15px] leading-relaxed text-fg">{renderBlocks(children ?? "")}</div>;
}

function renderBlocks(src: string): ReactNode[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Baris kosong → lewati (pemisah blok).
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Code block berpagar ``` … ```
    if (line.trim().startsWith("```")) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        buf.push(lines[i]);
        i++;
      }
      i++; // lewati fence penutup
      blocks.push(
        <pre
          key={key++}
          className="my-2 overflow-x-auto rounded-md bg-code-bg p-4 text-[13px] text-code-fg"
        >
          {buf.join("\n")}
        </pre>,
      );
      continue;
    }

    // Heading: satu atau lebih '#'
    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      const depth = heading[1].length;
      const Tag = `h${Math.min(depth + 1, 6)}` as "h2" | "h3" | "h4" | "h5" | "h6";
      blocks.push(
        <Tag key={key++} className="mb-1 mt-3 text-lg font-semibold leading-snug first:mt-0">
          {renderInline(heading[2])}
        </Tag>,
      );
      i++;
      continue;
    }

    // List: baris berurutan diawali '- ' atau '* '
    if (/^\s*[-*]\s+/.test(line)) {
      const items: ReactNode[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        const text = lines[i].replace(/^\s*[-*]\s+/, "");
        items.push(<li key={items.length}>{renderInline(text)}</li>);
        i++;
      }
      blocks.push(
        <ul key={key++} className="my-2 list-disc space-y-1 pl-6">
          {items}
        </ul>,
      );
      continue;
    }

    // Paragraf: kumpulkan baris sampai baris kosong / awal blok lain.
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^#{1,6}\s+/.test(lines[i]) &&
      !lines[i].trim().startsWith("```")
    ) {
      para.push(lines[i]);
      i++;
    }
    blocks.push(
      <p key={key++} className="my-2 first:mt-0 last:mb-0">
        {renderInline(para.join(" "))}
      </p>,
    );
  }

  return blocks;
}

/** Inline: `code` dan **bold**. Code span diproses lebih dulu (isinya literal). */
function renderInline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const parts = text.split(/(`[^`]+`)/g);
  let key = 0;

  for (const part of parts) {
    if (part.startsWith("`") && part.endsWith("`") && part.length >= 2) {
      out.push(
        <code
          key={key++}
          className="rounded bg-neutral-bg px-1.5 py-0.5 font-mono text-[0.9em]"
        >
          {part.slice(1, -1)}
        </code>,
      );
      continue;
    }
    // Di luar code span: tangani **bold**.
    const bold = part.split(/(\*\*[^*]+\*\*)/g);
    for (const seg of bold) {
      if (seg.startsWith("**") && seg.endsWith("**") && seg.length >= 4) {
        out.push(
          <strong key={key++} className="font-semibold">
            {seg.slice(2, -2)}
          </strong>,
        );
      } else if (seg) {
        out.push(<span key={key++}>{seg}</span>);
      }
    }
  }

  return out;
}
