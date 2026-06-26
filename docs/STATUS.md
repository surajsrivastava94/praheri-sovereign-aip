# Praheri — Project Status

**Last updated:** 2026-06-26
**Overall:** ✅ **Full functional build complete.** All 7 playbook phases shipped (U0–U16), 52 tests passing, MVP checkpoint tagged. Remaining work is rehearsal + pitch deck design, not code.

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

- **17 commits** on `main`, tag **`mvp-checkpoint`** at the U7 end-to-end path.
- Working modules: `praheri/{models,generate,store,agent,policy_rag,governance,sovereignty,models_procurement}.py`, `app/streamlit_app.py`.
- Docs: `docs/demo_script.md`, `docs/DECK_OUTLINE.md`, plan at `docs/plans/2026-06-25-001-feat-praheri-sovereign-aip-build-plan.md`.
- Tests: `tests/` — 52 passing (live tests need Ollama running).

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
- **No git remote** — local-only repo; nothing to push.

---

## What's next (next session focus)

1. **Manual click-through** of the tabs not yet eyeballed live: Approvals→Audit loop, Procurement (over-budget PO), OAG-vs-RAG expander.
2. **Record the backup demo video** (BUILD_BIBLE §11 insurance) following `docs/demo_script.md` checklist.
3. **Build the pitch deck** from `docs/DECK_OUTLINE.md`.
4. **Rehearse** the 3-min script + judge Q&A (BUILD_BIBLE §12).
