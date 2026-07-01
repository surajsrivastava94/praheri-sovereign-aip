# Praheri — Session Log

## [2026-07-01] Session 6 — Explainer reframed as a Jio Financial Services design-partner pitch (same-day continuation of S5)

### Outcome
After S5's stop_sync, continued same-day: turned `app/explainer.html` from a generic BFSI product page into a **design-partner pitch to Jio Financial Services**, grounded in JFS's real group structure. Committed, pushed, and re-deployed live to https://praheri.suraj94.cloud. Also answered two positioning questions (what Llama does vs traditional ML; OAG-vs-RAG in laymen terms) that shaped the copy. 1 commit; engine + both consoles untouched.

### What happened (in order)
1. User asked (conceptually) what Llama does here vs traditional ML, and OAG-vs-RAG in plain terms → clarified the honest division of labour: **detection = deterministic graph/rules code** (what ML/graph is best at, kept in Python); **Llama = filing-grade narrative synthesis + zero-retrain cross-domain generalization** (what ML structurally can't). OAG-vs-RAG = *how you feed the LLM* (structured objects+links vs flattened text), not "AI vs old software."
2. Feedback: reframe the explainer as a JFS pitch, double down on AML + Insurance (JFS-relevant), add "why BFSI / why now" + "why OAG/ontology now / what ML can't do", structured as Value/USP/Deliverables/Adoption.
3. Grounded JFS offerings via Wikipedia (Jio Payments Bank, Jio Finance/NBFC, Jio Insurance Broking, Allianz Jio Reinsurance, JioBlackRock). Mapping is tight: **AML → Jio Payments Bank/Finance/UPI; Insurance → Jio Insurance Broking/Allianz Jio Reinsurance.**
4. Decisions (AskUserQuestion): BFSI deck with JFS as *named* design partner (not JFS-branded throughout); sectors → two-tier (AML+Insurance = "Phase 1 with JFS", other 4 = platform roadmap).
5. Rewrote `app/explainer.html` (reusing existing CSS): hero/nav signal a design-partner proposal; new **Why BFSI / why now** (3 cards), **Why Llama / what ML can't do** (side-by-side), two-tier **Sectors**, and a **Design partner: JFS** section (offerings→mapping + VALUE/USP/DELIVERABLES + Stage 0/1/2 adoption roadmap). Verified tag balance + screenshots.
6. Feedback: the "filing-grade narrative / prose / subgraph" copy was too jargon-heavy → rewrote both "Why Llama" cards **plain-first** ("writes the report a human can sign", "one brain works for every department") with domain terms (STR/FIU-IND, feature engineering) tucked in muted grey as expert grounding.
7. Committed `b5f87d2`, pushed, `netlify deploy --prod` → live + verified (curl found "Jio Financial Services", "For JFS", "design partner"). Stopped all servers.

### Key decisions
- **Explainer = named JFS design-partner pitch**, BFSI-generic frame (reusable), AML+Insurance foregrounded and mapped to real Jio entities.
- **Honest ML/LLM framing** (now in the explainer): detection stays deterministic code; the LLM owns narrative synthesis + zero-retrain generalization. Don't overclaim "LLM finds fraud better."
- **Plain-first copy, jargon as grounding** — lead with what a non-expert understands, append the domain term in muted text so experts see it's researched.
- **`app/explainer.html` intentionally diverges** from the frozen multi-vertical build now — it's the pitch surface, not the engine (engine + consoles still zero-diff).

### Issues encountered + resolved
- **Backgrounded `npm run dev`/servers kept dying** (subshell cleanup) → relaunched with `nohup`; stable. ✅
- **`:8000` "Address already in use" after kill** — `serve_explainer.py` has no `allow_reuse_address`, socket sits in TIME_WAIT ~30s → retried until clear; noted the one-line fix as deferred (frozen `app/` stack). Workaround: open `file://…/app/explainer.html` directly. ✅
- **WebSearch API 400s** repeatedly → grounded JFS via WebFetch on Wikipedia instead. ✅

### Artifacts produced
- 1 commit `b5f87d2` on `main` (pushed): `docs(explainer): reframe as a Jio Financial Services design-partner pitch`.
- `app/explainer.html` rewritten (now 10 sections; new ids `why-bfsi`, `why-llama`, `jfs`).
- Re-deployed to Netlify prod → https://praheri.suraj94.cloud (deploy `6a4513a3…`).

### Carry-over to next session
- **Phase 6** (unchanged from S5): extend `sovereignty.scan_egress()` to `server/`+`web/`; harden Ollama-down fallbacks; cold-machine rehearsal. THEN switch explainer CTA links Streamlit(:8501)→Next.js(:3000/aml) + re-deploy.
- Optional 1-liner: add `allow_reuse_address = True` to `app/serve_explainer.py` (avoids the TIME_WAIT rebind pain) — deferred, in the frozen `app/` stack.
- Still deferred: backup demo video; range-aware flaky AML test fix.

## [2026-07-01] Session 5 — Next.js console rebuild: Phases 1–5 COMPLETE (full Streamlit parity + depth)

### Outcome
Drove the Next.js + FastAPI console from Phase 0 (scaffold) to **Phases 1–5 all complete** in one session — the new stack now matches the entire Streamlit feature set PLUS the Stage-3 depth, all over the byte-for-byte-unchanged engine. 12 commits, all pushed. Each phase: `/ce-plan` (grounded in verified engine contract) → `/ce-work` (server endpoints + offline tests → frontend → in-browser verify → commit). Streamlit + `praheri/` zero-diff throughout; Streamlit stays the linked fallback until Phase 6.

### What happened (in order)
1. `/start_sync` → goal was Phase 1. User chose `ce-plan` + `ce-work` over subagent-driven-development for the build loop.
2. **P1 — AML hero cached** (`d83c7ca`, `56c3ff8`): `/api/alerts/{id}/investigate`; AML page = graph + signal cards + recommendation badge + why-trail, instant from golden cache. Found + fixed a real `.gitignore` bug (bare `lib/` excluded `web/src/lib/` → Phase 0's api.ts/useEventStream.ts were never committed; added `!web/src/lib/`).
3. **P2 — STR/drill-down/OAG-RAG** (`1572a3f`, `06df727`): `/objects/{id}`, `/rag` (live), `/str/stream` (SSE, prompt grounded in cited ids); StrPanel + ObjectInspector + OagRagPanel; removed the Phase-0 "Ask Llama" demo. OAG-vs-RAG reads as the differentiator (OAG decisive+cited vs RAG hedged).
4. **P3 — governance loop** (`dd75ef8`, `5322420`): action/approve/audit endpoints; role context + sidebar toggle, ActionBar, /approvals (MLRO-gated) + /audit pages. Verified full propose→queue→approve→FROZEN→audit loop in-browser.
5. **P4 — sectors + platform** (`0c0797d`, `acd61fb`): `/api/verticals` + per-key endpoints; ONE generic `SectorWorkspace` renders all 4 investigation verticals from `VerticalConfig` + a `ProcurementWorkspace`; registry-driven sidebar; platform dashboard (live 6/18/18/6 counters). Sector "Refer to SIU" → SAME MLRO queue → approve → SAME audit (governance parity proven).
6. **P5 — depth polish** (`55a74b5`, `10de281`): `/confidence` (ALERT-R001 → 95% High, term-by-term) + `/timeline` (ring-scoped, sub-₹50k flags); ConfidenceMeter + EvidenceTimeline; **route-aware guided-demo overlay** (9 steps, Next/Back actually navigate — improvement over Streamlit).
7. Pushed after every phase; started both servers for the user to browse; `/stop_sync`.

### Key decisions
- **Build via `ce-plan` → `ce-work` per phase** (user preference) rather than subagent-driven-development. Inline serial execution (units small + share files).
- **Confidence + timeline as server endpoints** (not client TS) — testable, mirrors "detection is code".
- **Guided demo route-aware** — Next/Back call `router.push(step.href)`; an improvement over Streamlit (which only names the tab).
- **Sector actions reuse the P3 governance plumbing** — one MLRO queue + audit for every sector.
- **Procurement = config-flagged branch** (`ProcurementWorkspace`), not the investigation flow (it's a budget/PO gate).
- **Re-implement Streamlit-internal logic in `server/`** (root-id resolution, `_confidence`, `_ring_timeline`) — never import the frozen `app/streamlit_app.py`.

### Issues encountered + resolved
- **`.gitignore` bare `lib/`** silently excluded `web/src/lib/` → fixed with `!web/src/lib/` negation; Phase-0 lib files now tracked. ✅
- **Stale uvicorn on :8800** from a prior session ran old code (P1 investigate 404'd) → killed + restarted. ✅
- **`npm run build` kills the running `npm run dev`** on :3000 → restart dev after a build (noted in STATUS). ✅
- **agent-browser screenshot worked again** (broken in S4); quirk: a `screenshot` right after relaunch grabs a blank tab — re-`open`+`wait` first. ✅
- Non-cached vertical/AML alerts trigger a live (slow) `investigate`/`rag` — expected; demo drives cached ALERT-R001 + the 4 cached verticals.

### Artifacts produced
- 12 commits on `main` (`d83c7ca`→`10de281`), all pushed.
- Plans: `docs/plans/2026-06-30-00{1,2,3,4,5}-...-plan.md` (one per phase).
- New `server/`: `confidence.py`, `timeline.py`, `str_prompt.py`, `models.py`, `verticals_api.py` (+ many routes in `main.py`).
- New `web/`: lib (`useInvestigation`, `useObject`, `useRag`, `useGovernance`, `useVerticals`, `useAmlExtras`, `role.tsx`, `demo.tsx`, `demoSteps.ts`); components (`RecommendationBadge`, `SignalCards`, `WhyTrail`, `StrPanel`, `ObjectInspector`, `OagRagPanel`, `ActionBar`, `RoleToggle`, `SectorWorkspace`, `ProcurementWorkspace`, `ConfidenceMeter`, `EvidenceTimeline`, `DemoOverlay`, `DemoToggle`); pages (`/approvals`, `/audit`, rebuilt `/aml`, `/platform`, `/sectors/[key]`).
- `tests/test_server_api.py` — 33 tests, offline (1 live RAG test gated on Ollama).

### Carry-over to next session
- **Phase 6**: extend `sovereignty.scan_egress()` to walk `server/`+`web/` (currently only `praheri/`+`app/`); harden Ollama-down fallbacks; full cold-machine rehearsal.
- **Then** switch the explainer's "Launch console" / run-steps from Streamlit → Next.js (+ re-deploy explainer).
- Still deferred: record backup demo video; range-aware fix for the flaky AML live test.
- Runtime reminder: `.venv/bin/uvicorn server.main:app --workers 1 --port 8800` + `cd web && npm run dev` → http://localhost:3000/aml.

## [2026-06-30] Session 4 — Console UX polish (3 stages) → Next.js+FastAPI rebuild begun (Phase 0)

### Outcome
Polished the Streamlit console hard (self-explaining copy → visual polish → analytical depth), then pivoted to a **Next.js + Tailwind console rebuild** over a thin FastAPI layer, building it in parallel so the working Streamlit demo stays the guaranteed fallback. Phase 0 shipped: the two risky unknowns (interactive fraud-ring graph + live Llama token streaming) are proven end-to-end in the browser. 6 commits (unpushed).

### What happened (in order)
1. Fixed the explainer's "Launch console" nav button (CSS specificity bug: `.navlinks a` muted-grey overrode `.btn-solid`). Re-deployed to praheri.suraj94.cloud. Commit `17f9f1a`.
2. **Self-explaining console** (`eb3162f`): collapsed orientation + glossary expanders; `use_case`/`what_you_see` added to `VerticalConfig` + all 5 cartridges (copy from the explainer); "👁 What you'll see here" callouts on every tab; action tooltips + 🔒 on high-stakes.
3. **Guided demo mode** (`fc475f1`): `_DEMO_STEPS` (9 beats from demo_script.md) + persistent banner above the tab bar + sidebar 🎬 toggle/Back/Next/Restart. Works within Streamlit's "can't switch tabs programmatically" constraint (banner names the tab; manual Next advances; predicates only confirm ✓).
4. **Stage 2 visual polish** (`38c8db4`): bundled Inter (variable) + IBM Plex Mono locally (`app/static/`, served via `[[theme.fontFaces]]` + `enableStaticServing` — zero Google Fonts egress); segmented-control role picker (🔍 Analyst / ✅ MLRO + caption); subtler demo banner with a fade/slide @keyframes.
5. **Stage 3 deeper capability** (`8d7e47b`): confidence scoring (deterministic, explainable — ALERT-R001 → 95% High), "why this recommendation" 3-layer trail, evidence timeline (scoped ring-txn queries, sub-₹50k flags), object drill-down (selectbox → properties + linked groups). All display-only; engine zero-diff.
6. **Pivot to Next.js** (user: "Streamlit not that good"). Decided (AskUserQuestion): build in PARALLEL, full fidelity (interactive graph + SSE streaming), left-sidebar sector nav, same repo. Planned via Explore×3 + Plan agent.
7. **Phase 0 build** (`a189890`): `server/` FastAPI (health, alerts, alert graph-JSON via `serialize.py`, SSE `/api/ask/stream` via `stream.py`) + `web/` Next 16/React 19/Tailwind v4 (sidebar nav, local fonts via next/font/local, `GraphCanvas` react-force-graph-2d, `useTokenStream` EventSource hook, Palantir-dark tokens). Both spikes verified live; user confirmed "looks really good".

### Key decisions
- **KTD-3** — Next.js built in parallel; Streamlit + `praheri/` stay byte-for-byte the demo fallback (10-day deadline → don't bet the demo on a rebuild).
- **KTD-4** — FastAPI is a thin wrapper; engine zero-diff. Streaming added in NEW `server/stream.py` (imports agent constants read-only); single-worker (module-global state).
- **KTD-5** — sovereignty preserved: local fonts (no CDN), telemetry off, same-origin `/api` proxy. Verified zero external requests.
- Streamlit polish stages were all display-only (engine zero-diff) — three commits before the pivot are still valuable on the fallback console.

### Issues encountered + resolved
- Explainer button contrast (CSS specificity) → nav-scoped override. ✅
- Streamlit doesn't reload imported modules on rerun → had to restart the server to pick up `VerticalConfig`/config changes (noted for rehearsal resets). ✅
- 3 `_what_you_see` callouts had literal `**markdown**` inside HTML divs → switched to `<b>`/`<i>`. ✅
- FastAPI couldn't bind :8000 (explainer static server already there) → moved to **:8800**; updated Next proxy. ✅
- **agent-browser screenshot tool hung the entire session** (CDP issue) → verified all UI via DOM `eval` extraction. → carry-over (retry next session)
- 6 commits **not pushed** (stop_sync defers code push to user). → carry-over (push next session)

### Artifacts produced
- 6 commits on `main` (`17f9f1a`→`a189890`), unpushed.
- New stack: `server/{__init__,main,serialize,stream}.py`, `web/` (Next.js app — `src/app/{layout,page,providers,fonts,globals.css,aml,sectors/[key],platform}`, `src/components/{Sidebar,GraphCanvas}`, `src/lib/{api,useEventStream}`, `public/fonts/*.woff2`).
- Edited (Streamlit polish): `app/streamlit_app.py`, `praheri/verticals.py`, `app/explainer.html`, `.streamlit/config.toml`, `requirements.txt`, `.gitignore`; new `app/static/*.woff2`.
- Plan: `~/.claude/plans/shimmying-wandering-fern.md` (Phase 0 + full Next.js roadmap).

### Carry-over to next session
- **Push the 6 commits** (`git push` — main is 6 ahead of origin).
- **Phase 1 of the Next.js build**: AML hero cached — `/api/alerts/{id}/investigate` + AML page (graph + signal cards + recommendation badge + why-trail).
- Retry agent-browser screenshots (tool was broken); eyeball the Next console pixels.
- Runtime: `uvicorn server.main:app --workers 1 --port 8800` + `cd web && npm install && npm run dev` (:3000). `web/node_modules` gitignored.
- Still deferred: record backup demo video; range-aware fix for the flaky AML live test.

## [2026-06-29] Session 3 — P4+P5 complete · UI revamp · deployed shareable link

### Outcome
Finished the multi-vertical build (U8–U10, P4+P5), then revamped the UI into a Palantir-grade dark experience and **deployed a public shareable explainer at https://praheri.suraj94.cloud**. Merged `feat/multi-vertical-os` → `main`, made the repo public, pushed everything. 8 commits this session.

### What happened (in order)
1. `/start_sync` → goal was P4 (Platform dashboard + polish) then P5 (caches + rehearse).
2. **P4 via subagent-driven-development** (implementer → spec review → quality review per unit):
   - **U8** Platform dashboard: `render_platform()` + `verticals.platform_counters()` (counters derived from REGISTRY, test recomputes independently so they can't drift). Added as tab 0; all `tabs[N]` re-indexed +1; `test_app_renders` 9→10. Commit `8276942`.
   - **U9** `ui-ux-pro-max` polish: shared inline-HTML helpers (`_hero_band`/`_kpi_card_html`/`_section`) themed by `accent_color`, no global CSS bleed, AML untouched. Commit `62fde97`.
3. **Live browser click-through** (agent-browser) surfaced a real bug: hero/engine-box captions were dark-on-dark (gradient faded to pale over Streamlit's light page). Fixed by anchoring bands on opaque `_SURFACE` + accent tint on top. Commit `3a1afe6`.
4. **P5 (U10)**: closed the vertical narrative cache loop — `compute_vertical_investigation` drafts live via Llama on a FILE-case cache miss, writes back, degrades gracefully on `LlamaUnavailable` (CLEAR cases never call the model). Primed + committed 4 golden caches; demo script updated. Code-review caught a demo howler — corporate narrative said "United Business Owner" → hand-fixed to "Ultimate Beneficial Owner" in the committed JSON. Commit `5b19e5e`. Full suite 111 green (the 1 failure was the known flaky AML live test; passed on isolated retry).
5. **User feedback: disliked the UI, confused by it.** Chose (via AskUserQuestion) a Palantir-dark revamp: standalone explainer page + dark console, live click-through priority. Ran a background research agent (Palantir ontology framing + design tokens from their shipped CSS/Blueprint) → `docs/research/palantir-ontology-and-design-brief.md`.
6. Built **`app/explainer.html`** (animated network hero, ontology semantic+kinetic layers, OAG-vs-RAG, USP cards, 6 sectors with detailed "what it does"). Native dark Streamlit theme so console matches. `app/serve_explainer.py` static server. Commit `defff61`.
7. **User asked to deploy + share.** Chose Netlify (gh already authed; console can't/shouldn't go to a public host — sovereignty). Deployed → `praheri-sovereign-aip.netlify.app`, then added custom domain **praheri.suraj94.cloud** (Hostinger CNAME, SSL green in minutes). Made repo **public**; added a "Run it yourself" section (5-command steps + `mailto:emails2suraj@gmail.com`). Commits `a6ec4c5`, `31b6c97`, `965ff7e`.
8. **Merged `feat/multi-vertical-os` → `main`** (fast-forward), pushed `main` + branch. `/stop_sync`.

### Key decisions
- **Ship on Streamlit today, defer Next.js+Tailwind.** Full console rebuild is 3–5 days and risks the working demo; explainer carries the "wow". (User agreed.)
- **Deploy the explainer only; console stays local.** Hosting the console publicly would break the sovereignty premise AND no free host runs Ollama. CTAs route remote viewers to GitHub + local run steps + email.
- **Native Streamlit `[theme]` dark, not CSS hacks** — reliable, and the existing dark inline cards finally sit right.
- **Explainer accent = blue `#4C9AFF`** (matches console primaryColor) rather than Palantir's forest green, so explainer↔console feel like one product; borrowed all the structural Palantir language (hairlines, tight tracking, eyebrows, expo motion, network hero).
- **Merge via fast-forward** (main hadn't diverged) — clean linear history.

### Issues encountered + resolved
- Dark-on-dark hero/engine captions (U9) → re-based the gradient on opaque surface. ✅
- `*.html` gitignore rule silently excluded `app/explainer.html` → negated it (`!app/explainer.html`). ✅
- Corporate cached narrative "United Business Owner" factual error → hand-corrected committed JSON. ✅
- Netlify needed interactive `netlify login` (user ran it) + site had to be created before deploy. ✅
- Known flaky AML live test (`test_agent_calls_read_tool_…` / `test_str_narrative_cites_real_ids`, agent.py zero-diff) still intermittently fails under live Ollama; passes on isolated retry. → carry-over (AML-scoped range-aware assertion fix).

### Artifacts produced
- 8 commits on `main`/`feat/multi-vertical-os` (now identical, pushed, `965ff7e`).
- New: `app/explainer.html`, `app/serve_explainer.py`, `docs/research/palantir-ontology-and-design-brief.md`, `docs/research/design-reference-template.png`.
- Edited: `app/streamlit_app.py` (Platform dashboard, U9 polish, sidebar explainer link), `.streamlit/config.toml` (dark theme), `praheri/verticals.py` (`platform_counters`), `praheri/vertical_engine.py` (live narrative + cache), `tests/*`, `.gitignore`, `docs/demo_script.md`.
- Committed golden caches: `demo_cache/{insurance_siu__GAR-RING-01,lending_ews__DIR-RING-01,wealth__ADV-RING-01,corporate__CO-A}.json`.
- **Deployed:** https://praheri.suraj94.cloud (Netlify site `bb16afd0-2bf0-4f72-9b6e-aeb3f95e987a`).

### Carry-over to next session
- **Rehearse the live demo** (the original deferred goal) + record a backup video; build deck from `docs/DECK_OUTLINE.md`.
- Verify the 5 verticals live in-browser end-to-end (AML + Corporate were clicked through this session; the other 4 only render-checked).
- Fix the flaky AML live test (range-aware id assertion) — AML-scoped.
- **Optional / deferred:** Next.js+Tailwind console rebuild (FastAPI wrapper first). Port the explainer to Next.js (~1–2 hrs) if a framework-consistent stack is wanted.
- Tag a new checkpoint if desired (current `mvp-checkpoint` predates the multi-vertical work).

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
