# feat: Next.js — sectors + platform (generic SectorWorkspace) — Console rebuild Phase 4

**Created:** 2026-06-30
**Type:** feat
**Depth:** Standard
**Plan:** `~/.claude/plans/shimmying-wandering-fern.md` (Phase 4 — sectors + platform)
**Predecessors:** P1/P2/P3 (`...-001/002/003-...`) — all shipped.

---

## Summary

Bring the **5 sectors + the platform dashboard** to the Next.js console — the
"platform thesis made literal." A single generic `SectorWorkspace`, rendered from
each `VerticalConfig`, gives all 4 investigation verticals (insurance / lending /
wealth / corporate) the same investigate → ring → signals → recommendation flow as
AML, plus a procurement workspace (budget/PO gate), plus a Platform dashboard with
live registry-derived counters. Sector governed actions route through the **same
MLRO approval queue + audit** as AML (one governance engine, every sector).

Additive only. The vertical engine (`praheri/verticals.py`,
`vertical_store.py`, `vertical_engine.py`) and Streamlit stay **byte-for-byte
untouched** — the FastAPI layer imports + calls them; the root-id resolution
logic (currently inside `app/streamlit_app.py`, which we must NOT import) is
**re-implemented in `server/`** from the verified contract.

---

## Problem Frame

After P3 the Next.js console does the full AML arc (investigate → govern → audit),
but the sidebar's sector links + Platform page are still Phase-0 placeholders. The
Streamlit console renders all 5 verticals through one `render_vertical()` plus a
Platform dashboard. P4 brings that to Next.js as a generic, config-driven
workspace — proving "0 lines of engine code per vertical": one React component
renders any cartridge from its `VerticalConfig` + investigation output.

**Goal:** clicking any sector in the sidebar opens a working workspace
(investigate the planted ring, see the graph + signals + recommendation, propose a
governed action that hits the shared MLRO queue); the Platform page shows the
engine + 5 cartridges + live counters.

---

## Scope Boundaries

**In scope**
- `GET /api/verticals` — the registry as JSON (each `VerticalConfig` +
  platform counters), for the sidebar + platform page.
- `GET /api/verticals/{key}/alerts` — the cartridge's alerts (entry points).
- `GET /api/verticals/{key}/investigate?root_id=` — vertical investigation
  (traversal + signals + recommendation + cached narrative).
- `GET /api/verticals/{key}/graph?root_id=` — the vertical ring graph JSON.
- Sector governed actions via the existing `POST /api/actions/{name}` extended to
  allow `propose_vertical_action` + `approve_purchase_order` (same MLRO queue).
- Generic `SectorWorkspace` page (`/sectors/[key]`) for the 4 investigation
  verticals + a procurement view (budget/PO gate).
- Platform dashboard (`/platform`): engine box + 5 cartridge tiles + live counters.

**Out of scope (later phases)**
- Confidence meter, evidence timeline, guided demo overlay (P5).
- Egress-scan extension, Ollama-down hardening, rehearsal (P6).
- Re-implementing detector logic (it stays in `vertical_engine.py` — we call it).

### Deferred to Follow-Up Work
- Vertical object drill-down (the AML `ObjectInspector` pattern could extend to
  verticals via a generic-object endpoint, but that's not required for parity —
  defer unless trivial).

---

## Key Technical Decisions

**KTD-1 — One generic `SectorWorkspace`, driven by `VerticalConfig`.**
A single React component renders any investigation vertical from its config +
investigation output (mirrors Streamlit's one `render_vertical()`). This is the
platform thesis: no per-vertical UI code. The page route is `/sectors/[key]`
(already a placeholder from Phase 0).

**KTD-2 — Re-implement root-id resolution in `server/`, do NOT import Streamlit.**
The logic "an Alert's `raised_on` link (or `root_id` prop) is the investigation
entry point" lives inside `app/streamlit_app.py` (frozen). Re-implement it in a
small `server/verticals_api.py` helper from the verified contract:
`root = alert["linked_ids"].get("raised_on") or alert["properties"].get("root_id")`
(unwrap a list). The engine (`vertical_engine.compute_vertical_investigation`)
is imported and called unchanged.

**KTD-3 — Per-vertical store cache, built once from `sample_data_path`.**
`GenericOntologyStore(json.load(config.sample_data_path))` is built lazily per key
and memoized in a module dict (the data is static). Avoids re-reading JSON per
request. If `sample_data_path` is missing (data not generated), the endpoint
returns a clear 503-style message ("run `python -m praheri.generate_verticals`").

**KTD-4 — Procurement is action-centric, handled as a config-flagged branch.**
Procurement has no ring/alerts; it's a budget/PO gate. The `SectorWorkspace`
checks `key === "procurement"` and renders a procurement view (list POs / propose
`approve_purchase_order` → MLRO queue) instead of the investigate flow. Mirrors
Streamlit's `if config.key == "procurement"` branch. Its PO data comes from the
procurement cartridge's objects via the alerts/objects endpoints.

**KTD-5 — Sector actions reuse the P3 governance plumbing.**
Extend the `_ACTIONS` allow-list in `server/main.py` to include
`propose_vertical_action` (high-stakes → MLRO queue) and `approve_purchase_order`
(high-stakes → queue). The frontend reuses `useAction` + the existing
`/api/approvals` + `/api/audit` — so a sector freeze/refer/PO approval shows up in
the SAME Approvals page and Audit trail as AML. This is the governance-parity
story: one queue, every sector.

**KTD-6 — Platform counters from the live registry, not hardcoded.**
`GET /api/verticals` returns `governance`-independent `platform_counters()`
(6 ontologies / 18 object types / 18 link types / 6 actions) computed from
`REGISTRY`, so the dashboard can't drift from reality. The Platform page renders
the engine box + a tile per cartridge + the counters.

**KTD-7 — The sidebar sector list becomes registry-driven.**
Replace the hardcoded Phase-0 `NAV` sector entries with entries derived from
`GET /api/verticals` (key, icon, name, tagline). AML / Approvals / Audit / Platform
stay pinned. Keeps the nav in sync with the registry automatically.

**KTD-8 — Respect `web/AGENTS.md`.** Read `node_modules/next/dist/docs/` before
any new Next API. P4 uses the dynamic route `/sectors/[key]` (already scaffolded
in Phase 0) — confirm the params API shape (Next 16 may have async params) in the
installed docs before editing that page.

---

## Engine contract (verified — wrap, never modify)

- `verticals.REGISTRY: dict[key, VerticalConfig]`; `get_config(key)`;
  `platform_counters() -> {ontologies, object_types, link_types, actions}`.
- `VerticalConfig.model_dump()` is fully JSON-serializable (key, name, icon,
  accent_color, tagline, regulator, use_case, what_you_see, object_types,
  link_types, kpi_cards, signals, actions, sample_data_path, golden_cache_key).
- `GenericOntologyStore(data)`: `query_objects(type)`, `get_object`,
  `get_linked_objects`, `build_graph(ids) -> nx.Graph` (serializer-compatible —
  proven: insurance graph → 20 nodes/19 edges via `server.serialize.graph_json`).
- `vertical_engine.compute_vertical_investigation(config, store, root_id,
  use_cache=True) -> {vertical, root_id, objects_touched, signals[],
  recommendation, cited_ids, narrative, source}`. CLEAR cases never call Llama;
  FILE cases use the golden cache (4 committed: insurance/lending/wealth/corporate).
- Root-id resolution: `alert["linked_ids"].get("raised_on")` (list) or
  `alert["properties"].get("root_id")`. (Verified: insurance ALERT-INS-01 →
  GAR-RING-01 → FILE.)
- `governance.propose_vertical_action(actor, vertical, action_id, target_id,
  reason)` — high-stakes (MLRO queue). `governance.approve_purchase_order(actor,
  requisition_id, amount, budget_remaining)` — high-stakes.
- Frontend (P1–P3): `getJSON`/`postJSON`, `useAction`/`useApprovals`/`useAudit`,
  `RoleProvider`/`useRole`, `GraphCanvas`, `Sidebar`, status tokens.
- Vertical data: `data/verticals/{insurance,lending,wealth,corporate,procurement}.json`
  (gitignored — regenerate `python -m praheri.generate_verticals`).

---

## Implementation Units

### U1. Vertical API endpoints + root-id helper

**Goal:** Expose the registry, alerts, investigation, and graph for verticals.
**Dependencies:** none.
**Files:**
- `server/verticals_api.py` (new — store memoization + root-id resolution helper)
- `server/main.py` (add 4 routes; extend `_ACTIONS` allow-list — KTD-5)
- `tests/test_server_api.py` (extend)

**Approach:**
- `server/verticals_api.py`:
  - `get_store(key) -> GenericOntologyStore` — memoized per key; raises a
    `FileNotFoundError`-mapped condition if `sample_data_path` missing.
  - `root_id_for(alert) -> str` — `raised_on` link or `root_id` prop, list-unwrapped.
- `server/main.py` routes:
  - `GET /api/verticals` → `{verticals: [config.model_dump() for c in REGISTRY],
    counters: platform_counters()}`.
  - `GET /api/verticals/{key}/alerts` → `get_store(key).query_objects("Alert")`
    (404 if key unknown; 503 if data missing).
  - `GET /api/verticals/{key}/investigate?root_id=` →
    `compute_vertical_investigation(get_config(key), get_store(key), root_id)`.
  - `GET /api/verticals/{key}/graph?root_id=` → `graph_json(get_store(key).
    build_graph(inv["objects_touched"]), highlight=inv["cited_ids"])` (runs the
    investigation to scope + highlight, like the AML graph route).
  - Extend `_ACTIONS`: add `propose_vertical_action`, `approve_purchase_order`.

**Patterns to follow:** the AML `alert_graph` / `alert_investigate` routes; the
`_ACTIONS` dict (P3); Streamlit `render_vertical` root resolution (421–429).

**Test scenarios** (extend `tests/test_server_api.py`, offline — caches committed):
- `GET /api/verticals` → 200; `counters.ontologies == 6`; `verticals` has 5
  entries each with `key`, `name`, `signals`.
- `GET /api/verticals/insurance_siu/alerts` → 200, non-empty; first alert resolves
  a root id via the helper.
- `GET /api/verticals/insurance_siu/investigate?root_id=GAR-RING-01` → 200;
  `recommendation == "FILE"`, `source == "cached"`, `signals` non-empty.
- `GET /api/verticals/insurance_siu/graph?root_id=GAR-RING-01` → 200; `nodes`
  non-empty, at least one `highlight: true`.
- `GET /api/verticals/nope/alerts` → 404.
- `POST /api/actions/propose_vertical_action` with `role:"analyst"`, params
  `{vertical:"insurance_siu", action_id:"refer_to_siu", target_id:"GAR-RING-01",
  reason:"ring"}` → 200, `status == "PENDING_APPROVAL"` (proves sector actions hit
  the shared queue).
- `root_id_for` unit test: an alert dict with `raised_on:["X"]` → "X"; with only
  `properties.root_id:"Y"` → "Y".

**Verification:** `curl` each endpoint; vertical investigate returns FILE/cached;
sector action lands in `/api/approvals`. New tests green offline.

---

### U2. Frontend: vertical types + queries

**Goal:** Type the vertical endpoints and fetch them.
**Dependencies:** U1.
**Files:**
- `web/src/lib/api.ts` (add `VerticalConfig`, `KPI`, `SignalSpec`, `ActionSpec`,
  `VerticalsResponse`, `VerticalInvestigation` types)
- `web/src/lib/useVerticals.ts` (new — `useVerticals`, `useVerticalAlerts`,
  `useVerticalInvestigation`, `useVerticalGraph`)

**Approach:**
- Types mirror `VerticalConfig.model_dump()` + the investigation dict
  (`{vertical, root_id, objects_touched, signals, recommendation, cited_ids,
  narrative, source}`). `signals` here are the engine signals (`{typology, detail,
  evidence_ids}`) — reuse the existing `Signal` type where shapes match.
- `useVerticals()` (query, used by sidebar + platform). The per-key hooks gate on
  `key`/`root_id` (`enabled`) like `useObject`.

**Patterns to follow:** `useInvestigation`/`useObject` query shape; existing
`Signal` type.

**Test scenarios:** `Test expectation: none — types + thin query wrappers.
Verified via U4/U5 in-browser.`

**Verification:** TypeScript compiles; queries return typed data in U4/U5.

---

### U3. Registry-driven sidebar

**Goal:** Sidebar sector list derived from `/api/verticals`.
**Dependencies:** U2.
**Files:**
- `web/src/components/Sidebar.tsx` (modify)

**Approach:**
- Keep AML / Approvals / Audit / Platform pinned. Replace the hardcoded sector
  entries with a mapped list from `useVerticals()` (key → `/sectors/{key}`, icon,
  name, tagline). Show a graceful fallback (the pinned items) while loading or if
  the call fails. (KTD-7.)

**Patterns to follow:** existing `Sidebar` NAV rendering + active state.

**Test scenarios:** `Test expectation: none — presentational, registry-bound.
Verified in U4.`

**Verification:** sidebar lists the 5 sectors from the registry; clicking routes
to the workspace.

---

### U4. Generic `SectorWorkspace` (investigation verticals + procurement)

**Goal:** One component renders any vertical from its config + investigation.
**Dependencies:** U2.
**Files:**
- `web/src/components/SectorWorkspace.tsx` (new — the generic investigation view)
- `web/src/components/ProcurementWorkspace.tsx` (new — the budget/PO gate, KTD-4)
- `web/src/app/sectors/[key]/page.tsx` (modify — resolve key, pick workspace)

**Approach:**
- `page.tsx`: read the `[key]` route param (confirm Next 16 params API — KTD-8),
  look up the config via `useVerticals`; 404-ish state if unknown. If
  `key === "procurement"` render `ProcurementWorkspace`, else `SectorWorkspace`.
- `SectorWorkspace({ config })`:
  - Hero: name, tagline, regulator chip, accent color; KPI cards from
    `config.kpi_cards`.
  - Alert list (`useVerticalAlerts`) → clicking sets the active `root_id`.
  - On `root_id`: `useVerticalInvestigation` + `useVerticalGraph` →
    recommendation badge + Cached/Live badge (reuse P1 `RecommendationBadge` +
    SourceBadge pattern) + `GraphCanvas` + signal cards (reuse `SignalCards`) +
    narrative (if present).
  - **Action buttons** from `config.actions` → `useAction("propose_vertical_action",
    {vertical: key, action_id, target_id: root_id, reason: recommendation})` →
    high-stakes land in the shared MLRO queue (KTD-5). Toast like AML's ActionBar.
- `ProcurementWorkspace`: list POs/requisitions (from the procurement cartridge's
  objects) → propose `approve_purchase_order` → MLRO queue. Keep it small; mirror
  Streamlit's `_render_procurement_actions` intent.

**Patterns to follow:** the AML page composition (P1/P2) + `ActionBar` (P3);
reuse `RecommendationBadge`, `SignalCards`, `GraphCanvas`.

**Test scenarios:** `Test expectation: none (no web/ FE harness). Manual
in-browser verification in U6; data correctness covered by U1.`

**Verification:** see U6.

---

### U5. Platform dashboard

**Goal:** The engine + cartridges + live counters page.
**Dependencies:** U2.
**Files:**
- `web/src/app/platform/page.tsx` (modify — replace the Phase-0 placeholder)

**Approach:**
- `useVerticals()` → render: an "engine" hero box (one engine, all sectors); the
  live counters (ontologies / object types / link types / actions) as KPI tiles;
  a tile per cartridge (icon, name, tagline, regulator, accent) linking to its
  `/sectors/{key}` workspace. "0 lines of engine code per vertical" tagline.
  (Mirror Streamlit's `render_platform`.)

**Patterns to follow:** P1 card styling; Streamlit `render_platform` content.

**Test scenarios:** `Test expectation: none — presentational over /api/verticals
(tested in U1). Verified in U6.`

**Verification:** see U6.

---

### U6. Integration verification (in-browser)

**Goal:** Confirm sectors + platform + sector-governance end-to-end.
**Dependencies:** U3, U4, U5.
**Files:** none (verification unit).

**Verification (both servers up; `python -m praheri.generate_verticals` run):**
- Sidebar lists 5 sectors from the registry; Platform page shows engine box +
  counters (6/18/18/6) + 5 cartridge tiles.
- **Insurance** workspace: investigate the alert → ring graph renders (cited nodes
  glow) + shared-garage signal + FILE badge + Cached badge + narrative.
- Lending / wealth / corporate workspaces each investigate to FILE from cache.
- **Procurement** workspace: propose a PO approval → lands in the shared MLRO
  queue.
- **Sector governance parity:** propose a sector action (e.g. insurance "Refer to
  SIU") → it appears in the SAME `/approvals` page → switch to MLRO → approve →
  shows in the SAME `/audit` trail (with `propose_vertical_action`).
- DevTools Network: zero external requests.
- `git status`: only `server/`, `web/`, `tests/` changed (engine + Streamlit
  zero-diff). DB/queue reset documented.

---

## System-Wide Impact

- **Engine / Streamlit:** zero. `git status` must show only `server/`, `web/`,
  `tests/`. Any `praheri/` or `app/` diff is a defect.
- **Shared governance:** sector actions write to the same `PENDING` queue +
  `audit_log.jsonl` as AML — running a sector action mutates the same governance
  state (single-worker; resettable).
- **Vertical data dependency:** the vertical endpoints need
  `data/verticals/*.json` (gitignored) — regenerate before the demo.

---

## Risks & Dependencies

- **Vertical data is gitignored** — endpoints 503 cleanly if missing; the demo
  checklist must include `python -m praheri.generate_verticals`. (KTD-3.)
- **CLEAR-case verticals call Llama on a cache miss** — but the 4 investigation
  verticals are FILE cases with committed caches, so the demo path is instant +
  offline. A cache miss only happens if a cache file is deleted (then it degrades
  gracefully to no narrative).
- **Next 16 dynamic-route params API** (KTD-8) — confirm in `node_modules` before
  editing `/sectors/[key]/page.tsx` (Phase 0 scaffolded it; params may be async).
- **Procurement object/PO shape** — verify the procurement cartridge's object
  types when building `ProcurementWorkspace` (it's the one non-investigation
  vertical); keep that view minimal.
- **`web/AGENTS.md`** — read local Next docs before new Next APIs.

---

## Verification (phase-level)

1. **Endpoints:** `tests/test_server_api.py` green offline — verticals list +
   counters, alerts, investigate (FILE/cached), graph, 404, sector action →
   PENDING_APPROVAL, root_id helper.
2. **Build:** `cd web && npm run build` compiles, no type errors.
3. **In-browser:** all 5 sectors work; platform dashboard live; sector action →
   shared MLRO queue → approve → shared audit.
4. **Sovereignty:** zero external requests.
5. **Fallback + zero-diff:** Streamlit runs; `git status` shows only `server/`,
   `web/`, `tests/`.

---

## Reassess gate

After Phase 4 the Next.js console reaches **multi-tab parity** with Streamlit: AML
+ 5 sectors + platform + governance + audit, one engine. Remaining: P5 (confidence
meter, evidence timeline, guided demo overlay — the "depth" polish) and P6 (egress
scan extension, Ollama-down hardening, full rehearsal). Only after P5/P6 — when the
Next.js console is at full parity AND rehearsed — switch the explainer link from
Streamlit to Next.js. Streamlit stays the linked fallback until then.
