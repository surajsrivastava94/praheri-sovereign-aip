"""U4: render_vertical() + Procurement migrated to cartridge #1.

Render guards (AppTest) + the procurement config/data wiring. The AML hero tab
must still render unchanged (regression guard alongside test_app_renders.py)."""
import json

import pytest
from streamlit.testing.v1 import AppTest

from praheri.verticals import REGISTRY, get_config, platform_counters
from praheri.vertical_store import GenericOntologyStore

APP = "app/streamlit_app.py"


def test_app_boots_with_procurement_cartridge():
    # The whole app (incl. the migrated Procurement tab) renders without exception.
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception


def test_procurement_config_registered_and_wellformed():
    cfg = get_config("procurement")
    assert cfg.key == "procurement"
    assert cfg.actions and cfg.actions[0].id == "approve_purchase_order"
    assert cfg.actions[0].requires_approval is True
    # procurement is action-centric, not fraud-ring: no signals by design
    assert cfg.signals == []


def test_procurement_dataset_loads_into_generic_store():
    cfg = get_config("procurement")
    data = json.loads(open(cfg.sample_data_path).read())
    store = GenericOntologyStore(data)
    reqs = {o["id"] for o in store.query_objects("Requisition")}
    assert {"REQ-01", "REQ-02"} <= reqs
    # the over-budget requisition links to its vendor + budget
    req = store.get_object("Requisition", "REQ-02")
    assert req["linked_ids"]["from_vendor"] == ["VEN-02"]
    assert req["linked_ids"]["against_budget"] == ["BUD-IT"]


def test_budget_remaining_drives_over_budget_flag():
    cfg = get_config("procurement")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    remaining = store.query_objects("Budget")[0]["properties"]["remaining"]
    amounts = {o["id"]: o["properties"]["amount"]
               for o in store.query_objects("Requisition")}
    # REQ-01 under, REQ-02 over — the demo's whole point (the approval-gate beat)
    assert amounts["REQ-01"] <= remaining
    assert amounts["REQ-02"] > remaining


def test_generate_verticals_is_deterministic():
    from praheri.generate_verticals import build_procurement
    a_nodes, a_edges = build_procurement()
    b_nodes, b_edges = build_procurement()
    assert a_nodes == b_nodes and a_edges == b_edges


# --- U8: Platform dashboard ------------------------------------------------- #

def test_platform_counters_match_registry():
    # Recompute independently from REGISTRY so the assertion can't pass on magic
    # numbers — the dashboard's whole credibility is "counts can't drift".
    c = platform_counters()
    assert c["ontologies"] == len(REGISTRY) + 1  # +1 = AML (bespoke hero)
    assert c["object_types"] == sum(len(v.object_types) for v in REGISTRY.values())
    assert c["link_types"] == sum(len(v.link_types) for v in REGISTRY.values())
    assert c["actions"] == sum(len(v.actions) for v in REGISTRY.values())


def test_platform_tab_is_first_and_renders():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert at.tabs[0].label.endswith("Platform") or "Platform" in at.tabs[0].label


def test_platform_money_line_present():
    at = AppTest.from_file(APP, default_timeout=30).run()
    blob = " ".join(m.value for m in at.markdown)
    assert "0 lines of engine code changed per vertical" in blob


def test_cartridge_tile_click_sets_jump_target():
    at = AppTest.from_file(APP, default_timeout=30).run()
    # one tile per registered cartridge; clicking sets a predictable jump key
    btn = next(b for b in at.button if b.key == "platform_jump_procurement")
    btn.click().run()
    assert at.session_state["platform_jump"] == "procurement"
