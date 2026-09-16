<!-- Disalin apa adanya dari docs/ux-brief.md (§2, §3, §4, §8) — hasil triase keep/quarantine.
     Struktur asli (§5 IA, §6 flows, §7 screen specs) DIKARANTINA, tidak disalin ke sini. -->

## 2. Domain model (the skeleton)

The schema is deliberately **domain-agnostic** (`backend/app/models.py`): no `http_method` column,
no per-domain fields. Domain specificity lives in `grader_type` + the contents of `data/`. This is
why one loop serves FastAPI, React, and ML unchanged — and the UI must stay domain-agnostic too
(no `if domain == "react"` branches; the backend already derives editor `language` per node).

| Entity | Key fields (UI-relevant) | Relationships |
|---|---|---|
| **Domain** | `id`, `name`, `status` (draft/active/archived) | has many Node; has a `destination` (in `domain.yaml`, human-set, the one thing no machine sets) |
| **Node** | `id`, `concept`, `description`, `grader_type`, `estimated_minutes`, `timebox_seconds`, `status_default` | belongs to Domain; has many ChallengeInstance, ComprehensionProbe; linked by Edge; has one ScheduleItem |
| **Edge** | `from_node_id`, `to_node_id`, `type` (**hard** = locks order, **soft** = suggestion only) | Node → Node. AI-proposed edges are always `soft` |
| **ChallengeInstance** (variant) | `id`, `variant_label`, `prompt`, `starter_code`, `signature_contract`, `scaffold_level` (L3–L0) | belongs to Node. ≥2 variants required; L0 verify uses a *different* variant than teaching = transfer, not memorization |
| **ComprehensionProbe** | `id`, `type` (predict_output / spot_bug / trace), `question`, `options[]`, `correct_answer` (**server-only, never sent to client**) | belongs to Node. Deterministic — one right answer, no free text |
| **Attempt** | `id`, `mode` (placement/acquisition/verification/review), `scaffold_level`, `result` (pass/fail — **only execution writes this**), `test_output`, `probe_result`, `duration_seconds`, `submitted_code` | belongs to Node/Instance/Session. The atomic unit of truth |
| **ScheduleItem** | `node_id` (PK), `status` (locked/available/acquired/mastered/lapsed), `due_at`, `consecutive_success`, FSRS state | one per Node. The FSRS card |
| **Session** | `id`, `mode`, `ai_available` (**must be false for verification**) | groups Attempts (placement ordering) |
| **SkillHypothesis** | `node_id`, `source`, `confidence`, `rationale`, `status` (unverified → confirmed/refuted_by_attempt) | AI proposal; **never a verdict** — only an Attempt can confirm |
| **Library material** (files in `library/`, not DB) | `title`, `type` (note/transcription/outline/roadmap), `note_status` (outline/captured — a *label*, never progress), `node_ids[]` | maps to Nodes; "% reproduced" is computed by joining `node_ids` → Attempts, **never stored** |

**Status ladder (the spine of the map):** `locked → available → acquired → mastered`, with `lapsed`
as the decay branch (a failed review drops `acquired`/`mastered` → `lapsed`, which recovers to
`acquired`, never back to `available` — the memory decayed, the proof didn't).

**Scaffold ladder (the spine of a session):** `L3 worked example → L2 faded skeleton → L1 signature
only → L0 cold verify`. Only L0 sends a graded, KPI-counting attempt; L3–L1 are practice.

---

## 3. Capabilities (the verbs)

Every verb below is backed by a real endpoint. A screen with no backing endpoint is flagged as a
gap in §7, not designed as if it worked.

| Verb (user-facing) | Backing capability | Who |
|---|---|---|
| See my progress & the one KPI that matters | `GET /stats` | Bryant |
| Browse the node map (linear, per domain) | `GET /nodes` | Bryant |
| Open a node and fade the scaffold | `GET /nodes/{id}`, `GET /nodes/{id}/level/{L}` | Bryant |
| **Reproduce and get a verdict** (the heart) | `POST /attempts` | Bryant |
| Answer a comprehension probe | `GET /nodes/{id}/probe`, `POST /probes/answer` | Bryant |
| See just-in-time material — **only after I've failed** | `GET /nodes/{id}/explanation` (returns **403** until a failed attempt exists) | Bryant |
| Find my floor without being asked what I know | `POST /placement/start`, `GET /placement/{id}`, `POST /placement/{id}/submit` | Bryant |
| Do today's due reviews (cold, new variant) | `GET /review/due`, `GET /review/{id}/challenge`, `POST /review/submit`, `POST /review/probe` | Bryant |
| See how much of my Library I've *reproduced* | `GET /library/progress` | Bryant |
| Trigger AI authoring roles (R2/R3/R4/node) | `POST /authoring/{r2,r3,r4,node}` (async; `202`) | Author |
| Review / approve / reject an AI artifact | `GET /authoring/jobs`, `/jobs/{id}`, `POST …/approve`, `…/reject` | Author |
| Audit the curriculum by telemetry | `GET /authoring/audit` | Author |
| See integration status + AI's hard limits | `GET /authoring/status` | Author |
| Inspect R2 hypotheses (proposals, never verdicts) | `GET /authoring/hypotheses` | Author |
| **Retire a flagged node** | *no endpoint yet* — see §7 gap | Author |

**Never a capability, by invariant:** AI declaring mastery, AI grading free text, AI setting a final
`hard` prerequisite edge. The UI must never render an affordance implying any of these.

---

## 4. Role matrix

No permission enforcement exists in code; this is separation by **area and intent**, plus the
kill switch. Design the two areas so they never bleed together.

| Capability | Bryant (learner) | Author |
|---|---|---|
| Dashboard, node loop, placement, review, library | ✅ primary | (can view, not their job) |
| Just-in-time material | ✅ but only post-failure (403 gate) | — |
| Trigger AI roles / approve / reject | — (never surfaced to Bryant) | ✅ (disabled when kill switch off → 503) |
| Audit + retire | — | ✅ |
| Set domain `destination` | — | ✅ (the only human-only judgment) |

**Design consequence:** Bryant's surface must contain **zero** authoring affordances. The current
dashboard leaks a "Review authoring" link into Bryant's header — the reshape moves that behind an
explicit area switch (§5), because mixing "prove yourself" with "curate content" muddies the one
job.

---

## 8. Visual direction (tokens)

Ground: the subject is a **forge**. You don't read about the metal — you reproduce it, from cold,
and it's tested by execution, not opinion. The scaffold *fades* from a warm, fully-supported worked
example (L3) to a cold, bare, timeboxed verify (L0). That fade is the product's soul, and it's the
signature. Everything else stays quiet GitHub-Primer discipline (the brand constraint), so the one
bold move reads.

This is deliberately **none of the three AI-default looks** (cream+serif+terracotta; near-black+acid
accent; broadsheet hairlines). It's an engineered, instrument-panel identity — closer to a workshop
gauge than a magazine.

### The Proof Law (the design's governing rule)
> **Only what execution proved gets a solid fill and a check. Everything unproven is ghost/outline.**
Visited scaffold levels, read material, mapped-but-unproven nodes, AI proposals — all rendered as
outline, dotted, or muted. A solid fill or a ✓ is *earned by running code*, nowhere else. This is
not decoration; it's the visual encoding of the product's core invariant.

### Color (extends the audited Primer palette — new roles marked)
| Token | Hex | Role |
|---|---|---|
| `--fg` (steel ink) | `#1f2328` | text — *existing* |
| `--canvas` / `--surface` | `#f6f8fa` / `#ffffff` | grounds — *existing* |
| `--accent` (steel blue) | `#0969da` | primary action, "you are here" — *existing, AA-audited* |
| `--proof` (execution green) | `#1a7f37` | **reserved for execution-proven only** — *existing `--success`, renamed in intent* |
| `--fail` | `#cf222e` | test failed / lapsed — *existing* |
| `--ember` | `#bc4c00` | **NEW role: scaffold support / warmth.** The warm end of the temper line (L3), just-in-time material, "supported" affordances. A real Primer orange → stays in-family and auditable |
| `--fragile` (amber) | `#9a6700` | probe-wrong, decayed, needs-variants — *existing `--warning`* |

The temper line runs `--ember` (warm, supported, L3) → neutral steel → cold `--fg`/accent (L0).
Keep the dark-mode path the M-UI decision reserved (a `.dark { … }` block over the same tokens).

### Type (a designed superfamily, self-hosted for local-first)
The app is code-first (node IDs, contracts, test output, KPI numerals everywhere) — the mono face
should be *designed*, not a system fallback. Recommend **IBM Plex** — engineered, IBM-heritage,
"build not consume," and its mono is purpose-built for code:
- **Display / headings:** IBM Plex Sans, 600–700, tight tracking. Precise, mechanical, not soft.
- **Body:** IBM Plex Sans, 400–500 (cohesive superfamily).
- **Utility / data / code:** IBM Plex Mono — node IDs, `signature_contract`, the L3–L0 level
  markers, test output, all KPI numerals (`tabular-nums`).
- **Self-host** the fonts (as Monaco was self-hosted per the 2026-08-24 decision) so offline =
  local-first holds. Fallback stack `system-ui, -apple-system, …` stays.

### Layout concept
A persistent quiet frame (area switch: Forge · Library · Authoring — Authoring hidden when the kill
switch is off) around content at the existing `max-w-content` (820) / `max-w-wide` (980). The
acquisition session is laid out as a literal **descent**: the temper line at the top, then the
prompt, then the cold sandbox, so scrolling down = fading the scaffold.

```
DASHBOARD (/)
┌──────────────────────────────────────────────────────────────┐
│ ◆ Forge   ▤ Library   ⚙ Authoring            [area switch]    │
├──────────────────────────────────────────────────────────────┤
│  reproduce-without-AI     mastered      due       reproduced  │
│      72%  ▸solid          6 / 19        3         41%         │  ← KPI: proof green only
│  ────────────────────────────────────────────────────────    │
│  Due today                                    [run placement] │
│  ▸ Path param 404 · overdue 1.2d · spaced 2/4         [due]   │
│  ────────────────────────────────────────────────────────    │
│  FastAPI                                                       │
│   ┃ Paginate query        ● Mulai di sini →      [available]  │  ← next: accent left-border
│   ▫ Get JSON route        proven 100% (3/3)      [mastered]   │  ← solid = proven
│   ░ Nested body list      locked — finish prereq first        │  ← ghost = locked
└──────────────────────────────────────────────────────────────┘

NODE SESSION (/node/[id]) — the temper line signature
┌──────────────────────────────────────────────────────────────┐
│ ← Forge                              ⏱ 20:00 (L0 only)        │
│ Path parameter with 404                                       │
│ n003_path_param_404                                           │
│                                                               │
│  L3 ●───── L2 ●───── L1 ●───── L0 ◧    ← temper line: warm→cold│
│  ember      ·         ·        steel     (dots = visited, NOT ✓)│
│                                                               │
│  L0 · Verify (no AI, timebox running)                         │
│  ┌───────────────────────────── prompt ──────────────────┐   │
│  │ Return 404 when the item id is unknown …               │   │
│  └────────────────────────────────────────────────────────┘   │
│  ┌──────────────── cold sandbox (AI OFF) ─────────────────┐   │
│  │ 1                                                       │   │
│  │   Write from scratch — no example, no AI.               │   │
│  └────────────────────────────────────────────────────────┘   │
│  [ Run & Verify ]  ⌘⏎                                         │  ← the primary CTA, unmistakable
└──────────────────────────────────────────────────────────────┘
```

### Signature
**The temper line** — the L3·L2·L1·L0 ladder drawn as a horizontal support-gradient that visibly
cools from ember (fully-scaffolded worked example) to cold steel (bare L0 verify). It appears on
every session and placement, encodes something true (support fades; only the cold end counts), and
is the one element the product is remembered by. Paired with the Proof Law, it needs no other
flourish — keep everything else disciplined and quiet.

### Brand constraints to honor (from `CLAUDE.md` §7 M-UI decisions)
- Tokens are the **single source of truth** (CSS variables → Tailwind); never hard-code a hex.
- **No emoji** anywhere — status/verdict use token color + inline line-SVG icons.
- Keep the WCAG-AA contrast fixes (`--subtle #656d76`, explicit `--fg-disabled`, no opacity-dimming).
- Keep the distinct primary CTA, fixed-width timebox slot (no layout shift), and the empty-editor
  caption approach.
- Reduced-motion respected; visible keyboard focus (`:focus-visible` outline) already global — keep.
