# Praheri — 3-Minute Demo Script

> Bound to the actual built UI and the real planted-ring IDs. Rehearse until the
> beats are muscle memory. The hero ring is **ALERT-R001 / ACC-BENEF-STRUCT**.

---

## Pre-demo checklist (run T-10 minutes)

```bash
cd ~/Praheri-AIP
source .venv/bin/activate

# 1. Ollama warm + models present
ollama list            # must show llama3.1:8b AND nomic-embed-text
ollama run llama3.1:8b "ok"   # warm the model so first investigate isn't cold

# 2. Fresh, deterministic data (resets any frozen accounts from prior runs)
python -m praheri.generate              # AML: reprints the planted ring IDs
python -m praheri.generate_verticals    # the 5 vertical cartridges' synthetic data

# 3. Prime the golden caches so every replay is instant + crash-proof
#    a) AML hero + device ring
python -c "from praheri import agent; agent.investigate('ALERT-R001'); \
           agent.investigate('ALERT-R005'); print('AML cache primed')"
#    b) the 4 investigation verticals (insurance/lending/wealth/corporate)
python -m praheri.vertical_engine       # prints source + length per vertical

# 4. Launch
streamlit run app/streamlit_app.py
```

- [ ] Ollama responding; both models pulled
- [ ] `praheri.db` freshly regenerated (no leftover frozen accounts)
- [ ] `data/verticals/*.json` present (vertical cartridge data generated)
- [ ] `demo_cache/` primed for ALERT-R001 (hero) + ALERT-R005 (device ring)
      **and** the 4 verticals (insurance_siu / lending_ews / wealth / corporate)
- [ ] Sovereignty expander shows ✅ no external egress
- [ ] Backup video ready (see below)
- [ ] Browser zoomed so the graph is legible from the back of the room

---

## The 3-minute script

| Time | Beat | Action | Say |
|---|---|---|---|
| **0:00** | Hook + the OS | App opens on **🌐 Platform**. Point at the live counters + the cartridge tiles. | *"An Indian bank cannot legally send this data to OpenAI — RBI forbids it. So we built the alternative on-prem on Llama. And it's not one app — it's an OS: one engine, six ontologies, zero lines of engine code changed per sector. Let me show you the flagship: financial crime."* |
| **0:25** | Alert Queue | Open **🚨 Alert Queue**. Point at the top rows. Click **Investigate →** on **ALERT-R001**. | *"Open AML alerts, ranked by risk. Let's take the hottest — a funnel account."* |
| **0:45** | Investigate → ring | Go to **🔎 Investigation**, click **Run investigation**. Wait for the graph. | *"Llama is traversing the bank's ontology — accounts, transactions, devices — as structured objects. This is Ontology-Augmented Generation, not a chatbot guessing from text."* |
| **1:05** | The graph | Point at the lit-up ring (mules → beneficiary, green glow). | *"There's the ring: seven mule accounts, each fed sub-₹50,000 deposits to dodge reporting, all funnelling to one beneficiary. The engine detected the structuring pattern deterministically — the model explains it."* |
| **1:25** | STR narrative | Scroll to **🚦 signals** + **STR narrative**. Point at cited IDs. | *"It drafts a Suspicious Transaction Report, citing the actual account and transaction IDs as evidence, grounded in the bank's own AML policy. Recommendation: FILE."* |
| **1:50** | Governance | Click **Propose Freeze**. Switch sidebar role to **mlro**. Open **✅ Approvals (MLRO)**, approve it. Open **📜 Audit Trail**. | *"The AI cannot act on its own. It proposes a freeze — which lands in the MLRO's approval queue. The compliance officer approves… and every step is written to an immutable audit log: who, what, when, which model. Copilot, not autopilot."* |
| **2:15** | Sovereignty | Open sidebar **🛡️ Verify sovereignty** expander. (Optional: turn off Wi-Fi, re-run.) | *"The system audits its own network calls. Zero external egress — the only connection is to the Llama model on this box. Pull the network cable and it still works. The only RBI-compliant architecture."* |
| **2:35** | Platform → swap a sector | Back to **🌐 Platform** (point at the tiles), then click **🏢 Corporate** → **Run investigation**. Let the same cockpit light up a circular-ownership ring. | *"Now watch the OS thesis. Same engine, same cockpit — but a completely different sector. Corporate ownership: it unwinds a circular shell structure (CO-A→CO-B→CO-C) to the hidden beneficial owner. Zero engine code changed — Insurance, Lending, Wealth all run off the same loop."* |
| **2:50** | Procurement gate | Open **🧾 Procurement**. Submit the over-budget PO. | *"And the governance layer is reusable too — this over-budget purchase order hits the exact same approval gate. One platform, every Reliance workflow."* |
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
