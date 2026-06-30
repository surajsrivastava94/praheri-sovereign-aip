# feat: Next.js AML — streaming STR + object drill-down + OAG-vs-RAG (Console rebuild Phase 2)

**Created:** 2026-06-30
**Type:** feat
**Depth:** Standard
**Plan:** `~/.claude/plans/shimmying-wandering-fern.md` (Phase 2 of the full Next.js console roadmap)
**Predecessor:** `docs/plans/2026-06-30-001-feat-nextjs-aml-hero-cached-plan.md` (Phase 1 — shipped)

---

## Summary

Extend the Next.js AML hero past Phase-1 parity with the three Phase-2 deliverables:
1. **Streaming STR** — generate the Suspicious Transaction Report with a
   structured-first reveal (instant cached narrative) plus an opt-in **live
   token stream** over the existing Phase-0 SSE plumbing.
2. **Object drill-down** — inspect any cited/touched object's *real* properties
   and links, proving the ontology is a queryable graph, not a chatbot.
3. **OAG-vs-RAG** — a side-by-side that shows why structured-object retrieval
   beats flattened-text RAG (the core differentiator).

Additive only. `praheri/` and `app/streamlit_app.py` stay **byte-for-byte
untouched** (Streamlit remains the linked fallback). All new code lives in
`server/` + `web/`. The streaming path reuses `server/stream.py` (imports
`agent` constants read-only — `call_llama` is never edited).

---

## Problem Frame

After Phase 1 the AML page shows the cached investigation (graph + signals +
recommendation + why-trail) but stops there. The Streamlit console additionally
offers: the full STR narrative, an object drill-down inspector, and the OAG-vs-RAG
comparison. Phase 2 brings those three to Next.js — adding the one capability
Streamlit *never had* (live token streaming of the STR) on top.

**Goal:** the AML page reaches Streamlit parity for the investigation surface
(everything except governance actions, which are P3), plus live STR streaming.

---

## Scope Boundaries

**In scope**
- `GET /api/objects/{id}` — single object's properties + linked_ids (read-only).
- `GET /api/alerts/{id}/rag` — the RAG comparison answer (live, uncached).
- `POST`-free streaming STR over the existing `GET /api/ask/stream` pattern — a
  new `GET /api/alerts/{id}/str/stream` that streams a real STR from the
  structured ring (live), plus the cached `str_narrative` shown instantly.
- UI: STR panel (cached-first + live-stream button), object drill-down inspector,
  OAG-vs-RAG side-by-side panel.

**Out of scope (later phases)**
- Governance loop: actions, approvals, audit, role toggle (P3) — the STR/freeze
  buttons stay in Streamlit only until P3.
- Sectors / platform (P4); confidence meter / evidence timeline (P5).
- Removing the Phase-0 "Ask Llama (stream)" demo section — it's now *replaced* by
  the real STR stream (see U6); remove it as part of this phase.

### Deferred to Follow-Up Work
- Caching the RAG answer. `investigate_rag()` is intentionally live (the contrast
  is the point — it's slow AND wrong). Matches Streamlit. Not cached here.

---

## Key Technical Decisions

**KTD-1 — STR is structured-first, live-stream opt-in (mirrors P1 KTD-2).**
The STR panel shows the cached `inv.str_narrative` immediately (instant,
demo-stable). A "Stream live" button then streams a freshly-generated STR
token-by-token. The demo can run entirely on the instant path; live streaming is
the "wow" on top. Never block the page on a model call.

**KTD-2 — Live STR streaming reuses `server/stream.py`, engine zero-diff.**
A new endpoint `GET /api/alerts/{id}/str/stream` builds the STR prompt from the
*cached structured investigation* (typology, cited_ids, ring_summary, rationale)
and feeds it to `stream_chat()`. This imports `agent` constants read-only; it does
NOT call or edit `agent.call_llama` / `agent.investigate`. The STR prompt text
lives in `server/` (a new small prompt builder), not in `praheri/`.

**KTD-3 — Drill-down endpoint mirrors the Streamlit inspector exactly.**
`GET /api/objects/{id}` uses `store._type_of(id)` → `store.get_object(type, id)`
and returns `{type, id, properties, linked_ids}`. 404 when `_type_of` is falsy or
the object is missing. Same data Streamlit's `selectbox` drill-down shows. (Note:
`_type_of` is a module-level helper in `praheri.store` — imported read-only, like
the Streamlit app does.)

**KTD-4 — RAG endpoint is a thin wrapper over `investigate_rag()`, live + uncached.**
`GET /api/alerts/{id}/rag` calls `agent.investigate_rag(alert_id, store=_store)`
and returns `{answer, mode}`. It calls the model each request (no cache) — that's
faithful to the contrast. Degrades to a 503 with a clear message on
`LlamaUnavailable` so the UI shows a graceful error, not a hang.

**KTD-5 — OAG side reads the P1 cache; no second investigation.**
The OAG column of the comparison reuses the already-fetched `useInvestigation`
data (typology, recommendation, rationale, cited_ids). Only the RAG side hits the
new endpoint. Keeps OAG instant and avoids a duplicate investigate call.

**KTD-6 — Respect `web/AGENTS.md`.** This Next version has breaking changes vs.
training data; read `node_modules/next/dist/docs/` before any new Next API. Low
risk here — React state + TanStack Query + the existing EventSource hook.

---

## Engine & Phase-1 contract (verified — wrap, never modify)

- `agent.investigate_rag(alert_id, store=None) -> {answer: str, mode: "RAG"}`.
  Calls the model live; raises `agent.LlamaUnavailable` if Ollama is down.
- `store.get_object(type, id) -> {type, id, properties, linked_ids} | None`.
  `linked_ids` is a dict like `{sends: [...], receives: [...], used_on: [...],
  held_by: [...]}` (varies by object type).
- `praheri.store._type_of(object_id) -> type str | None` (e.g. "ACC-…" → Account,
  "TXN-…" → Transaction). Module-level helper; import read-only.
- `server/stream.py` `stream_chat(messages) -> Iterator[str]` yields content
  tokens; raises `LlamaUnavailable` on connection failure before first token.
- `server/main.py` `_sse(event, data)` helper + the `GET /api/ask/stream` pattern
  (named SSE events `token`/`done`/`error`) already exist — reuse both.
- Cached investigation (P1, `demo_cache/ALERT-R001.json`) carries
  `str_narrative` (775 chars), `typology`, `recommendation`, `rationale`,
  `cited_ids`, `objects_touched`, `ring_summary`, `policy_citations`.
- Frontend (P1): `useInvestigation`, `useTokenStream` (`{text, streaming, error,
  start(url)}`), `Investigation`/`Signal` types, status Tailwind tokens.
- FastAPI MUST run `--workers 1 --port 8800` (module-global engine state).

---

## Implementation Units

### U1. `GET /api/objects/{id}` drill-down endpoint

**Goal:** Expose a single object's properties + links.
**Dependencies:** none.
**Files:**
- `server/main.py` (add route)
- `tests/test_server_api.py` (extend)

**Approach:**
- `from praheri.store import _type_of` (module-level, read-only). Route
  `@app.get("/api/objects/{object_id}")`: `t = _type_of(object_id)`; 404 if falsy;
  `obj = _store.get_object(t, object_id)`; 404 if None; return `obj` as-is.
- No reshaping — `get_object` already returns `{type, id, properties, linked_ids}`.

**Patterns to follow:** existing `alert_investigate()` route (404 guard + direct return).

**Test scenarios** (extend `tests/test_server_api.py`):
- `GET /api/objects/ACC-MULE-01` → 200; body has `type == "Account"`, `properties`
  (non-empty), `linked_ids` (dict).
- `GET /api/objects/TXN-R00011` → 200; `type == "Transaction"`.
- `GET /api/objects/NOPE-999` → 404 (unknown prefix → `_type_of` falsy).

**Verification:** `curl .../api/objects/ACC-MULE-01` returns the account dict with
links; new tests green offline.

---

### U2. `GET /api/alerts/{id}/rag` comparison endpoint

**Goal:** Expose the flattened-text RAG answer for the side-by-side.
**Dependencies:** none.
**Files:**
- `server/main.py` (add route)
- `tests/test_server_api.py` (extend — guarded, see below)

**Approach:**
- `@app.get("/api/alerts/{alert_id}/rag")`: 404 if alert missing (mirror existing
  guard). `try: return agent.investigate_rag(alert_id, store=_store)` →
  `{answer, mode}`. `except agent.LlamaUnavailable as e: raise HTTPException(503,
  str(e))`. Live + uncached by design (KTD-4).

**Patterns to follow:** existing `alert_graph()` 404 guard; the `LlamaUnavailable`
handling already in `ask_stream()`.

**Test scenarios** (extend `tests/test_server_api.py`):
- `GET /api/alerts/NOPE/rag` → 404 (no model call needed — guard fires first;
  deterministic, offline-safe).
- (Skipped-by-default live test) a test that asserts a 200 `{answer, mode:"RAG"}`
  for `ALERT-R001` marked `@pytest.mark.skipif` on Ollama being down — keep the
  offline gate green. Follow how the existing live tests are gated in
  `tests/test_investigate.py` / `tests/test_agent_tools.py`.

**Verification:** with Ollama up, `curl .../rag` returns a prose answer + `mode:
RAG`; with Ollama down, returns 503 (not a hang). 404 test green offline.

---

### U3. Live STR streaming endpoint

**Goal:** Stream a freshly-generated STR token-by-token from the structured ring.
**Dependencies:** none (reuses `stream_chat`).
**Files:**
- `server/str_prompt.py` (new — builds the STR messages from the cached investigation)
- `server/main.py` (add SSE route)
- `tests/test_server_api.py` (extend — prompt-builder unit test, offline)

**Approach:**
- `server/str_prompt.py`: `build_str_messages(inv: dict) -> list[dict]` — a
  system+user message pair instructing the model to draft a concise STR grounded
  in the given typology, cited object ids, and rationale (all pulled from the
  cached investigation dict). Pure string assembly; no model call, no engine import.
- `server/main.py`: `@app.get("/api/alerts/{alert_id}/str/stream")` → 404 if alert
  missing; `inv = agent.investigate(alert_id, store=_store, use_cache=True)`
  (cache hit, instant); `messages = build_str_messages(inv)`; stream via
  `stream_chat(messages)` using the SAME `_sse` event protocol + StreamingResponse
  headers as `ask_stream` (token/done/error, `LlamaUnavailable` → error event).

**Patterns to follow:** the existing `ask_stream()` route end-to-end (gen()
closure, `_sse`, StreamingResponse headers).

**Test scenarios** (extend `tests/test_server_api.py`):
- `build_str_messages()` unit test (offline): given the cached ALERT-R001 dict,
  returns a 2-message list whose user content contains the typology
  ("structuring") and at least one cited id (e.g. "ACC-MULE-01"). Proves the STR
  is grounded in structured objects, not free text.
- `GET /api/alerts/NOPE/str/stream` → 404 (guard fires before any stream).

**Verification:** with Ollama up, hitting the endpoint streams `event: token`
lines then `event: done`; with Ollama down, a single `event: error`. The streamed
text reads as an STR grounded in the cited ids.

---

### U4. Frontend: types + `useObject` / `useRag` queries

**Goal:** Type the new endpoints and fetch them.
**Dependencies:** U1, U2.
**Files:**
- `web/src/lib/api.ts` (add `OntologyObject`, `RagAnswer` types)
- `web/src/lib/useObject.ts` (new — `useObject(id, enabled)`)
- `web/src/lib/useRag.ts` (new — `useRag(alertId, enabled)`, manual/lazy)

**Approach:**
- `OntologyObject {type, id, properties: Record<string, unknown>, linked_ids:
  Record<string, string[]>}`. `RagAnswer {answer: string, mode: string}`.
- `useObject(id: string | null)` — `useQuery` with `enabled: !!id` so it only
  fetches when an object is selected.
- `useRag(alertId)` — `useQuery` with `enabled: false` + a manual `refetch()`
  trigger (RAG is slow/live; only run on explicit button click). Mirror P1 query
  patterns.

**Patterns to follow:** `web/src/lib/useInvestigation.ts`; existing `getJSON` typing.

**Test scenarios:** `Test expectation: none — types + thin query wrappers, no
behavioral logic. Verified via U6 in-browser.`

**Verification:** TypeScript compiles; queries return typed data when wired in U6.

---

### U5. Frontend components: `StrPanel`, `ObjectInspector`, `OagRagPanel`

**Goal:** The three new UI surfaces.
**Dependencies:** U4.
**Files:**
- `web/src/components/StrPanel.tsx` (new)
- `web/src/components/ObjectInspector.tsx` (new)
- `web/src/components/OagRagPanel.tsx` (new)

**Approach:**
- `StrPanel({ inv })` — renders `inv.str_narrative` immediately in a bordered
  surface (the instant path). A "Stream live" button uses `useTokenStream` to hit
  `/api/alerts/{inv.alert_id}/str/stream`, swapping in the live tokens + caret
  while streaming (KTD-1). A small caption notes "instant from cache · stream live
  to watch Llama draft it."
- `ObjectInspector({ ids })` — a `<select>` over the cited+touched ids (dedup,
  sorted, with a "— select —" default). On selection, `useObject(id)` fetches and
  the panel renders `type · id`, a properties table, and linked objects grouped by
  link type as monospace chips (mirror Streamlit U798–823).
- `OagRagPanel({ inv })` — a "Run comparison" button; two columns: **OAG** (green)
  shows `typology → recommendation` + `rationale` + "cites real object_ids" from
  `inv` (instant, KTD-5); **RAG** (red) triggers `useRag(inv.alert_id).refetch()`,
  shows a spinner, then the prose `answer` + "links gone — can't reconstruct the
  ring", or the 503 error message.

**Patterns to follow:** P1 components (`SignalCards` card styling, `WhyTrail` step
layout, `RecommendationBadge` color tokens); the existing SSE button + caret in
`aml/page.tsx`.

**Test scenarios:** `Test expectation: none — presentational components reading
endpoint data validated by U1–U3 tests. Verified in U6.`

**Verification:** each component renders correctly when composed in U6 (see U6
in-browser checks).

---

### U6. Compose into the AML page

**Goal:** Wire the three new surfaces in; replace the Phase-0 SSE demo with the
real STR stream.
**Dependencies:** U5.
**Files:**
- `web/src/app/aml/page.tsx` (modify)

**Approach:**
- After the why-trail, add three sections: **Suspicious Transaction Report**
  (`StrPanel`), **Inspect a cited object** (`ObjectInspector` over
  `inv.cited_ids ∪ inv.objects_touched`), **OAG vs RAG** (`OagRagPanel`).
- **Remove** the Phase-0 "Ask Llama (stream)" throwaway section — the STR stream
  replaces it (Scope: it was deferred-then-superseded in P1).
- Keep loading/error handling consistent with P1.

**Patterns to follow:** the P1 section structure in `aml/page.tsx`.

**Test scenarios:** `Test expectation: none (no web/ FE test harness this phase).
Manual in-browser verification below; data correctness covered by U1–U3.`

**Verification (in-browser, both servers up):**
- STR panel shows the cached narrative instantly; "Stream live" streams tokens
  (Ollama up) or shows a graceful error (down).
- Object inspector: selecting `ACC-MULE-01` shows its properties + linked txns/
  devices/customer as chips; `TXN-R00011` shows the transaction.
- OAG-vs-RAG: OAG column instant (structuring → FILE + rationale); RAG column
  spins then shows prose (Ollama up) or a 503 message (down).
- DevTools Network: zero external (CDN/font) requests.
- The Phase-0 "Ask Llama (stream)" section is gone.

---

## System-Wide Impact

- **Engine / Streamlit:** zero. `git status` after this phase must show changes
  only under `server/`, `web/`, `tests/`. Any `praheri/` or `app/` diff is a defect.
- **Fallback intact:** `streamlit run app/streamlit_app.py` unchanged.
- **Runtime:** unchanged — single-worker FastAPI :8800, Next dev :3000.

---

## Risks & Dependencies

- **RAG + live STR require Ollama.** Both are live model calls (~tens of seconds).
  The demo's safe path is the instant cached STR + instant OAG column; live STR
  and the RAG column are the opt-in "wow"/contrast and degrade gracefully
  (`error` SSE event / 503) when Ollama is down. The drill-down and OAG column are
  fully offline (store + P1 cache).
- **`investigate_rag()` latency** — surfaced via an explicit spinner; only runs on
  button click (lazy query), never on page load.
- **`web/AGENTS.md` Next caveat** (KTD-6) — read local Next docs before any new
  Next API. Low risk (no new Next APIs expected).
- **No web/ test harness** — FE verified in-browser; data correctness covered by
  Python endpoint tests.

---

## Verification (phase-level)

1. **Endpoints:** `tests/test_server_api.py` green offline (objects 404 +
   shape, rag 404, str prompt-builder + 404). Live rag/str spot-checked with Ollama up.
2. **Build:** `cd web && npm run build` compiles, no type errors.
3. **In-browser parity:** STR (cached + live stream), drill-down inspector, and
   OAG-vs-RAG all work; Phase-0 demo section removed.
4. **Sovereignty:** zero external requests.
5. **Fallback + zero-diff:** Streamlit runs; `git status` shows only `server/`,
   `web/`, `tests/`.

---

## Reassess gate

After Phase 2: the AML investigation surface is at Streamlit parity plus live STR
streaming. Proceed to P3 (governance loop — actions, approvals, audit, role
toggle), which completes the judged core. Streamlit stays the linked fallback
until the full Next.js console reaches parity across all tabs.
