# Praheri Reference Brief — Palantir Ontology Framing, Sector Detail, USP & Design Language

> Research compiled for the Praheri explainer/landing page (`explainer.html`).
> Sections 1 & 5 sourced from Palantir's own docs + shipped front-end CSS (cited).
> Sections 2–4 are synthesis/distillation for Praheri (domain terms verified vs. standard AML/SEBI/RBI/FATF usage).

---

## 1. How Palantir Explains "Ontology"

**Core definition (verbatim from Palantir docs):** the Ontology is *"a categorization of the world"* and *"the digital twin of an organization, a rich semantic layer that sits on top of the digital assets"* — *"an operational layer for the organization."* It goes *"far beyond data cataloging or schema design."*

**Two-layer structure (the spine of the explanation):**
- **Semantic layer — what things are and how they relate.** Object types & objects (object type ≈ dataset/table; object ≈ row). Properties (≈ columns). Link types & links (≈ joins) — turns flat tables into a connected graph of reality. "Complete with granular security and governance."
- **Kinetic layer — how you act on the world.** Action types = *"a schema for sets of changes users can apply to objects, property values, and links,"* with side effects on submission. This is how decisions **write back** and push to existing systems. Functions = business logic over objects.

**The kinetic move:** the Ontology is bidirectional — not a read-only graph. Decisions flow back as Actions. *"The goal of investing in the Ontology is to facilitate better decision-making in an organization at scale."* Canonical blog: **"The Ontology: Investing in Decisions."** Arc: data → semantic model → decisions captured as Actions → write-back → model stays live.

**AIP (their AI layer) over the Ontology** — directly analogous to Praheri: LLMs use objects + Actions as tools. Human-in-the-loop, verbatim: users *"inspect the logic behind each proposed action and, upon approval, have changes automatically applied."* Governance: *"detailed audit trails, explanations, and evaluations of model decisions,"* *"historical lineage in AI operations."*

**Exec narrative arc:** (1) data in silos describes the world but isn't *about* it → (2) Ontology builds a digital twin (objects+properties+links) → (3) analysts & AI explore the map, not raw tables → (4) decisions captured as Actions that write back → (5) everything governed & audited.

Sources: palantir.com/docs/foundry/ontology/overview, /core-concepts, /aip/overview, /aip/aip-features.

---

## 2. The Ontology, Distilled (plain English, for Praheri)

**Typed ontology:** model the world as **typed objects** (`Account`, `Transaction`, `Company`, `Claim`) with **typed properties** (balance, risk_score) connected by **typed links** (`Account —sent→ Transaction —received_by→ Account`). A graph of nouns and verbs mirroring reality; the type system enforces what can connect to what.

**Beats raw tables:** relationships in tables are implicit (foreign keys, fragile JOINs). Tracing a ring 6 hops deep in SQL = a monstrous recursive query. In an ontology it's a **native graph traversal** — the links *are* the structure.

**Beats RAG-over-text (= the "OAG" differentiator):** RAG retrieves prose that *mentions* entities; the model re-parses English to guess connections — and hallucinates links or misses them. **OAG (Ontology-Augmented Generation)** retrieves structured objects with real links — `{type, id, properties, linked_ids}` — so the model reasons over ground-truth structure. Every claim cites a real `object_id`.

**Concrete example:** *RAG* = 10 fuzzy case notes ("Account 4471 received several transfers... shares an address with a flagged customer"); model can't reliably tell you it's 5 accounts + 12 transactions, may invent links. *OAG* = 5 `Account` objects + 12 `Transaction` links forming a near-cycle + 2 `Person` objects on a shared-address link; model traverses, sees the cycle, names every node by ID, UI lights up the actual ring. **The structure is the evidence.**

One-liner: *RAG retrieves what was written about the world. OAG retrieves the world itself — typed, linked, and verifiable.*

---

## 3. Per-Sector "What It Actually Does"

- **AML (hero):** Banks drown in transaction-monitoring false positives while real laundering hides. Traverse from flagged `Account` across `Transaction` links to counterparties, `Customer`/`Person`, shared `Device`/`Address`. Detect structuring/smurfing (sub-threshold deposits dodging CTR reporting), layering/pass-through, fan-in/out funnels, circular mule flows. Draft an STR/SAR narrative tied to evidence objects. Governed action (MLRO approves): `request_account_freeze` / `file_str` (FIU-IND). Built: 3 planted rings — structuring (7 mules→1 beneficiary), circular layering (A→B→C→A), shared-device ring (12 accts).

- **Insurance SIU:** A single claim looks fine; fraud is in the links *between* claims. Traverse `Claim` → `Policyholder`, `Garage`, `Claimant`, `Policy`. Detect staged-accident rings, garage/provider collusion (one workshop across many claims), identity reuse. Signal = shared-node density. Governed action (SIU lead): `refer_to_siu` (hold payout). Built: shared-garage ring.

- **Lending EWS:** Loans go bad over months; stress signals scatter before NPA classification. Traverse `Borrower` → `Loan`, `Director`, `Inflow`. Detect EMI-bounce stress, common-director contagion (a director whose other companies already default), circular related-party lending. Governed action (credit officer): `margin_call` / `downgrade_rating` / SMA. Built: common-director cluster + EMI-bounce stress.

- **Wealth (suitability/mis-selling):** Advisors pushed to sell high-commission products to ill-fitting clients → SEBI exposure. Traverse `Client` → `SuitabilityProfile`, `Sale`, `Product`, `Adviser`. Detect suitability breaches (conservative retiree → leveraged product), churning, advisor-level patterns. Signal = RiskProfile↔Holding mismatch. Governed action (compliance): `flag_misselling`. Built: adviser mis-selling cluster.

- **Corporate UBO:** FATF Rec 24 / RBI require knowing the real human owner; ownership is obscured via layered holdings. Traverse `Company —owns→ Company/UBO` shareholding graph through layers. Detect circular/cross holdings, shell layers, threshold evasion (<25% line), opaque cross-border layering. Signal = the shape of the ownership graph. Governed action (KYC officer): `escalate_kyc_review` / EDD. Built: circular ownership + shared-UBO cluster.

- **Procurement:** Off-contract buying & order-splitting erode margin and invite collusion. Traverse `Requisition` → `Vendor`, `Budget`, `Contract`. Detect maverick spend, budget/DoA breach, invoice-splitting, vendor-collusion affinity. Governed action (finance controller): `approve_purchase_order` (over-budget → MLRO gate). Built: over-budget PO gate.

---

## 4. USP / Key Principles (headline-ready)

**(a) OAG > RAG:** "RAG retrieves text about your data. OAG retrieves your data — typed, linked, verifiable." · "Structure in, not paragraphs in." · "Every claim cites an object ID." · "The fraud ring is the evidence."

**(b) Sovereign / on-prem / open-weight:** "Your data never leaves the building." · "RBI data-localization isn't a setting, it's the architecture." · "No per-token tax, no vendor lock-in." · "Auditable weights, fine-tunable model." · "A frozen API can change under you. Open weights can't."

**(c) Governance — copilot, not autopilot:** "The model proposes. A human approves. Everything is audited." · "No mutation without a governed Action." · "High-stakes actions need a human signature." · "Append-only audit on every query, proposal, approval — actor, timestamp, model name."

**(d) Platform thesis:** "One engine. Swap the ontology cartridge. New sector — zero engine code." · "The investigation loop is universal; only the nouns change." · "Six verticals, one codebase." · "Build the platform once, monetize it six times."

---

## 5. Palantir Visual / UX Design Language (borrowable tokens — from shipped CSS + Blueprint)

**Color — charcoal not black; color rationed as signal (~90% grayscale).**
- Canvas `#1c2127`/`#1e2124` · elevated panel `#2f343c` · deepest `#111418`
- Text: primary `#f6f7f9`/`#fff` headlines · body `#e5e5e5` · muted `#abb3bf` · faint `#738694`
- Hairline `rgba(255,255,255,0.12–0.2)` · brand accent ONE: `#2b5945` forest + 10% wash
- Intent: primary `#2d72d2` · success `#238551` · warning `#c87619` · danger `#cd4246`
- Qualitative data palette (graph nodes): `#2d9cdb #3dcc4a #e0ad2b #eb6847 #7c6ad4 #13c9ba #9bbf30`, neutral `#a7b6c2`

**Typography:** grotesque (Alliance → use **Inter**), only 400/700. Mono (**IBM Plex Mono**) for `object_id`s/numeric cells. Big headlines with **-0.02em** tracking. Uppercase eyebrows/labels with **+0.1em** tracking (classification-tag vibe).

**Motion:** easing `cubic-bezier(.19,1,.22,1)` (easeOutExpo) & `cubic-bezier(.645,.045,.355,1)` (easeInOutCubic) — never plain ease. Durations `.125s–.25s`. Staggered scroll reveals (translateY+opacity, per-item delay 75/100/220ms). Network-graph motif as hero (nodes + thin edges lighting up sequentially).

**Layout:** hairline borders not boxes. Near-zero radius (0–4px). Negative space + huge tight headlines. Data-dense surfaces: 4px grid, ~14px base, thin dividers, mono numeric columns, status dots.

**Why it reads operational:** monochrome discipline · charcoal not black · grotesque + tight tracking · uppercase +0.1em micro-labels · sharp corners + hairlines + dense grids · fast expo motion · data-viz as hero.
