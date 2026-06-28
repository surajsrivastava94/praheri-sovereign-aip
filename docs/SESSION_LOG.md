# Praheri — Session Log

## [2026-06-28] Session 2 — Pivot to multi-vertical "Sovereign AIP OS" (P0–P3 shipped)

### Outcome
Reframed Praheri from a single AML demo into a **config-driven multi-vertical platform** and built 7 of 10 planned units. The full engine kernel + **all 5 shallow verticals** (Procurement, Insurance SIU, Lending EWS, Wealth, Corporate) now investigate end-to-end and route governed actions through one shared engine — with the AML hero kept byte-for-byte untouched. 47 new tests; 106 deterministic-green.

### What happened (in order)
1. Researched the BFSI service landscape (3 parallel agents) → mapped where the typed-ontology + OAG + governed-actions + audit pattern fits across payments/lending/insurance/wealth/corporate; grounded the India data-localization (RBI 2018, DPDP) sovereignty argument and the Palantir/Quantexa white space.
2. Brainstormed (superpowers) → committed the vision **spec** (`0dc6995`): one themeable `render_vertical()` + `VerticalConfig` cartridges + a Platform dashboard. Locked: Option Y lineup (Procurement as the non-financial 6th cartridge), real-traversal/cached-narrative, one beautiful config-driven template (not 5 bespoke pages).
3. `ce-plan` → committed the 10-unit **plan** (`c289b83`), P0–P5. Reading the code first surfaced the load-bearing decision (KTD-1): `OntologyStore` is AML-schema-hardcoded, so verticals need a separate `GenericOntologyStore`, not a retrofit.
4. `ce-work` on branch `feat/multi-vertical-os`:
   - **P0** (U1+U2): `verticals.py` (VerticalConfig + registry), `vertical_store.py` (GenericOntologyStore over networkx, same structured-object contract as OntologyStore).
   - **P1** (U3+U4): `vertical_engine.py` (3 config-driven detectors reusing AML `_has_cycle` by import; `compute_signals_for`; cached investigation), `render_vertical()` + `render_vertical_graph()`, **Procurement migrated to cartridge #1**.
   - **P2** (U5): Insurance SIU (shared-garage ring) + Lending EWS (common-director + EMI-bounce) cartridges + data + nav.
   - **P3** (U6+U7): Wealth (mis-selling) + Corporate (circular ownership + shared-UBO) cartridges + nav (9 tabs); vertical actions wired through governance additively (+17/-0).
5. P3 full suite surfaced 1 failure → systematic-debugging proved it a **pre-existing flaky AML live test** (8B writes id-ranges; `agent.py` zero-diff), not a regression. User chose to note-and-not-touch (keep hero zero-diff).

### Key decisions
- **KTD-1** — new `GenericOntologyStore` beside `OntologyStore` (don't retrofit the AML store); both speak the identical `{type,id,properties,linked_ids}` contract so traversal/signals/renderer are store-agnostic.
- **KTD-2** — config-driven detectors reuse AML's `_has_cycle` by *import* (not copy/move), so `agent.py` stays byte-for-byte untouched.
- **Procurement = cartridge #1** (Option Y): migrated the hard-coded tab into the registry so Platform counters can't lie.
- **Flaky AML live test**: note as known issue; fix later in an AML-scoped change — do not touch the hero mid-build.

### Issues encountered + resolved
- Directed-vs-undirected edges in the cycle/threshold detectors (false cycles / missed inbound counts) → fixed to read `linked_ids` direction; locked by tests. ✅
- Stale `test_app_renders` tab-count assertion (5) as verticals were added → updated to 9 (legitimate, deliberate). ✅
- 1 flaky AML live STR test → root-caused as pre-existing 8B nondeterminism, not a P3 regression → noted in STATUS. → carry-over (AML-scoped fix later)

### Artifacts produced
- 12 commits on `feat/multi-vertical-os` (not yet pushed — **no git remote**).
- Spec: `docs/superpowers/specs/2026-06-28-praheri-multi-vertical-os-design.md`.
- Plan: `docs/plans/2026-06-28-001-feat-multi-vertical-sovereign-aip-os-plan.md`.
- Code: `praheri/{verticals,vertical_store,vertical_engine,generate_verticals}.py`, additive edits to `app/streamlit_app.py` + `praheri/governance.py`.
- Tests: `tests/test_{verticals_config,vertical_store,vertical_engine,app_verticals,generate_verticals,vertical_governance}.py` (47 new); data under `data/verticals/` (gitignored, regenerate via `python -m praheri.generate_verticals`).

### Carry-over to next session
- **P4** — U8 Platform dashboard (registry-derived live counters) + U9 `ui-ux-pro-max` polish pass.
- **P5** — U10 prime golden caches, update `docs/demo_script.md` with the cartridge-swap beat, rehearse.
- Eyeball the 5 verticals live in the browser (verified programmatically, not yet clicked through).
- Fix the flaky AML live test (range-aware assertion) — AML-scoped, separate from the vertical build.
- **No git remote** — 12 commits are local-only; set up a remote if off-machine backup/push is wanted.
- Eventually merge `feat/multi-vertical-os` → `main` once P4/P5 land.

## [2026-06-25] Session 1 — Plan + full build to all-phases-complete

### Outcome
Went from a partially-scaffolded starter kit to a complete, working Praheri build: planned the whole 16-unit implementation, then executed every unit (U0–U16) with tests green at each step. 17 commits, MVP checkpoint tagged, 52 tests passing.

### What happened (in order)
1. Set up env: `.venv` on Python 3.11 (avoided conda base / 3.14 wheel risk), installed deps, verified Ollama serving `llama3.1:8b`.
2. Ran `/ce-plan` → wrote the Deep implementation plan (16 units) grounded in the scaffold + a live `llama3.1:8b` tool-call probe.
3. Locked two key forks with the user: **hybrid agent + live loop** (not pure tool-calling), and **golden-cache** demo insurance.
4. Ran `/ce-work` → executed U0–U16 serially, committing each green unit. Reached the MVP checkpoint (U7) and tagged it.
5. User caught a `ModuleNotFoundError` at U7 (streamlit `sys.path`) — fixed + added an `AppTest` render guard.
6. Hero beat was mushy (model hedged "appears independent") → added deterministic `compute_signals()` so Python detects typologies and Llama narrates. Hero ring now → FILE.
7. Finished evidence (U8 RAG, U9 STR), governance wiring (U10/U11), procurement (U12), OAG-vs-RAG (U13), sovereignty check (U14), docs (U15/U16).

### Key decisions
- KTD-1 hybrid pipeline: Python traverses + detects signals, Llama reasons/decides/narrates; separate live tool loop for "Ask Praheri".
- KTD-2 golden cache for crash-proof hero replay.
- Local Ollama embeddings (`nomic-embed-text`) for policy RAG to preserve airplane-mode.
- Typology detection lives in code (`compute_signals`), not the model — reliability + a stronger auditable-sovereignty story.

### Issues encountered + resolved
- Streamlit couldn't import `praheri` (script dir on path, not repo root) → added `sys.path` insert + `AppTest` regression guard. ✅
- 8B fabricated `link_type` values → `get_linked_objects` normalizes loose values. ✅
- 8B hedged on patterns it couldn't aggregate → deterministic signal computation. ✅
- chromadb default embedder would download a model (breaks sovereignty) → switched to local Ollama embeddings. ✅
- Traversal didn't reach mules from beneficiary (signals computed from BFS depth) → `compute_signals` queries the store directly. ✅

### Artifacts produced
- 17 commits on `main`; tag `mvp-checkpoint`.
- Code: all of `praheri/*.py` + `app/streamlit_app.py` + `praheri/sovereignty.py` + `praheri/models_procurement.py`.
- Tests: `tests/` (52 passing).
- Docs: `docs/demo_script.md`, `docs/DECK_OUTLINE.md`, `docs/plans/2026-06-25-001-feat-praheri-sovereign-aip-build-plan.md`.

### Carry-over to next session
- **Run the full demo live** in the browser (next session's focus).
- Manual click-through of Approvals/Audit, Procurement, OAG-vs-RAG tabs (verified programmatically, not yet eyeballed live).
- Record the backup demo video.
- Build the pitch deck from the outline; rehearse the 3-min script + Q&A.

### Addendum (same session) — workspace restructure
After the build, user confirmed `Cowork-Brainstorm/` was only context. Moved the
entire build repo (incl. `.git`) up so **`~/Praheri-AIP/` is now the project root**;
`Cowork-Brainstorm/` (Build Bible source + starter zip) is reference-only and
gitignored. `.venv` recreated at the new path; `pytest` added to requirements
(was missing); wiki restored into `docs/` with root-relative paths. Full suite
re-verified **52 green** from the new root. (+3 commits: `ebeebd3`, `e725fd6`→
already counted, `0832d98`; now 20 commits total.)
