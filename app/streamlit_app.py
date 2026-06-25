"""Praheri analyst console (UI skeleton). See BUILD_BIBLE.md §9 for the demo flow.

Tabs map directly to the demo beats:
  Alert Queue -> Investigation (graph + STR) -> Approvals (MLRO) -> Audit Trail -> Procurement

Run: streamlit run app/streamlit_app.py
TODO(playbook steps 3.1, 5.2, 6.1, 6.2): wire each tab to the modules.
"""
from __future__ import annotations

import streamlit as st

from praheri import governance
from praheri.governance import Actor
from praheri.store import OntologyStore


@st.cache_resource
def get_store() -> OntologyStore:
    return OntologyStore()


store = get_store()

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
    st.write("TODO 3.1/4.2: run agent.investigate(alert_id); render pyvis ring graph + "
             "STR narrative with object_id citations + recommendation. "
             "Buttons: Clear / Escalate / Propose Freeze / Propose STR (route via governance).")

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
    st.dataframe(rows if rows else [{"info": "no audit entries yet"}], use_container_width=True)

with tabs[4]:
    st.subheader("Procurement — same engine, different ontology")
    st.write("TODO 6.1: prove the platform thesis. Requisition/Vendor/Contract/Budget ontology, "
             "one action approve_purchase_order behind a budget-threshold gate, reusing "
             "agent + governance + store unchanged.")
