# Reproduction Learning Engine — design system

React + Tailwind CSS with CSS-variable design tokens (GitHub Primer base). All 14
components import from `window.RLE.*`. Self-hosted **IBM Plex Sans/Mono** ship with the
bundle. No emoji anywhere — status and verdicts use token color + inline line-SVG icons.

## Setup / wrapping
- **No provider or theme wrapper is required.** Tokens are CSS variables on `:root`,
  always loaded via `styles.css`. Just render a component.
- One exception, only if you use it: `ConfirmDialog` is normally driven by
  `ConfirmProvider` + the `useConfirm()` hook, but it also renders standalone from props
  (`open`, `title`, `onConfirm`, `onCancel`). It portals to `document.body`.
- Icons (`IconCheck`, `IconX`, `IconArrowRight`, `IconInbox`, `IconLock`, `IconClock`,
  `IconStopwatch`, `IconTarget`) are exports too — line SVGs sized via a `size` prop.

## Styling idiom — Tailwind utilities bound to semantic tokens
Style layout with Tailwind utilities; never hard-code hex — use the token classes:

| Role | Classes |
|---|---|
| Primary action / "you are here" | `bg-accent` `text-accent-fg` `text-accent` `border-l-accent` |
| **Proven by execution only** | `text-success` `bg-success-bg` |
| Fail / lapsed | `text-danger` `bg-danger-bg` |
| **Ember — scaffold warmth (identity role)** | `text-ember` `bg-ember-bg` |
| Caution (fragile / decayed) | `text-warning` `bg-warning-bg` |
| Text hierarchy | `text-fg` `text-muted` `text-subtle` |
| Surfaces | `bg-canvas` `bg-surface` `bg-surface-muted` `border-border` |
| Code / test output | `bg-code-bg` `text-code-fg` `font-mono` |
| Radius / width / scale | `rounded-md` (8px) `rounded-lg` (12px) · `max-w-content` (820) `max-w-wide` (980) · `text-13` · `tabular-nums` |

## The Proof Law (governing rule of this product)
Only what **code execution proved** gets a solid fill or a check. Everything unproven —
read, visited, mapped, AI-proposed — is outline/ghost. Concretely: `Badge` and
`StatusBadge` render proven states solid and unproven states with `variant="outline"`.
Never show "read" or "visited" as if it were proven. Green (`text-success`) means an
execution passed, nowhere else.

## Where the truth lives
- `styles.css` → imports `fonts/fonts.css` + `_ds_bundle.css` (tokens + all component CSS).
- Per-component `<Name>.d.ts` (props) and `<Name>.prompt.md` (usage). Read these before
  composing a component.

## One idiomatic snippet
```tsx
import { Card, Button, StatusBadge, IconArrowRight } from "reproduction-learning-engine-frontend";

<Card className="flex items-center justify-between gap-3 border-l-4 border-l-accent p-4">
  <div>
    <div className="font-semibold text-fg">Paginasi query</div>
    <div className="font-mono text-xs text-subtle">n001_paginate · mulai di sini</div>
  </div>
  <StatusBadge status="available" />        {/* unproven → renders outline */}
  <Button variant="primary">Jalankan &amp; Verifikasi <IconArrowRight size={15} /></Button>
</Card>
```
