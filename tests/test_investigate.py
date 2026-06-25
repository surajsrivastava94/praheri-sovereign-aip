"""U5 tests — investigate() hero pipeline on the 3 planted rings.

This IS the demo, so it carries the most coverage. Live (needs Ollama) for the
reasoning assertions; cache + citation enforcement tested without the model.
"""
import json

import pytest
import requests

from praheri import agent
from praheri.store import OntologyStore


def _ollama_up() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2).raise_for_status()
        return True
    except Exception:
        return False


live = pytest.mark.skipif(not _ollama_up(), reason="Ollama not running")


@pytest.fixture
def store():
    return OntologyStore()


def test_traverse_ring_reaches_shared_device_accounts(store):
    """Pure-Python traversal (no LLM): from a device-ring account, reach the ring."""
    touched = agent.traverse_ring(store, "ACC-DEV-01")
    ids = {o["id"] for o in touched}
    assert "DEV-RING-001" in ids
    # 2-hop: device -> the other ring accounts
    dev_accts = [i for i in ids if i.startswith("ACC-DEV-")]
    assert len(dev_accts) >= 10


def test_traverse_structuring_reaches_beneficiary(store):
    # From the beneficiary, traversal pulls in the funnel txns + mules.
    touched = agent.traverse_ring(store, "ACC-BENEF-STRUCT")
    ids = {o["id"] for o in touched}
    assert any(i.startswith("ACC-MULE-") for i in ids)


def test_citation_enforcement_drops_hallucinated_ids(monkeypatch, store):
    """If the model cites an id not in the ring, it's filtered out."""
    fake_resp = {"message": {"content": json.dumps({
        "typology": "shared_device_ring", "recommendation": "FILE",
        "rationale": "ring among ACC-DEV-01 and FAKE-999",
        "cited_ids": ["ACC-DEV-01", "FAKE-999"]})}, "trace": []}
    monkeypatch.setattr(agent, "call_llama", lambda *a, **k: fake_resp)
    out = agent.investigate("ALERT-R005", store=store, use_cache=False)
    assert "ACC-DEV-01" in out["cited_ids"]
    assert "FAKE-999" not in out["cited_ids"]  # hallucinated id removed


def test_invalid_recommendation_defaults_to_escalate(monkeypatch, store):
    fake_resp = {"message": {"content": json.dumps({
        "typology": "none", "recommendation": "DELETE_EVERYTHING",
        "rationale": "x", "cited_ids": []})}, "trace": []}
    monkeypatch.setattr(agent, "call_llama", lambda *a, **k: fake_resp)
    out = agent.investigate("ALERT-R005", store=store, use_cache=False)
    assert out["recommendation"] == "ESCALATE"


def test_cache_roundtrip(monkeypatch, store, tmp_path):
    monkeypatch.setattr(agent, "CACHE_DIR", tmp_path)
    fake_resp = {"message": {"content": json.dumps({
        "typology": "shared_device_ring", "recommendation": "FILE",
        "rationale": "ring", "cited_ids": ["ACC-DEV-01"]})}, "trace": []}
    monkeypatch.setattr(agent, "call_llama", lambda *a, **k: fake_resp)
    first = agent.investigate("ALERT-R005", store=store, use_cache=True)
    assert first["source"] == "live"
    # second call must come from cache and be identical (minus source flag)
    second = agent.investigate("ALERT-R005", store=store, use_cache=True)
    assert second["source"] == "cached"
    assert second["objects_touched"] == first["objects_touched"]


# ---------------- live reasoning assertions (the actual demo behaviour) ----------------
@live
@pytest.mark.parametrize("alert_id,expect_account_prefix", [
    ("ALERT-R001", "ACC-MULE"),   # structuring beneficiary -> mules in ring
    ("ALERT-R004", "ACC-CIRC"),   # circular
    ("ALERT-R005", "ACC-DEV"),    # shared device
])
def test_investigate_each_ring(store, alert_id, expect_account_prefix):
    out = agent.investigate(alert_id, store=store, use_cache=False)
    ids = out["objects_touched"]
    assert any(i.startswith(expect_account_prefix) for i in ids), \
        f"{alert_id}: ring accounts not surfaced"
    assert out["recommendation"] in ("ESCALATE", "FILE"), \
        f"{alert_id}: a real ring should not be CLEARed"
