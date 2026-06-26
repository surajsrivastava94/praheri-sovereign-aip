# Praheri — Pitch Deck Outline (~11 slides)

> Spine from BUILD_BIBLE.md §10. One idea per slide. Quotes are load-bearing —
> use them verbatim. Slide *design* is manual; this is the content skeleton.

---

### 1 — Title
**Sovereign AIP on Llama · Praheri**
Sovereign financial-crime defence, running entirely inside the bank.
*(Subtitle: Meta–Reliance Intelligence Hackathon · synthetic data · decision-support)*

### 2 — The trap
Everyone at this hackathon is building "a Llama chatbot for X."
A chatbot is a feature, and the model is interchangeable. **That loses.**

### 3 — The Palantir lesson
The moat was never the model. It's three things stacked:
**Ontology** (typed digital twin) + **Action layer** (governed, human-approved) +
**Governance in the runtime** (permissioned, fully audited).
Swap GPT for Llama and the value doesn't move — *the layer* is the IP.

### 4 — The Reliance thesis
> Mukesh Ambani: *"India cannot afford to rent intelligence."*
> Akash Ambani: Reliance Intelligence will deliver *"sovereign hosting within
> India… so every enterprise can own its AI journey."* — *"What Jio did for data,
> Reliance Intelligence will do for AI."*

### 5 — The wedge (sovereignty as law, not preference)
In Indian BFSI, sending customer/transaction data to OpenAI or Gemini isn't a
privacy nicety — **it's illegal.** RBI payment-data localization (enforced:
Amex, Mastercard, Diners onboarding bans). Finance-Ministry ChatGPT ban (Jan 2025).
DRDO: *"we can't afford to depend on AI models coming from abroad."*
**On-prem open-weight Llama is the only compliant architecture.**

### 6 — The product (Praheri, in one line + one screenshot)
A Llama copilot that investigates AML alerts over a live ontology, proposes
governed actions a compliance officer approves, and logs every step for the
regulator. *(Screenshot: the lit-up fraud-ring graph.)*

### 7 — How it works (architecture diagram)
Synthetic core-bank data → **Ontology** (SQLite + networkx) → **OAG traversal** →
Llama (Ollama, on-prem) reasons → **proposes action** → **MLRO approval gate** →
**immutable audit log**. Policy RAG (local Chroma) grounds the evidence.
*(One diagram: OAG → action → governance, inside an on-prem perimeter.)*

### 8 — Demo
Live (or the backup video). The four beats: ring lights up → STR with citations →
freeze → MLRO approves → audit entry → airplane-mode → procurement tab.

### 9 — Why Llama / why on-prem
Open-weight → fine-tune on proprietary typologies, no per-token lock-in, auditable
weights, 60–80% cost savings at scale, IndiaAI subsidized GPUs.
**Depth point:** Llama is *open-weight, not open-source* (OSI is explicit) — and the
700M-MAU license ceiling is *exactly why a Meta–Reliance JV matters*: it licenses +
hosts Llama for India and neutralizes that ceiling for enterprises.

### 10 — The platform
AML today → procurement next (we built it — same engine) → Jio, Retail, O2C.
**The reusable ontology + action + governance layer is what Reliance Intelligence
sells. That's the PaaS.**

### 11 — The ask / close
*"Praheri today. The Sovereign AIP layer underneath — tomorrow, across JFS, Jio,
Retail and O2C. India shouldn't rent its intelligence. It should own it."*

---

## Differentiator one-liner (for the back pocket)
*"Hawk and Quantifind are SaaS detection, often foreign-hosted. Praheri is a
sovereign, on-prem, open-weight decision + action + audit layer the bank owns —
and one instance of a reusable platform."*
