# Praheri — Session Log

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
- Manual browser click-through of Approvals/Audit, Procurement, OAG-vs-RAG tabs (verified programmatically, not yet eyeballed live).
- Record the backup demo video.
- Build the pitch deck from the outline; rehearse the 3-min script + Q&A.
