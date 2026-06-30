# feat: Next.js AML hero — cached investigation view (Console rebuild Phase 1)

**Created:** 2026-06-30
**Type:** feat
**Depth:** Standard
**Plan:** `~/.claude/plans/shimmying-wandering-fern.md` (Phase 1 of the full Next.js console roadmap)

---

## Summary

Turn the Phase-0 AML *spike* page into the real **cached investigation view** — the
first parity step in replacing the Streamlit console with Next.js + Tailwind. Add
one read-only endpoint (`GET /api/alerts/{id}/investigate`) that returns the full
cached `investigate()` dict, then build the AML page out into a complete
investigation surface: the existing fraud-ring graph + **signal cards** +
**recommendation badge** + a **"why this recommendation" trail**. Everything reads
from the golden cache (`demo_cache/ALERT-R001.json`) so the hero is instant and
crash-proof.

This is additive only. The `praheri/` engine and `app/streamlit_app.py` stay
**byte-for-byte untouched** — the Streamlit console remains the guaranteed demo
fallback (and is the console currently linked from the deployed explainer).

---

## Problem Frame

Phase 0 proved the two risky unknowns (interactive graph + live Llama SSE) work in
the browser, but the AML page is still a *spike*: it shows the ring graph and a
throwaway "Ask Llama" button, with no investigation result, no signals, no
recommendation, no reasoning. To reach Streamlit parity for the AML hero, the
Next.js page must surface the same analytical content the Streamlit Investigation
tab does — driven by the same cached `investigate()` output, so it's deterministic
and demo-stable.

**Goal of this phase:** the AML page, on load, runs (cached) → shows the ring,
the detected typology signals, the recommendation, and a plain-language trail of
*why* — all instant, all from cache, no model call on the hot path.

---

## Scope Boundaries

**In scope**
- `GET /api/alerts/{id}/investigate` — returns the cached `investigate()` dict (read-only).
- AML page: investigation runs on load (cached), with a clear Cached/Live source badge.
- Signal cards (typology + detail + evidence ids).
- Recommendation badge (FILE / ESCALATE / CLEAR, color-coded by status token).
- "Why this recommendation" trail — a 3-step narrative grounded in the cached dict
  (signals detected → typology classified → recommendation + rationale + policy refs).
- Graph stays driven by the existing `/api/alerts/{id}/graph` endpoint (unchanged).

**Out of scope (later phases — do not build here)**
- Streaming STR narrative + object drill-down + OAG-vs-RAG (P2).
- Governance loop: actions, approvals, audit, role toggle (P3).
- Sectors / platform counters (P4).
- Confidence meter, evidence timeline, guided demo overlay (P5).
- Egress-scan extension to `server/`+`web/` (P6).

### Deferred to Follow-Up Work
- The Phase-0 "Ask Llama (stream)" SSE section stays on the page for now (proven,
  harmless). It is **superseded** by the P2 streaming-STR work and should be
  removed/replaced then — not in this phase.
- Confidence scoring exists in Streamlit (`_confidence()` in `app/streamlit_app.py`)
  but is explicitly a P5 deliverable here; do not port it now.

---

## Key Technical Decisions

**KTD-1 — `/investigate` is a thin pass-through of the cached dict.**
The endpoint calls `agent.investigate(alert_id, store=_store, use_cache=True)` and
returns the dict as-is (FastAPI serializes it). No reshaping in `server/` beyond
what's needed for the frontend types. Rationale: the cached dict is already the
exact shape the UI needs (`signals`, `typology`, `recommendation`, `rationale`,
`cited_ids`, `policy_citations`, `str_narrative`, `source`); reshaping would
duplicate engine semantics in the wrapper. Matches the Phase-0 posture (KTD-4:
FastAPI is a thin wrapper; engine zero-diff).

**KTD-2 — `source` field drives an honest Cached/Live badge.**
The dict carries `source: "live" | "cached"`. Surface it verbatim as a small badge
so the demo never misrepresents provenance (mirrors the Streamlit Live/Cached
badge and KTD-2 of the main build).

**KTD-3 — The "why" trail is a UI composition over existing fields, not new engine output.**
Build the 3-step reasoning trail purely from fields already in the dict
(`signals[].detail`, `typology`, `recommendation`, `rationale`, `policy_citations`).
No new computation, no engine change. This keeps the trail faithful to what the
engine actually produced.

**KTD-4 — Graph endpoint stays separate (two round-trips).**
Keep `/api/alerts/{id}/graph` as-is rather than embedding graph JSON in
`/investigate`. The graph endpoint already works (Phase 0) and internally calls
`investigate()` for the cited-id highlight; merging them would mean editing
working code for a marginal round-trip saving. Least-change wins this close to a demo.

**KTD-5 — Respect `web/AGENTS.md`: read the local Next docs before writing TSX.**
`web/AGENTS.md` warns this Next.js version has breaking changes vs. training data
and mandates reading `node_modules/next/dist/docs/` before writing code. The
implementer must do this for any new Next-specific API used (it's unlikely this
phase needs new Next APIs — it's React state + TanStack Query + Tailwind over the
existing shell — but the rule stands).

---

## Engine & Phase-0 contract (verified — wrap, never modify)

- `agent.investigate(alert_id, store=None, use_cache=True) -> dict` with keys:
  `alert_id, account_id, objects_touched, ring_summary, signals, typology,
  recommendation, rationale, cited_ids, policy_citations, str_narrative, source`.
  Golden-cached at `demo_cache/{alert_id}.json`; `ALERT-R001` is primed.
- `signals: list[{typology, detail, evidence_ids: list[str]}]`.
- `recommendation: "FILE" | "ESCALATE" | "CLEAR"`.
- `policy_citations: list[{source, text}]`.
- `ring_summary: {counts: {<type>: n}, accounts: [...], devices: [...], n_objects}`.
- `source: "live" | "cached"`.
- Existing endpoints in `server/main.py`: `/api/health`, `/api/alerts`,
  `/api/alerts/{id}/graph`, `/api/ask/stream`. `_store = OntologyStore()` is a
  module global → FastAPI MUST run `--workers 1 --port 8800`.
- Frontend shell (Phase 0): `web/src/lib/api.ts` (`getJSON<T>`, `Alert`/`GraphData`
  types), `web/src/components/GraphCanvas.tsx`, `web/src/app/aml/page.tsx`,
  Tailwind tokens (`fg`, `muted`, `accent`, `surface`, `border`, status colors
  `file`/`escalate`/`clear`) already defined in `globals.css`.

---

## Implementation Units

### U1. Add `GET /api/alerts/{id}/investigate` endpoint

**Goal:** Expose the cached investigation dict to the frontend.
**Dependencies:** none.
**Files:**
- `server/main.py` (add one route)
- `tests/test_server_api.py` (new — endpoint tests via FastAPI `TestClient`)

**Approach:**
- Add `@app.get("/api/alerts/{alert_id}/investigate")`. 404 if
  `_store.get_object("Alert", alert_id)` is falsy (mirror the existing `/graph`
  guard). Otherwise return `agent.investigate(alert_id, store=_store, use_cache=True)`.
- No reshaping (KTD-1). FastAPI serializes the dict directly.
- Keep the docstring style of the existing routes.

**Patterns to follow:** the existing `alert_graph()` route in `server/main.py`
(same 404 guard, same `investigate(..., use_cache=True)` call).

**Test scenarios** (`tests/test_server_api.py`, FastAPI `TestClient`):
- `GET /api/alerts/ALERT-R001/investigate` → 200; body has keys
  `recommendation`, `signals`, `typology`, `cited_ids`, `source`.
- Response `recommendation == "FILE"` and `typology == "structuring"` for
  `ALERT-R001` (the primed cache — deterministic).
- `signals[0]` has `typology`, `detail`, `evidence_ids` (non-empty list).
- `GET /api/alerts/NOPE/investigate` → 404.
- (Smoke, same file) `GET /api/health` → 200 `{ok: true}`; `GET /api/alerts`
  returns a non-empty list sorted by `score` descending.

**Verification:** `uvicorn server.main:app --workers 1 --port 8800` boots;
`curl localhost:8800/api/alerts/ALERT-R001/investigate` returns the full dict with
`recommendation: "FILE"`. New tests pass offline (cache hit → no Ollama needed).

---

### U2. Frontend types + `useInvestigation` query

**Goal:** Type the investigation dict and fetch it with TanStack Query.
**Dependencies:** U1.
**Files:**
- `web/src/lib/api.ts` (add `Investigation`, `Signal`, `PolicyCitation` types)
- `web/src/lib/useInvestigation.ts` (new — thin `useQuery` wrapper)

**Approach:**
- Add types mirroring the dict exactly: `Signal {typology, detail, evidence_ids:
  string[]}`, `PolicyCitation {source, text}`, `Investigation {alert_id,
  account_id, objects_touched: string[], ring_summary, signals: Signal[],
  typology, recommendation: "FILE"|"ESCALATE"|"CLEAR", rationale, cited_ids:
  string[], policy_citations: PolicyCitation[], str_narrative, source:
  "live"|"cached"}`. `ring_summary` can be loosely typed (`Record<string,
  unknown>`) — not consumed in this phase beyond counts, keep it minimal.
- `useInvestigation(alertId)` → `useQuery({ queryKey: ["investigation", alertId],
  queryFn: () => getJSON<Investigation>(\`/api/alerts/${alertId}/investigate\`) })`.
  Mirror the existing `graph` query in `aml/page.tsx`.

**Patterns to follow:** existing types + `getJSON` in `web/src/lib/api.ts`; the
`useQuery` shape already used inline in `web/src/app/aml/page.tsx`.

**Test scenarios:** `Test expectation: none — pure types + a thin query wrapper,
no behavioral logic. Verified via U5 in-browser.`

**Verification:** TypeScript compiles (`npm run build` or editor); the query
returns the typed dict when the AML page uses it (proven in U5).

---

### U3. `RecommendationBadge` component

**Goal:** Color-coded FILE/ESCALATE/CLEAR badge.
**Dependencies:** U2.
**Files:**
- `web/src/components/RecommendationBadge.tsx` (new)

**Approach:**
- Props: `{ recommendation: "FILE"|"ESCALATE"|"CLEAR" }`. Map to the existing
  Tailwind status tokens: FILE → `file` (red), ESCALATE → `escalate` (amber),
  CLEAR → `clear` (green). Pill style consistent with the page's existing
  rounded/bordered elements. Include a short label (e.g. "Recommendation: FILE").
- Self-contained, presentational. No data fetching.

**Patterns to follow:** the inline badge/button styling already in
`aml/page.tsx`; status color tokens in `web/src/app/globals.css`.

**Test scenarios:** `Test expectation: none — presentational component, styling
only. Verified visually in U5.`

**Verification:** renders the correct color per recommendation value when wired in U5.

---

### U4. `SignalCards` + `WhyTrail` components

**Goal:** Surface the detected typology signals and the "why this recommendation" reasoning.
**Dependencies:** U2.
**Files:**
- `web/src/components/SignalCards.tsx` (new)
- `web/src/components/WhyTrail.tsx` (new)

**Approach:**
- `SignalCards({ signals }: { signals: Signal[] })` — one card per signal: typology
  as the heading, `detail` as the body, `evidence_ids` rendered as small monospace
  chips (these are the cited objects — same visual language as the graph's glowing
  nodes; no interactivity required this phase, drill-down is P2).
- `WhyTrail({ inv }: { inv: Investigation })` — a 3-step vertical trail composed
  purely from the dict (KTD-3):
  1. **Signals detected** — count + the signal `detail` line(s).
  2. **Typology classified** — `inv.typology` (the model's classification over the
     structured objects).
  3. **Recommendation** — `inv.recommendation` + `inv.rationale`, with
     `policy_citations[].source` listed as the grounding (e.g. "per
     aml_thresholds.md"). Do **not** render full policy `text` blobs — just the
     source labels (full text/STR is P2).
- Both presentational; data passed in as props from the page.

**Patterns to follow:** the bordered-surface card styling in `aml/page.tsx`
(`rounded-xl border border-border bg-surface p-4`); the `border-l-2 border-accent`
section-heading style already used on the page.

**Test scenarios:** `Test expectation: none — presentational components reading
fields already validated by U1's endpoint tests. Faithfulness (no invented
content) is enforced by composing only from dict fields; verified in U5.`

**Verification:** with `ALERT-R001`, SignalCards shows the structuring signal with
its 12 evidence ids; WhyTrail reads "1 signal detected → structuring → FILE
(rationale…) per aml_thresholds.md". All text traces to the cached dict.

---

### U5. Compose the AML investigation page

**Goal:** Wire U2–U4 into `aml/page.tsx` so the page is the real cached
investigation view, at Streamlit-parity for the AML hero.
**Dependencies:** U2, U3, U4.
**Files:**
- `web/src/app/aml/page.tsx` (modify — replace the spike framing with the
  investigation view; keep the graph section and, for now, the SSE section)

**Approach:**
- Call `useInvestigation(alertId)` alongside the existing `alerts` and `graph`
  queries. On load it resolves from cache → instant.
- Page layout (top → bottom): alert picker (existing) → **header row** with the
  `RecommendationBadge` + a small Cached/Live badge from `inv.source` (KTD-2) →
  **fraud-ring graph** (existing `GraphCanvas`, unchanged) → **SignalCards** →
  **WhyTrail**. Update the page intro copy from "Phase 0 spike" to an
  investigation framing.
- Keep the existing graph node/edge counts caption.
- **Leave the Phase-0 "Ask Llama (stream)" SSE section at the bottom** (Deferred
  to Follow-Up — it's superseded by P2, not this phase). Optionally drop a one-line
  caption that live STR streaming arrives in the next phase.
- Loading/error states: mirror the existing `graph.isLoading` / `graph.error`
  handling for the investigation query (cache hit makes this near-instant, but
  handle it for correctness).

**Patterns to follow:** the existing query + section structure in
`aml/page.tsx`; `useState` alert picker already present.

**Test scenarios:** `Test expectation: none (no automated FE test harness in web/
this phase). Manual in-browser verification below; the data correctness it depends
on is covered by U1's endpoint tests.`

**Verification (in-browser, both servers up):**
- `uvicorn server.main:app --workers 1 --port 8800` + `cd web && npm run dev`.
- `http://localhost:3000/aml` loads instantly showing: FILE badge (red), Cached
  badge, the ring graph with 8 glowing cited nodes, one structuring signal card
  with evidence chips, and the 3-step why-trail.
- Switching the alert picker re-runs the investigation query for that id.
- DevTools Network shows **zero external** (gstatic/googleapis/CDN) requests
  (sovereignty — fonts local).

---

## System-Wide Impact

- **Engine / Streamlit:** zero. `git status` after this phase must show changes
  only under `server/`, `web/`, and `tests/` (new test file). If anything under
  `praheri/` or `app/` is modified, that's a defect — revert it.
- **Fallback intact:** `streamlit run app/streamlit_app.py` still works unchanged.
- **Runtime:** unchanged from Phase 0 — single-worker FastAPI on :8800, Next dev on :3000.

---

## Risks & Dependencies

- **Ollama not required on the hot path.** Because the AML page reads the primed
  `ALERT-R001` cache, a cold investigate is never triggered in the demo. (If the
  cache were missing, `investigate()` would call Llama and could raise
  `LlamaUnavailable` — but `ALERT-R001.json` is committed, so this is not a Phase-1
  risk. Other alert ids in the picker may not be cached; if an uncached id is
  selected with Ollama down, the query errors — acceptable, surfaced via the
  error state, and the demo only drives `ALERT-R001`.)
- **`web/AGENTS.md` Next-version caveat** (KTD-5) — read local Next docs before any
  new Next API. Low risk here (mostly React + Tailwind).
- **No web/ test harness** — frontend correctness is verified manually in-browser;
  data correctness is covered by the Python endpoint tests (U1). Acceptable for a
  demo console at this stage; a FE test harness is not in scope.

---

## Verification (phase-level)

1. **U1 endpoint:** `tests/test_server_api.py` green offline; `curl
   .../investigate` returns the FILE dict.
2. **Build:** `cd web && npm run build` (or dev) compiles with no type errors.
3. **In-browser parity:** `/aml` shows graph + signals + recommendation + why-trail,
   instant, from cache, with an honest Cached/Live badge.
4. **Sovereignty:** DevTools Network — zero external requests.
5. **Fallback + zero-diff:** Streamlit still runs; `git status` shows only
   `server/`, `web/`, `tests/` changes.

---

## Reassess gate

After Phase 1: if the AML hero reads at Streamlit parity (graph + signals +
recommendation + reasoning, instant from cache), proceed to P2 (streaming STR +
drill-down + OAG-vs-RAG). The Streamlit console remains the linked fallback until
the full Next.js console reaches parity across all tabs (the user's stated bar
before switching the explainer link).
