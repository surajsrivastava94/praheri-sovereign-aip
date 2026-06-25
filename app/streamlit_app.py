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
    st.write("TODO 3.1: list alerts from store.query_objects('Alert'); click to select.")

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
