"""U2 tests — OntologyStore returns structured objects and traverses the ring."""
import sqlite3

import pytest

from praheri import generate
from praheri.store import OntologyStore


@pytest.fixture(scope="module")
def store(tmp_path_factory):
    db = tmp_path_factory.mktemp("data") / "store.db"
    # build a full DB on disk so OntologyStore opens it normally
    generate.fake.seed_instance(generate.SEED)
    generate.random.seed(generate.SEED)
    generate._txn_counter["n"] = 0
    c = sqlite3.connect(db)
    generate.build_base(c)
    rings = {
        "structuring": generate.plant_structuring(c),
        "circular": generate.plant_circular(c),
        "shared_device": generate.plant_shared_device(c),
    }
    generate.create_alerts_for_rings(c, ["ACC-BENEF-STRUCT", "ACC-DEV-01"])
    c.commit()
    c.close()
    return OntologyStore(str(db)), rings


def test_reads_return_structured_dicts(store):
    s, _ = store
    alerts = s.query_objects("Alert")
    assert alerts, "no alerts"
    for a in alerts:
        assert set(a) == {"type", "id", "properties", "linked_ids"}
        assert isinstance(a["properties"], dict)
        assert not isinstance(a, str)


def test_query_with_filter(store):
    s, _ = store
    open_alerts = s.query_objects("Alert", status="open")
    assert all(a["properties"]["status"] == "open" for a in open_alerts)


def test_get_object_missing_returns_none(store):
    s, _ = store
    assert s.get_object("Account", "ACC-DOES-NOT-EXIST") is None


def test_linked_objects_mule_has_txns_and_funnel(store):
    s, _ = store
    linked = s.get_linked_objects("ACC-MULE-01")
    types = {o["type"] for o in linked}
    assert "Transaction" in types
    # the mule funnels to the beneficiary -> a txn whose to_account is beneficiary
    to_benef = [o for o in linked if o["type"] == "Transaction"
                and o["properties"]["to_account"] == "ACC-BENEF-STRUCT"]
    assert to_benef, "mule->beneficiary funnel txn not reachable"


def test_loose_link_type_is_normalised_not_raised(store):
    """The 8B model passed link_type='transactions' (not a real edge). Must not raise."""
    s, _ = store
    linked = s.get_linked_objects("ACC-MULE-01", "transactions")  # invalid enum
    assert any(o["type"] == "Transaction" for o in linked)


def test_link_type_none_returns_all(store):
    s, _ = store
    all_links = s.get_linked_objects("ACC-MULE-01", None)
    assert len(all_links) >= len(s.get_linked_objects("ACC-MULE-01", "sends"))


def test_shared_device_traversal(store):
    s, _ = store
    # from a device-ring account -> its device -> back to >=10 accounts
    devs = s.get_linked_objects("ACC-DEV-01", "used_on")
    assert devs and devs[0]["type"] == "Device"
    accts = s.get_linked_objects(devs[0]["id"])
    assert len([a for a in accts if a["type"] == "Account"]) >= 10


def test_build_graph_scoped_to_ring(store):
    s, rings = store
    g = s.build_graph(rings["shared_device"])
    # all ring accounts present + the shared device node
    for a in rings["shared_device"]:
        assert a in g
    device_nodes = [n for n, d in g.nodes(data=True) if d.get("kind") == "device"]
    assert device_nodes, "shared device not in graph"
