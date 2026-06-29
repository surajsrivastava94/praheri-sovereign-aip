# Praheri — Project Status

**Last updated:** 2026-06-29
**Overall:** ✅ **Multi-vertical "Sovereign AIP OS" build COMPLETE (U1–U10, P0–P5)** + **UI revamped + deployed.** All 10 vertical units shipped; AML hero zero-diff throughout. A Palantir-dark **explainer/landing page is live at https://praheri.suraj94.cloud** (Netlify + Hostinger DNS, auto-SSL), and the Streamlit console is restyled dark to match. Branch `feat/multi-vertical-os` **merged to `main` and pushed** (repo now public). 111 deterministic + vertical tests green (+1 pre-existing flaky AML live test). Next: demo rehearsal / record backup video (and, deferred, an optional Next.js+Tailwind console rebuild).

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

---

## Open questions / known issues

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

## Deferred (after the multi-vertical build lands)

**Run the demo.** Full 3-min flow per `docs/demo_script.md`: Alert Queue → Investigate `ALERT-R001` → ring → STR → propose freeze → MLRO approve → audit → sovereignty check → procurement. Then record backup video, build deck from `docs/DECK_OUTLINE.md`, rehearse Q&A (BUILD_BIBLE §12).
