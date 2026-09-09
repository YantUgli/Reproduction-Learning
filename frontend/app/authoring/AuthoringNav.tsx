"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

/**
 * Sub-nav meja Isyah (brief §5): **Audit desk** (primer) + **AI queue** (sekunder).
 *
 * Sejak 2026-08-31 approve manusia bukan lagi gerbang blokir — gerbang mesin +
 * promosi otomatis yang memutuskan, dan peran Isyah pindah ke belakang jadi auditor.
 * Maka audit yang jadi landing; antrean approve turun jadi tab kedua (masih relevan
 * saat `CLAUDE_AUTO_PROMOTE=0`).
 */
const TABS = [
  { href: "/authoring", label: "Audit desk", hint: "telemetri kurikulum" },
  { href: "/authoring/queue", label: "AI queue", hint: "picu · approve · reject" },
];

export default function AuthoringNav() {
  const pathname = usePathname() ?? "/authoring";
  return (
    <nav className="mb-6 flex flex-wrap gap-1 border-b border-border">
      {TABS.map((t) => {
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            aria-current={active ? "page" : undefined}
            className={`-mb-px inline-flex items-baseline gap-2 border-b-2 px-3 py-2 text-sm font-semibold no-underline hover:no-underline ${
              active
                ? "border-accent text-fg"
                : "border-transparent text-muted hover:text-fg"
            }`}
          >
            {t.label}
            <span className="font-mono text-[11px] font-normal text-subtle">{t.hint}</span>
          </Link>
        );
      })}
    </nav>
  );
}
