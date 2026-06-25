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

st.set_page_config(page_title="Praheri — Sovereign AIP", layout="wide")
st.title("🛡️ Praheri — Sovereign Financial-Crime Copilot")
st.caption("Llama · on-prem · ontology + governed actions + audit. Synthetic data; decision-support only.")

# Demo persona toggle (analyst proposes, MLRO approves).
role = st.sidebar.radio("Acting as", ["analyst", "mlro"])
actor = Actor(id=f"demo_{role}", role=role)
oag_mode = st.sidebar.toggle("OAG mode (structured objects)", value=True,
                             help="Off = naive RAG over flattened text, for the side-by-side.")
st.sidebar.info("Sovereignty demo: this runs with no external network calls. "
                "Try airplane mode during the pitch.")

tabs = st.tabs(["🚨 Alert Queue", "🔎 Investigation", "✅ Approvals (MLRO)",
                "📜 Audit Trail", "🧾 Procurement (vertical #2)"])

with tabs[0]:
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

with tabs[1]:
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

with tabs[2]:
    st.subheader("Pending approvals")
    for item in governance.PENDING.list_pending():
        st.json(item)
        if role == "mlro" and st.button(f"Approve {item['ref']}", key=item["ref"]):
            st.success(governance.approve(item["ref"], actor))
    if not governance.PENDING.list_pending():
        st.write("No pending actions. (Propose a freeze/STR from Investigation.)")

with tabs[3]:
    st.subheader("Immutable audit trail")
    rows = governance.read_audit()
    st.dataframe(rows if rows else [{"info": "no audit entries yet"}], width="stretch")

with tabs[4]:
    st.subheader("Procurement — same engine, different ontology")
    st.write("TODO 6.1: prove the platform thesis. Requisition/Vendor/Contract/Budget ontology, "
             "one action approve_purchase_order behind a budget-threshold gate, reusing "
             "agent + governance + store unchanged.")
