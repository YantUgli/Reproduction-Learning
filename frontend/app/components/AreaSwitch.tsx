"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { IconAuthoring, IconForge, IconLibrary } from "./ui/Icon";

/**
 * Frame orientasi persisten (brief §5/§8) — satu-satunya nav global.
 *
 * Dua lajur belajar Bryant (Forge, Library) + satu meja kurasi Isyah (Authoring).
 * Sebelum reshape tiap halaman menempel "← Dashboard" sendiri tanpa penanda lokasi;
 * ini menggantinya dengan satu bar tenang + cue "kamu di sini".
 *
 * INVARIANT (§4): permukaan Bryant nol afordansi authoring. Tab **Authoring
 * disembunyikan saat kill switch integrasi mati** (`GET /authoring/status`
 * → `enabled=false`). Jalur Bryant (Forge/Library) tak pernah bergantung padanya.
 */

type Area = "forge" | "library" | "authoring";

const TABS: { area: Area; href: string; label: string; Icon: typeof IconForge }[] = [
  { area: "forge", href: "/", label: "Forge", Icon: IconForge },
  { area: "library", href: "/library", label: "Library", Icon: IconLibrary },
  { area: "authoring", href: "/authoring", label: "Authoring", Icon: IconAuthoring },
];

function areaOf(pathname: string): Area {
  if (pathname.startsWith("/library")) return "library";
  if (pathname.startsWith("/authoring")) return "authoring";
  return "forge"; // "/", "/node/*", "/placement", "/review"
}

export default function AreaSwitch() {
  const pathname = usePathname() ?? "/";
  const active = areaOf(pathname);
  // null = belum tahu (jangan kedip); false = kill switch mati → sembunyikan tab.
  const [authoringVisible, setAuthoringVisible] = useState<boolean | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getIntegrationStatus()
      .then((s) => alive && setAuthoringVisible(s.enabled))
      // Backend mati / integrasi off → jaga permukaan Bryant tetap bersih.
      .catch(() => alive && setAuthoringVisible(false));
    return () => {
      alive = false;
    };
  }, []);

  const tabs = TABS.filter((t) => {
    if (t.area !== "authoring") return true;
    // Sembunyikan sampai jelas aktif — dan saat aktif tetap tampil meski sedang di
    // halaman authoring (dicapai via URL langsung), supaya nav tak "menghilang".
    return authoringVisible === true || active === "authoring";
  });

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-surface">
      <div className="mx-auto flex w-full max-w-wide items-center justify-between gap-4 px-4 py-2.5 sm:px-6">
        <Link
          href="/"
          className="flex min-w-0 items-center gap-2 text-fg no-underline hover:no-underline"
        >
          <IconForge size={16} className="shrink-0 text-accent" />
          <span className="truncate text-sm font-semibold tracking-tight">
            Reproduction Learning Engine
          </span>
        </Link>

        <nav aria-label="Area" className="flex shrink-0 items-center gap-1">
          {tabs.map(({ area, href, label, Icon }) => {
            const isActive = area === active;
            return (
              <Link
                key={area}
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-13 font-semibold no-underline transition-colors hover:no-underline ${
                  isActive
                    ? "bg-info-bg text-accent"
                    : "text-muted hover:bg-surface-muted hover:text-fg"
                }`}
              >
                <Icon size={14} />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
