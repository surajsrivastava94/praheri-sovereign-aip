# Praheri — Session Handoff

**Project root:** `~/Praheri-AIP/` (the git repo + all code live here). `Cowork-Brainstorm/` is reference-only material (the Build Bible source + original starter zip) and is gitignored.

**Today's goal:** **First: `git push`** (6 commits unpushed — `main` is 6 ahead of origin). Then **Phase 1 of the Next.js console rebuild** — AML hero, cached: add `GET /api/alerts/{id}/investigate` to `server/`, then build the AML page (`web/src/app/aml/page.tsx` already has the graph + SSE spike) into the full investigation view: fraud-ring graph + signal cards + recommendation badge + "why this recommendation" trail, all from the golden cache (instant). Build alongside Streamlit — **never touch `praheri/` or `app/streamlit_app.py`** (the guaranteed fallback). Plan: `~/.claude/plans/shimmying-wandering-fern.md`. Reassess after Phase 1 before Phases 2–6. Still deferred: record backup demo video; range-aware flaky-test fix.

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
ollama serve                       # llama3.1:8b + nomic-embed-text must be pulled
python -m praheri.generate         # fresh AML data (resets frozen accounts)
python -m praheri.generate_verticals   # vertical data (gitignored; regenerate)
python -m app.serve_explainer &    # explainer at http://localhost:8000/explainer.html
streamlit run app/streamlit_app.py # FALLBACK console at http://localhost:8501
pytest                             # tests (live ones need Ollama; 1 known flaky AML)
```
**New Next.js console (Session 4+, the rebuild):**
```bash
# backend — MUST be single-worker (engine state is module-global). Port 8800
# because :8000 is the explainer static server.
.venv/bin/uvicorn server.main:app --workers 1 --port 8800
# frontend (separate terminal)
cd web && npm install && npm run dev     # console at http://localhost:3000/aml
```
`web/node_modules` + `.next` are gitignored — `npm install` in `web/` on a fresh checkout.
**Shareable explainer (deployed):** https://praheri.suraj94.cloud
**Re-deploy explainer after edits:** `cp app/explainer.html .deploy/index.html && netlify deploy --dir .deploy --prod --site bb16afd0-2bf0-4f72-9b6e-aeb3f95e987a`

## Constraints (from CLAUDE.md — still in force)
- MVP scope only; model stays Llama; mutations only via `@action`; synthetic data only; everything audited; commit per green increment.
- The build is code-complete — remaining work is rehearsal + deck, not new features. Don't gold-plate.

## State at handoff
**Multi-vertical build COMPLETE (U1–U10) + UI revamped + deployed.** AML hero (U0–U16) zero-diff throughout. Platform dashboard + 5 verticals + golden caches all shipped; Palantir-dark `app/explainer.html` live at **https://praheri.suraj94.cloud** (Netlify + Hostinger DNS); console restyled dark to match. `feat/multi-vertical-os` **merged to `main`** (fast-forward, `965ff7e`) and pushed; **repo is now public**. 111 deterministic + vertical tests green (+1 known flaky AML live test). Remaining work is rehearsal + deck, not new features.
