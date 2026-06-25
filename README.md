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

# 2. Local Llama (sovereignty = it runs on your machine, no API)
#    install Ollama from https://ollama.com, then:
ollama pull llama3.1:8b
ollama serve            # exposes OpenAI-compatible API at http://localhost:11434/v1

# 3. Generate synthetic data with planted fraud rings
python -m praheri.generate

# 4. Run the console
streamlit run app/streamlit_app.py
```

## How to build it

- `CLAUDE.md` — the rules Claude Code follows (read first).
- `PROMPT_PLAYBOOK.md` — the exact prompts to drive Claude Code, in order.
- `BUILD_BIBLE.md` — the full spec: ontology, governance, architecture, 2-week plan, demo script, pitch, judge Q&A.

## Status

Skeleton. Files contain typed stubs and `TODO(playbook step N)` markers. Follow the playbook to fill them in. **Synthetic data only — not a certified AML system.**
