# UI/UX Design Brief — Reproduction Learning Engine

> Handoff artifact. Self-contained: a designer (human or Claude Design) needs nothing but this
> document. Derived by reading the code directly (backend routers, models, existing frontend),
> not from a file tree. Scope: **whole app**. Direction: **reshape the existing Next.js + Tailwind
> frontend**, honoring the M-UI token decisions in `CLAUDE.md` §7.

---

## 1. Essence

- **Subject:** A reproduction-based learning engine — you don't learn by consuming material, you
  learn by *re-producing* code from cold (a FastAPI endpoint, a React component, an ML function),
  and **only code execution — never AI — decides whether you've mastered it.**
- **Primary users / roles:**
  - **Bryant (learner)** → the whole loop: dashboard, node acquisition, placement, review, library.
  - **Author (Isyah / curator)** → the authoring + audit area, explicitly *not* Bryant's path.
  - There is **no auth layer** in the code (single-user, local-first). "Roles" are areas of intent,
    not permission gates. The only real gate is the kill switch `CLAUDE_INTEGRATION_ENABLED` →
    authoring triggers return `503`.
- **Primary job:** *Reproduce a node without AI and have that verdict trusted.* Everything else —
  the map, the schedule, the library — exists to feed or protect that one signal.
- **Scope of this brief:** whole app (Forge loop + Library lane + Authoring/Audit).
- **Reshape or greenfield:** reshape. Keep the token discipline (CSS variables as single source of
  truth, GitHub Primer base, **no emoji**, SVG line icons, distinct primary CTA, WCAG-AA-audited
  contrast) and give it a deliberate identity it currently lacks.

**The one thing the design must protect:** the difference between *proven by execution* and
*merely seen*. The product is built to kill the "illusion of competence." A design that lets
"read" or "visited" feel like progress betrays the whole thesis (see the Proof Law in §8).

---

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

## 5. Information architecture

Two lanes, one persistent orientation. The current app has **no global nav** — every page
hand-rolls a "← Dashboard" link, and there's no active-location cue. The reshape introduces one
quiet persistent frame.

```
Reproduction Learning Engine
│
├─ ◆ FORGE  (Bryant — the loop)
│   ├─ /            Dashboard — the one KPI, due today, the node map
│   ├─ /placement   Find the floor (descending cold challenges)
│   ├─ /node/[id]   Acquisition session — descend L3 → L0 (the temper line)
│   └─ /review      Due reviews (cold, new variant, FSRS reschedule)
│
├─ ▤ LIBRARY  (Bryant — the map)
│   └─ /library     "% reproduced, not % read" — course → module → material
│
└─ ⚙ AUTHORING  (Author — off Bryant's path; hidden when kill switch off)
    ├─ /authoring         Audit desk (telemetry-flagged nodes, edges, destinations)  ← primary
    └─ /authoring/queue   AI job queue + triggers (now auto-promote by default)      ← secondary
```

- **Primary destination = `/` dashboard**, whose spine is the node map (a **linear list grouped by
  domain**, deliberately *not* a DAG/graph explorer — §8 of the PRD calls the DAG explorer the
  "builder's version of the avoidance trap").
- Nested views: Node → its scaffold levels; Course → Module → Material.
- The audit desk becomes the authoring landing (per the 2026-08-31 decision that moved humans from
  a *blocking gate* to a *back-of-house auditor*). The blocking approve queue survives as a
  secondary tab, since auto-promote is now the default.

---

## 6. Primary flows

Each flow must end in an unambiguous **closure** the user recognizes.

### Flow A — Acquire a node (L3 → L0) · the core loop
```
Dashboard → pick "Mulai di sini" node → /node/[id]
  L3 worked example (read the annotated reference)   [no run; "I get it — try it"]
  L2 faded skeleton (fill the gaps)   → Run (practice)  ─┐ decision: iterate or descend
  L1 signature only                   → Run (practice)  ─┤ (practice never counts, said plainly)
  L0 COLD VERIFY (new variant, timebox running, no AI)
      → Run & Verify  →  PASS ──→ comprehension probe
                          │           ├─ correct → ACQUIRED (or MASTERED) + next due date  ✅ closure
                          │           └─ wrong  → still acquired-blocked; interval shortened; try probe again
                          └─ FAIL ──→ test output shown + just-in-time material unlocks (was 403 until now)
                                       → retry level, or climb back up a scaffold
```
- **Decision points:** descend vs iterate (L2/L1); after fail, retry vs climb scaffold.
- **Error points:** timebox expiry (auto-submits — disclosed up front); execution timeout
  (`timed_out` shown, not hidden); submit network error (retry).

### Flow B — Placement (find the floor)
```
/placement → "Start" → descending cold challenges (max 7)
  each: cold sandbox + timebox → Run
  stop at first PASS = your floor  → floor node ACQUIRED, its prerequisites UNLOCKED  ✅ closure
  or 7 fails = exhausted → no status assigned, honest "floor not found yet"  ✅ (also a closure)
```

### Flow C — Daily review
```
/review → due list (or deep-linked ?node=) → cold challenge on a NEW variant → Run
  FAIL → immediately LAPSED (no probe — verdict is already final)  ✅ closure
  PASS → probe → FSRS reschedule (Again/Hard/Good) → outcome panel with next due date  ✅ closure
```

### Flow D — Author: generate + audit
```
/authoring/queue → trigger R3/R4/R2/node → job runs async (pending→running)
  → machine gates (triad, probe executed, verbatim citation) → auto-promote to data/ (default)
     or CLAUDE_AUTO_PROMOTE=0 → stops at "ready", waits for Approve  ✅ closure
/authoring (audit) → telemetry flags suspicious nodes → [Retire] (needs new endpoint)  ⚠ gap
```

---

## 7. Screen specs

The core of the brief. Every state below is real — the current code already implements loading
skeletons, empty-as-invitation, and retryable errors; the reshape keeps those and fixes the gaps
called out per screen.

### 7.1 Dashboard — `/`
- **Job:** answer "what should I do right now, and is my one number healthy?"
- **Data shown:** `GET /stats` (reproduce-without-AI pass rate, mastered count, due count,
  placement floor, per-node status/pass-rate/consecutive-success/due), `GET /review/due`,
  `GET /library/progress` (one number only).
- **Actions:** open next node (`/node/[id]`), start review (`/review?node=`), run placement,
  open library. Each is a real navigation to a backed screen.
- **States:**
  - *Loading:* KPI-row skeleton (exists).
  - *Empty:* no due items → "Nothing due — take an *available* node below, or run placement."
    (invitation, exists). Fresh install (all locked) → point to placement as the entry.
  - *Partial:* Library KPI may be null without breaking the page (Library is a companion, not a
    core KPI source) — show "—", never a crash (exists).
  - *Error:* human sentence + Retry (exists, but currently prints raw `String(e)` like "500: …" —
    **fix:** map to a sentence, keep the code in a "details" disclosure).
  - *Success:* the map renders; the single *next* node is marked "Mulai di sini" with an accent
    left-border (exists — keep, it's the best affordance on the page).
- **Notes:** the map is a **linear list grouped by domain**, never a graph. Locked nodes are
  quiet one-line rows with a *visible* reason (not a hover tooltip). **Remove** the "Review
  authoring" link from Bryant's header (§4) — it belongs in the Authoring area.

### 7.2 Node acquisition session — `/node/[id]` · **the signature screen**
- **Job:** descend the scaffold from worked example to cold verify, and prove reproduction at L0.
- **Data shown:** `GET /nodes/{id}` (concept, id, levels), `GET /nodes/{id}/level/{L}` per level
  (kind, title, prompt, code, signature_contract, editable, show_timebox, language), on demand
  `GET /nodes/{id}/probe`, and — only after a fail — `GET /nodes/{id}/explanation`.
- **Actions:** navigate levels (the temper line), Run (practice) at L2/L1, **Run & Verify** at L0
  (`POST /attempts`), answer probe (`POST /probes/answer`).
- **States:**
  - *Loading:* editor skeleton (exists).
  - *Empty:* editor empty at a cold level → caption "Write from scratch — no example, no AI"
    (exists; keep — it's an invitation, not a placeholder hack).
  - *Partial / practice:* L2/L1 pass shows an explicit "this is practice — **not** counted as
    reproduce-without-AI" note (exists — this honesty is load-bearing; keep it prominent).
  - *Error:* test failure is **shown** (mirror, never hidden); `timed_out` surfaced; the
    just-in-time material appears *only here, after real failure* (403 until then).
  - *Success:* **cleanPass** → green "Node acquired/mastered" panel with next due date + progress
    to mastery (exists). Probe-wrong-but-test-passed → warning panel explaining "produced but
    understanding is fragile; spaced success did **not** increment" (exists — keep verbatim).
- **Notes / invariants the design must not break:**
  - **Visited ≠ proven.** Passed scaffold levels are marked with a *neutral dot*, **never a green
    check**. Green check = "verified by execution" only. This is the Proof Law (§8) in miniature.
  - The sandbox must keep **all AI-assist / autocomplete / suggestions off** (SandboxEditor already
    enforces this at the Monaco layer). No Copilot-style ghost text, ever — it's an invariant, not
    a preference.
  - Dirty-navigation guard (confirm before discarding unrun code) exists — keep it.

### 7.3 Placement — `/placement`
- **Job:** discover the floor by execution, never by self-report.
- **Data shown:** `POST /placement/start` / `GET /placement/{id}` (tested[], current challenge,
  position/max, finished, exhausted, floor).
- **Actions:** Start, submit each cold challenge, restart.
- **States:**
  - *Loading:* pre-start explainer card ("what will happen", 3 steps) — a deliberate empty state
    that sets expectations (exists; keep).
  - *Partial:* per-node pass/fail chips accumulate as you descend (exists).
  - *Error:* submit error + Retry (exists).
  - *Success:* two distinct closures — **floor found** (green, floor node + unlocked prerequisites,
    "unlocked, not claimed mastered") and **exhausted** (warning, "floor not found yet — that's
    itself information; no status assigned"). Both are dignified, neither reads as failure.
- **Notes:** there is intentionally **no "what can you already do?" question** anywhere. Don't add
  one in the redesign — it would reintroduce self-report.

### 7.4 Review — `/review`
- **Job:** re-prove a due node cold, on a variant you haven't just done.
- **Data shown:** `GET /review/due`, `GET /review/{id}/challenge` (new variant, previous variant id,
  `needs_more_variants` flag), then submit/probe outcomes with FSRS rating + next interval.
- **Actions:** pick a due node, submit cold challenge, answer probe.
- **States:**
  - *Empty:* no due → "Spaced repetition only works if the spacing is respected — come back later."
    (invitation-shaped honesty; exists).
  - *Partial:* `needs_more_variants` warning → "variants are thinning; that's a signal to author a
    new one, not a reason to stop" (exists).
  - *Error:* fail → **immediately lapsed** outcome panel (red) — the design must make lapse feel
    like decay to recover from, not punishment (copy already does this; keep).
  - *Success:* outcome panel with status badge, FSRS rating, next due, spaced-success counter, and
    the nuance line ("not yet due, so not counted" / "probe wrong: produced but fragile").
- **Notes:** the "new variant" promise is central — surface the variant label so Bryant *sees* it's
  different from last time.

### 7.5 Library — `/library`
- **Job:** show how much of the map has been **reproduced**, never how much has been read.
- **Data shown:** `GET /library/progress` → course → module → material, each material's `state`
  (`unmapped` / `mapped_unproven` / `reproduced`), `note_status` (label only), `mastered`,
  `decayed`, `missing_node_ids`.
- **Actions:** open the node behind a material (only when mapped and not missing).
- **States:**
  - *Empty:* no courses → point to `course-intake` / `learn-intake` skills (invitation; exists).
  - *Partial:* course bars show a **hole** where materials are unmapped — the hole is the point,
    not a rendering bug. Materials with `missing_node_ids` flagged in danger color.
  - *Success:* the single "% reproduced" card, capped at 99% until truly complete (never rounds up
    to a lying 100%; exists — this rule is sacred, keep it).
- **Notes:** `note_status` may appear as a *neutral label per row* — **never** accumulated into a
  percentage, progress bar, or sort order. If the design ever aggregates it, the lane has become
  the consumption-comfort trap the product rejects.

### 7.6 Authoring — Audit desk (`/authoring`) · **primary authoring surface**
- **Job:** let the author see which nodes the telemetry distrusts, and act — without standing in
  Bryant's way.
- **Data shown:** `GET /authoring/audit` → `coverage` (how much curriculum even has data — vital
  with n=1), `node_signals` (flagged nodes: never-fails=trivia, never-passes=broken, low
  discrimination), `edge_findings` (uncorroborated edges), `domains_without_destination`.
- **Actions:** inspect a flagged node; **retire a node** ⚠; set a domain `destination` ⚠.
- **States:**
  - *Loading:* skeleton.
  - *Empty:* no flags → must **not** read as "all healthy" with one learner. Copy: "No flags yet —
    with a single learner this usually means *not enough data*, not *all good*." Show `coverage`
    prominently so emptiness is legible.
  - *Error:* human sentence + retry.
  - *Success:* a ranked, reason-annotated list — "list with reasons and numbers," decidable in
    seconds (per the router's own design note). Not a dashboard, not a graph.
- **⚠ GAP (be honest to the user):** the **retire** action and **set-destination** action have
  **no backing endpoint** — `GET /authoring/audit` is read-only. Design the buttons, but mark them
  as *requires a new backend capability* (`POST /authoring/nodes/{id}/retire`,
  `PUT /domains/{id}/destination`). Don't ship them as if they work — a screen whose action has no
  endpoint is a fiction.

### 7.7 Authoring — AI job queue (`/authoring/queue`) · secondary
- **Job:** trigger AI roles and, when auto-promote is off, approve/reject artifacts.
- **Data shown:** `GET /authoring/status` (enabled, CLI available, counts, **"never does" list**),
  `GET /authoring/jobs` + `/jobs/{id}` (role, status, gate result, artifact files, existing-file
  diff, prompt), `GET /authoring/hypotheses`.
- **Actions:** trigger R3/R4/R2/node; approve → promote; reject with reason.
- **States:**
  - *Loading / partial:* pending/running jobs poll every 4s (exists).
  - *Disabled:* kill switch off → triggers disabled + a clear "integration off; the core loop runs
    fully without it" message (exists).
  - *Error:* gate failure shows the machine reason (e.g. "starter passed hidden test") — keep it
    technical here; this is the author's tool.
  - *Success:* "approved — files written: …" confirmation (exists).
- **Notes / fixes:**
  - **Replace `window.prompt("reason…")`** for rejection with an in-UI field (a raw browser prompt
    breaks consistency and the interface voice).
  - Always surface the **"never does"** list (declares mastery / grades free text / sets final
    edges) — it's the honesty that makes the AI integration acceptable. Keep it visible, not buried.
  - The `AuthoringJob` type still says `role: "r2"|"r3"|"r4"` while the backend added `node` (L4) —
    reconcile in the type + the UI so the L4 node-birth job renders.

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

---

## 9. HCI compliance (Phase 4 audit)

Checked every screen and flow against Shneiderman's 8 Golden Rules + Nielsen's 10 Heuristics. The
current build is already unusually strong on **state & feedback** and **honest closure** — most
fixes are about consistency, orientation, and one fiction to remove.

**Already compliant (keep, don't regress):**
- *All five states designed* on every core screen (loading skeletons, empty-as-invitation, partial,
  shown errors with retry, explicit success closures). Rare and good.
- *Errors as learning, not punishment* — test failure is shown, not hidden (mirror invariant).
- *Reversal / control* — dirty-code confirm before navigation; timebox auto-submit disclosed in
  advance so it's not a surprise.
- *Recognition over recall* — the "Mulai di sini" next-node cue; the temper line always shows where
  you are in the ladder.
- *Aesthetic honesty* — practice-pass is labeled "not counted"; % reproduced never rounds up to a
  lying 100%; visited levels get a neutral dot, never a green check.

**Fixed in this spec (violation → change):**
1. *Consistency / voice* — rejection reason uses a raw `window.prompt` (§7.7). **Fix:** in-UI field
   in the interface's voice.
2. *Error voice* — dashboard/others render raw `String(e)` ("500: …"). **Fix:** human sentence up
   top, technical detail in a disclosure.
3. *Orientation* — no global nav; each page reinvents "← Dashboard," no active-location cue.
   **Fix:** the persistent quiet area-switch frame (§5/§8).
4. *Role bleed* — authoring link sits in Bryant's dashboard header. **Fix:** move it into the
   Authoring area (§4). Bryant's surface carries zero authoring affordances.
5. *Empty ≠ healthy* — the audit desk's empty state could read as "curriculum is fine" when it
   really means "n=1, not enough data." **Fix:** coverage-forward empty copy (§7.6).
6. *Fiction removed* — the **retire** and **set-destination** buttons have no endpoint. **Fix:**
   marked as requiring new backend capability, not shipped as working controls (§7.6).
7. *Efficiency* — keep and extend accelerators (⌘/Ctrl+Enter to run already exists); the author's
   queue benefits from keyboard approve/reject.

**Invariant checks (product-specific, beyond generic HCI):**
- No screen offers AI a path to declare mastery, grade text, or set a final edge. ✅
- The sandbox never suggests solutions (AI-assist off at the Monaco layer). ✅ — must never regress.
- Nothing renders "read/visited/mapped" as proof (Proof Law). ✅

---

## 10. Claude Design handoff

> **For Claude Design:** This brief is the complete source of truth — you do **not** need to inspect
> a repository or a file tree. The data model (§2), capabilities (§3), roles (§4), IA (§5), flows
> (§6), and per-screen specs including all states (§7) are already derived from the actual codebase.
> Build the screens in §7 to the visual direction in §8, honoring every state and the HCI notes in
> §9. If anything is ambiguous, ask — don't invent data or actions that aren't in §2–§3. In
> particular: the **retire** and **set-destination** controls have no backend yet (§7.6) — design
> them as clearly pending, not as working actions.

### How to load this into Claude Design (two steps)
1. **Establish the design system once — via `/design-sync`, not by pasting.** From Claude Code, run
   `/design-sync` to pull this repo's real components (`app/components/ui/*` — Button, Card, Badge,
   PageHeader, EmptyState, ErrorState, Skeleton) and the token layer (`globals.css`,
   `tailwind.config.ts`) into Claude Design as a design system. There's already a clean, reusable
   component layer, so detection will be reliable. (Optional MCP route:
   `claude mcp add --scope user --transport http claude-design https://api.anthropic.com/v1/design/mcp`.)
2. **Generate screens — set the selector, then paste.** In the "Design a…" prompt, set the **Design
   system** dropdown to the system from step 1 (leaving it on **"None"** yields generic output).
   Paste this brief (or a single §7 screen spec). Start with **§7.2 (the node session / temper
   line)** — it's the signature and the hardest; everything else is calmer.

Reality check: Claude Design is a front-end research preview — it won't wire up the FastAPI backend
read in Phase 1, and it has rough edges. Treat its output as a strong first draft to refine in-repo,
not a final deliverable.

---

*Brief generated by reading the codebase directly (models, routers, config, all six frontend pages,
the API client, the sandbox editor). Scope: whole app, reshape. If you'd rather work area-by-area, I
can split this into Forge / Library / Authoring briefs.*
