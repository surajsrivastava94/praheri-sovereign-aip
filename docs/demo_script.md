# Praheri — 3-Minute Demo Script

> Bound to the actual built UI and the real planted-ring IDs. Rehearse until the
> beats are muscle memory. The hero ring is **ALERT-R001 / ACC-BENEF-STRUCT**.

---

## Pre-demo checklist (run T-10 minutes)

```bash
cd praheri-starter
source .venv/bin/activate

# 1. Ollama warm + models present
ollama list            # must show llama3.1:8b AND nomic-embed-text
ollama run llama3.1:8b "ok"   # warm the model so first investigate isn't cold

# 2. Fresh, deterministic data (resets any frozen accounts from prior runs)
python -m praheri.generate     # reprints the planted ring IDs

# 3. Prime the golden cache so the hero beat is instant + crash-proof
python -c "from praheri import agent; agent.investigate('ALERT-R001'); \
           agent.investigate('ALERT-R005'); print('cache primed')"

# 4. Launch
streamlit run app/streamlit_app.py
```

- [ ] Ollama responding; both models pulled
- [ ] `praheri.db` freshly regenerated (no leftover frozen accounts)
- [ ] `demo_cache/` primed for ALERT-R001 (hero) and ALERT-R005 (device ring)
- [ ] Sovereignty expander shows ✅ no external egress
- [ ] Backup video ready (see below)
- [ ] Browser zoomed so the graph is legible from the back of the room

---

## The 3-minute script

| Time | Beat | Action | Say |
|---|---|---|---|
| **0:00** | Hook | (slide or just talk) | *"An Indian bank cannot legally send this transaction data to OpenAI — RBI forbids it. Here's what it can do instead: a financial-crime copilot running fully on-prem on Llama."* |
| **0:20** | Alert Queue | Open **🚨 Alert Queue**. Point at the top rows. | *"Open AML alerts, ranked by risk. The top ones are flagged high-risk. Let's take the hottest — a funnel account."* Click **Investigate →** on **ALERT-R001**. |
| **0:40** | Investigate → ring | Go to **🔎 Investigation**, click **Run investigation**. Wait for the graph. | *"Llama is traversing the bank's ontology — accounts, transactions, devices — as structured objects. This is Ontology-Augmented Generation, not a chatbot guessing from text."* |
| **1:00** | The graph | Point at the lit-up ring (mules → beneficiary, green glow). | *"There's the ring: seven mule accounts, each fed sub-₹50,000 deposits to dodge reporting, all funnelling to one beneficiary. The engine detected the structuring pattern deterministically — the model explains it."* |
| **1:20** | STR narrative | Scroll to **🚦 signals** + **STR narrative**. Point at cited IDs. | *"It drafts a Suspicious Transaction Report, citing the actual account and transaction IDs as evidence, grounded in the bank's own AML policy. Recommendation: FILE."* |
| **1:50** | Governance | Click **Propose Freeze**. Switch sidebar role to **mlro**. Open **✅ Approvals**, approve it. Open **📜 Audit Trail**. | *"The AI cannot act on its own. It proposes a freeze — which lands in the MLRO's approval queue. The compliance officer approves… and every step is written to an immutable audit log: who, what, when, which model. Copilot, not autopilot."* |
| **2:20** | Sovereignty | Open sidebar **🛡️ Verify sovereignty** expander. (Optional: turn off Wi-Fi, re-run.) | *"Watch this — the system audits its own network calls. Zero external egress. The only connection is to the Llama model on this box. I can pull the network cable and it still works. This is the only RBI-compliant architecture."* |
| **2:40** | Platform | Open **🧾 Procurement** tab. Submit the over-budget PO. | *"And the ontology + action + governance layer underneath is reusable. Here's procurement — a completely different workflow, the same engine. The over-budget purchase order hits the exact same approval gate. One platform, every Reliance workflow."* |
| **3:00** | Close | (slide) | *"Praheri today — sovereign financial-crime defence. The Sovereign AIP layer underneath, tomorrow: across JFS, Jio, Retail and O2C. India shouldn't rent its intelligence. It should own it."* |

---

## Backup plan (live failure insurance)

1. **Golden cache** — if Ollama stalls, the hero investigation replays from
   `demo_cache/` instantly (the **💾 Cached** badge shows honestly).
2. **Backup video** — record a full clean run (see below) the day before. If the
   laptop melts, play the video and narrate over it.
3. **If a tab errors live** — fall back to the Alert Queue → Investigation hero
   path only; that single beat carries the story.

### Record the backup video (Day 14)
```bash
# Prime cache + launch, then screen-record the full 3-min run end to end.
# Save as docs/praheri_backup_demo.mp4. Watch it once to confirm audio + legibility.
```

---

## Q&A quick-reference (see BUILD_BIBLE §12 for full answers)
- **Why not RAG?** → RAG returns flat text; it can't traverse a ring. We showed it
  live — the OAG-vs-RAG toggle: same facts, RAG hedges, OAG files. Lower
  hallucination, real lineage, and the ability to *act*.
- **Why Llama / on-prem?** → RBI localization is criminal liability; data never
  egresses (verifiable — we audited it on screen); fine-tune on proprietary
  typologies; no per-token lock-in; auditable weights.
- **Scale across Reliance?** → The engine is workflow-agnostic. Swap ontology +
  actions → procurement, telecom ops, retail supply chain. That's the JV's PaaS.
- **Open-weight vs open-source?** → Correct, open-weight — which is *why* a
  Meta–Reliance JV matters: it licenses and hosts Llama for India.
- **Real vs mocked?** → Ontology, OAG traversal, Llama reasoning, action/approval/
  audit loop are real on synthetic data. Production needs real data integration +
  model-risk validation — that's the roadmap.
