# PROMPT_PLAYBOOK.md — driving Claude Code, in order

Paste these into Claude Code **one at a time**, in order. After each, run the **Verify** check before moving on. Don't batch them — the point is to keep control and a working build at every step.

> First message of every new session: *"Read CLAUDE.md and BUILD_BIBLE.md before doing anything. Confirm the golden rules back to me in one line, then wait."*

---

### Phase 1 — Ontology + data (Days 2–3)

**Prompt 1.1**
> Implement `praheri/models.py`: Pydantic models for the 7 object types in BUILD_BIBLE §3.1 (Customer, Account, Transaction, Counterparty, Device, Alert, Case) with the listed properties and sensible types. Add a `LINKS` dict documenting the link types. No persistence yet.

*Verify:* `python -c "from praheri import models; print(models.Customer.model_fields.keys())"`

**Prompt 1.2**
> Implement `praheri/generate.py` per BUILD_BIBLE §7. Use Faker. Generate ~500 customers, ~1500 accounts, ~20k transactions, counterparties, devices, and matching alerts. Then plant exactly 3 rings as separate functions: `plant_structuring()`, `plant_circular()`, `plant_shared_device()`. Write everything to a SQLite db `praheri.db`. Print a summary of planted rings (the account_ids) so I know the demo entry points.

*Verify:* run it; confirm `praheri.db` exists and the planted ring account_ids are printed.

**Prompt 1.3**
> Implement `praheri/store.py`: an `OntologyStore` class over `praheri.db` with `query_objects(type, **filters)`, `get_object(type, id)`, `get_linked_objects(object_id, link_type)`, and `build_graph()` returning a networkx graph of accounts/transactions/devices/counterparties. Every read returns structured dicts `{type, id, properties, linked_ids}` — never strings.

*Verify:* query one planted-ring account and confirm `get_linked_objects` returns its transactions + shared device.

---

### Phase 2 — The risky spike: Llama + OAG (Days 4–6)

**Prompt 2.1**
> Implement `praheri/agent.py`: the `SYSTEM_PROMPT` from BUILD_BIBLE §5, a `TOOLS` spec for `query_objects`, `get_linked_objects`, `search_policy`, and the 4 action proposers, and `call_llama(messages, tools)` hitting the local Ollama OpenAI-compatible endpoint (`http://localhost:11434/v1`, model `llama3.1:8b`). Implement a tool-calling loop. No actions execute yet — just wire reads.

*Verify:* ask the agent "investigate account <planted ring id>"; confirm it calls `get_linked_objects` and returns structured objects, not invented text.

**Prompt 2.2**
> Implement `investigate(alert_id)` in `agent.py`: triage the alert → traverse from the alerted account to assemble the ring as structured objects → return a structured `Investigation` result (objects touched, ring summary, recommendation CLEAR/ESCALATE/FILE). Enforce that the model cites `object_id`s.

*Verify:* `investigate()` on each of the 3 planted rings returns the correct accounts and a FILE/ESCALATE recommendation.

---

### Phase 3 — UI + the graph (Day 7) → MVP CHECKPOINT

**Prompt 3.1**
> Build `app/streamlit_app.py` with an **Alert Queue** tab (list alerts sorted by score, click to select) and an **Investigation** tab that runs `investigate()` and renders the touched objects as a **pyvis** network graph, highlighting the ring. Show the agent's recommendation.

*Verify:* end-to-end in the browser — pick an alert, see the ring light up. **This is the MVP checkpoint; commit and tag it.**

---

### Phase 4 — Evidence + narrative (Day 8)

**Prompt 4.1**
> Implement `praheri/policy_rag.py` using chromadb over `policies/*.md`. Add `search_policy(query)`. Wire it as the `search_policy` tool so the agent grounds thresholds/typologies in policy.

**Prompt 4.2**
> Add STR narrative drafting to `investigate()`: the agent drafts a structured STR narrative citing `object_id`s and the matched policy clause. Render it in the Investigation tab.

*Verify:* narrative references real planted-ring object_ids and a policy clause.

---

### Phase 5 — Actions, approval, audit (Day 9)

**Prompt 5.1**
> Implement `praheri/governance.py` per BUILD_BIBLE §4: an append-only audit log, an `@action` decorator with role + `requires_approval`, the 5 actions, and a pending-approvals queue. `request_account_freeze` and `file_str` must NOT execute — they enqueue for MLRO approval.

**Prompt 5.2**
> Add an **Approvals (MLRO)** tab and an **Audit Trail** tab to Streamlit. Proposing freeze/file from Investigation creates a pending item; approving it executes and writes an audit entry visible in the Audit tab.

*Verify:* full loop — propose → approve → execute → audit entry with actor/timestamp/model.

---

### Phase 6 — Platform proof + sovereignty (Days 10–11)

**Prompt 6.1**
> Add a **Procurement** tab proving vertical #2: a tiny ontology (Requisition, Vendor, Contract, Budget) in a new `models_procurement.py`, reusing the SAME `agent`, `governance`, and `store` machinery, with one action `approve_purchase_order` behind a budget-threshold approval gate. Keep it minimal — the point is to show the engine is workflow-agnostic.

**Prompt 6.2**
> Add an **OAG vs RAG** toggle in the Investigation tab: RAG mode flattens objects to text chunks before sending to the model; OAG mode sends structured objects + links. Show both answers side by side so the difference is visible.

*Verify:* procurement runs through the same approval/audit loop; OAG visibly beats RAG on the ring.

---

### Phase 7 — Polish (Days 12–14)

- Day 12: clean the UI, write the 3-min demo script (BUILD_BIBLE §9), rehearse.
- Day 13: build the pitch deck (BUILD_BIBLE §10).
- Day 14: **record a backup demo video**, rehearse the judge Q&A (BUILD_BIBLE §12).

> Ongoing prompt when Claude Code over-builds: *"Stop — re-read the Do NOT list in CLAUDE.md. Revert anything outside MVP scope."*
