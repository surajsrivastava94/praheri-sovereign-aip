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


def _section(label: str, accent: str) -> None:
    """Accent-themed section subheader (replaces plain `##### …`)."""
    st.markdown(
        f"<div style='font-size:0.95rem;font-weight:600;color:{_FG};"
        f"margin:20px 0 8px;padding-left:10px;border-left:3px solid {accent}'>"
        f"{label}</div>", unsafe_allow_html=True)


def _hero_band(config, accent: str) -> None:
    """Cohesive accent-themed sector header: icon+name, tagline, regulator chip."""
    st.markdown(
        f"<div style='background:{_SURFACE};"
        f"background-image:linear-gradient(135deg,{accent}3a,transparent 72%);"
        f"border:1px solid {accent}55;border-radius:14px;padding:18px 22px;"
        f"margin-bottom:10px'>"
        f"<div style='font-size:1.5rem;font-weight:700;color:{_FG}'>"
        f"{config.icon} {config.name}</div>"
        f"<div style='color:{_MUTED};font-size:0.95rem;margin:4px 0 12px'>"
        f"{config.tagline}</div>"
        f"<span style='background:{accent};color:#fff;padding:3px 12px;"
        f"border-radius:10px;font-size:0.78rem;font-weight:500'>"
        f"{config.regulator}</span>"
        f"</div>", unsafe_allow_html=True)


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
        acts = st.columns(len(config.actions))
        for col, act in zip(acts, config.actions):
            if col.button(act.label, key=f"vact_{config.key}_{act.id}"):
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
        if cols[3].button("Submit PO", key=f"po_{req['id']}"):
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
st.title("🛡️ Praheri — Sovereign Financial-Crime Copilot")
st.caption("Llama · on-prem · ontology + governed actions + audit. Synthetic data; decision-support only.")

# Demo persona toggle (analyst proposes, MLRO approves).
role = st.sidebar.radio("Acting as", ["analyst", "mlro"])
actor = Actor(id=f"demo_{role}", role=role)
st.session_state["_actor"] = actor  # so render_vertical's actions can reach it
oag_mode = st.sidebar.toggle("OAG mode (structured objects)", value=True,
                             help="Off = naive RAG over flattened text, for the side-by-side.")
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

tabs = st.tabs(["🌐 Platform", "🚨 Alert Queue", "🔎 Investigation",
                "✅ Approvals (MLRO)", "📜 Audit Trail", "🧾 Procurement",
                "🛡 Insurance SIU", "🏦 Lending EWS",
                "📈 Wealth", "🏢 Corporate"])

with tabs[0]:
    render_platform()

with tabs[1]:
    st.subheader("Open alerts (sorted by score)")
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
            c1, c2, c3 = st.columns(3)
            c1.metric("Recommendation", f"{badge} {inv['recommendation']}")
            c2.metric("Typology", inv["typology"])
            c3.metric("Source", src)

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
            b1, b2, b3, b4 = st.columns(4)
            if b1.button("Clear"):
                st.write(governance.clear_alert(actor, alert_id=alert_id,
                                                rationale=inv["rationale"][:200]))
            if b2.button("Escalate"):
                st.write(governance.escalate_alert_to_case(
                    actor, alert_id=alert_id, reason=inv["typology"]))
            if b3.button("Propose Freeze"):
                r = governance.request_account_freeze(
                    actor, account_id=inv["account_id"], reason=inv["typology"])
                st.warning(f"{r['status']} — see Approvals (MLRO) tab.")
            if b4.button("Propose STR"):
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
    for item in governance.PENDING.list_pending():
        st.json(item)
        if role == "mlro" and st.button(f"Approve {item['ref']}", key=item["ref"]):
            st.success(governance.approve(item["ref"], actor))
    if not governance.PENDING.list_pending():
        st.write("No pending actions. (Propose a freeze/STR from Investigation.)")

with tabs[4]:
    st.subheader("Immutable audit trail")
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
