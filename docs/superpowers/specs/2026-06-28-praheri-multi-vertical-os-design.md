# Praheri — Multi-Vertical "Sovereign AIP OS" Design

**Date:** 2026-06-28
**Status:** Approved (brainstorm complete) — ready for implementation plan
**Author:** Suraj + Claude (brainstorming session)
**Supersedes nothing.** Builds on the shipped AML demo (U0–U16) without modifying it.

---

## 1. Purpose

Praheri today is a single, deep, fully-working AML/financial-crime investigation copilot. This
design turns it into what it always was architecturally: a **domain-agnostic operating system**
for governed, auditable, on-prem AI investigation over a typed ontology — with AML as vertical #1
and **five more sector dashboards** that prove the platform thesis by running on the *same engine*.

This document is **dual-purpose**:
- **Pitch story** for the 10 July 2026 hackathon (Meta × Reliance): "not a fraud tool — an OS."
- **Post-hackathon build plan** for actually expanding into lending, insurance, wealth, corporate.

### Success criteria
1. A judge can click **six sector dashboards** (AML + 5) and see the **same investigation cockpit**
   render different domains — visually proving "one engine, swappable ontologies."
2. A **Platform dashboard** shows the kernel + cartridges + live counters derived from config
   (so the "0 lines of engine code changed per vertical" claim is self-evidently true, not asserted).
3. The existing **AML hero demo is untouched** and carries zero regression risk.
4. Each new vertical does **real** graph traversal + signal detection on its sample data
   (ring graph lights up live); only the Llama narrative is pre-cached for stage stability.

---

## 2. The load-bearing concept (why this is an OS, not a fraud tool)

Two layers:

**Layer 1 — the ontology = typed nouns + typed links.** AML's nouns are `Account`, `Transaction`,
`Customer`, `Device`; its links are *owns*, *sent-money-to*, *shares-device-with*. The ontology is
just a vocabulary of object types and how they connect.

**Layer 2 — the engine = a domain-agnostic pipeline** that does the same five moves regardless of
what the nouns are:
1. **Triage** — pick the high-risk object
2. **Traverse** — walk the links to pull connected objects (a link is a link; the traversal code
   does not care whether it is *sent-money-to* or *treated-at* or *guaranteed-loan-of*)
3. **Detect signals** — run typology checks (structuring, circular flow, shared device, …)
4. **Decide** — Llama classifies and recommends CLEAR / ESCALATE / FILE
5. **Govern + audit** — propose an action, human approves, everything logged

**The punchline:** the engine never changes. A new vertical swaps only three things:

| Swap | AML | Insurance SIU | Lending EWS |
|---|---|---|---|
| **Nouns + links** | Account, Txn, Device | Claim, Policy, Hospital, Garage | Borrower, Loan, Collateral, Director |
| **Signals** | structuring, circular flow | staged-accident, ghost-hospital, shared-garage ring | EMI bounces, utilization creep, shared-director stress |
| **Actions** | freeze account, file STR | deny claim, refer to SIU | margin call, downgrade rating |

Same traversal. Same decide step. Same approval gate. Same audit log. Insurance fraud-ring
detection is *literally the same graph code* as AML — just different nouns. **That** is the OS.

---

## 3. Market grounding (from BFSI research, 2026-06-28)

The same structural signature recurs across **every** BFSI segment: workflows that are
**traversal-intensive** (link 3–6 object types), **judgment-laden** (a human must own the call),
**audit-mandated**, and **data-sovereignty-sensitive**. Highest-fit (all HIGH) workflows:

- **Payments:** AML/STR (the hero), payment-fraud triage, sanctions false-positive clearance, disputes/chargebacks.
- **Lending:** MSME underwriting, **Early-Warning-Signals (NPA prevention)**, collateral/LTV, stressed-asset restructuring.
- **Insurance:** health-claims adjudication, motor-claims + garage-fraud rings, **SIU claims-fraud investigation** (structurally identical to AML).
- **Wealth:** SEBI suitability assessment, portfolio rebalancing, **mis-selling investigation** (the audit log *is* the compliance artifact).
- **Corporate:** **UBO traversal**, trade-finance LC document checking, credit-memo review.

**Why on-prem open-weight is a legal argument, not a preference (India):**
- **RBI 2018 data-localization circular** — payment data must be stored *only in India*; piping txn data to a cloud LLM is arguably a breach.
- **DPDP Act 2023** — customer PII / health / claims data can't leave India without consent.
- **FSB (June 2026, finalizing Oct 2026)** — 12 sound practices: board accountability, human oversight. We build to a spec being written now.

**White space:** Palantir AIP (proprietary, US-centric, $100M+, no India residency) is the reference
architecture; Quantexa is the closest AML competitor (proprietary, no open-weight story). **Nobody**
offers open-weight Llama + on-prem + India residency + a *reusable* cross-vertical ontology platform.

---

## 4. Scope decisions (locked during brainstorm)

| Decision | Choice | Rationale |
|---|---|---|
| Demo-day breadth | **Hero + Platform + all 5 verticals shallow** | Breadth proves the platform thesis; judges must be able to *click* sectors. |
| Vertical liveness | **Real traversal + signals, cached narrative** | Genuine engine + live ring graph; narrative cached (same golden-cache pattern AML uses) for stage stability. |
| Page architecture | **One beautiful, themeable, config-driven template** (not 5 bespoke pages, not a bare generic page) | A shared template *is* the platform proof; divergent per-page code (Approach B) weakens the pitch and 6×'s the bug surface. Beauty comes from rich config + a design-skill polish pass, not divergent code. |
| Vertical lineup | **Option Y** | AML hero doubles as the Payments/financial-crime vertical; the 5 shallow ones are Lending, Insurance, Wealth, Corporate, **Procurement** (reuses the U12 stub → a *non-financial* sector strengthens "OS for anything"). |

### Navigation
```
🏛  PLATFORM                       ← the "OS" hero screen (kernel + 6 cartridges, live counters)
🔍  AML / Financial Crime          ← deep, fully-live hero (UNCHANGED — zero regression risk)
🏦  Lending — Early Warning Signals      ┐
🛡  Insurance — Claims Fraud (SIU)       │  5 shallow verticals,
📈  Wealth — Suitability & Mis-selling   │  one shared render_vertical()
🏢  Corporate — UBO / Trade Finance      │  driven by config cartridges
📦  Procurement — Maverick Spend         ┘  (procurement reuses U12)
+ existing tabs: Approvals · Audit · OAG-vs-RAG · Sovereignty
```

Every shallow vertical renders through the **same** `render_vertical(config)` function — they look
identical by construction, which *is* the proof.

---

## 5. Architecture

### 5.1 New module: `praheri/verticals.py`

Holds the `VerticalConfig` schema + the registry of 5 shallow-vertical configs. The Platform
dashboard and the shallow-vertical renderer both read this registry, so they cannot drift.

```python
class ObjectTypeSpec(BaseModel):
    name: str                     # "Claim"
    icon: str                     # node glyph/color hint for the graph
    key_props: list[str]          # properties surfaced in the object card

class SignalSpec(BaseModel):
    id: str                       # "ghost_hospital"
    label: str                    # "Ghost hospital ring"
    why: str                      # plain-English explanation shown in the UI

class ActionSpec(BaseModel):
    id: str                       # "deny_claim"
    label: str                    # "Deny claim"
    requires_approval: bool       # high-stakes → MLRO/approver queue

class KPI(BaseModel):
    label: str                    # "₹ at risk"
    value: str                    # "₹4.2 Cr"
    delta: str | None = None

class VerticalConfig(BaseModel):
    # identity / theming
    key: str                      # "insurance_siu"
    name: str                     # "Insurance — Claims Fraud (SIU)"
    icon: str
    accent_color: str             # hex — drives KPI cards + ring-graph palette
    tagline: str
    regulator: str                # "IRDAI · DPDP Act 2023" — chip

    # ontology cartridge
    object_types: list[ObjectTypeSpec]
    link_types: list[str]

    # domain content
    kpi_cards: list[KPI]
    signals: list[SignalSpec]
    actions: list[ActionSpec]

    # demo data + cached narrative
    sample_data_path: str         # synthetic objects for this vertical
    golden_cache_key: str         # pre-generated STR narrative (crash-safe)
```

### 5.2 New renderer: `render_vertical(config)` in the Streamlit app

A single function rendering any shallow vertical from its config:
1. **Sector hero band** — icon, name, tagline, regulator chip (themed by `accent_color`)
2. **KPI row** — 3–4 domain cards, bento-style
3. **Alert queue** — the canned alert(s) for this sector
4. **Investigate** → **real traversal** + **real signal detection** on the sample data →
   **ring graph lights up** (themed palette)
5. **Decision panel** — signals found + recommendation + **cached** narrative
6. **Govern** — propose action → drops into the **same shared Approvals queue** → Audit

The renderer calls the **existing** engine functions parameterized by config — it does **not**
reimplement them:
- traversal → existing `traverse_ring()` / `OntologyStore.get_linked_objects()`
- signals → `compute_signals()` generalized to accept a vertical's signal set
- governance → existing `@action` decorator + `approve()` + `read_audit()` from `governance.py`

### 5.3 Engine generalization (the only existing-code change)

`compute_signals()` (`agent.py`) and the action set (`governance.py`) are currently AML-specific.
They will be **extended to be config-driven**, in a way that is **additive** — the AML hero keeps
calling them exactly as today. Approach:
- Keep AML's bespoke path intact (the hero page calls the current functions unchanged).
- Add a generic entry point (e.g. `compute_signals_for(config, store, root_id)`) that dispatches to
  per-signal detector functions named in the config. AML's detectors are reused where they overlap
  (e.g. shared-device / shared-attribute ring detection ≈ shared-garage ring).

### 5.4 Platform dashboard

One screen that *shows* the architecture:
- **Center:** the engine as one box — *Triage → Traverse → Detect → Decide → Govern → Audit* —
  labeled "unchanged across all verticals."
- **Around it:** 6 cartridge tiles (AML, Lending, Insurance, Wealth, Corporate, Procurement),
  each clickable → jumps to that vertical.
- **Live counters, computed from the registry** (so they can't lie):
  `1 engine · 6 ontologies · N object types · M link types · K governed actions ·
  0 lines of engine code changed per vertical`.
- **On-screen money line:** *"Every vertical above is the same kernel + a config cartridge.
  Adding a sector = defining nouns, links, signals, actions. No new engine."*

Because counters + tiles derive from the same `VerticalConfig` registry the verticals render from,
the Platform screen is auto-consistent: add a config, it appears here for free.

---

## 6. Data flow (a shallow vertical investigation)

```
User picks alert (canned, from config)
        │
        ▼
render_vertical(config)
        │  reads config.sample_data_path → loads synthetic objects into the store
        ▼
traverse_ring(store, root_id)                 ← REAL, live (same code as AML)
        │  walks typed links → touched objects
        ▼
compute_signals_for(config, store, root_id)   ← REAL, live (config-driven detectors)
        │  fires this vertical's typology checks
        ▼
pyvis ring graph renders (themed by accent_color)   ← REAL, live
        │
        ▼
decision panel: signals + recommendation + narrative
        │  narrative = golden cache (config.golden_cache_key)   ← CACHED for stability
        ▼
propose action (config.actions) → shared Approvals queue → approve → Audit   ← REAL governance
```

---

## 7. Build sequence (phased; AML hero untouched until the end)

| Phase | What | Verify |
|---|---|---|
| **P0** | Add `verticals.py` (`VerticalConfig` + empty registry) and a `render_vertical()` skeleton **beside** the AML page. Do **not** modify the AML page. | AML demo runs identically; existing 52 tests green. |
| **P1** | Generic renderer + **1st config: Procurement** (reuse U12 data + `models_procurement.py`). Generalize `compute_signals` additively. | Procurement renders via `render_vertical`; traversal + graph live; cached narrative; AML still green. |
| **P2** | Add configs: **Insurance SIU** (cheapest — reuses AML ring code) + **Lending EWS**, with synthetic data + 1 planted ring each. | Both render; rings light up; signals fire; propose→approve→audit works. |
| **P3** | Add configs: **Wealth** + **Corporate**. | All 6 verticals in nav; each has 1–2 alerts + a planted ring. |
| **P4** | **Platform dashboard** (reads the registry) + `ui-ux-pro-max` polish pass on the shared template (bento cards, spacing, theming by `accent_color`). | Counters correct; per-vertical theming; layout polished, not default-Streamlit gray. |
| **P5** | Update `docs/demo_script.md` with the "swap a config → new sector" beat; rehearse full 6-tab click-through. | Full click-through clean; AML hero + 5 verticals + Platform all land. |

**Commit per green phase** (golden rule #8).

---

## 8. Constraints carried from `CLAUDE.md` (non-negotiable, still in force)

- **MVP / shallow scope** for the 5 new verticals: 1–2 alerts + a single planted ring each — enough
  to demo, **not** a second AML. Depth lives in AML; breadth lives in the configs.
- **Mutations only via `@action`** — new verticals' actions are real `@action`s through `governance.py`.
- **Everything audited** — new verticals write to the same `audit_log.jsonl`.
- **Synthetic data only** — no real financial data, ever.
- **Model stays Llama** — narratives (where live) come from local Ollama; shallow verticals use the
  golden cache.
- **OAG, not RAG-of-text** — retrieval returns structured objects, including in the new verticals.
- **Don't gold-plate the UI before the path works** — P0–P3 prove the path; P4 polishes.

---

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| New verticals destabilize the flawless AML demo | P0 isolates: AML page untouched; engine changes are additive; tests gate every phase. |
| 5 verticals = too much before 10 July | Shallow by design (1 ring each); config-driven means each is ~a config file, not a page; Procurement reuses U12. |
| Shallow verticals "feel fake" to a sharp judge | Real traversal + real signals + live ring graph; only narrative is cached (honest Live/Cached badge, as AML already does). |
| Config-driven pages look generic / hurt the sell | Rich per-sector config (domain KPIs, tailored copy, themed graph palette) + `ui-ux-pro-max` polish on the shared template. |
| Engine generalization breaks AML's bespoke path | Keep AML's current calls intact; add a parallel generic entry point rather than rewriting in place. |

---

## 10. Out of scope (roadmap slides, not code)

- Real ERP / core-banking / bureau / IRDAI / SEBI integrations.
- Document-extraction layer for trade-finance / claims docs (the verticals assume already-structured objects).
- Multi-tenant RBAC, OAuth, fine-tuning, Docker/k8s.
- Deep build-out of any shallow vertical into a second flagship.

---

## 11. Definition of done (demo must show, in order)

1. **Platform dashboard** — kernel + 6 cartridges + live counters; the "one engine" line.
2. **AML hero** — unchanged end-to-end (alert → investigate → ring → STR → freeze → approve → audit).
3. Click **Insurance SIU** → same cockpit, different domain → garage-fraud ring lights up → propose "refer to SIU."
4. Click **Lending / Wealth / Corporate / Procurement** → same cockpit each → real ring + cached narrative.
5. **The money beat:** "I didn't rebuild anything — I swapped a config cartridge. That's the OS."
6. Sovereignty + OAG-vs-RAG beats still land.
```
