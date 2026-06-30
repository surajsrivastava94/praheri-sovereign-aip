# feat: Next.js AML — confidence meter · evidence timeline · guided demo (Console rebuild Phase 5)

**Created:** 2026-06-30
**Type:** feat
**Depth:** Standard
**Plan:** `~/.claude/plans/shimmying-wandering-fern.md` (Phase 5 — depth polish)
**Predecessors:** P1–P4 (`...-001..004-...`) — all shipped. Next.js console is at
multi-tab parity with Streamlit.

---

## Summary

Bring the three Streamlit "Stage 3" depth features to the Next.js console:
1. **Confidence meter** — a deterministic, explainable confidence score (0–100 +
   band + term-by-term reasons) for the recommendation.
2. **Evidence timeline** — the ring's transactions in chronological order
   (ring-scoped queries, capped, sub-₹50,000 flags).
3. **Guided demo overlay** — a scripted 9-step walkthrough (the demo narration),
   route-aware (Next/Back actually navigate), dismissible, persisted.

Confidence + timeline are **server endpoints** (the math is testable; the queries
stay server-side, mirroring "detection is code"). The guided demo is frontend-only.
Additive: `praheri/` + `app/streamlit_app.py` stay **byte-for-byte untouched** —
the confidence/timeline logic is **re-implemented in `server/`** from the verified
Streamlit functions (`_confidence`, `_ring_timeline`), not imported.

---

## Problem Frame

After P4 the Next.js console matches Streamlit's tabs, but Streamlit's Stage-3
polish (confidence scoring, evidence timeline, guided demo) isn't ported yet.
These are the features that make the demo *read as deep* to a judge: "how is
confidence computed?" (term-by-term answer), "show me the money movement over
time" (timeline), and a self-narrating walkthrough so the operator never loses the
thread. P5 brings them over.

**Goal:** the AML investigation shows a confidence meter (with an explainable
breakdown) and an evidence timeline; a guided-demo overlay scripts the full 3-min
flow and navigates the console as it advances.

---

## Scope Boundaries

**In scope**
- `GET /api/alerts/{id}/confidence` — `{score, band, reasons[]}` (ports `_confidence`).
- `GET /api/alerts/{id}/timeline` — `{rows[], total}` chronological ring txns
  (ports `_ring_timeline`), each row flagged `sub_threshold` if amount < 50,000.
- AML page: a confidence meter + breakdown, and an evidence timeline section.
- A guided-demo overlay: 9 steps, banner with Back/Next/Restart, route-aware,
  dismissible, persisted in localStorage; a sidebar 🎬 toggle to start/stop.

**Out of scope (later phase)**
- Egress-scan extension to `server/`+`web/`, Ollama-down hardening, cold-machine
  rehearsal (P6).
- Confidence/timeline for the verticals (AML-only this phase — the verticals use a
  binary FILE/CLEAR; a vertical confidence model is not in the Streamlit baseline).

### Deferred to Follow-Up Work
- Animating the timeline / charting amounts. A simple chronological list with
  sub-threshold flags matches the Streamlit baseline; charts are gold-plating.

---

## Key Technical Decisions

**KTD-1 — Confidence is a server endpoint, ported faithfully from `_confidence`.**
Re-implement the exact term-by-term scoring in a new `server/confidence.py`
(base-by-recommendation + per-typology adds + multi-typology corroboration +
policy-grounded bonus, clamped 0–100, banded High/Med/Low). It's a pure function
of the cached `inv`. Server-side so it's unit-testable and the breakdown is
authoritative. Mirrors the engine's "detection is code, not the model" principle.

**KTD-2 — Timeline is a server endpoint, ring-scoped (never a full-table scan).**
Re-implement `_ring_timeline` in `server/timeline.py`: for each ring account, query
`Transaction` by `from_account`/`to_account` (indexed), dedupe by txn id, sort by
timestamp, cap at 40, return `{rows, total}`. Each row carries a `sub_threshold`
boolean (amount < 50,000 — the structuring tell). Read-only; the 20k-txn table is
never scanned wholesale.

**KTD-3 — Ring accounts come from the cached investigation.**
Both endpoints derive the ring from `agent.investigate(id, use_cache=True)` —
`objects_touched` filtered to `ACC-` (same as the existing graph route). No new
traversal; instant from cache.

**KTD-4 — Guided demo is frontend-only and route-aware.**
A `DemoOverlay` component holds the 9 steps (title, route, action, narration). Each
step has an optional `href`; Next/Back navigate there (improvement over Streamlit,
which only names the tab). State (active step, on/off) persists in localStorage so
it survives navigation. A sidebar 🎬 toggle starts/stops it. No "done predicate"
auto-detection (Streamlit's ✓ checks) — keep it operator-driven (manual Next),
which is simpler and demo-robust.

**KTD-5 — Reuse the AML investigation query; no new client state coupling.**
The confidence + timeline components take `alertId` and fetch their own endpoints
(gated like `useObject`). They mount on the AML page alongside the existing
investigation. The demo overlay is mounted once in the layout (above the page),
not per-page.

**KTD-6 — Respect `web/AGENTS.md`.** The demo overlay uses `next/navigation`
`useRouter().push()` for route-aware Next/Back — confirm the App-Router navigation
API in `node_modules` before writing (Next 16). Low risk; it's a documented hook.

---

## Engine contract (verified — wrap, never modify)

- `_confidence(inv)` logic (from `app/streamlit_app.py` 209–242): base
  `{FILE:60, ESCALATE:35, CLEAR:15}`; per signal by typology — `structuring`:
  `min(15+3*(n-1), 30)`; `circular_layering`: `+20`; `shared_device_ring`:
  `min(15+2*(n-5), 25)`; else `+10`; `+10` if ≥2 typologies; `+5` if
  `policy_citations`; clamp 0–100; band High≥75 / Med≥45 / Low. `n` = leading
  integer in the signal `detail` (regex `^\s*(\d+)`), else count of `ACC-` evidence
  ids. (`_signal_count`, 198–206.)
- `_ring_timeline(store, ring_accounts, cap=40)` (245–256): per-account
  `query_objects("Transaction", from_account=acct)` + `to_account=acct`; dedupe by
  txn id; sort by `timestamp`; return `(rows[:cap], total)`. Txn props:
  `{txn_id, from_account, to_account, amount, currency, channel, timestamp,
  counterparty_id}`.
- `agent.investigate(id, store=_store, use_cache=True)` → cached dict with
  `objects_touched`, `signals`, `recommendation`, `policy_citations`.
- `_DEMO_STEPS` (110–...): 9 steps (n, title, tab, action, say). Port the
  narration; map "tab" → a Next route.
- Frontend (P1–P4): `getJSON`, query hooks, `Investigation` type, `Sidebar`,
  status tokens, `RoleToggle` placement.

---

## Implementation Units

### U1. Confidence + timeline endpoints

**Goal:** Serve the explainable confidence score and the ring timeline.
**Dependencies:** none.
**Files:**
- `server/confidence.py` (new — ports `_confidence` + `_signal_count`)
- `server/timeline.py` (new — ports `_ring_timeline` + sub-threshold flag)
- `server/main.py` (add 2 routes)
- `tests/test_server_api.py` (extend)

**Approach:**
- `server/confidence.py`: `signal_count(detail, evidence_ids) -> int` and
  `confidence(inv) -> {score, band, reasons}`. Faithful port of the Streamlit math
  (KTD-1).
- `server/timeline.py`: `ring_timeline(store, ring_accounts, cap=40) -> {rows,
  total}`; each row = the txn properties + `sub_threshold: amount < 50000`.
- `server/main.py`:
  - `GET /api/alerts/{id}/confidence`: 404 if alert missing; `inv = investigate(
    ..., use_cache=True)`; return `confidence(inv)`.
  - `GET /api/alerts/{id}/timeline`: 404 if missing; ring accounts =
    `[i for i in inv["objects_touched"] if i.startswith("ACC-")]`; return
    `ring_timeline(_store, ring_accounts)`.

**Patterns to follow:** the `alert_graph` route (ring-account derivation); the
Streamlit `_confidence`/`_ring_timeline` functions (port, don't import).

**Test scenarios** (extend `tests/test_server_api.py`, offline — cache committed):
- `signal_count("7 mule account(s)…", [...])` → 7; `signal_count("no number",
  ["ACC-A","ACC-B","TXN-X"])` → 2 (ACC- count).
- `confidence(inv)` for ALERT-R001 (FILE + structuring): `score >= 75`,
  `band == "High"`, `reasons` includes a "base FILE = 60" term and a structuring
  term. (Matches Streamlit's "ALERT-R001 → 95% High" from the build notes.)
- `GET /api/alerts/ALERT-R001/confidence` → 200, `{score, band, reasons}` shapes;
  `band == "High"`.
- `GET /api/alerts/ALERT-R001/timeline` → 200; `rows` non-empty; `total >=
  len(rows)`; rows sorted by `timestamp`; at least one row has `sub_threshold`
  true or false (boolean present); `rows` length ≤ 40.
- `GET /api/alerts/NOPE/confidence` → 404; `GET /api/alerts/NOPE/timeline` → 404.

**Verification:** `curl` both for ALERT-R001 → High-confidence breakdown + a
chronological ring timeline. New tests green offline.

---

### U2. Frontend: confidence + timeline types + queries

**Goal:** Type and fetch the two endpoints.
**Dependencies:** U1.
**Files:**
- `web/src/lib/api.ts` (add `Confidence`, `TimelineRow`, `Timeline` types)
- `web/src/lib/useAmlExtras.ts` (new — `useConfidence`, `useTimeline`)

**Approach:**
- `Confidence {score: number, band: "High"|"Medium"|"Low", reasons: string[]}`.
- `TimelineRow {txn_id, from_account, to_account, amount, currency, channel,
  timestamp, sub_threshold: boolean}`. `Timeline {rows: TimelineRow[], total:
  number}`.
- `useConfidence(alertId)` / `useTimeline(alertId)` — queries gated on `alertId`.

**Patterns to follow:** `useInvestigation`/`useObject` query shape.

**Test scenarios:** `Test expectation: none — types + thin query wrappers. Verified
in U4 in-browser.`

**Verification:** TypeScript compiles; queries return typed data in U4.

---

### U3. Confidence meter + evidence timeline components

**Goal:** The two display components.
**Dependencies:** U2.
**Files:**
- `web/src/components/ConfidenceMeter.tsx` (new)
- `web/src/components/EvidenceTimeline.tsx` (new)

**Approach:**
- `ConfidenceMeter({ alertId })` — `useConfidence`; render a horizontal meter
  (score 0–100, color by band: High→clear, Medium→escalate, Low→muted) + the band
  label + an expandable term-by-term breakdown (`reasons[]`). The breakdown is the
  "how computed?" answer.
- `EvidenceTimeline({ alertId })` — `useTimeline`; a chronological list (time,
  from→to, ₹amount, channel), with a small red flag/badge on `sub_threshold` rows
  ("sub-₹50k"). Show "showing N of M" when `total > rows.length`.

**Patterns to follow:** `SignalCards` card styling; status color tokens; the
`SourceBadge` pill style for the sub-threshold flag.

**Test scenarios:** `Test expectation: none — presentational over U1 endpoints
(tested in U1). Verified in U4.`

**Verification:** meter shows High for ALERT-R001 with the breakdown; timeline
lists ring txns with sub-₹50k flags.

---

### U4. Mount confidence + timeline on the AML page

**Goal:** Wire the two components into the investigation view.
**Dependencies:** U3.
**Files:**
- `web/src/app/aml/page.tsx` (modify)

**Approach:**
- Add a confidence meter next to / under the recommendation header (it qualifies
  the recommendation). Add an "Evidence timeline" section after the signals (or
  after the why-trail). Both take `alertId` and fetch independently (instant from
  cache).

**Patterns to follow:** the P1/P2 section structure in `aml/page.tsx`.

**Test scenarios:** `Test expectation: none (no web/ FE harness). In-browser
verification in U6.`

**Verification:** see U6.

---

### U5. Guided demo overlay

**Goal:** A scripted, route-aware 9-step walkthrough.
**Dependencies:** none (frontend-only; can build in parallel with U1–U4).
**Files:**
- `web/src/lib/demoSteps.ts` (new — the 9 steps: title, href, action, say)
- `web/src/lib/demo.tsx` (new — `DemoProvider` + `useDemo`: active step, on/off,
  localStorage-persisted)
- `web/src/components/DemoOverlay.tsx` (new — the banner: step pill, narration,
  action, Back/Next/Restart/Close, route-aware)
- `web/src/components/DemoToggle.tsx` (new — sidebar 🎬 start/stop)
- `web/src/app/providers.tsx` (modify — wrap with `DemoProvider`)
- `web/src/app/layout.tsx` (modify — mount `DemoOverlay` above the page content)
- `web/src/components/Sidebar.tsx` (modify — mount `DemoToggle`)

**Approach:**
- `demoSteps.ts`: port the 9 `_DEMO_STEPS` (narration `say` + `action`); map each
  step's "tab" to a route (`/platform`, `/aml`, `/approvals`, `/audit`,
  `/sectors/corporate`, `/sectors/procurement`). Step 1 → `/platform`, steps 2–6 →
  `/aml` (+ approvals/audit for governance), step 8 → `/sectors/corporate`, step 9
  → `/sectors/procurement`.
- `demo.tsx`: context with `{active, step, start, stop, next, prev, goto}`,
  persisted to localStorage.
- `DemoOverlay`: a fixed banner (top, above content) shown when `active`. Shows
  "Step N/9 · title", the narration `say` (the line to read), the `action` hint,
  and Back / Next / Restart / Close. Next/Back call `router.push(step.href)` then
  advance (KTD-4, KTD-6). Hidden when inactive.
- `DemoToggle`: a 🎬 button in the sidebar that calls `start()`/`stop()`.

**Patterns to follow:** `RoleProvider`/`useRole` (context + localStorage shape);
`Sidebar` button styling; `next/navigation` `useRouter`.

**Test scenarios:** `Test expectation: none — frontend-only scripted overlay, no
behavioral logic to unit-test. Verified in U6.`

**Verification:** toggling 🎬 shows the banner at step 1 (/platform); Next
navigates to /aml and advances; Restart returns to step 1; Close hides it.

---

### U6. Integration verification (in-browser)

**Goal:** Confirm confidence + timeline + guided demo end-to-end.
**Dependencies:** U4, U5.
**Files:** none.

**Verification (both servers up):**
- AML page: confidence meter shows **High** for ALERT-R001 with an expandable
  term-by-term breakdown ("base FILE = 60", "structuring (…) +…", "policy-grounded
  +5"); evidence timeline lists ring transactions chronologically with sub-₹50k
  flags.
- Guided demo: 🎬 toggle → banner at Step 1/9 on /platform → Next routes to /aml
  and advances through the script → Restart → Close.
- DevTools Network: zero external requests.
- `git status`: only `server/`, `web/`, `tests/` changed (engine + Streamlit
  zero-diff).

---

## System-Wide Impact

- **Engine / Streamlit:** zero. `git status` must show only `server/`, `web/`,
  `tests/`. Any `praheri/` or `app/` diff is a defect.
- **No new state mutation:** confidence + timeline are read-only; the guided demo
  is client-only localStorage. No DB/audit writes this phase.
- **Runtime:** unchanged.

---

## Risks & Dependencies

- **Confidence parity with Streamlit:** the port must match the Streamlit math
  exactly (judges may compare). The unit test pins the ALERT-R001 score to High
  and checks the reason terms. (KTD-1.)
- **Timeline scoping:** must stay ring-scoped (per-account indexed queries), never
  a full scan of the 20k-txn table. (KTD-2.)
- **Next 16 router API** (KTD-6) — confirm `useRouter().push` in `node_modules`
  before writing the overlay.
- **No Ollama needed** — both endpoints read from the cache + SQLite; the guided
  demo is client-only. Whole phase verifies offline.
- **`web/AGENTS.md`** — read local Next docs before new Next APIs.

---

## Verification (phase-level)

1. **Endpoints:** `tests/test_server_api.py` green offline — confidence (High +
   reason terms), timeline (sorted, capped, sub-threshold flags), 404s,
   `signal_count` unit.
2. **Build:** `cd web && npm run build` compiles, no type errors.
3. **In-browser:** confidence meter + breakdown, evidence timeline, route-aware
   guided demo all work.
4. **Sovereignty:** zero external requests.
5. **Fallback + zero-diff:** Streamlit runs; `git status` shows only `server/`,
   `web/`, `tests/`.

---

## Reassess gate

After Phase 5 the Next.js console has full Streamlit parity **plus** the Stage-3
depth (confidence, timeline, guided demo). Only P6 remains: extend the egress scan
to `server/`+`web/`, harden Ollama-down fallbacks, and run a full cold-machine
rehearsal. After P6 — when the Next.js console is parity-complete AND rehearsed —
switch the explainer link from Streamlit to Next.js. Streamlit stays the linked
fallback until then.
