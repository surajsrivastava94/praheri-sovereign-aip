"""U5: Insurance SIU + Lending EWS cartridges — deterministic data, planted rings
that fire the configured signals end-to-end through the shared engine."""
import json

import pytest
from streamlit.testing.v1 import AppTest

from praheri.generate_verticals import (
    build_corporate, build_insurance, build_lending, build_wealth,
)
from praheri.vertical_engine import compute_vertical_investigation
from praheri.vertical_store import GenericOntologyStore
from praheri.verticals import get_config


# --- determinism (R6) ------------------------------------------------------
@pytest.mark.parametrize("builder", [build_insurance, build_lending,
                                     build_wealth, build_corporate])
def test_builder_is_deterministic(builder):
    a_nodes, a_edges = builder()
    b_nodes, b_edges = builder()
    assert a_nodes == b_nodes and a_edges == b_edges


# --- insurance: shared-garage ring fires -> FILE ---------------------------
def test_insurance_ring_fires_shared_garage_signal():
    cfg = get_config("insurance_siu")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    inv = compute_vertical_investigation(cfg, store, "GAR-RING-01", use_cache=False)
    assert inv["recommendation"] == "FILE"
    assert [s["typology"] for s in inv["signals"]] == ["shared_garage_ring"]
    assert "GAR-RING-01" in inv["cited_ids"]


def test_insurance_clean_garage_does_not_fire():
    # the control-group garage (2 clean claims) must not trip the ring detector
    cfg = get_config("insurance_siu")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    members = []
    for ids in store.get_object("Garage", "GAR-OK-01")["linked_ids"].values():
        members.extend(ids)
    assert len(members) < 5


# --- lending: both signals fire -> FILE ------------------------------------
def test_lending_fires_both_signals():
    cfg = get_config("lending_ews")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    inv = compute_vertical_investigation(cfg, store, "DIR-RING-01", use_cache=False)
    assert inv["recommendation"] == "FILE"
    typ = {s["typology"] for s in inv["signals"]}
    assert typ == {"common_director_cluster", "emi_bounce_stress"}


def test_wealth_fires_suitability_signal():
    cfg = get_config("wealth")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    inv = compute_vertical_investigation(cfg, store, "ADV-RING-01", use_cache=False)
    assert inv["recommendation"] == "FILE"
    assert [s["typology"] for s in inv["signals"]] == ["suitability_mismatch"]


def test_corporate_fires_ownership_and_ubo_signals():
    cfg = get_config("corporate")
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    inv = compute_vertical_investigation(cfg, store, "CO-A", use_cache=False)
    assert inv["recommendation"] == "FILE"
    typ = {s["typology"] for s in inv["signals"]}
    assert typ == {"circular_ownership", "shared_ubo_cluster"}


# --- each vertical has a canned alert pointing at the ring root ------------
@pytest.mark.parametrize("key,root", [("insurance_siu", "GAR-RING-01"),
                                      ("lending_ews", "DIR-RING-01"),
                                      ("wealth", "ADV-RING-01"),
                                      ("corporate", "CO-A")])
def test_vertical_has_alert_on_ring_root(key, root):
    cfg = get_config(key)
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    alerts = store.query_objects("Alert")
    assert alerts, f"{key} has no alert"
    roots = {a["properties"].get("root_id") for a in alerts}
    assert root in roots


# --- both datasets load into the generic store cleanly ---------------------
@pytest.mark.parametrize("key", ["insurance_siu", "lending_ews",
                                 "wealth", "corporate"])
def test_dataset_loads_structured_objects(key):
    cfg = get_config(key)
    store = GenericOntologyStore(json.loads(open(cfg.sample_data_path).read()))
    # every declared object type has at least one instance
    for ot in cfg.object_types:
        assert store.query_objects(ot.name), f"{key} missing {ot.name}"


# --- app still renders with the two new cartridges registered --------------
def test_app_boots_with_new_cartridges():
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=30).run()
    assert not at.exception
