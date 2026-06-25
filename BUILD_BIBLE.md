# Praheri — Sovereign AIP on Llama
### Build Bible · Meta–Reliance Intelligence Hackathon (10 July 2026)

**Builder:** Suraj (solo, product/strategy lead) · **Runway:** ~15 days · **Model:** Meta Llama (open-weight, on-prem)

> Working names — change freely. **Praheri** (प्रहरी, "sentinel") = the AML vertical product. **Sovereign AIP** = the reusable platform layer underneath. **Neev** (नींव, "foundation") is an alternative platform name if you want something Indian.

---

## 0. The one sentence

> *"Praheri is a sovereign financial-crime copilot: a Llama model running entirely inside the bank investigates alerts over a live ontology of accounts and transactions, proposes governed actions a compliance officer approves, and logs every step for the regulator — and the ontology + action + governance layer underneath is the reusable platform Reliance Intelligence can sell across JFS, Jio, Retail and O2C."*

Everything below serves that sentence.

---

## 1. The thesis (why this wins)

Everyone at the hackathon builds "a Llama chatbot for X." A chatbot is a feature and the model is interchangeable — that loses. Palantir's moat was never the model; it was three things stacked:

1. **Ontology** — a typed, living "digital twin" of the business (objects, links, and *actions*). The LLM reasons over **structured objects**, not text chunks. Palantir calls this **OAG** (Ontology-Augmented Generation), vs. plain RAG.
2. **Action layer** — the AI doesn't just answer; it **proposes a specific, permissioned action** a human approves before anything writes back. "A copilot, not autonomous driving."
3. **Governance in the runtime** — the AI only sees what the calling user can see; every action is audited; nothing is a black box.

Swap GPT for Llama and the value doesn't move. **The ontology + action + governance layer is the durable IP** — and it happens to be exactly what the Meta–Reliance JV sells: an enterprise platform to *customize, deploy, and **govern*** GenAI on Llama.

**The wedge — sovereignty as legal necessity, not preference.** In Indian BFSI, sending customer/transaction data to OpenAI or Gemini is not a privacy nicety — it is illegal. RBI's payment-data localization rule is enforced with real onboarding bans (American Express, Mastercard, Diners). The Finance Ministry banned ChatGPT/DeepSeek on government devices (Jan 2025). DRDO's DG: *"we can't afford to depend on AI models coming from abroad."* On-prem open-weight Llama is the **only compliant architecture**. That is the most powerful single sentence available in this entire problem space.

**The Reliance framing (quote these):** Mukesh Ambani — *"India cannot afford to rent intelligence."* Akash Ambani — Reliance Intelligence will deliver *"sovereign hosting within India, with full model transparency and portability… so every enterprise can own its AI journey,"* and *"what Jio did for data, Reliance Intelligence will do for AI."*

---

## 2. Scope discipline (the most important page)

The #1 failure mode for a solo 2-week build is breadth. Your edge is **one flawless path**, not five flaky ones.

**In the MVP demo (must work, must be polished):**
- One ontology with ~7 object types and the links between them.
- One Llama-driven **investigation pipeline** (not a 5-agent swarm — see §5).
- **3 actions**, with 2 of them behind a human-approval gate.
- An **immutable audit log** you can show on screen.
- A **graph visualization** of the fraud ring (your single most memorable visual).
- A **local-only / "airplane mode"** run to prove sovereignty live.
- A **thin procurement "workflow #2"** reusing the same engine — even a stub — to prove the platform thesis.

**Vision slides only (do NOT build):** real ERP/core-banking integration, model-risk validation, multi-tenant RBAC, fine-tuning, production scale. Say these are "next" — judges respect a sharp MVP + a credible roadmap over a broken everything.

**Hard rules:** synthetic data only; frame as decision-support copilot, never a certified AML system; reliability beats architectural flourish.

---

## 3. The Ontology (the moat — build this first)

Model the **nouns** (objects + links) and the **verbs** (actions). This is what makes it "Palantir-grade" instead of a chatbot.

### 3.1 Object types

| Object | Key properties | Links |
|---|---|---|
| **Customer** | customer_id, name, kyc_risk_rating, pep_flag, nationality, occupation, onboarding_date | owns → Account |
| **Account** | account_id, customer_id, type, branch, balance, status, open_date | held_by → Customer; sends/receives → Transaction; used_on → Device |
| **Transaction** | txn_id, from_account, to_account, amount, currency, channel, timestamp | from/to → Account; to → Counterparty |
| **Counterparty** | counterparty_id, name, type, bank, country, risk_flags | receives → Transaction |
| **Device** | device_id, ip, geo, first_seen | used_by → Account(s) |
| **Alert** | alert_id, account_id, rule, score, status, created_at | raised_on → Account; bundled_in → Case |
| **Case** | case_id, alert_ids, assigned_to, status, decision, narrative | bundles → Alert(s) |

### 3.2 Actions (permissioned, audited "verbs")

| Action | Params | Permission | Approval gate? |
|---|---|---|---|
| `clear_alert` | alert_id, rationale | analyst | no (but audited) |
| `escalate_alert_to_case` | alert_id, reason | analyst | no |
| `request_account_freeze` | account_id, reason | analyst proposes | **yes — MLRO approves** |
| `file_str` | case_id, narrative | analyst proposes | **yes — MLRO approves** |
| `add_case_note` | case_id, note | analyst | no |

### 3.3 Object schema — starter code (paste into an AI coding assistant)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

class Customer(BaseModel):
    customer_id: str
    name: str
    kyc_risk_rating: Literal["low", "medium", "high"]
    pep_flag: bool = False
    nationality: str = "IN"
    occupation: Optional[str] = None
    onboarding_date: datetime

class Transaction(BaseModel):
    txn_id: str
    from_account: str
    to_account: str
    counterparty_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    channel: Literal["UPI", "IMPS", "NEFT", "RTGS", "CASH"]
    timestamp: datetime
# ...Account, Counterparty, Device, Alert, Case follow the same pattern
```

**The first design decision that makes this "AIP, not a chatbot":** retrieval always returns the **structured object** (`{type, id, properties, linked_ids}`) to the model — never a text paragraph. That is OAG.

---

## 4. Governance layer (your second differentiator)

**The second design decision:** the LLM can **only act through defined, permissioned, audited actions** — it never writes to the database directly.

- **Permission scope** — the agent runs *as the calling analyst*. What the analyst can't see, the model can't see. No "run as admin" for the AI.
- **Human-approval gate** — any action with `requires_approval=True` does **not** execute. It writes a row to `pending_approvals`; the MLRO reviews and approves in the UI; only then does it execute. This is "copilot, not autopilot."
- **Immutable audit log** — append-only. Every object query, every proposed action, every approval/rejection, with `actor`, `timestamp`, `model_name`, and a `prompt_hash`. This is the slide that wins the governance argument — and the thing a regulator actually wants.

### Action + audit pattern — starter code

```python
def action(requires_role, requires_approval=False):
    def wrap(fn):
        def inner(actor, **params):
            assert actor.role == requires_role or actor.role == "mlro"
            entry = audit.log("ACTION_PROPOSED", actor, fn.__name__, params)
            if requires_approval:
                pending.add(entry.id, fn.__name__, params, proposed_by=actor.id)
                return {"status": "PENDING_APPROVAL", "ref": entry.id}
            result = fn(actor, **params)
            audit.log("ACTION_EXECUTED", actor, fn.__name__, params, result=result)
            return result
        return inner
    return wrap

@action(requires_role="analyst", requires_approval=True)
def request_account_freeze(actor, account_id, reason): ...
```

---

## 5. The agent pipeline (a pipeline, NOT a swarm)

Multi-agent "swarms" are fragile and break on stage. Collapse the roles into a **legible deterministic pipeline** where one Llama instance does tool-calling at each step. Reliability is your friend.

```
[1] TRIAGE        rank open alerts by score → pick the hottest
        ↓
[2] INVESTIGATE   OAG: traverse the ontology from the alerted account →
                  pull linked accounts, transactions, shared devices,
                  counterparties → assemble the ring as STRUCTURED OBJECTS
        ↓
[3] EVIDENCE      RAG over a small policy/KYC store (thresholds, typologies)
        ↓
[4] DECIDE+DRAFT  Llama recommends CLEAR / ESCALATE / FILE and drafts the
                  STR narrative, CITING object_ids as evidence
        ↓
[5] HUMAN GATE    analyst/MLRO reviews → approves action → execute → AUDIT
```

### Llama system-prompt skeleton

```
You are an AML investigation copilot operating inside a bank's secure environment.

You can ONLY use these tools to read data: query_objects, get_linked_objects, search_policy.
You can ONLY act by PROPOSING these actions: clear_alert, escalate_alert_to_case,
request_account_freeze, file_str. You may never write data directly.

Rules:
1. Always query objects and traverse links BEFORE forming a conclusion.
2. Ground every claim in specific object_ids. Cite them in your narrative.
3. Recommend exactly one of: CLEAR, ESCALATE, FILE.
4. request_account_freeze and file_str require human approval — propose, don't assume.
5. If evidence is insufficient or ambiguous, escalate to a human. Do not guess.
```

Tools exposed to the model: `query_objects(type, filter)`, `get_linked_objects(object_id, link_type)`, `search_policy(query)`, plus the four action proposers. Use a plain Python tool-calling loop (or LangGraph if you're comfortable) — keep it simple.

---

## 6. Reference architecture + sovereign stack

```
┌─────────────────────────────────────────────────────────────┐
│  ON-PREM / IN-COUNTRY PERIMETER  (data never egresses)        │
│                                                               │
│  Synthetic core-bank data ──► Ontology store (SQLite +        │
│                                Pydantic) + graph (networkx)    │
│                                      │                         │
│  Policy/KYC docs ──► Vector store (Chroma)                    │
│                                      │                         │
│         ┌────────────────────────────┴───────────┐            │
│         │  Llama (Ollama / vLLM / NVIDIA NIM)     │            │
│         │  tool-calling investigation pipeline    │            │
│         └────────────────────────────┬───────────┘            │
│                                      │                         │
│   Streamlit console: alert queue · ring graph · proposed      │
│   action · MLRO approval · audit trail                        │
│                                      │                         │
│                          Append-only AUDIT LOG (SQLite)        │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Pick (solo-friendly) | Notes |
|---|---|---|
| Model | **Llama 3.3 70B** in prod story; **Llama 3.1 8B** for the laptop demo | via **Ollama** (OpenAI-compatible). Mention vLLM/NVIDIA NIM for production throughput. |
| Ontology store | SQLite + Pydantic | typed objects; foreign keys = links |
| Graph | **networkx** + **pyvis**/Cytoscape.js | pyvis renders the ring beautifully with little code |
| Policy RAG | **Chroma** (local) | 5–10 short AML policy/threshold docs |
| Orchestration | plain Python tool-loop | LangGraph optional |
| UI | **Streamlit** | ideal for a product/strategy builder |
| Audit | SQLite append-only table | the regulator's view |

**Keep the model = Llama.** (The earlier idea set referenced *Nemotron* — that's an NVIDIA model and would be tone-deaf here. NVIDIA stays as *infrastructure*: GB300/NIM. Llama is the star.)

---

## 7. Synthetic data plan (this makes or breaks the demo)

Write one generator that produces a believable bank and **plants the rings you'll demo**:

- ~500 Customers, ~1,500 Accounts, ~20,000 Transactions, ~300 Counterparties, ~400 Devices.
- **Planted typology A — Structuring/smurfing:** many sub-threshold cash/UPI deposits into 6–8 mule accounts that funnel to one beneficiary. (Your hero demo.)
- **Planted typology B — Circular layering:** A→B→C→A loops to obscure origin.
- **Planted typology C — Shared-device ring:** 10+ "unrelated" accounts transacting from one device_id/IP.
- Generate matching **Alerts** on the entry points so triage has something to grab.

Because *you* planted the rings, the demo is deterministic and clean — but the investigation (traversal + reasoning + narrative) is genuinely done by Llama.

---

## 8. The 15-day plan (today → 10 July)

Always keep a demoable build. Date anchors assume start ~26 June.

| Day | Goal |
|---|---|
| **1** | Lock scope. Repo + Ollama + pull Llama 3.1 8B. Streamlit "hello world". |
| **2–3** | Ontology models + synthetic data generator with the 3 planted rings. Load into SQLite + networkx. |
| **4** | Read layer: `query_objects`, `get_linked_objects`. Streamlit **alert queue** screen. |
| **5–6** | Llama tool-calling loop: **investigate** step returns structured objects and narrates the ring. |
| **7** | **Graph viz** (pyvis) — the ring lights up. ✅ **MIDPOINT CHECKPOINT: one alert, end-to-end, works.** |
| **8** | Policy RAG (Chroma) + **STR narrative** drafting grounded in object_ids. |
| **9** | **Action layer + approval gate + audit log** (freeze/file behind MLRO approval). |
| **10** | **Workflow #2 (procurement) stub** — same engine, tiny Requisition/Vendor/Contract ontology + one action. Proves reuse. |
| **11** | Sovereignty proof: local-only run + "airplane mode" path; **OAG-vs-RAG toggle** for the side-by-side. |
| **12** | Polish UI; write & rehearse the 3-min demo. |
| **13** | Build the pitch deck (see §10). |
| **14** | Buffer + **record a backup demo video** (insurance against live failure) + rehearse Q&A. |
| **15 (10 Jul)** | Hackathon. |

---

## 9. The 3-minute demo script

| Time | Beat |
|---|---|
| 0:00 | **Hook:** "An Indian bank cannot legally send this data to OpenAI — RBI forbids it. Here's what it can do instead, running fully on-prem on Llama." |
| 0:20 | Open the **alert queue** → pick a high-score flagged account. |
| 0:40 | Click **Investigate** → graph lights up the ring (mules → shared device → beneficiary). *"It's reasoning over structured objects and their links — Ontology-Augmented Generation, not a chatbot guessing from text."* |
| 1:20 | Show the **STR narrative** with inline citations to object IDs + the recommendation: **FILE**. |
| 1:50 | **Governance beat:** propose **freeze** → it lands in the **MLRO approval queue** → approve → a new **audit entry** appears (who/what/when/which model). *"The AI can't act on its own."* |
| 2:20 | **Sovereignty beat:** toggle airplane mode / show zero network egress. *"Data never left the box. This is the only RBI-compliant architecture."* |
| 2:40 | **Platform beat:** switch to the **procurement tab** — same engine, different ontology. *"One layer. Every Reliance workflow. That's the JV's PaaS."* |
| 3:00 | **Close:** "Praheri today. The sovereign AIP layer underneath — tomorrow, across JFS, Jio, Retail and O2C." |

---

## 10. Pitch deck spine (~11 slides)

1. **Title** — Sovereign AIP on Llama · Praheri.
2. **The trap** — everyone's building Llama chatbots (a feature, not a moat).
3. **The Palantir lesson** — Ontology + Action + Governance is the moat.
4. **The Reliance thesis** — Ambani quotes ("cannot afford to rent intelligence" / "sovereign hosting… own your AI journey").
5. **The wedge** — regulated India: data legally can't leave (RBI bans, Finance-Ministry ChatGPT ban, DRDO).
6. **The product** — Praheri in one line + one screenshot.
7. **How it works** — the architecture diagram (OAG → action → governance).
8. **Demo** (live or the backup video).
9. **Why Llama / why on-prem** — open-weight, 60–80% cost savings at scale, IndiaAI subsidized GPUs. **Depth signal:** Llama is *open-weight, not open-source* (OSI is explicit) — and the 700M-MAU license ceiling is *exactly why a Meta–Reliance JV matters*: it licenses + hosts Llama for India and neutralizes that ceiling for enterprises.
10. **The platform** — AML today → procurement next → Jio/Retail/O2C. The reusable layer RI sells.
11. **The ask / close.**

---

## 11. Risks & how to de-risk

| Risk | Mitigation |
|---|---|
| Multi-agent fragility | Use a **pipeline**, not a swarm. |
| Live demo dies | **Pre-record a backup video** on Day 14. |
| Llama too big for laptop | Demo on **8B**; cite 70B for production. |
| "Looks like vapor" | Real working investigation on (synthetic) data — the traversal & reasoning are genuinely Llama. |
| "How is this different from Hawk/Quantifind?" | They're SaaS detection (often foreign-hosted). You're a **sovereign, on-prem, open-weight decision + action + audit layer the bank owns** — and one instance of a reusable platform. |
| Overclaiming | "Decision-support copilot, synthetic data, not a certified AML system." Say it before they ask. |

---

## 12. Anticipated judge Q&A

- **"Why not just RAG?"** → RAG returns flat text chunks; it can't traverse a fraud ring or guarantee permissioned, structured facts. OAG returns **governed objects with explicit links** → lower hallucination, real lineage, and the ability to *act*.
- **"Why on-prem / why does Llama specifically matter?"** → RBI localization is criminal liability; data never egresses (a verifiable engineering fact, not a vendor promise); fine-tune on proprietary typologies; no per-token lock-in; auditable weights. Closed APIs **cannot** offer this by architecture.
- **"How does it scale across Reliance?"** → The ontology + action + governance engine is workflow-agnostic. Swap the ontology + actions and you get procurement, telecom ops, retail supply chain. That *is* the JV's Platform-as-a-Service.
- **"Isn't Llama only open-weight, not open source?"** → Correct — and that's precisely why the Meta–Reliance JV is the right vehicle: it licenses and hosts Llama for the Indian market, giving enterprises a sovereign, supported path and neutralizing the 700M-MAU ceiling.
- **"What's real vs mocked?"** → The ontology, OAG traversal, Llama reasoning, and the action/approval/audit loop are real and working on synthetic data. Production needs real data integration and model-risk validation — that's the roadmap.

---

*Build the moat first (ontology + governance), keep the model swappable, and let the demo — fraud-ring graph + the airplane-mode moment + the procurement tab — tell the story.*
