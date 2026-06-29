# Praheri — Session Handoff

**Project root:** `~/Praheri-AIP/` (the git repo + all code live here). `Cowork-Brainstorm/` is reference-only material (the Build Bible source + original starter zip) and is gitignored.

**Today's goal:** The build is done and deployed — **rehearse the live demo and record a backup video.** Walk the full 3-min flow per `docs/demo_script.md` (Platform → Alert Queue → Investigate `ALERT-R001` → ring → STR → propose freeze → MLRO approve → audit → sovereignty → a vertical swap, e.g. Corporate). Click through the 4 not-yet-eyeballed verticals (Insurance/Lending/Wealth/Procurement) live. Build the deck from `docs/DECK_OUTLINE.md`. The shareable explainer is live at **https://praheri.suraj94.cloud**. Optional/deferred: Next.js+Tailwind console rebuild; range-aware fix for the flaky AML live test. Keep the AML hero zero-diff.

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
streamlit run app/streamlit_app.py # console at http://localhost:8501
pytest                             # 111 tests (live ones need Ollama; 1 known flaky AML)
```
**Shareable explainer (deployed):** https://praheri.suraj94.cloud
**Re-deploy explainer after edits:** `cp app/explainer.html .deploy/index.html && netlify deploy --dir .deploy --prod --site bb16afd0-2bf0-4f72-9b6e-aeb3f95e987a`

## Constraints (from CLAUDE.md — still in force)
- MVP scope only; model stays Llama; mutations only via `@action`; synthetic data only; everything audited; commit per green increment.
- The build is code-complete — remaining work is rehearsal + deck, not new features. Don't gold-plate.

## State at handoff
**Multi-vertical build COMPLETE (U1–U10) + UI revamped + deployed.** AML hero (U0–U16) zero-diff throughout. Platform dashboard + 5 verticals + golden caches all shipped; Palantir-dark `app/explainer.html` live at **https://praheri.suraj94.cloud** (Netlify + Hostinger DNS); console restyled dark to match. `feat/multi-vertical-os` **merged to `main`** (fast-forward, `965ff7e`) and pushed; **repo is now public**. 111 deterministic + vertical tests green (+1 known flaky AML live test). Remaining work is rehearsal + deck, not new features.
