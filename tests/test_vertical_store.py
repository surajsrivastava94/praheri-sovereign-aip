"""U2: GenericOntologyStore. Asserts it matches OntologyStore's structured-object
contract so downstream traversal / signals / render_ring_graph stay store-agnostic."""
import pytest

from praheri.vertical_store import GenericOntologyStore

# 5 nodes / 4 edges: a tiny insurance-shaped ring.
#   GAR-1 (garage) serviced 3 claims; CLM-1 filed_by CLT-1.
DATA = {
    "nodes": [
        {"type": "Garage", "id": "GAR-1", "properties": {"name": "QuickFix"}},
        {"type": "Claim", "id": "CLM-1", "properties": {"amount": 80000}},
        {"type": "Claim", "id": "CLM-2", "properties": {"amount": 60000}},
        {"type": "Claim", "id": "CLM-3", "properties": {"amount": 90000}},
        {"type": "Claimant", "id": "CLT-1", "properties": {"name": "A. Roy"}},
    ],
    "edges": [
        {"from": "CLM-1", "to": "GAR-1", "link_type": "serviced_by"},
        {"from": "CLM-2", "to": "GAR-1", "link_type": "serviced_by"},
        {"from": "CLM-3", "to": "GAR-1", "link_type": "serviced_by"},
        {"from": "CLM-1", "to": "CLT-1", "link_type": "filed_by"},
    ],
}


@pytest.fixture
def store():
    return GenericOntologyStore(DATA)


def test_get_object_returns_structured_contract(store):
    obj = store.get_object("Claim", "CLM-1")
    assert obj is not None
    # exact contract shape, matching OntologyStore._structured
    assert set(obj.keys()) == {"type", "id", "properties", "linked_ids"}
    assert obj["type"] == "Claim"
    assert obj["id"] == "CLM-1"
    assert obj["properties"]["amount"] == 80000
    assert isinstance(obj["linked_ids"], dict)


def test_get_object_wrong_type_or_missing_returns_none(store):
    assert store.get_object("Garage", "CLM-1") is None   # wrong type
    assert store.get_object("Claim", "NOPE") is None      # missing


def test_query_objects_filters_by_type(store):
    claims = store.query_objects("Claim")
    assert {o["id"] for o in claims} == {"CLM-1", "CLM-2", "CLM-3"}


def test_query_objects_filters_by_property(store):
    hits = store.query_objects("Claim", amount=60000)
    assert [o["id"] for o in hits] == ["CLM-2"]


def test_linked_ids_groups_by_link_type_with_reverse_name(store):
    # outgoing edges from the claim
    claim = store.get_object("Claim", "CLM-1")
    assert claim["linked_ids"]["serviced_by"] == ["GAR-1"]
    assert claim["linked_ids"]["filed_by"] == ["CLT-1"]
    # incoming edges on the garage use the "_in" reverse name
    garage = store.get_object("Garage", "GAR-1")
    assert set(garage["linked_ids"]["serviced_by_in"]) == {"CLM-1", "CLM-2", "CLM-3"}


def test_get_linked_objects_all_then_filtered(store):
    all_links = store.get_linked_objects("CLM-1")
    assert {o["id"] for o in all_links} == {"GAR-1", "CLT-1"}
    only = store.get_linked_objects("CLM-1", "filed_by")
    assert [o["id"] for o in only] == ["CLT-1"]


def test_get_linked_objects_unknown_link_type_returns_all(store):
    # mirrors OntologyStore: never raise on a bad link_type
    res = store.get_linked_objects("CLM-1", "bogus_link")
    assert res == []  # filtered to a link_type that doesn't exist -> nothing
    # but None / empty means everything
    assert {o["id"] for o in store.get_linked_objects("CLM-1", None)} == {"GAR-1", "CLT-1"}


def test_get_linked_objects_missing_node_returns_empty(store):
    assert store.get_linked_objects("NOPE") == []


def test_build_graph_carries_kind_and_label_for_renderer(store):
    g = store.build_graph(["GAR-1"])
    # one hop out from the garage pulls in its 3 claims
    assert "GAR-1" in g
    assert {"CLM-1", "CLM-2", "CLM-3"} <= set(g.nodes)
    # node data shape the existing render_ring_graph consumes
    assert g.nodes["GAR-1"]["kind"] == "Garage"
    assert g.nodes["GAR-1"]["label"] == "QuickFix"   # falls back to name
    assert g.nodes["CLM-1"]["label"] == "CLM-1"       # no name -> id
    # edges carry a label
    assert g.has_edge("CLM-1", "GAR-1")
    assert g.edges["CLM-1", "GAR-1"]["label"] == "serviced_by"


def test_build_graph_whole_graph_when_no_scope(store):
    g = store.build_graph()
    assert set(g.nodes) == {"GAR-1", "CLM-1", "CLM-2", "CLM-3", "CLT-1"}
