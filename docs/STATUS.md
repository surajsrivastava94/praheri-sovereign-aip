# Praheri — Project Status

**Last updated:** 2026-06-30
**Overall:** ✅ Multi-vertical build complete + deployed (prior sessions). **Session 4: Streamlit console got 3 stages of UX polish, then the Next.js+Tailwind console rebuild STARTED — Phase 0 shipped and proven.** The console now exists as a parallel **Next.js 16 + FastAPI** stack (`web/` + `server/`) with both risky spikes de-risked end-to-end (interactive fraud-ring graph + live Llama SSE token streaming). The **Streamlit console + `praheri/` engine are byte-for-byte untouched** and remain the guaranteed demo fallback. 6 commits this session (**unpushed**, see below). 90 deterministic tests green. Next: **Phase 1** of the Next.js build (AML hero — investigate + graph + signals + why-trail, cached).

---

## Progress tracker (Implementation Units U0–U16)

| Unit | What | Status |
|---|---|---|
| U0 | Scaffold + env baseline verify | ✅ |
| U1 | Synthetic bank + 3 planted rings (deterministic) | ✅ |
| U2 | OntologyStore — OAG reads + ring graph | ✅ |
| U3 | Alert Queue tab | ✅ |
| U4 | `call_llama` + read-tool loop (the spike) | ✅ |
| U5 | `investigate()` hybrid hero pipeline + golden cache | ✅ |
| U6 | "Ask Praheri" live model-driven tool loop | ✅ |
| U7 | Investigation tab + pyvis ring graph | ✅ **MVP checkpoint (tagged)** |
| U8 | Policy RAG (Chroma + local Ollama embeddings) | ✅ |
| U9 | STR narrative grounded in object_ids + policy | ✅ |
| U10 | Wire 5 actions to store mutations | ✅ |
| U11 | Approvals (MLRO) + Audit tabs live loop | ✅ |
| U12 | Procurement vertical #2 (platform thesis) | ✅ |
| U13 | OAG vs RAG side-by-side toggle | ✅ |
| U14 | Sovereignty proof (no-egress self-check) | ✅ |
| U15 | 3-min demo script + rehearsal checklist | ✅ |
| U16 | Pitch deck outline | ✅ |

---

## Milestone shipped

- **20 commits** on `main`, tag **`mvp-checkpoint`** at the U7 end-to-end path.
- Working modules: `praheri/{models,generate,store,agent,policy_rag,governance,sovereignty,models_procurement}.py`, `app/streamlit_app.py`.
- Docs: `docs/demo_script.md`, `docs/DECK_OUTLINE.md`, plan at `docs/plans/2026-06-25-001-feat-praheri-sovereign-aip-build-plan.md`.
- Tests: `tests/` — 52 passing (live tests need Ollama running).
- **Project root is now `~/Praheri-AIP/`** (moved up out of `Cowork-Brainstorm/praheri-starter/`). `Cowork-Brainstorm/` is reference-only (Build Bible source + starter zip) and gitignored. `.venv` recreated at the new path; suite re-verified green.

---

## Key decisions

- **KTD-1 — Hybrid investigation pipeline.** Python does deterministic triage + ring traversal + typology-signal detection; Llama classifies, decides CLEAR/ESCALATE/FILE, and drafts the STR. Plus a separate genuine model-driven tool loop ("Ask Praheri"). Chosen because `llama3.1:8b` fabricates tool args and hedges on patterns it must derive from raw rows — proven live. More demo-stable AND more faithful to a real auditable AML engine; matches the 70B production story downscaled.
- **KTD-2 — Golden cache** per alert_id (`demo_cache/`) for 1ms crash-proof hero replay, with an honest Live/Cached badge.
- **U8 — Local embeddings** via Ollama `nomic-embed-text` (not Chroma's default ONNX, which downloads a model) — keeps airplane-mode airtight.
- **Detection is code, not the model.** `compute_signals()` queries the store directly for structuring/circular/shared-device signatures. Stronger sovereignty story (auditable logic, not a black box) and reliable FILE recommendations.
- **KTD-3 (Session 4) — Next.js console built in PARALLEL; Streamlit stays the backup.** With 10 days to the demo, a from-scratch rebuild that *replaces* the working console is too risky. So the new stack (`web/` Next.js + `server/` FastAPI) is additive; `praheri/` engine and `app/streamlit_app.py` are never touched and remain the guaranteed fallback. Demo on whichever is ready.
- **KTD-4 — FastAPI is a THIN wrapper; engine zero-diff.** The engine is Python (Llama/Ollama, SQLite, networkx, chromadb) and can't move to JS. `server/` imports + calls it. New capabilities (token streaming) go in NEW files (`server/stream.py`) that import agent constants read-only — `agent.call_llama` is never edited. Engine state (`PENDING`, `default_store()`, audit) is module-global ⇒ FastAPI MUST run `--workers 1`.
- **KTD-5 — Sovereignty preserved in the new stack.** Fonts bundled locally via `next/font/local` (served from `/_next/static/media/`, NO Google Fonts CDN); `NEXT_TELEMETRY_DISABLED=1`; `/api/*` proxied same-origin via Next `rewrites()`. Verified zero external requests in-browser. (Note: `scan_egress()` only walks `praheri/`+`app/` `.py` — a later phase adds a wrapper extending it to `server/`+`web/`.)

---

## Open questions / known issues

- **⚠️ 6 commits UNPUSHED** (Session 4) — `main` is 6 ahead of `origin/main`. stop_sync left the push to the user's judgment per the workflow; **push at next session start** (or now): `git push`. Commits `17f9f1a`→`a189890`.
- **Next.js dev runtime (Session 4).** FastAPI runs on **:8800** (NOT 8000 — that port is taken by the explainer static server `app.serve_explainer` started earlier in dev). Next `rewrites()` proxy points `/api/*` → `localhost:8800`. **Must run `uvicorn server.main:app --workers 1`** (engine state is module-global). Launch: `uvicorn server.main:app --workers 1 --port 8800` + `cd web && npm run dev` (:3000). `web/node_modules` + `.next` are gitignored (regenerate with `npm install` in `web/`).
- **agent-browser screenshot tool was broken all of Session 4** (CDP rendering hang — `screenshot` never returns/saves). Verified everything via DOM `eval` extraction instead (conclusive for function, but no pixel captures this session). Retry screenshots next session; may just need an agent-browser restart.
- **Next.js console NOT yet eyeballed as pixels by Claude** — user confirmed it "looks really good" live, but only Phases 0 done (sidebar nav + AML spike page + placeholder sector/platform pages). Phases 1–6 (~8 days) are roadmap, not built.

- **`PENDING` approvals are in-memory** — a Streamlit restart clears them. Fine for a single demo session; the `audit_log.jsonl` is the durable record. (Documented in the plan, U11.)
- **DB mutates during demo** — proposing/approving a freeze sets an account to `frozen` in `praheri.db`. Re-run `python -m praheri.generate` between rehearsals to reset (in the demo checklist).
- **3 harmless chromadb deprecation warnings** (`get_config()` on the embedding function) — cosmetic, no action needed.
- **Git remote** — repo `surajsrivastava94/praheri-sovereign-aip` is now **PUBLIC**. `feat/multi-vertical-os` **merged (fast-forward) to `main`** and pushed; both branches + `main` at `965ff7e`. Tag `mvp-checkpoint` still at the U7 AML checkpoint.
- **Deploy / shareable link** — explainer live at **https://praheri.suraj94.cloud** (and `praheri-sovereign-aip.netlify.app`). Netlify site id `bb16afd0-2bf0-4f72-9b6e-aeb3f95e987a`, team MoodFlix. **Re-deploy after editing `app/explainer.html`:** `cp app/explainer.html .deploy/index.html && netlify deploy --dir .deploy --prod --site bb16afd0-2bf0-4f72-9b6e-aeb3f95e987a`. (`.deploy/` + `.netlify/` are gitignored.) The console is NOT deployed (sovereign-by-design — runs locally only); explainer CTAs point remote viewers to GitHub + local run steps.
- **Console UI = Streamlit (not Next.js).** User wants an eventual Next.js+Tailwind rebuild; decided to ship today on Streamlit and defer. Path when ready: FastAPI wrapper over the existing Python engine (~½ day, engine unchanged) → Next.js console (~3–4 days; graph viz + live Ollama streaming are the long poles). The explainer is already effectively a Next.js-quality static page — porting just it is ~1–2 hrs.
- **Flaky AML live test `test_str_narrative_cites_real_ids`** (pre-existing, not from the vertical build — `agent.py` is zero-diff). It asserts a cited `object_id` appears verbatim in the live-8B STR narrative, but the model sometimes writes a *range* ("ACC-MULE-01 to ACC-MULE-06"), so intermediate ids aren't literal substrings → intermittent fail when Ollama is up. Deterministic tests + all 47 new vertical tests pass. Fix later in an AML-scoped change (make the assertion range-aware, e.g. match the `ACC-MULE-` prefix); deliberately NOT touched now to keep the hero zero-diff during the vertical build.

---

## Active build — Multi-Vertical "Sovereign AIP OS" (branch `feat/multi-vertical-os`)

**Pivot (2026-06-28):** before running the demo, expanding Praheri from a single AML demo into a
config-driven **multi-vertical platform** (the "OS" thesis). Brainstormed → spec → plan, now executing.

- **Spec:** `docs/superpowers/specs/2026-06-28-praheri-multi-vertical-os-design.md` (commit `0dc6995`).
- **Plan:** `docs/plans/2026-06-28-001-feat-multi-vertical-sovereign-aip-os-plan.md` (commit `c289b83`) — 10 units (U1–U10), phased P0–P5.
- **Shape:** one themeable `render_vertical()` + `VerticalConfig` cartridges for Lending, Insurance SIU, Wealth, Corporate, Procurement; a Platform dashboard with registry-derived live counters. AML hero stays untouched (KTD-1); engine changes additive (KTD-2); real traversal+signals, cached narrative.

**Progress:**
- ✅ **P0 (U1+U2)** — `praheri/verticals.py` (VerticalConfig + registry), `praheri/vertical_store.py` (GenericOntologyStore over networkx, same contract as OntologyStore). Commits `44fe420`, `d18874c`.
- ✅ **P1 (U3+U4)** — `praheri/vertical_engine.py` (3 config-driven detectors + `compute_signals_for` + `compute_vertical_investigation`, reuses AML `_has_cycle` by import), `render_vertical()` + `render_vertical_graph()` shared renderer, **Procurement migrated to cartridge #1**. Commits `61e9e4e`, `cc082f4`.
- ✅ **P2 (U5)** — **Insurance SIU** (shared-garage ring) and **Lending EWS** (common-director cluster + EMI-bounce stress) cartridges + data + nav tabs; both fire → FILE. Commit `40ff546`.
- ✅ **P3 (U6+U7)** — **Wealth** (adviser mis-selling cluster → suitability_mismatch) + **Corporate** (circular ownership + shared-UBO) cartridges + nav (now **9 tabs**: 4 core + 5 verticals). **U7**: `propose_vertical_action`/`execute_vertical_action` added to governance (+17/-0, additive) — every vertical's actions route through the SAME MLRO queue + audit. Commits `1fce7da`, `1781ba3`. AML `agent.py`/`store.py` zero-diff; governance AML actions untouched. **All 5 shallow verticals now investigate end-to-end AND propose→approve→audit through one engine.**
- ✅ **P4 (U8+U9)** — **U8**: Platform dashboard (`render_platform()` + `verticals.platform_counters()` — engine box + 5 cartridge tiles + live counters derived from REGISTRY: 6 ontologies/18 object types/18 link types/6 actions, "0 lines of engine code per vertical"). **U9**: `ui-ux-pro-max` polish pass on the shared template (accent-themed hero band, bento KPI cards, section headers; pure inline-HTML, no global CSS bleed). Commits `8276942`, `62fde97` (+ `3a1afe6` contrast follow-up — hero/engine-box captions were dark-on-dark; fixed live in the browser).
- ✅ **P5 (U10)** — vertical golden caches + live narrative generation (`compute_vertical_investigation` now drafts via Llama on a cache miss for FILE cases, writes back, degrades gracefully on `LlamaUnavailable`). 4 primed caches committed (insurance/lending/wealth/corporate). `docs/demo_script.md` updated (Platform→vertical-swap beat, prime commands, fixed stale path). Commit `5b19e5e`.
- ✅ **UI revamp + deploy (Session 3)** — Palantir-dark **`app/explainer.html`** (animated network hero, ontology semantic+kinetic layers, OAG-vs-RAG, USP, 6 sectors with detailed "what it does", "Run it yourself" steps + mailto). Native dark Streamlit theme (`.streamlit/config.toml`). `app/serve_explainer.py` (localhost static server). **Deployed to Netlify → https://praheri.suraj94.cloud** (custom domain on Hostinger DNS, SSL green). Repo made **public**; `feat/multi-vertical-os` **merged to `main`**. Commits `defff61`, `a6ec4c5`, `31b6c97`, `965ff7e`.

**Reminder:** vertical data is gitignored (`data/verticals/`); regenerate with `python -m praheri.generate_verticals` (like AML's `python -m praheri.generate`).

**Test note:** full suite takes ~145s offline (pre-existing Ollama retry-backoff in `test_agent_tools`/`test_investigate`, 22 tests). Fast gate (everything except those two files) = ~4s, 45 tests — use it between units; run the full suite at phase boundaries.

## Next.js console rebuild (Session 4 → ongoing) — phased roadmap

Plan: `~/.claude/plans/shimmying-wandering-fern.md` (Phase 0 section + full roadmap). Build alongside Streamlit; reassess after each phase.
- ✅ **Phase 0** — scaffold + de-risk spikes. `server/` (FastAPI: health, alerts, alert graph-JSON, SSE `/api/ask/stream`) + `web/` (Next 16/React 19/Tailwind v4: sidebar sector nav, local fonts, `GraphCanvas` via react-force-graph-2d, `useTokenStream`). Both spikes proven live.
- **Phase 1 (next)** — AML hero, cached: `/api/alerts/{id}/investigate`; AML page with graph + signal cards + recommendation badge + why-trail. All from golden cache → instant.
- **Phase 2** — streaming STR (structured-first event then live tokens) + object drill-down + OAG-vs-RAG.
- **Phase 3** — governance loop: actions, pending, approve (mlro-gated), audit, role toggle. **Judged core complete.**
- **Phase 4** — sectors (generic `SectorWorkspace` from `VerticalConfig` via `/api/verticals`) + platform counters.
- **Phase 5** — guided demo overlay, confidence endpoint, evidence timeline.
- **Phase 6** — extend egress scan to `server/`+`web/`, harden Ollama-down fallbacks, rehearse.

## Deferred (independent of the Next.js build)

**Run the demo + record backup video.** Full 3-min flow per `docs/demo_script.md` (works on the Streamlit console today): Platform → Alert Queue → Investigate `ALERT-R001` → ring → STR → propose freeze → MLRO approve → audit → sovereignty → vertical swap. Build deck from `docs/DECK_OUTLINE.md`, rehearse Q&A (BUILD_BIBLE §12). Also still deferred: range-aware fix for the flaky AML live test.
