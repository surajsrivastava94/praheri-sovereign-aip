# Praheri — Session Handoff

**Project root:** `~/Praheri-AIP/` (the git repo + all code live here). `Cowork-Brainstorm/` is reference-only material (the Build Bible source + original starter zip) and is gitignored.

**Today's goal:** Click through the not-yet-eyeballed tabs (Approvals→Audit, Procurement over-budget PO, OAG-vs-RAG), then record the backup demo video and build the pitch deck from `docs/DECK_OUTLINE.md`.

---

## Resume prompt (paste at the start of a new session)

> Read `docs/STATUS.md`, the latest `docs/SESSION_LOG.md` entry, and `BUILD_BIBLE.md`. Confirm the golden rules back to me in one line and tell me the current state + today's goal, then wait.

## Read order
1. `docs/STATUS.md` — where the build stands, open issues, what's next.
2. `docs/SESSION_LOG.md` (latest entry) — what happened last session.
3. `CLAUDE.md` — the golden rules + scope guards (non-negotiable).
4. `BUILD_BIBLE.md` — full spec, demo script (§9), deck (§10), Q&A (§12).
5. `docs/plans/2026-06-25-001-feat-praheri-sovereign-aip-build-plan.md` — the implementation plan (all units shipped).

## How to run
```bash
cd ~/Praheri-AIP
source .venv/bin/activate
ollama serve                  # llama3.1:8b + nomic-embed-text must be pulled
python -m praheri.generate    # fresh deterministic data (resets frozen accounts)
streamlit run app/streamlit_app.py
pytest                        # 52 tests (live ones need Ollama)
```

## Constraints (from CLAUDE.md — still in force)
- MVP scope only; model stays Llama; mutations only via `@action`; synthetic data only; everything audited; commit per green increment.
- The build is code-complete — remaining work is rehearsal + deck, not new features. Don't gold-plate.

## State at handoff
All 17 units (U0–U16) shipped · MVP checkpoint tagged · 52 tests green · no git remote (local-only). This session: restructured so `~/Praheri-AIP/` is the project root (moved up out of `Cowork-Brainstorm/praheri-starter/`); `.venv` recreated; suite re-verified green at the new root.
