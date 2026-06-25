# CLAUDE.md — Praheri (Sovereign AIP on Llama)

> This file is read automatically by Claude Code. It is the contract for how to build this project. Read `BUILD_BIBLE.md` for the full spec. Read `PROMPT_PLAYBOOK.md` for the exact build sequence.

## What we are building

**Praheri** is a sovereign financial-crime (AML) investigation copilot for a hackathon (Meta–Reliance Intelligence, 10 July 2026). A **Llama** model running **fully on-prem** investigates AML alerts over a **typed ontology** of accounts/transactions, traverses links to expose fraud rings, drafts a Suspicious Transaction Report, and **proposes governed actions a human approves** — with a full audit trail. The ontology + action + governance layer is a **reusable platform** ("Sovereign AIP"); AML is vertical #1, procurement is vertical #2.

This is a **demo**, judged on demoability + the sovereignty narrative. Optimize for a flawless 3-minute demo, not production completeness.

## Golden rules (non-negotiable)

1. **MVP scope only.** Smallest thing that demos. If unsure whether to build something, don't — ask or leave a `TODO`.
2. **Pipeline, not swarm.** One Llama instance doing tool-calling across a deterministic pipeline (triage → investigate → evidence → decide). Do NOT build a multi-agent framework.
3. **OAG, not RAG-of-text.** Retrieval returns **structured objects** (`{type, id, properties, linked_ids}`) to the model — never raw text paragraphs about objects. This is the core differentiator.
4. **The model never writes data directly.** All mutations go through **Actions** in `governance.py`. High-stakes actions (`request_account_freeze`, `file_str`) require **human approval** before executing.
5. **Everything is audited.** Every object query, proposed action, and approval writes to the append-only audit log with actor, timestamp, model name.
6. **The model is Llama.** Served locally via **Ollama** (OpenAI-compatible endpoint). Never swap in a non-Llama model — the entire pitch depends on open-weight Llama on-prem. (NVIDIA NIM/vLLM are acceptable *serving* alternatives; the model stays Llama.)
7. **Synthetic data only.** No real financial data, ever. Frame as decision-support, not a certified AML system.
8. **Commit per working increment** so we can always roll back to a demoable state.

## Stack (pinned — do not change without asking)

- Python 3.11+
- Model: Llama 3.1 8B (demo) via **Ollama**; reference Llama 3.3 70B for the "production" story
- Ontology store: **SQLite** + **Pydantic** models; graph via **networkx**
- Graph viz: **pyvis** (rendered into the Streamlit page)
- Policy retrieval: **chromadb** (local)
- UI: **Streamlit**
- Audit: append-only table/JSONL

## Repo layout

```
praheri/
  models.py       # Pydantic object types (the ontology nouns)
  store.py        # SQLite + networkx: load, query_objects, get_linked_objects, build_graph
  generate.py     # synthetic data + 3 PLANTED fraud rings (the demo centrepiece)
  governance.py   # audit log + @action decorator + the 5 actions + approval queue
  agent.py        # Llama system prompt + tool specs + the investigation pipeline
  policy_rag.py   # Chroma policy/threshold store (evidence step)
app/streamlit_app.py   # UI: Alert Queue · Investigation (graph+narrative) · Approvals · Audit · Procurement
policies/              # sample AML policy docs for RAG
```

## Build order (follow PROMPT_PLAYBOOK.md)

1. Ontology models (`models.py`) + synthetic data with planted rings (`generate.py`) → load into SQLite + networkx (`store.py`).
2. Read layer: `query_objects`, `get_linked_objects`. Streamlit **Alert Queue**.
3. **Spike the risky bit early:** Llama tool-calling that traverses the ontology and returns structured objects (`agent.py`).
4. Graph viz of the ring (pyvis). ✅ **MVP CHECKPOINT: one alert investigated end-to-end.**
5. Policy RAG + STR narrative grounded in `object_id`s.
6. Action layer + approval gate + audit (`governance.py`).
7. Procurement vertical #2 stub (reuse the same engine, new tiny ontology).
8. Sovereignty proof (local-only + OAG-vs-RAG toggle) → polish → rehearse.

## Conventions

- Type everything (Pydantic / type hints). Keep functions small and pure where possible.
- Every claim the agent makes must cite `object_id`s. Enforce this in the prompt and surface citations in the UI.
- No secrets in code; use `.env` (already gitignored). No network calls except to the local Ollama endpoint.
- Leave `# TODO(playbook step N):` markers rather than half-building.

## Do NOT (scope guards)

- ❌ Real ERP / core-banking integration, OAuth, multi-tenant RBAC, fine-tuning, Docker/k8s — these are **roadmap slides**, not code.
- ❌ A generic multi-agent orchestration framework.
- ❌ Writing to the store outside an `@action`.
- ❌ Swapping Llama for any other model.
- ❌ Gold-plating the UI before the end-to-end path works.

## Definition of done (the demo must show, in order)

1. Pick a high-score alert from the queue.
2. Click Investigate → Llama traverses the ontology → **fraud-ring graph lights up**.
3. **STR narrative** appears with inline `object_id` citations + recommendation (CLEAR/ESCALATE/FILE).
4. Propose **freeze** → lands in **MLRO approval queue** → approve → executes → **audit entry** appears.
5. **Sovereignty beat:** runs with no network egress ("airplane mode").
6. **OAG vs RAG** toggle shows the difference.
7. **Procurement tab:** same engine, different ontology — proves the platform thesis.
