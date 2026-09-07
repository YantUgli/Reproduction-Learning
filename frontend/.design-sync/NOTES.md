# design-sync NOTES — reproduction-learning-engine-frontend

Repo-specific gotchas for future syncs. This is a Next.js **app**, not a packaged
design system, so the sync runs in `package` shape with a **hand-written entry**.

## Setup that must be re-done on a fresh clone
- Run everything from `frontend/` (the JS project root; `node_modules`, `tsconfig`,
  components all live here). `.design-sync/` and `.ds-sync/` live under `frontend/`.
- `--node-modules ./node_modules`, `--entry ./.design-sync/entry.ts`.
- Playwright/chromium: the machine cache has `chromium-1234`, which is pinned by
  **playwright 1.62.1** (NOT latest — latest wants 1243). Install
  `playwright@1.62.1 playwright-core@1.62.1` in `.ds-sync/`, and run validate with
  `PLAYWRIGHT_BROWSERS_PATH=$HOME/.cache/ms-playwright`. Bare `playwright` installs
  1.63 → chromium 1243 → `Executable doesn't exist`.

## Why the hand-written entry (`.design-sync/entry.ts`)
- No component `dist/` exists. The converter's auto-synth entry uses `export * from`,
  which **drops default exports** — and every component here is `export default`.
  So `entry.ts` re-exports each default as a **named** export (+ icon/helper named
  exports). Add new components there AND in `cfg.componentSrcMap`.

## next/link poisons the browser bundle (fixed via shim)
- PageHeader imports `next/link`, which references `process.env.__NEXT_ROUTER_BASEPATH`
  etc. at eval time. In the browser IIFE `process` is undefined → the WHOLE
  `window.RLE` assignment crashes (`[BUNDLE_EXPORT] 14/14 missing`,
  `ReferenceError: process is not defined`).
- Fix: `.design-sync/shims/next-link.tsx` (a plain `<a>`), aliased via
  `.design-sync/tsconfig.sync.json` (`paths: { "next/link": [...] }`), pointed at by
  `cfg.tsconfig`. PageHeader only renders a Link when `backHref` is set, so the shim is
  visually faithful. The real app keeps real `next/link` — the alias is sync-only.

## CSS / Tailwind
- Components use Tailwind utility classes, not shipped CSS. Before each sync, compile:
  `./node_modules/.bin/tailwindcss -i app/globals.css -o .design-sync/compiled.css --minify`
  (content globs in `tailwind.config.ts` scan `app/**`, capturing every utility the app
  uses + tokens + `@font-face`). `cfg.cssEntry` points at `compiled.css`.
- **Re-sync risk:** `compiled.css` is a build artifact committed as the cssEntry input.
  If component/page classes change, RECOMPILE before building or the new utilities won't
  ship and cards render unstyled.

## Fonts
- IBM Plex self-hosted at `public/fonts/*.woff2`; `@font-face` lives in `globals.css`
  (→ compiled.css). `cfg.extraFonts` lists the 6 woff2 so they land in `fonts/`.
  Build log's `extraFonts: ... add a matching @font-face` line is benign — the
  @font-face already ships via compiled.css (urls rewritten to `fonts/`).

## Authored-preview gotcha: Tailwind JIT only emits USED classes
- `compiled.css` contains only the utilities the app actually uses. A preview that uses an
  ad-hoc class the app never uses (e.g. `h-4`, `w-1/2`) renders it as 0-size / unstyled.
  Skeleton's `Base` cell hit this (blank bars) — fixed by using `h-6/h-3/w-2/3/w-32/w-24`,
  which KpiRow/EditorSkeleton already use. When authoring previews, prefer classes the app
  uses, or inline styles for layout glue.
- All 14 components have authored, graded-good previews (no floor cards remain).

## Re-sync risks
- `compiled.css` staleness (see CSS section) — the #1 thing to re-run.
- Playwright version pin (1.62.1) tied to the machine's cached chromium build; a new
  machine with a different cache needs the matching version (see Setup).
- The hand entry + componentSrcMap must both list every synced component; adding a
  component in one but not the other silently drops it or breaks its card.
