# feat: Next.js AML — governance loop (actions · approvals · audit · role) — Console rebuild Phase 3

**Created:** 2026-06-30
**Type:** feat
**Depth:** Standard
**Plan:** `~/.claude/plans/shimmying-wandering-fern.md` (Phase 3 — the judged core)
**Predecessors:** Phase 1 (`...-001-...`), Phase 2 (`...-002-...`) — both shipped.

---

## Summary

Bring the **governance loop** to the Next.js console — the judged core of the
demo: the analyst *proposes* an action, the model never writes data, high-stakes
actions wait in the **MLRO approval queue**, an MLRO approves, it **executes and
mutates state**, and **every step is audited**. Adds a role toggle
(Analyst/MLRO), the four action buttons on the AML page, an Approvals page, and
an Audit page.

This is the first Next.js phase that **mutates state**. All mutation still routes
through `praheri/governance.py` `@action`s — the FastAPI layer only *calls* them
(it never writes data itself, and never edits the engine). `praheri/` and
`app/streamlit_app.py` stay **byte-for-byte untouched**.

---

## Problem Frame

After Phase 2 the Next.js AML page can investigate, draft an STR, drill down, and
contrast OAG-vs-RAG — but it cannot *act*. The Streamlit console additionally
offers: action buttons (Clear / Escalate / 🔒 Propose Freeze / 🔒 Propose STR), a
role switch (Analyst/MLRO), a Pending-Approvals view with an MLRO-gated Approve
button, and an immutable Audit Trail. Phase 3 brings those to Next.js — completing
the **propose → approve → execute → audit** story that is the heart of the pitch
("the model proposes; a human disposes; everything is logged").

**Goal:** the four console-critical tabs (Investigation, Approvals, Audit + the
role toggle) work end-to-end in Next.js, mutating real state through the governed
action layer, with a full audit trail.

---

## Scope Boundaries

**In scope**
- Role model: a client-side Analyst/MLRO toggle; the role is sent with each
  request and the **server constructs the `Actor` and lets governance enforce it**
  (PermissionError → 403). (Decision: "Server-passed actor, UI toggle".)
- `POST /api/actions/{name}` — invoke a governed AML action (clear / escalate /
  request_account_freeze / file_str) through `governance`.
- `GET /api/approvals` + `POST /api/approvals/{ref}/approve` — list pending,
  MLRO-approve (executes + audits).
- `GET /api/audit` — the immutable audit rows.
- UI: role toggle in the sidebar; action buttons on the AML page (low-stakes
  execute immediately, high-stakes route to the queue); an Approvals page; an
  Audit page.

**Out of scope (later phases)**
- Sectors / platform governance (the generic vertical actions exist in the engine
  but their Next.js surface is P4).
- Confidence meter, evidence timeline, guided demo overlay (P5).
- A **reject/deny** path — the engine has no reject (only `approve`); do NOT add
  one to `praheri/`. The UI is approve-only, mirroring Streamlit.
- Any real auth/session. The role toggle is a demo control, not security.

### Deferred to Follow-Up Work
- Persisting `PENDING` across restarts (it's in-memory by design; `audit_log.jsonl`
  is the durable record — documented in the main build, U11).
- A demo-reset endpoint. (Decision: document-only — reset via
  `python -m praheri.generate`, already in the demo checklist.)

---

## Key Technical Decisions

**KTD-1 — The server constructs the `Actor`; governance enforces the role.**
Action/approve endpoints take a `role` ("analyst" | "mlro") in the request body,
build `Actor(id=f"demo_{role}", role=role)` (mirroring Streamlit's `demo_{role}`
id), and call the governance function. `governance` raises `PermissionError` for
a disallowed role and `ValueError` for a bad approval ref; the server maps those
to **403** and **400/404** respectively. The server never writes data — it only
calls `@action`s. This is faithful to the golden rule "the model never writes
data directly" extended to the API layer.

**KTD-2 — Reuse the existing module-global engine singletons; single-worker only.**
`governance.PENDING`, the audit log (`audit_log.jsonl`), and
`store.default_store()` are process-global. The action endpoints call
`governance.*` directly (which use `default_store()` internally for mutations).
The server's read `_store` and governance's `default_store()` are two connections
to the same `praheri.db`; the mutators `commit()`, so reads see writes. FastAPI
**MUST** run `--workers 1 --port 8800` (already required) — re-state it in the
endpoint docstrings.

**KTD-3 — Action set is the four AML actions, by name, via a small allow-list.**
`POST /api/actions/{name}` accepts only `{clear_alert, escalate_alert_to_case,
request_account_freeze, file_str}` (an explicit dict mapping name → governance
fn). Unknown name → 404. This keeps the surface tight and avoids exposing
vertical/procurement actions (P4) or `add_case_note` (not used by the AML UI).
Params are passed through from the request body to the governance fn as kwargs.

**KTD-4 — Mirror Streamlit's button semantics exactly.**
Low-stakes (`clear_alert`, `escalate_alert_to_case`) execute immediately and
return `{status: "EXECUTED", ...}`. High-stakes (`request_account_freeze`,
`file_str`) return `{status: "PENDING_APPROVAL", ref}` and land in the queue. The
UI shows 🔒 on the high-stakes buttons and a "routed to MLRO queue" toast, exactly
like Streamlit (lines 848–874).

**KTD-5 — Approvals Approve button is MLRO-gated client-side AND server-side.**
The Approve button only renders when role === "mlro" (mirrors Streamlit line
900); the server *also* enforces it (an analyst POSTing approve gets the
governance behavior — `approve()` re-invokes the action as the passed actor;
since approve takes the MLRO actor, the gate is the UI + the role sent). Match
Streamlit: approve is shown only to MLRO.

**KTD-6 — Audit page is read-only `read_audit()`, newest-first.**
`GET /api/audit` returns `governance.read_audit()`. The UI renders a table
(actor, role, action, event, ts, model, result) — the compliance artifact. Newest
first for demo readability (reverse the list in the UI, not the engine).

**KTD-7 — Respect `web/AGENTS.md`.** Read `node_modules/next/dist/docs/` before
any new Next API. P3 introduces the first **mutations** from the client — use
TanStack Query `useMutation` + `invalidateQueries` to refresh approvals/audit
after an action. Confirm the installed TanStack Query mutation API in
`web/node_modules` before writing (it's already a dependency from P1).

---

## Engine contract (verified — wrap, never modify)

- `governance.Actor(id: str, role: str)` — role is "analyst" | "mlro".
- `@action` functions return:
  - low-stakes: `{status: "EXECUTED", ref, result}`.
  - high-stakes (requires_approval): `{status: "PENDING_APPROVAL", ref}`.
  - raise `PermissionError` if `actor.role not in (requires_role, "mlro")`.
- AML actions + their params:
  - `clear_alert(actor, alert_id, rationale)` — low-stakes.
  - `escalate_alert_to_case(actor, alert_id, reason)` — low-stakes.
  - `request_account_freeze(actor, account_id, reason)` — **high-stakes**.
  - `file_str(actor, case_id, narrative)` — **high-stakes**.
- `governance.PENDING.list_pending() -> list[{ref, action, params, proposed_by,
  ts, status}]`.
- `governance.approve(ref, mlro: Actor) -> {status:"EXECUTED", ref, result}`;
  raises `ValueError("no such pending action")` for a bad/used ref.
- `governance.read_audit() -> list[dict]` (rows: id, ts, event, actor, role,
  action, params, result, model).
- Mutators commit to `praheri.db`; demo reset = `python -m praheri.generate`.
- Frontend (P1/P2): `getJSON`, TanStack Query provider, `Investigation` type,
  status Tailwind tokens, `Sidebar` component.

---

## Implementation Units

### U1. Governance POST endpoints (actions + approve) + audit/approvals reads

**Goal:** Expose the governed actions, the approval queue, and the audit log.
**Dependencies:** none.
**Files:**
- `server/main.py` (add routes; `from praheri import governance`)
- `server/models.py` (new — small Pydantic request bodies for action/approve)
- `tests/test_server_api.py` (extend)

**Approach:**
- `server/models.py`: `ActionRequest` (`role: str`, `params: dict[str, Any]`),
  `ApproveRequest` (`role: str`). Pydantic models for clean request parsing.
- Action allow-list (KTD-3): `_ACTIONS = {"clear_alert": governance.clear_alert,
  "escalate_alert_to_case": ..., "request_account_freeze": ..., "file_str": ...}`.
- `POST /api/actions/{name}`: 404 if name not in `_ACTIONS`; build `Actor(id=
  f"demo_{body.role}", role=body.role)`; `try: return fn(actor, **body.params)`
  `except PermissionError as e: raise HTTPException(403, str(e))`. Returns the
  governance dict ({status: EXECUTED|PENDING_APPROVAL, ...}).
- `GET /api/approvals`: return `governance.PENDING.list_pending()`.
- `POST /api/approvals/{ref}/approve`: build MLRO `Actor`; `try: return
  governance.approve(ref, actor)` `except ValueError as e: raise HTTPException(404,
  str(e))` `except PermissionError as e: raise HTTPException(403, str(e))`.
- `GET /api/audit`: return `governance.read_audit()`.

**Patterns to follow:** existing route style + `HTTPException` mapping in
`server/main.py`; Streamlit governance wiring (`app/streamlit_app.py` 848–912).

**Execution note:** Tests here mutate process-global state (PENDING, audit log,
praheri.db). Order tests so a high-stakes propose is asserted *before* its
approve, and treat the audit log as append-only (assert "contains a row", not
exact counts). Use a throwaway alert/account id where possible, or assert on
status strings rather than DB side-effects, to stay re-runnable.

**Test scenarios** (extend `tests/test_server_api.py`, FastAPI `TestClient`):
- `POST /api/actions/clear_alert` with `role:"analyst"`, params `{alert_id:
  "ALERT-R001", rationale:"test"}` → 200, `status == "EXECUTED"`.
- `POST /api/actions/request_account_freeze` with `role:"analyst"`, params
  `{account_id:"ACC-MULE-07", reason:"test"}` → 200, `status ==
  "PENDING_APPROVAL"`, has `ref`.
- `GET /api/approvals` → 200, list contains the ref just proposed (action ==
  "request_account_freeze").
- `POST /api/approvals/{ref}/approve` with `role:"mlro"` → 200, `status ==
  "EXECUTED"`.
- `POST /api/approvals/BADREF/approve` with `role:"mlro"` → 404.
- `POST /api/actions/nonesuch` → 404 (not in allow-list).
- `GET /api/audit` → 200, non-empty list; rows have `actor`, `action`, `event`,
  `model` keys.
- (Permission) `POST /api/actions/clear_alert` is allowed for analyst; assert a
  role the engine rejects maps to 403 — pick a case governance refuses (e.g.
  approve as analyst when the gate requires mlro, per the engine's actual rule).
  If the engine permits both roles for an action, assert the allowed path instead
  and note it — do not assert a 403 the engine won't raise.

**Verification:** `curl` an action (executed + pending), list approvals, approve,
read audit. New tests green offline (these don't need Ollama — pure governance +
SQLite). After the run, `python -m praheri.generate` resets the DB.

---

### U2. Frontend: role context + governance types + queries/mutations

**Goal:** A role toggle shared across pages; typed governance calls.
**Dependencies:** U1.
**Files:**
- `web/src/lib/role.tsx` (new — a tiny React context + provider + `useRole`)
- `web/src/lib/api.ts` (add `postJSON`, `PendingItem`, `AuditRow` types)
- `web/src/lib/useGovernance.ts` (new — `useApprovals`, `useAudit`,
  `useAction`, `useApprove` hooks)
- `web/src/app/providers.tsx` (modify — wrap with the role provider)

**Approach:**
- `role.tsx`: `RoleProvider` holding `"analyst" | "mlro"` in state (default
  "analyst"), persisted to `localStorage` so it survives navigation; `useRole() ->
  {role, setRole}`.
- `api.ts`: `postJSON<T>(path, body)` (POST + JSON, throws on !ok with the server
  detail). `PendingItem {ref, action, params, proposed_by, ts, status}`,
  `AuditRow {id, ts, event, actor, role, action, params, result, model}`.
- `useGovernance.ts`: `useApprovals()` (query), `useAudit()` (query),
  `useAction()` (mutation → `postJSON('/api/actions/'+name, {role, params})`,
  invalidates approvals+audit), `useApprove()` (mutation →
  `postJSON('/api/approvals/'+ref+'/approve', {role})`, invalidates
  approvals+audit). Mutations read the current role from `useRole`.

**Patterns to follow:** `useInvestigation`/`useRag` query shape; `providers.tsx`
existing QueryClient wrapper.

**Test scenarios:** `Test expectation: none — context + typed query/mutation
wrappers, no behavioral logic. Verified in U5 in-browser.`

**Verification:** TypeScript compiles; role persists across navigation; mutations
invalidate the right queries (proven in U5).

---

### U3. Sidebar role toggle

**Goal:** An Analyst/MLRO switch visible on every page.
**Dependencies:** U2.
**Files:**
- `web/src/components/Sidebar.tsx` (modify — add the toggle)
- `web/src/components/RoleToggle.tsx` (new)

**Approach:**
- `RoleToggle` — a two-button segmented control (🔍 Analyst / ✅ MLRO) bound to
  `useRole`. Mirror Streamlit's segmented role picker (analyst/mlro values).
- Mount it in the `Sidebar` (e.g. just above the "Llama · on-prem · zero egress"
  footer), so the role is always visible/switchable.

**Patterns to follow:** `Sidebar.tsx` existing nav-item styling; the alert-picker
button style in `aml/page.tsx` for the segmented look.

**Test scenarios:** `Test expectation: none — presentational toggle bound to
context. Verified in U5.`

**Verification:** clicking toggles the role; the Approve button in U5 appears only
when MLRO is selected.

---

### U4. Action buttons on the AML page

**Goal:** Clear / Escalate / 🔒 Propose Freeze / 🔒 Propose STR on the investigation.
**Dependencies:** U2.
**Files:**
- `web/src/components/ActionBar.tsx` (new)
- `web/src/app/aml/page.tsx` (modify — mount `ActionBar` after the recommendation
  header or below the why-trail)

**Approach:**
- `ActionBar({ inv })` — four buttons calling `useAction()`:
  - **Clear** → `clear_alert` `{alert_id: inv.alert_id, rationale: inv.rationale.slice(0,200)}`.
  - **Escalate** → `escalate_alert_to_case` `{alert_id: inv.alert_id, reason: inv.typology}`.
  - **🔒 Propose Freeze** → `request_account_freeze` `{account_id: inv.account_id,
    reason: inv.typology}`.
  - **🔒 Propose STR** → `file_str` `{case_id: inv.alert_id, narrative:
    inv.str_narrative || inv.rationale}`.
  - Low-stakes show an "executed" toast; high-stakes show a "routed to MLRO queue
    — see Approvals" toast (read `status` from the mutation result). 🔒 prefix +
    tooltip on the high-stakes two. Mirror Streamlit captions (848–874).
- Show a small inline result/error line (e.g. PermissionError → "MLRO only").

**Patterns to follow:** Streamlit action block (`app/streamlit_app.py` 848–874);
button styles already in `aml/page.tsx`.

**Test scenarios:** `Test expectation: none — UI wiring over U1 endpoints (tested
in U1). Verified in U5 in-browser.`

**Verification:** Clear/Escalate execute + toast; Propose Freeze/STR toast
"routed to queue" and appear in Approvals (U5).

---

### U5. Approvals + Audit pages + nav

**Goal:** The MLRO queue and the audit trail as their own pages.
**Dependencies:** U2, U3, U4.
**Files:**
- `web/src/app/approvals/page.tsx` (new)
- `web/src/app/audit/page.tsx` (new)
- `web/src/components/Sidebar.tsx` (modify — add Approvals + Audit nav entries)

**Approach:**
- **Approvals page**: `useApprovals()` → list each pending item (ref, action,
  proposed_by, params, ts). When `role === "mlro"`, show an **Approve** button per
  item calling `useApprove()`; on success the item leaves the list (query
  invalidated). When analyst, show a hint: "Switch to MLRO to approve." Empty
  state: "No pending actions — propose a freeze/STR from AML." (Mirror Streamlit
  892–903.)
- **Audit page**: `useAudit()` → a table newest-first (KTD-6) with columns ts /
  actor / role / event / action / result / model. Empty state: "No audit entries
  yet." (Mirror Streamlit 905–912.)
- **Sidebar**: add Approvals (✅) and Audit (📜) nav entries (core console tabs,
  not sectors). Place them after AML / before sectors, or in a small "Governance"
  group — match the existing nav item style.

**Patterns to follow:** `SignalCards`/`ObjectInspector` card+table styling;
`Sidebar.tsx` NAV array + active-state styling; Streamlit Approvals/Audit tabs.

**Test scenarios:** `Test expectation: none (no web/ FE test harness). Manual
in-browser verification below; endpoint correctness covered by U1.`

**Verification (in-browser, both servers up):**
- As **Analyst**: AML → Propose Freeze → toast "routed to queue"; Approvals shows
  the pending item, no Approve button; a hint to switch to MLRO.
- Switch to **MLRO** (sidebar toggle): Approve button appears; click → item clears;
  Audit page shows ACTION_PROPOSED + ACTION_APPROVED_AND_EXECUTED rows with actor/
  role/model.
- Clear/Escalate (low-stakes) → immediate audit rows, no queue entry.
- DevTools Network: zero external requests.
- After rehearsal, `python -m praheri.generate` resets the DB (frozen account /
  alert status), and the in-memory queue clears on server restart.

---

## System-Wide Impact

- **Engine / Streamlit:** zero. `git status` after this phase must show changes
  only under `server/`, `web/`, `tests/`. Any `praheri/` or `app/` diff is a defect.
- **State mutation (new this phase):** actions write to `praheri.db` (alert
  status, frozen accounts, cases) and append to `audit_log.jsonl`; high-stakes
  proposals sit in the in-memory `PENDING`. This is the same state the Streamlit
  console mutates — running both consoles against the same DB shares that state
  (fine for a single demo; reset between rehearsals).
- **Single-worker constraint** (KTD-2) — already required; now load-bearing for
  correctness (PENDING is in-process).

---

## Risks & Dependencies

- **State bleed across rehearsals.** Proposing/approving mutates `praheri.db` and
  the audit log; the queue is in-memory. Mitigation: documented reset
  (`python -m praheri.generate`) + server restart, already in the demo checklist.
  No new code (Decision: document-only).
- **Tests mutate global state.** U1 tests touch PENDING/audit/DB. Mitigation:
  assert on status strings + "contains a row" (append-only), use a spare
  account/alert id, and accept that the offline suite leaves audit rows behind
  (the suite already does for governance tests — see `tests/test_governance_wiring.py`).
- **No Ollama needed** — governance is pure Python + SQLite; the whole phase
  verifies offline (unlike P2's RAG/STR).
- **`web/AGENTS.md`** (KTD-7) — confirm the TanStack Query `useMutation` API in
  `web/node_modules` before writing; it's already a P1 dependency.

---

## Verification (phase-level)

1. **Endpoints:** `tests/test_server_api.py` green offline — action (executed +
   pending), approvals list, approve, audit, 404/403 mappings.
2. **Build:** `cd web && npm run build` compiles, no type errors.
3. **In-browser loop:** propose (analyst) → queue → approve (MLRO) → execute →
   audit, all visible; low-stakes execute immediately; role toggle gates Approve.
4. **Sovereignty:** zero external requests.
5. **Fallback + zero-diff:** Streamlit runs; `git status` shows only `server/`,
   `web/`, `tests/`. DB reset documented.

---

## Reassess gate

After Phase 3 the **judged core is complete** in Next.js: investigate → graph →
STR → drill-down → OAG-vs-RAG → propose → approve → audit, with a role toggle.
Remaining phases (P4 sectors/platform, P5 confidence/timeline/guided-demo, P6
egress-scan + hardening + rehearsal) bring full multi-tab parity before switching
the explainer link from the Streamlit console to Next.js. Streamlit stays the
linked fallback until then.
