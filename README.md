# Praheri — Sovereign AIP on Llama

A sovereign financial-crime (AML) investigation copilot. A **Llama** model running **fully on-prem** investigates AML alerts over a typed **ontology**, exposes fraud rings by traversing links, drafts an STR, and **proposes governed actions a human approves** — with a full audit trail. AML is vertical #1 of a reusable platform; procurement is vertical #2.

Built for the Meta–Reliance Intelligence Hackathon (10 July 2026).

## Why it matters (the pitch in one line)

Indian banks **cannot legally** send customer/transaction data to OpenAI/Gemini (RBI data-localization). On-prem open-weight **Llama** is the only compliant architecture — and the ontology + action + governance layer is the platform Reliance Intelligence can sell across JFS, Jio, Retail and O2C.

## Quickstart

```bash
# 1. Python env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Local Llama + embeddings (sovereignty = it runs on your machine, no API)
#    install Ollama from https://ollama.com, then:
ollama pull llama3.1:8b        # the investigation model
ollama pull nomic-embed-text   # local embeddings for policy RAG (no network)
ollama serve                   # OpenAI-compatible API at http://localhost:11434/v1

# 3. Generate synthetic data with planted fraud rings
python -m praheri.generate     # prints the planted ring IDs (demo entry points)

# 4. (optional) prime the golden cache so the demo is instant + crash-proof
python -c "from praheri import agent; agent.investigate('ALERT-R001')"

# 5. Run the console
streamlit run app/streamlit_app.py
```

Full demo flow and a pre-demo checklist live in `docs/demo_script.md`.
Verify zero network egress any time with `python -m praheri.sovereignty`.

## How to build it

- `CLAUDE.md` — the rules Claude Code follows (read first).
- `PROMPT_PLAYBOOK.md` — the exact prompts to drive Claude Code, in order.
- `BUILD_BIBLE.md` — the full spec: ontology, governance, architecture, 2-week plan, demo script, pitch, judge Q&A.

## Status

**Built and working** (all playbook phases complete; 52 tests passing). End-to-end:
pick alert → Llama traverses the ontology → fraud-ring graph lights up → STR with
cited `object_id`s → propose freeze → MLRO approves → audit entry. Plus the
procurement vertical, OAG-vs-RAG toggle, and a verifiable no-egress sovereignty
check.

Run the tests: `pytest` (live tests need Ollama running).

**Synthetic data only — decision-support copilot, not a certified AML system.**

## Architecture (what's real)

| Module | Role |
|---|---|
| `praheri/models.py` | 7-type ontology (the nouns + links) |
| `praheri/generate.py` | synthetic bank + 3 planted fraud rings (deterministic) |
| `praheri/store.py` | OAG read layer — structured objects, not text; ring graph |
| `praheri/agent.py` | hybrid pipeline: Python traverses + detects signals, Llama classifies/decides/drafts; plus a live model-driven tool loop |
| `praheri/policy_rag.py` | local Chroma + Ollama-embedding policy retrieval |
| `praheri/governance.py` | audit log + `@action` + approval gate + the actions (AML & procurement) |
| `praheri/sovereignty.py` | verifiable no-external-egress self-check |
| `app/streamlit_app.py` | the analyst console (5 tabs = the demo beats) |
