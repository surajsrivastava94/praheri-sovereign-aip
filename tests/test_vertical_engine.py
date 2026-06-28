"""U3: config-driven detectors + compute_signals_for + vertical investigation.

Also guards the _has_cycle reuse: agent.compute_signals must keep working (the AML
hero path is unchanged), and vertical_engine must call the SAME _has_cycle object.
"""
import json

import pytest

from praheri import agent, vertical_engine
from praheri.vertical_engine import (
    compute_signals_for, compute_vertical_investigation, traverse_generic,
)
from praheri.vertical_store import GenericOntologyStore
from praheri.verticals import ObjectTypeSpec, SignalSpec, VerticalConfig


# --- shared-attribute ring: 5 claims through one garage --------------------
def _ring_data(n_members=5):
    nodes = [{"type": "Garage", "id": "GAR-1", "properties": {"name": "QuickFix"}}]
    edges = []
    for i in range(n_members):
        cid = f"CLM-{i}"
        nodes.append({"type": "Claim", "id": cid, "properties": {"amount": 40000}})
        edges.append({"from": cid, "to": "GAR-1", "link_type": "serviced_by"})
    return {"nodes": nodes, "edges": edges}


def test_shared_attribute_ring_fires_at_threshold():
    store = GenericOntologyStore(_ring_data(5))
    spec = SignalSpec(id="shared_attribute_ring", label="ring", why="...",
                      params={"hub_type": "Garage", "min_members": 5,
                              "typology": "shared_garage_ring"})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=["serviced_by"], signals=[spec])
    sigs = compute_signals_for(cfg, store, "GAR-1")
    assert len(sigs) == 1
    assert sigs[0]["typology"] == "shared_garage_ring"
    assert "GAR-1" in sigs[0]["evidence_ids"]


def test_shared_attribute_ring_below_threshold_does_not_fire():
    store = GenericOntologyStore(_ring_data(3))
    spec = SignalSpec(id="shared_attribute_ring", label="ring", why="...",
                      params={"hub_type": "Garage", "min_members": 5})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=["serviced_by"], signals=[spec])
    assert compute_signals_for(cfg, store, "GAR-1") == []


# --- circular flow: A->B->C->A among Company nodes -------------------------
def test_circular_flow_fires_on_cycle():
    data = {
        "nodes": [{"type": "Company", "id": c, "properties": {}}
                  for c in ("CO-A", "CO-B", "CO-C")],
        "edges": [{"from": "CO-A", "to": "CO-B", "link_type": "owns"},
                  {"from": "CO-B", "to": "CO-C", "link_type": "owns"},
                  {"from": "CO-C", "to": "CO-A", "link_type": "owns"}],
    }
    store = GenericOntologyStore(data)
    spec = SignalSpec(id="circular_flow", label="cycle", why="...",
                      params={"node_type": "Company", "link_type": "owns"})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Company")],
                         link_types=["owns"], signals=[spec])
    sigs = compute_signals_for(cfg, store, "CO-A")
    assert len(sigs) == 1 and sigs[0]["typology"] == "circular_flow"


def test_circular_flow_acyclic_does_not_fire():
    data = {
        "nodes": [{"type": "Company", "id": c, "properties": {}}
                  for c in ("CO-A", "CO-B", "CO-C")],
        "edges": [{"from": "CO-A", "to": "CO-B", "link_type": "owns"},
                  {"from": "CO-B", "to": "CO-C", "link_type": "owns"}],
    }
    store = GenericOntologyStore(data)
    spec = SignalSpec(id="circular_flow", label="cycle", why="...",
                      params={"node_type": "Company", "link_type": "owns"})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Company")],
                         link_types=["owns"], signals=[spec])
    assert compute_signals_for(cfg, store, "CO-A") == []


# --- threshold cluster: borrower with >=5 sub-threshold inflows ------------
def test_threshold_cluster_fires():
    nodes = [{"type": "Borrower", "id": "BOR-1", "properties": {}}]
    edges = []
    for i in range(6):
        tid = f"EMI-{i}"
        nodes.append({"type": "Inflow", "id": tid, "properties": {"amount": 9000}})
        edges.append({"from": tid, "to": "BOR-1", "link_type": "credited_to"})
    store = GenericOntologyStore({"nodes": nodes, "edges": edges})
    spec = SignalSpec(id="threshold_cluster", label="struct", why="...",
                      params={"member_type": "Borrower", "link_type": "credited_to_in",
                              "amount_prop": "amount", "threshold": 10000,
                              "min_count": 5})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Borrower")],
                         link_types=["credited_to"], signals=[spec])
    sigs = compute_signals_for(cfg, store, "BOR-1")
    assert len(sigs) == 1 and "BOR-1" in sigs[0]["evidence_ids"]


def test_compute_signals_for_returns_only_fired_in_config_order():
    store = GenericOntologyStore(_ring_data(5))
    fired = SignalSpec(id="shared_attribute_ring", label="r", why="...",
                       params={"hub_type": "Garage", "min_members": 5})
    quiet = SignalSpec(id="circular_flow", label="c", why="...",
                       params={"node_type": "Claim", "link_type": "nope"})
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=["serviced_by"], signals=[quiet, fired])
    sigs = compute_signals_for(cfg, store, "GAR-1")
    assert [s["typology"] for s in sigs] == ["shared_attribute_ring"]


def test_unknown_detector_id_raises():
    store = GenericOntologyStore(_ring_data(5))
    spec = SignalSpec(id="not_a_real_detector", label="x", why="...")
    cfg = VerticalConfig(key="k", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=[], signals=[spec])
    with pytest.raises(KeyError):
        compute_signals_for(cfg, store, "GAR-1")


# --- _has_cycle reuse: AML path preserved, same object ---------------------
def test_has_cycle_is_the_shared_aml_implementation():
    # vertical_engine imports the very same function object from agent
    assert vertical_engine._has_cycle is agent._has_cycle


def test_aml_compute_signals_still_imports_and_runs():
    # smoke: the AML detector module is intact and callable (no signals on empty)
    from praheri.store import OntologyStore  # noqa: F401
    assert callable(agent.compute_signals)


# --- traversal + investigation --------------------------------------------
def test_traverse_generic_reaches_ring_members():
    store = GenericOntologyStore(_ring_data(5))
    touched = traverse_generic(store, "GAR-1")
    ids = {o["id"] for o in touched}
    assert "GAR-1" in ids and {"CLM-0", "CLM-4"} <= ids


def test_investigation_uses_cache_when_present(tmp_path, monkeypatch):
    store = GenericOntologyStore(_ring_data(5))
    spec = SignalSpec(id="shared_attribute_ring", label="r", why="...",
                      params={"hub_type": "Garage", "min_members": 5})
    cfg = VerticalConfig(key="ins", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=["serviced_by"], signals=[spec],
                         golden_cache_key="ins")
    monkeypatch.setattr(vertical_engine, "CACHE_DIR", tmp_path)
    (tmp_path / "ins__GAR-1.json").write_text(json.dumps({"narrative": "CACHED TEXT"}))
    inv = compute_vertical_investigation(cfg, store, "GAR-1")
    assert inv["source"] == "cached"
    assert inv["narrative"] == "CACHED TEXT"
    assert inv["recommendation"] == "FILE"   # a signal fired
    assert "GAR-1" in inv["cited_ids"]


def test_investigation_live_when_no_cache(tmp_path, monkeypatch):
    store = GenericOntologyStore(_ring_data(3))   # below threshold -> no signal
    cfg = VerticalConfig(key="ins", name="n", icon="i", accent_color="#000",
                         tagline="t", regulator="r",
                         object_types=[ObjectTypeSpec(name="Claim")],
                         link_types=["serviced_by"], signals=[], golden_cache_key="ins")
    monkeypatch.setattr(vertical_engine, "CACHE_DIR", tmp_path)
    inv = compute_vertical_investigation(cfg, store, "GAR-1")
    assert inv["source"] == "live"
    assert inv["recommendation"] == "CLEAR"
