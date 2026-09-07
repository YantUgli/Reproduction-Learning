import type { AnchorHTMLAttributes, ReactNode } from "react";

/**
 * Shim `next/link` untuk bundle design-system (di-render DI LUAR Next).
 *
 * `next/link` asli memakai `process.env.__NEXT_ROUTER_BASEPATH` dkk. di waktu-eval;
 * di browser (tanpa Next) `process` tak ada → seluruh IIFE `window.RLE` crash. Di
 * produk, PageHeader hanya merender Link bila `backHref` diberikan, jadi shim <a>
 * biasa ini setia secara visual untuk kartu preview tanpa menyeret runtime router.
 * Hanya dipakai oleh design-sync (alias di tsconfig.sync.json) — app asli tetap
 * memakai `next/link` sungguhan.
 */
export default function Link({
  href,
  children,
  ...rest
}: { href: string } & AnchorHTMLAttributes<HTMLAnchorElement> & { children?: ReactNode }) {
  return (
    <a href={typeof href === "string" ? href : "#"} {...rest}>
      {children}
    </a>
  );
}
