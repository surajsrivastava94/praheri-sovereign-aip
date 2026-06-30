"""Praheri analyst console (UI skeleton). See BUILD_BIBLE.md §9 for the demo flow.

Tabs map directly to the demo beats:
  Alert Queue -> Investigation (graph + STR) -> Approvals (MLRO) -> Audit Trail -> Procurement

Run: streamlit run app/streamlit_app.py
TODO(playbook steps 3.1, 5.2, 6.1, 6.2): wire each tab to the modules.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Streamlit puts this script's dir (app/) on sys.path, not the repo root, so the
# praheri package isn't importable by default. Add the repo root explicitly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

from praheri import agent, governance
from praheri.governance import Actor
from praheri.store import OntologyStore


@st.cache_resource
def get_store() -> OntologyStore:
    return OntologyStore()


store = get_store()

# Node styling by ontology kind — makes the ring structure pop on screen.
_NODE_STYLE = {
    "account": {"color": "#4C9AFF", "shape": "dot", "size": 18},
    "device": {"color": "#FF5630", "shape": "diamond", "size": 26},
    "counterparty": {"color": "#FFAB00", "shape": "triangle", "size": 20},
}


def render_ring_graph(account_ids: list[str], highlight: set[str]) -> None:
    """Render the scoped ring as a pyvis network inside the Streamlit page."""
    g = store.build_graph(account_ids)
    net = Network(height="520px", width="100%", bgcolor="#1a1a2e",
                  font_color="white", directed=True)
    net.barnes_hut(spring_length=120)
    for node, data in g.nodes(data=True):
        kind = data.get("kind", "account")
        style = dict(_NODE_STYLE.get(kind, _NODE_STYLE["account"]))
        if node in highlight:  # alerted account / ring core glows
            style["color"] = "#36B37E"
            style["size"] = style["size"] + 10
        net.add_node(node, label=data.get("label", node), title=f"{kind}: {node}",
                     **style)
    for u, v, data in g.edges(data=True):
        net.add_edge(u, v, title=data.get("label", ""), label=data.get("label", ""))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        net.save_graph(f.name)
        html = open(f.name).read()
    components.html(html, height=540)

def render_vertical_graph(g, highlight: set[str], accent: str = "#36B37E") -> None:
    """Render any GenericOntologyStore.build_graph() output as a pyvis network.
    Sibling of render_ring_graph (which is AML-store-bound) — keeps that untouched.
    Node colour comes from per-type styling; highlighted nodes glow in `accent`."""
    net = Network(height="520px", width="100%", bgcolor="#1a1a2e",
                  font_color="white", directed=True)
    net.barnes_hut(spring_length=120)
    palette = ["#4C9AFF", "#FFAB00", "#FF5630", "#00B8D9", "#998DD9", "#57D9A3"]
    kinds = sorted({d.get("kind", "node") for _, d in g.nodes(data=True)})
    kind_color = {k: palette[i % len(palette)] for i, k in enumerate(kinds)}
    for node, data in g.nodes(data=True):
        kind = data.get("kind", "node")
        color = accent if node in highlight else kind_color.get(kind, "#4C9AFF")
        size = 28 if node in highlight else 18
        net.add_node(node, label=data.get("label", node),
                     title=f"{kind}: {node}", color=color, size=size)
    for u, v, data in g.edges(data=True):
        net.add_edge(u, v, title=data.get("label", ""), label=data.get("label", ""))
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        net.save_graph(f.name)
        html = open(f.name).read()
    components.html(html, height=540)


# --------------------------------------------------------------------------- #
# Shared visual system (U9). Pure inline-styled HTML blocks rendered via        #
# st.markdown — scoped to the HTML we emit, so NO global CSS bleed into the AML #
# hero tabs. Theming is driven entirely by each config's accent_color; nothing  #
# here branches per vertical. Dark-mode (OLED) tokens align with the canvas.    #
# --------------------------------------------------------------------------- #
_SURFACE = "#0F172A"        # card surface
_BORDER = "#334155"         # neutral border
_FG = "#F8FAFC"             # foreground text
_MUTED = "#94A3B8"          # muted label text
_PLATFORM_ACCENT = "#4C9AFF"  # brand accent for the multi-vertical Platform view
_STATUS_COLOR = {"FILE": "#FF5630", "ESCALATE": "#FFAB00", "CLEAR": "#36B37E"}

# --------------------------------------------------------------------------- #
# Guided Demo mode (Stage 1). The canonical 3-min flow as a stepper. The banner #
# above the tab bar names the tab to click + the action + the narration line;   #
# `done` is a pure-read predicate that marks a beat ✓ (it never auto-advances —  #
# Next/Back is the only advancer, so the 4 narration-only beats work too). Copy  #
# is lifted from docs/demo_script.md so on-screen guide & spoken script can't    #
# drift. Streamlit can't switch tabs programmatically, so the banner *tells* the #
# judge which tab to open (same idiom as the Platform 'Open →' jump).            #
# --------------------------------------------------------------------------- #
_DEMO_STEPS = [
    {"n": 1, "title": "Hook — the sovereign OS", "tab": "🌐 Platform",
     "action": "Point at the live counters + the cartridge tiles.",
     "say": "An Indian bank cannot legally send this data to OpenAI — RBI forbids "
            "it. So we built the alternative on-prem on Llama. And it's not one "
            "app — it's an OS: one engine, six ontologies, zero lines of engine "
            "code changed per sector. Here's the flagship: financial crime.",
     "done": None},
    {"n": 2, "title": "Pick the hottest alert", "tab": "🚨 Alert Queue",
     "action": "Click  Investigate →  on  ALERT-R001  (top row).",
     "say": "Open AML alerts, ranked by risk. Let's take the hottest — a funnel "
            "account.",
     "done": lambda s: s.get("selected_alert_id") == "ALERT-R001"},
    {"n": 3, "title": "Investigate → traverse", "tab": "🔎 Investigation",
     "action": "Click  🔎 Run investigation.",
     "say": "Llama is traversing the bank's ontology — accounts, transactions, "
            "devices — as structured objects. This is Ontology-Augmented "
            "Generation, not a chatbot guessing from text.",
     "done": lambda s: (s.get("investigation") or {}).get("alert_id") == "ALERT-R001"},
    {"n": 4, "title": "The ring lights up", "tab": "🔎 Investigation",
     "action": "Point at the lit-up fraud ring (mules → beneficiary).",
     "say": "There's the ring: mule accounts each fed sub-₹50,000 deposits to dodge "
            "reporting, all funnelling to one beneficiary. The engine detected the "
            "structuring pattern deterministically — the model explains it.",
     "done": lambda s: (s.get("investigation") or {}).get("alert_id") == "ALERT-R001"},
    {"n": 5, "title": "STR narrative + signals", "tab": "🔎 Investigation",
     "action": "Scroll to the 🚦 signals + draft STR narrative; point at the cited IDs.",
     "say": "It drafts a Suspicious Transaction Report, citing the actual account "
            "and transaction IDs as evidence, grounded in the bank's own AML "
            "policy. Recommendation: FILE.",
     "done": lambda s: bool((s.get("investigation") or {}).get("str_narrative"))},
    {"n": 6, "title": "Governance — propose, approve, audit", "tab": "✅ Approvals (MLRO)",
     "action": "On Investigation: 🔒 Propose Freeze. Switch sidebar role to mlro, "
               "approve here, then check 📜 Audit Trail.",
     "say": "The AI cannot act on its own. It proposes a freeze — which lands in "
            "the MLRO's queue. The officer approves, and every step is written to "
            "an immutable audit log: who, what, when, which model. Copilot, not "
            "autopilot.",
     "done": None},
    {"n": 7, "title": "Sovereignty", "tab": "🛡️ (sidebar) Verify sovereignty",
     "action": "Open the 🛡️ Verify sovereignty expander in the sidebar. "
               "(Optional: pull Wi-Fi and re-run.)",
     "say": "The system audits its own network calls. Zero external egress — the "
            "only connection is to the Llama model on this box. Pull the cable and "
            "it still works. The only RBI-compliant architecture.",
     "done": None},
    {"n": 8, "title": "Swap the sector — same engine", "tab": "🏢 Corporate",
     "action": "Open 🏢 Corporate, click Investigate, then 🔎 Run investigation.",
     "say": "Now the OS thesis. Same engine, same cockpit — a completely different "
            "sector. Corporate ownership: it unwinds a circular shell structure to "
            "the hidden beneficial owner. Zero engine code changed — Insurance, "
            "Lending, Wealth all run off the same loop.",
     "done": lambda s: bool(s.get("vinv_corporate"))},
    {"n": 9, "title": "Reusable governance", "tab": "🧾 Procurement",
     "action": "Open 🧾 Procurement, submit the over-budget PO.",
     "say": "The governance layer is reusable too — this over-budget purchase order "
            "hits the exact same approval gate. One platform, every Reliance "
            "workflow. India shouldn't rent its intelligence — it should own it.",
     "done": None},
]


def _kpi_card_html(label: str, value: str, delta: str | None, accent: str) -> str:
    """One accent-bordered bento KPI card as a self-contained HTML string."""
    delta_html = (
        f"<div style='color:{accent};font-size:0.78rem;font-weight:500;"
        f"margin-top:6px'>{delta}</div>" if delta else "")
    return (
        f"<div style='background:{_SURFACE};border:1px solid {_BORDER};"
        f"border-top:3px solid {accent};border-radius:12px;padding:16px 18px;"
        f"min-height:104px;word-break:break-word'>"
        f"<div style='color:{_MUTED};font-size:0.78rem;font-weight:500;"
        f"letter-spacing:0.02em'>{label}</div>"
        f"<div style='color:{_FG};font-size:1.5rem;font-weight:700;"
        f"margin-top:4px;line-height:1.2'>{value}</div>"
        f"{delta_html}</div>")


def _what_you_see(text: str, accent: str = _PLATFORM_ACCENT) -> None:
    """A quiet 'what to watch here' guide-rail callout (matches the vertical hero)."""
    st.markdown(
        f"<div style='background:{accent}14;border-left:3px solid {accent};"
        f"border-radius:0 8px 8px 0;padding:10px 14px;margin:4px 0 14px;"
        f"color:{_FG};font-size:0.86rem;line-height:1.5'>"
        f"<b style='color:{accent}'>👁 What you'll see here</b> · {text}</div>",
        unsafe_allow_html=True)


def _signal_count(detail: str, evidence_ids: list[str]) -> int:
    """Pull the headline count from a signal's detail string (it leads with the
    number — '7 mule account(s)…', '6 …accounts transact…'); fall back to counting
    the account evidence ids. Used by the confidence score (Stage 3)."""
    import re
    m = re.match(r"\s*(\d+)", detail or "")
    if m:
        return int(m.group(1))
    return sum(1 for i in evidence_ids if i.startswith("ACC-"))


def _confidence(inv: dict) -> tuple[int, str, list[str]]:
    """Deterministic, UI-derived confidence for the recommendation — explainable
    term-by-term (judges ask 'how computed?'). Pure function of the cached `inv`;
    no engine change, no model call. Returns (score 0-100, band, reasons)."""
    rec = inv.get("recommendation", "ESCALATE")
    score = {"FILE": 60, "ESCALATE": 35, "CLEAR": 15}.get(rec, 35)
    reasons = [f"base {rec} = {score}"]
    typ_seen = set()
    for s in inv.get("signals", []):
        typ = s["typology"]
        typ_seen.add(typ)
        n = _signal_count(s.get("detail", ""), s.get("evidence_ids", []))
        if typ == "structuring":
            add = min(15 + 3 * max(0, n - 1), 30)
            reasons.append(f"structuring ({n} mules) +{add}")
        elif typ == "circular_layering":
            add = 20
            reasons.append(f"circular layering +{add}")
        elif typ == "shared_device_ring":
            add = min(15 + 2 * max(0, n - 5), 25)
            reasons.append(f"shared-device ring ({n} accts) +{add}")
        else:
            add = 10
            reasons.append(f"{typ} +{add}")
        score += add
    if len(typ_seen) >= 2:
        score += 10
        reasons.append(f"{len(typ_seen)} typologies corroborate +10")
    if inv.get("policy_citations"):
        score += 5
        reasons.append("policy-grounded +5")
    score = max(0, min(100, score))
    band = "High" if score >= 75 else "Medium" if score >= 45 else "Low"
    return score, band, reasons


def _ring_timeline(store, ring_accounts: list[str], cap: int = 40) -> tuple[list[dict], int]:
    """Chronological transactions among the ring accounts. Scoped to the ring via
    per-account indexed queries — never a full-table scan of the 20k+ txns. Returns
    (rows up to cap, total found). Read-only; engine untouched."""
    seen: dict[str, dict] = {}
    ring = set(ring_accounts)
    for acct in ring_accounts:
        for direction in ("from_account", "to_account"):
            for t in store.query_objects("Transaction", **{direction: acct}):
                seen[t["id"]] = t["properties"]
    rows = sorted(seen.values(), key=lambda p: str(p.get("timestamp", "")))
    return rows[:cap], len(rows)


def _render_demo_guide(step: dict, idx: int, total: int) -> None:
    """The persistent guided-demo banner (above the tab bar, so it survives tab
    clicks). Shows the step pill, the tab to open, the action, and the narration
    'say' line. A ✓ appears when the beat's pure-read predicate is satisfied."""
    accent = _PLATFORM_ACCENT
    done = bool(step["done"] and step["done"](st.session_state))
    # mono eyebrow (quiet, tracked) instead of a loud solid-fill pill
    pill = (f"<span style='background:{accent}1f;color:{accent};font-weight:600;"
            f"font-size:0.66rem;letter-spacing:0.14em;text-transform:uppercase;"
            f"font-family:\"IBM Plex Mono\",monospace;padding:2px 8px;"
            f"border-radius:6px;white-space:nowrap'>Step {idx + 1} / {total}</span>")
    check = (f"<span style='color:{_STATUS_COLOR['CLEAR']};font-weight:500;"
             f"font-size:0.74rem;margin-left:8px'>✓ done — Next ▶</span>"
             if done else "")
    st.markdown(
        f"<div class='praheri-demo-banner' style='background:{_SURFACE};"
        f"border:1px solid {accent}33;border-left:2px solid {accent};"
        f"border-radius:10px;padding:10px 14px;margin-bottom:12px'>"
        f"<div style='display:flex;align-items:center;gap:9px;margin-bottom:5px'>"
        f"{pill}"
        f"<span style='color:{_FG};font-weight:600;font-size:0.9rem'>"
        f"{step['title']}</span>{check}</div>"
        f"<div style='color:{_FG};font-size:0.82rem;line-height:1.5'>"
        f"<b style='color:{accent}'>Go to</b> the <b>{step['tab']}</b> tab · "
        f"{step['action']}</div>"
        f"<div style='color:{_MUTED};font-size:0.76rem;line-height:1.5;"
        f"margin-top:5px;font-style:italic'>🗣 “{step['say']}”</div>"
        f"</div>", unsafe_allow_html=True)


def _render_orientation() -> None:
    """Collapsed 'how to read this console' + glossary, for a judge with no context.
    Display-only; collapsed by default so the live demo stays uncluttered."""
    with st.expander("🧭 New here? How to read this console", expanded=False):
        st.markdown(
            "**Praheri investigates financial-crime alerts the way an analyst "
            "would** — but over a *typed ontology* (a live graph of accounts, "
            "claims, companies…) instead of documents. One on-prem Llama model "
            "runs the same six-step pipeline for every sector:")
        st.markdown(
            "1. **Triage** — rank the day's alerts by risk.\n"
            "2. **Traverse** — walk the graph from the flagged object to everything "
            "linked to it.\n"
            "3. **Detect** — run typology checks (deterministic code) to spot the "
            "fraud pattern.\n"
            "4. **Decide** — recommend CLEAR · ESCALATE · FILE, citing the exact "
            "object IDs.\n"
            "5. **Govern** — the model *proposes* an action; a human approves it.\n"
            "6. **Audit** — every query, proposal and approval is logged, immutably.")
        st.markdown(
            "**The tabs:** &nbsp; 🌐 **Platform** = the one-engine-many-sectors "
            "overview · 🚨 **Alert Queue** → 🔎 **Investigation** = the AML hero "
            "flow · ✅ **Approvals** = the human sign-off gate · 📜 **Audit** = the "
            "immutable trail · the rest (🧾🛡🏦📈🏢) = the *same engine* on five "
            "other sectors. Use the **sidebar** to switch between acting as an "
            "*analyst* (proposes) or *MLRO* (approves).")
        st.caption("Synthetic data only — decision-support, not a certified AML "
                   "system. Runs fully on-prem with no external network calls.")

    with st.expander("📖 Glossary — the jargon, in plain English", expanded=False):
        st.markdown(
            "- **Ontology** — a typed graph of real-world objects (accounts, claims, "
            "companies) and the links between them; Praheri's 'digital twin'.\n"
            "- **OAG (Ontology-Augmented Generation)** — the model retrieves "
            "*structured objects + their links*, not text paragraphs. It's why the "
            "ring can be reconstructed. The opposite is **RAG**, which flattens "
            "everything to prose and loses the links.\n"
            "- **Typology** — a known fraud pattern (e.g. *structuring*, "
            "*staged-accident ring*, *circular ownership*).\n"
            "- **STR (Suspicious Transaction Report)** — the regulatory filing a "
            "bank submits to the financial-intelligence unit.\n"
            "- **MLRO (Money Laundering Reporting Officer)** — the human who must "
            "approve high-stakes actions (freezes, filings).\n"
            "- **Ring / cluster** — a group of objects connected in a way that "
            "reveals coordinated fraud (e.g. mule accounts moving money in a loop).\n"
            "- **SIU** — Insurance Special Investigation Unit. **EWS** — Lending "
            "Early-Warning Signals. **NPA** — Non-Performing Asset (a bad loan). "
            "**DPD** — Days Past Due. **UBO** — Ultimate Beneficial Owner (the real "
            "human behind layered companies).")


def _section(label: str, accent: str) -> None:
    """Accent-themed section subheader (replaces plain `##### …`)."""
    st.markdown(
        f"<div style='font-size:0.95rem;font-weight:600;color:{_FG};"
        f"margin:20px 0 8px;padding-left:10px;border-left:3px solid {accent}'>"
        f"{label}</div>", unsafe_allow_html=True)


def _hero_band(config, accent: str) -> None:
    """Cohesive accent-themed sector header: icon+name, tagline, regulator chip, and
    (for a cold reader) the real-world use case + a 'what you'll see here' callout."""
    use_case_html = (
        f"<div style='color:{_FG};font-size:0.9rem;line-height:1.55;"
        f"margin:10px 0 12px;max-width:80ch'>{config.use_case}</div>"
        if getattr(config, "use_case", "") else "")
    st.markdown(
        f"<div style='background:{_SURFACE};"
        f"background-image:linear-gradient(135deg,{accent}3a,transparent 72%);"
        f"border:1px solid {accent}55;border-radius:14px;padding:18px 22px;"
        f"margin-bottom:10px'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:{_FG}'>"
        f"{config.icon} {config.name}</div>"
        f"<div style='color:{_MUTED};font-size:0.95rem;margin:4px 0 0'>"
        f"{config.tagline}</div>"
        f"{use_case_html}"
        f"<span style='background:{accent};color:#fff;padding:3px 12px;"
        f"border-radius:10px;font-size:0.78rem;font-weight:500'>"
        f"{config.regulator}</span>"
        f"</div>", unsafe_allow_html=True)
    # "What you'll see here" — a quiet guide rail for a judge with no context.
    if getattr(config, "what_you_see", ""):
        st.markdown(
            f"<div style='background:{accent}14;border-left:3px solid {accent};"
            f"border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;"
            f"color:{_FG};font-size:0.86rem;line-height:1.5'>"
            f"<b style='color:{accent}'>👁 What you'll see here</b> · "
            f"{config.what_you_see}</div>", unsafe_allow_html=True)


def render_vertical(config) -> None:
    """Shared renderer for the config-driven shallow verticals. Same six bands for
    every cartridge — the visual sameness IS the platform proof. Real traversal +
    signal detection; narrative golden-cached. AML keeps its own bespoke tab."""
    import json as _json

    from praheri import vertical_engine
    from praheri.governance import approve_purchase_order
    from praheri.vertical_store import GenericOntologyStore

    accent = config.accent_color
    # 1) sector hero band — cohesive accent-themed header (icon+name+tagline+chip)
    _hero_band(config, accent)

    # 2) KPI row — accent-bordered bento cards (own HTML; no global st.metric restyle)
    if config.kpi_cards:
        cols = st.columns(len(config.kpi_cards))
        for col, kpi in zip(cols, config.kpi_cards):
            col.markdown(_kpi_card_html(kpi.label, kpi.value, kpi.delta, accent),
                         unsafe_allow_html=True)

    # load the cartridge's synthetic data (skip gracefully if not generated yet)
    try:
        data = _json.loads(open(config.sample_data_path).read())
    except FileNotFoundError:
        st.warning(f"No data for `{config.key}`. Run "
                   "`python -m praheri.generate_verticals`.")
        return
    vstore = GenericOntologyStore(data)

    # 3) Procurement is action-centric (budget gate), not investigation-centric.
    if config.key == "procurement":
        _render_procurement_actions(vstore, approve_purchase_order)
        return

    # 3') Investigation-centric verticals: alert queue -> investigate -> signals.
    _section("🚨 Alerts", accent)
    alerts = vstore.query_objects("Alert")
    if not alerts:
        st.info("No alerts seeded for this vertical yet.")
        return
    for a in alerts:
        root = a["linked_ids"].get("raised_on", a["properties"].get("root_id", ""))
        root = root[0] if isinstance(root, list) and root else root
        if st.button(f"Investigate {a['id']} →", key=f"vinv_{config.key}_{a['id']}"):
            st.session_state[f"vinv_{config.key}"] = root

    root_id = st.session_state.get(f"vinv_{config.key}")
    if not root_id:
        return
    inv = vertical_engine.compute_vertical_investigation(config, vstore, root_id)
    badge = {"FILE": "🔴", "ESCALATE": "🟠", "CLEAR": "🟢"}.get(inv["recommendation"], "⚪")
    rec_color = _STATUS_COLOR.get(inv["recommendation"], accent)
    src = "🟢 Live" if inv["source"] == "live" else "💾 Cached"
    c1, c2 = st.columns(2)
    c1.markdown(_kpi_card_html("Recommendation", f"{badge} {inv['recommendation']}",
                               None, rec_color), unsafe_allow_html=True)
    c2.markdown(_kpi_card_html("Source", src, None, accent), unsafe_allow_html=True)

    _section("Ring graph (OAG traversal)", accent)
    render_vertical_graph(vstore.build_graph(inv["objects_touched"]),
                          highlight=set(inv["cited_ids"]), accent=accent)

    if inv["signals"]:
        _section("🚦 Detected typology signals (engine)", accent)
        for s in inv["signals"]:
            st.markdown(f"- **{s['typology']}** — {s['detail']}")
    if inv["narrative"]:
        _section("Draft narrative", accent)
        st.write(inv["narrative"])
    st.caption("Cited: " + ", ".join(f"`{i}`" for i in inv["cited_ids"]))

    # govern: propose the vertical's action(s) into the SAME approval queue
    if config.actions:
        from praheri import governance as _gov

        _section("Actions", accent)
        st.caption("The model never writes data. It *proposes* an action; a human "
                   "approves it. High-stakes ones (🔒) wait in the MLRO approval "
                   "queue, and every proposal + approval is written to the audit "
                   "trail.")
        acts = st.columns(len(config.actions))
        for col, act in zip(acts, config.actions):
            label = f"🔒 {act.label}" if act.requires_approval else act.label
            tip = ("Routes to the MLRO approval queue — nothing executes until a "
                   "human approves." if act.requires_approval
                   else "Executes immediately and is recorded in the audit trail.")
            if col.button(label, key=f"vact_{config.key}_{act.id}", help=tip):
                actor = st.session_state.get("_actor")
                fn = (_gov.propose_vertical_action if act.requires_approval
                      else _gov.execute_vertical_action)
                r = fn(actor, vertical=config.key, action_id=act.id,
                       target_id=root_id, reason=inv["recommendation"])
                if r["status"] == "PENDING_APPROVAL":
                    st.warning(f"{r['status']} — {act.label} routed to MLRO "
                               "(same gate as account freeze). See Approvals.")
                else:
                    st.success(f"{r['status']}: {r.get('result', '')}")


def _render_procurement_actions(vstore, approve_purchase_order) -> None:
    """Procurement's per-requisition budget gate, rendered from the generic store."""
    from praheri.verticals import get_config as _get_config

    accent = _get_config("procurement").accent_color
    budget = vstore.query_objects("Budget")[0]["properties"]
    remaining = budget["remaining"]
    _section("Requisitions", accent)
    st.caption(f"Budget remaining: **₹{remaining:,.0f}**. A purchase order within "
               "budget executes immediately; one that exceeds it is routed to the "
               "MLRO approval queue — the same gate as an AML account freeze. Every "
               "decision is audited.")
    for req in vstore.query_objects("Requisition"):
        p = req["properties"]
        vendor_ids = req["linked_ids"].get("from_vendor", [])
        vname = (vstore.get_object("Vendor", vendor_ids[0])["properties"]["name"]
                 if vendor_ids else "?")
        over = p["amount"] > remaining
        cols = st.columns([3, 2, 2, 2])
        cols[0].write(f"**{req['id']}** · {p['description']}")
        cols[1].write(f"`{vname}`")
        cols[2].write(f"₹{p['amount']:,.0f}")
        cols[2].caption("🔴 over budget" if over else "🟢 within budget")
        tip = ("Over budget → routes to MLRO approval." if over
               else "Within budget → executes immediately.")
        if cols[3].button("Submit PO", key=f"po_{req['id']}", help=tip):
            actor = st.session_state.get("_actor")
            r = approve_purchase_order(actor, requisition_id=req["id"],
                                       amount=p["amount"], budget_remaining=remaining)
            if r["status"] == "PENDING_APPROVAL":
                st.warning(f"{r['status']} — over budget, routed to MLRO "
                           "(same approval gate as account freeze).")
            else:
                st.success(r)


def render_platform() -> None:
    """The hero 'OS' screen: one engine, many sectors. Counters come from
    platform_counters() (derived from REGISTRY) so they can't drift from reality."""
    from praheri.verticals import REGISTRY, platform_counters

    c = platform_counters()
    accent = _PLATFORM_ACCENT

    # center engine box — the pipeline that is identical across every vertical
    st.markdown("### One sovereign engine. Every sector is a cartridge.")
    st.markdown(
        f"<div style='background:{_SURFACE};"
        f"background-image:linear-gradient(135deg,{accent}40,transparent 72%);"
        f"border:1px solid {accent}66;border-radius:14px;padding:22px 24px;"
        f"text-align:center'>"
        f"<div style='font-size:1.2rem;font-weight:700;color:{_FG}'>"
        f"🛡️ Triage → Traverse → Detect → Decide → Govern → Audit</div>"
        f"<div style='color:{_MUTED};font-size:0.85rem;margin-top:8px'>"
        f"This pipeline is unchanged across all verticals.</div>"
        f"</div>", unsafe_allow_html=True)

    # live counters — the proof. ontologies = all registered cartridges + AML hero.
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    counters = [("Ontologies", c["ontologies"], "incl. AML hero"),
                ("Object types", c["object_types"], None),
                ("Link types", c["link_types"], None),
                ("Governed actions", c["actions"], None)]
    cols = st.columns(4)
    for col, (label, value, sub) in zip(cols, counters):
        col.markdown(_kpi_card_html(label, str(value), sub, accent),
                     unsafe_allow_html=True)

    # the money line — built from the counters, not hardcoded.
    st.markdown(
        f"<div style='margin:18px 0 6px;font-size:1.05rem;color:{_FG}'>"
        f"1 engine · {c['ontologies']} ontologies · {c['object_types']} object "
        f"types · <b style='color:{accent}'>0 lines of engine code changed per "
        f"vertical</b></div>", unsafe_allow_html=True)

    # one clickable bento tile per registered cartridge (AML hero is bespoke, not here)
    _section("Sector cartridges", accent)
    cols = st.columns(len(REGISTRY))
    for col, cfg in zip(cols, REGISTRY.values()):
        with col:
            taccent = cfg.accent_color
            st.markdown(
                f"<div style='background:{_SURFACE};border:1px solid {_BORDER};"
                f"border-top:3px solid {taccent};border-radius:12px;"
                f"padding:14px 16px;min-height:96px'>"
                f"<div style='font-size:1.4rem'>{cfg.icon}</div>"
                f"<div style='color:{_FG};font-weight:600;font-size:0.9rem;"
                f"margin-top:4px'>{cfg.name}</div>"
                f"<div style='color:{_MUTED};font-size:0.74rem;margin-top:4px'>"
                f"{cfg.regulator}</div></div>", unsafe_allow_html=True)
            # no programmatic tab switch in Streamlit — set a jump target + guide.
            if st.button("Open →", key=f"platform_jump_{cfg.key}"):
                st.session_state["platform_jump"] = cfg.key
    jump = st.session_state.get("platform_jump")
    if jump:
        st.info(f"→ open the **{REGISTRY[jump].name}** tab above.")


st.set_page_config(page_title="Praheri — Sovereign AIP", layout="wide")

# Global polish (Stage 2). Scoped to headings + the demo-banner animation only —
# no div/color rules, so it can't bleed into the inline-styled cards (their inline
# styles out-specify tag selectors). Fonts themselves come from config.toml
# [[theme.fontFaces]] (bundled locally; no network). Tracking mirrors the explainer.
st.markdown(
    "<style>"
    "h1,h2,h3{letter-spacing:-0.02em;font-weight:700}"
    "h1{letter-spacing:-0.03em}"
    "@keyframes praheriBannerIn{from{opacity:0;transform:translateY(6px)}"
    "to{opacity:1;transform:translateY(0)}}"
    ".praheri-demo-banner{animation:praheriBannerIn .42s cubic-bezier(.19,1,.22,1)}"
    "</style>", unsafe_allow_html=True)

st.title("🛡️ Praheri — Sovereign Financial-Crime Copilot")
st.caption("Llama · on-prem · ontology + governed actions + audit. Synthetic data; decision-support only.")

_render_orientation()

# Link back to the standalone explainer ("why/what" narrative). Served by the
# tiny helper in app/serve_explainer.py (or opened directly); see HANDOFF.
st.sidebar.markdown(
    "<a href='http://localhost:8000/explainer.html' target='_blank' "
    "style='display:block;text-align:center;font-family:monospace;font-size:0.8rem;"
    "letter-spacing:0.04em;padding:8px 12px;border:1px solid #4C9AFF;color:#4C9AFF;"
    "border-radius:3px;text-decoration:none;margin-bottom:14px'>"
    "📖 What is Praheri? — open explainer</a>",
    unsafe_allow_html=True)

# Demo persona control — the two-person governance model made legible. The
# segmented control's *values* stay "analyst"/"mlro" (engine + the role=="mlro"
# check downstream depend on them); only the labels are prettied.
st.sidebar.markdown("**Acting as**")
role = st.sidebar.segmented_control(
    "Acting as", options=["analyst", "mlro"],
    format_func=lambda v: {"analyst": "🔍 Analyst", "mlro": "✅ MLRO"}[v],
    default="analyst", label_visibility="collapsed")
if role is None:
    role = "analyst"
st.sidebar.caption("Two-person rule: the **Analyst** *proposes* an action; the "
                   "**MLRO** *approves* it. Nothing the model proposes touches "
                   "data until the MLRO signs off.")
actor = Actor(id=f"demo_{role}", role=role)
st.session_state["_actor"] = actor  # so render_vertical's actions can reach it
oag_mode = st.sidebar.toggle("OAG mode (structured objects)", value=True,
                             help="Off = naive RAG over flattened text, for the side-by-side.")

# Guided Demo control (Stage 1). ON by default so a context-free judge can
# self-navigate; a presenter flips it off for the uncluttered view. Next/Back
# move the step; the banner (rendered above the tab bar) shows the instruction.
demo_on = st.sidebar.toggle("🎬 Guided demo", value=True,
                            help="A step-by-step walkthrough of the 3-min demo. "
                                 "Off = clean console.")
if demo_on:
    st.session_state.setdefault("demo_step", 0)
    _total = len(_DEMO_STEPS)
    _i = min(st.session_state["demo_step"], _total - 1)
    st.sidebar.caption(f"Step {_i + 1} of {_total} · {_DEMO_STEPS[_i]['title']}")
    _b, _n, _r = st.sidebar.columns(3)
    if _b.button("◀ Back", use_container_width=True, disabled=_i == 0):
        st.session_state["demo_step"] = max(0, _i - 1)
        st.rerun()
    if _n.button("Next ▶", use_container_width=True, disabled=_i >= _total - 1,
                 type="primary"):
        st.session_state["demo_step"] = min(_total - 1, _i + 1)
        st.rerun()
    if _r.button("↺", use_container_width=True, help="Restart the walkthrough"):
        st.session_state["demo_step"] = 0
        st.rerun()

st.sidebar.info("Sovereignty demo: this runs with no external network calls. "
                "Try airplane mode during the pitch.")
with st.sidebar.expander("🛡️ Verify sovereignty"):
    from praheri.sovereignty import scan_egress
    rep = scan_egress()
    if rep["ok"]:
        st.success("No external egress. Data never leaves the box.")
    else:
        st.error(f"External egress: {rep['external_endpoints']}")
    st.caption("Local only: " + ", ".join(rep["local_endpoints"]))

# Guided-demo banner — above the tab bar so it persists across every tab click.
# Renders nothing when the toggle is off, leaving the hero flow unchanged.
if demo_on:
    _i = min(st.session_state.get("demo_step", 0), len(_DEMO_STEPS) - 1)
    _render_demo_guide(_DEMO_STEPS[_i], _i, len(_DEMO_STEPS))

tabs = st.tabs(["🌐 Platform", "🚨 Alert Queue", "🔎 Investigation",
                "✅ Approvals (MLRO)", "📜 Audit Trail", "🧾 Procurement",
                "🛡 Insurance SIU", "🏦 Lending EWS",
                "📈 Wealth", "🏢 Corporate"])

with tabs[0]:
    render_platform()

with tabs[1]:
    st.subheader("Open alerts (sorted by score)")
    _what_you_see("The day's transaction-monitoring alerts, ranked by risk score. "
                  "🔴 high-risk ones sit at the top — pick one and click "
                  "<b>Investigate →</b> to send it to the Investigation tab. "
                  "(For the demo, start with the highest-scoring alert.)")
    alerts = store.query_objects("Alert")
    alerts.sort(key=lambda a: a["properties"]["score"], reverse=True)
    if not alerts:
        st.warning("No alerts. Run `python -m praheri.generate` to seed the demo bank.")
    for a in alerts:
        p = a["properties"]
        score = p["score"]
        cols = st.columns([1, 3, 3, 2, 2])
        cols[0].metric("Score", f"{score:.0f}")
        cols[1].write(f"**{p['alert_id']}**")
        cols[2].write(f"`{p['account_id']}`")
        cols[3].write(p["rule"])
        # High-score (ring) alerts get a flag so the demo entry points pop.
        cols[3].caption("🔴 high risk" if score >= 70 else "🟡 routine")
        if cols[4].button("Investigate →", key=f"sel_{p['alert_id']}"):
            st.session_state["selected_alert_id"] = p["alert_id"]
            st.session_state["selected_account_id"] = p["account_id"]
            st.success(f"Selected {p['alert_id']} — open the Investigation tab.")

with tabs[2]:
    st.subheader("Investigation")
    _what_you_see("Click <b>Run investigation</b> and watch Llama traverse the "
                  "ontology: the fraud-ring graph lights up, the engine names the "
                  "typology, and a draft Suspicious Transaction Report (STR) "
                  "appears — every claim cited to a real object ID. Then propose a "
                  "governed action below.")
    alert_id = st.session_state.get("selected_alert_id")
    if not alert_id:
        st.info("Pick an alert from the **Alert Queue** tab to investigate.")
    else:
        st.markdown(f"Investigating **{alert_id}** · account "
                    f"`{st.session_state.get('selected_account_id', '?')}`")
        if st.button("🔎 Run investigation", type="primary"):
            with st.spinner("Llama is traversing the ontology…"):
                try:
                    st.session_state["investigation"] = agent.investigate(alert_id)
                except agent.LlamaUnavailable as e:
                    st.error(f"Llama unavailable: {e}. Is Ollama running?")

        inv = st.session_state.get("investigation")
        if inv and inv["alert_id"] == alert_id:
            badge = {"FILE": "🔴", "ESCALATE": "🟠", "CLEAR": "🟢"}.get(
                inv["recommendation"], "⚪")
            src = "🟢 Live" if inv["source"] == "live" else "💾 Cached"
            conf_score, conf_band, conf_reasons = _confidence(inv)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Recommendation", f"{badge} {inv['recommendation']}")
            c2.metric("Typology", inv["typology"])
            c3.metric("Confidence", f"{conf_score}% · {conf_band}")
            c4.metric("Source", src)
            st.caption("Confidence basis: " + " · ".join(conf_reasons))

            st.markdown("##### Fraud-ring graph (OAG traversal)")
            highlight = {inv["account_id"]} | set(
                i for i in inv["objects_touched"] if i.startswith("ACC-"))
            ring_accounts = [i for i in inv["objects_touched"] if i.startswith("ACC-")]
            render_ring_graph(ring_accounts, highlight)

            if inv.get("signals"):
                st.markdown("##### 🚦 Detected typology signals (engine)")
                for s in inv["signals"]:
                    st.markdown(f"- **{s['typology']}** — {s['detail']}")

            st.markdown("##### Rationale (cited object_ids)")
            st.write(inv["rationale"])
            st.caption("Cited: " + ", ".join(f"`{i}`" for i in inv["cited_ids"]))
            if inv.get("str_narrative"):
                st.markdown("##### Draft STR narrative")
                st.write(inv["str_narrative"])

            _accent = _STATUS_COLOR.get(inv["recommendation"], _PLATFORM_ACCENT)

            # --- Why this recommendation: the auditable decision trail (Stage 3) ---
            with st.expander("🧠 Why this recommendation — the decision trail"):
                _section("1 · Signals fired (deterministic engine)", _accent)
                if inv.get("signals"):
                    for s in inv["signals"]:
                        chips = " ".join(f"`{i}`" for i in s.get("evidence_ids", []))
                        st.markdown(f"- **{s['typology']}** — {s['detail']}")
                        st.caption("Evidence: " + (chips or "—"))
                else:
                    st.markdown("- No typology signals fired.")
                _section("2 · Deterministic floor rule", _accent)
                st.markdown(
                    "A fired signal is a *confirmed* typology — the engine forbids "
                    "**CLEAR** and floors a real ring at **FILE**. The model may "
                    "soften FILE→ESCALATE in genuine ambiguity, but can **never** "
                    "downgrade a detected ring to CLEAR. Detection is code, not the "
                    "model — that's what makes it auditable.")
                if inv.get("signals") and inv["recommendation"] in ("FILE", "ESCALATE"):
                    st.success("Floor applied: signals present → CLEAR was disallowed.")
                _section("3 · Model judgment (Llama, layered on top)", _accent)
                st.write(inv["rationale"] or "—")
                st.caption("Cited: " + ", ".join(f"`{i}`" for i in inv["cited_ids"]))

            # --- Evidence timeline: the fraud unfolding over time (Stage 3) ---
            _section("🕐 Evidence timeline — the fraud unfolding", _accent)
            try:
                tl_accounts = inv.get("ring_summary", {}).get("accounts", []) or \
                    [i for i in inv["objects_touched"] if i.startswith("ACC-")]
                rows, n_total = _ring_timeline(store, tl_accounts)
                if rows:
                    table = [{
                        "Time": str(p.get("timestamp", ""))[:16].replace("T", " "),
                        "From": p.get("from_account", ""),
                        "To": p.get("to_account", ""),
                        "Amount": f"₹{p.get('amount', 0):,.0f}",
                        "Channel": p.get("channel", ""),
                        "Flag": "🔴 sub-₹50k" if p.get("amount", 0) < 50_000 else "",
                    } for p in rows]
                    st.dataframe(table, width="stretch", hide_index=True)
                    st.caption(f"Showing {len(rows)} of {n_total} transactions among "
                               "the ring accounts, chronological. 🔴 = sub-threshold "
                               "deposit (the structuring/smurfing layer).")
                else:
                    st.caption("No ring transactions found for the timeline.")
            except Exception as e:  # demo-safe: never crash the hero tab
                st.caption(f"Timeline unavailable: {e}")

            # --- Object drill-down: the ontology is a queryable graph (Stage 3) ---
            _section("🔬 Inspect a cited object", _accent)
            st.caption("The ontology is a live graph, not a chatbot — pick any "
                       "object to see its real properties and links.")
            _opts = ["— select —"] + sorted(
                set(inv.get("cited_ids", [])) | set(inv.get("objects_touched", [])))
            _oid = st.selectbox("Inspect object", _opts, key="drill_object_id",
                                label_visibility="collapsed")
            if _oid and _oid != "— select —":
                try:
                    from praheri.store import _type_of
                    obj = store.get_object(_type_of(_oid), _oid)
                    if obj is None:
                        st.warning(f"Object {_oid} not found in store.")
                    else:
                        st.markdown(f"**{obj['type']}** · `{obj['id']}`")
                        props = [{"property": k, "value": str(v)}
                                 for k, v in obj["properties"].items()]
                        st.table(props)
                        links = obj.get("linked_ids", {})
                        if any(links.values()):
                            st.markdown("**Linked objects**")
                            for lt, ids in links.items():
                                if ids:
                                    chips = " ".join(f"`{i}`" for i in ids)
                                    st.markdown(f"- *{lt}* → {chips}")
                except Exception as e:  # demo-safe
                    st.caption(f"Inspect unavailable: {e}")

            # --- OAG vs RAG side-by-side (U13): the differentiator ---
            with st.expander("⚖️ OAG vs RAG — why structured objects win"):
                if st.button("Run side-by-side comparison", key="oag_rag"):
                    cL, cR = st.columns(2)
                    with cL:
                        st.markdown("**🟢 OAG (structured objects + links)**")
                        st.success(f"{inv['typology']} → {inv['recommendation']}")
                        st.write(inv["rationale"])
                        st.caption("Traversed the ring via explicit links; "
                                   "cites real object_ids.")
                    with cR:
                        st.markdown("**🔴 RAG (flattened text, links stripped)**")
                        with st.spinner("RAG over text chunks…"):
                            try:
                                rag = agent.investigate_rag(alert_id)
                                st.warning(rag["answer"])
                                st.caption("Same facts as prose — but the links are "
                                           "gone, so it can't reconstruct the ring.")
                            except agent.LlamaUnavailable as e:
                                st.error(str(e))

            # --- governed action buttons (full wiring in U10/U11) ---
            st.markdown("##### Actions")
            st.caption("The model never writes data — it *proposes*; a human "
                       "decides. **Clear**/**Escalate** are low-stakes and log "
                       "immediately. **🔒 Propose Freeze**/**🔒 Propose STR** are "
                       "high-stakes and wait in the MLRO approval queue. Everything "
                       "is audited.")
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("Clear", help="Close the alert as not suspicious. Logged "
                         "immediately to the audit trail."):
                st.write(governance.clear_alert(actor, alert_id=alert_id,
                                                rationale=inv["rationale"][:200]))
            if b2.button("Escalate", help="Open a formal case for review. Logged "
                         "immediately to the audit trail."):
                st.write(governance.escalate_alert_to_case(
                    actor, alert_id=alert_id, reason=inv["typology"]))
            if b3.button("🔒 Propose Freeze", help="Request a freeze on the account. "
                         "Routes to the MLRO queue — nothing happens until a human "
                         "approves."):
                r = governance.request_account_freeze(
                    actor, account_id=inv["account_id"], reason=inv["typology"])
                st.warning(f"{r['status']} — see Approvals (MLRO) tab.")
            if b4.button("🔒 Propose STR", help="File the Suspicious Transaction "
                         "Report. Routes to the MLRO queue for human approval."):
                r = governance.file_str(actor, case_id=alert_id,
                                        narrative=inv.get("str_narrative") or inv["rationale"])
                st.warning(f"{r['status']} — see Approvals (MLRO) tab.")

    # --- Ask Praheri: genuine model-driven tool loop (U6) ---
    st.divider()
    st.markdown("##### 💬 Ask Praheri (live tool-calling)")
    q = st.text_input("Ask a free-form question about the data",
                      placeholder="Which accounts share a device with ACC-DEV-01?")
    if q:
        with st.spinner("Llama is calling tools…"):
            try:
                res = agent.ask(q)
                st.write(res["answer"])
                if res["trace"]:
                    st.caption("🔧 Tool calls: " + " · ".join(
                        f"{t['tool']}({t['result_count']})" for t in res["trace"]))
            except agent.LlamaUnavailable as e:
                st.error(f"Llama unavailable: {e}")

with tabs[3]:
    st.subheader("Pending approvals")
    _what_you_see("The human gate. High-stakes actions proposed by the model wait "
                  "here until the <b>MLRO</b> approves them — switch the sidebar "
                  "role to <i>mlro</i> to see the Approve button. Nothing the model "
                  "proposed has touched the data yet.")
    for item in governance.PENDING.list_pending():
        st.json(item)
        if role == "mlro" and st.button(f"Approve {item['ref']}", key=item["ref"]):
            st.success(governance.approve(item["ref"], actor))
    if not governance.PENDING.list_pending():
        st.write("No pending actions. (Propose a freeze/STR from Investigation.)")

with tabs[4]:
    st.subheader("Immutable audit trail")
    _what_you_see("Every object query, proposed action and approval — with the "
                  "actor, timestamp and model name. This append-only log is the "
                  "compliance artifact: it proves who did what, and that a human "
                  "(not the model) authorized each high-stakes action.")
    rows = governance.read_audit()
    st.dataframe(rows if rows else [{"info": "no audit entries yet"}], width="stretch")

with tabs[5]:
    # Procurement is now cartridge #1 — rendered through the SAME shared
    # render_vertical() as every other shallow vertical (the platform thesis,
    # made literal). The over-budget PO still hits the MLRO approval gate.
    from praheri.verticals import get_config as _get_config

    render_vertical(_get_config("procurement"))

with tabs[6]:
    # Insurance SIU — same cockpit, fraud-ring ontology. (U5)
    from praheri.verticals import get_config as _get_config

    render_vertical(_get_config("insurance_siu"))

with tabs[7]:
    # Lending EWS — same cockpit, contagion + EMI-stress signals. (U5)
    from praheri.verticals import get_config as _get_config

    render_vertical(_get_config("lending_ews"))

with tabs[8]:
    # Wealth — same cockpit, suitability mis-selling cluster. (U6)
    from praheri.verticals import get_config as _get_config

    render_vertical(_get_config("wealth"))

with tabs[9]:
    # Corporate — same cockpit, circular ownership + shared-UBO. (U6)
    from praheri.verticals import get_config as _get_config

    render_vertical(_get_config("corporate"))
