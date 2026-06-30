"""U1 tests — the FastAPI layer's read-only endpoints.

These exercise server/main.py against the real seeded praheri.db and the
committed golden cache (demo_cache/ALERT-R001.json), so they run fully offline:
the investigate path is a cache hit and never calls Ollama.
"""
import pytest
import requests
from fastapi.testclient import TestClient

from server.main import app
from server.str_prompt import build_str_messages

client = TestClient(app)


def _ollama_up() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2).raise_for_status()
        return True
    except Exception:
        return False


live = pytest.mark.skipif(not _ollama_up(), reason="Ollama not running")


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_alerts_sorted_by_score_desc():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    alerts = r.json()
    assert len(alerts) > 0
    scores = [a["properties"]["score"] for a in alerts]
    assert scores == sorted(scores, reverse=True)


def test_investigate_returns_full_cached_dict():
    r = client.get("/api/alerts/ALERT-R001/investigate")
    assert r.status_code == 200
    inv = r.json()
    for key in ("recommendation", "signals", "typology", "cited_ids", "source"):
        assert key in inv, f"missing key: {key}"


def test_investigate_alert_r001_is_deterministic_file_structuring():
    inv = client.get("/api/alerts/ALERT-R001/investigate").json()
    assert inv["recommendation"] == "FILE"
    assert inv["typology"] == "structuring"


def test_investigate_signal_shape():
    inv = client.get("/api/alerts/ALERT-R001/investigate").json()
    assert len(inv["signals"]) >= 1
    sig = inv["signals"][0]
    assert {"typology", "detail", "evidence_ids"} <= set(sig)
    assert isinstance(sig["evidence_ids"], list) and sig["evidence_ids"]


def test_investigate_unknown_alert_404():
    r = client.get("/api/alerts/NOPE/investigate")
    assert r.status_code == 404


# --- P2-U1: object drill-down ---

def test_inspect_account_object():
    r = client.get("/api/objects/ACC-MULE-01")
    assert r.status_code == 200
    obj = r.json()
    assert obj["type"] == "Account"
    assert obj["properties"]
    assert isinstance(obj["linked_ids"], dict)


def test_inspect_transaction_object():
    r = client.get("/api/objects/TXN-R00011")
    assert r.status_code == 200
    assert r.json()["type"] == "Transaction"


def test_inspect_unknown_object_404():
    r = client.get("/api/objects/NOPE-999")
    assert r.status_code == 404


# --- P2-U2: OAG-vs-RAG ---

def test_rag_unknown_alert_404():
    # Guard fires before any model call — deterministic, offline-safe.
    r = client.get("/api/alerts/NOPE/rag")
    assert r.status_code == 404


@live
def test_rag_returns_answer_for_real_alert():
    r = client.get("/api/alerts/ALERT-R001/rag")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "RAG"
    assert body["answer"]


# --- P2-U3: STR prompt builder (offline) ---

def test_build_str_messages_grounded_in_structured_objects():
    inv = client.get("/api/alerts/ALERT-R001/investigate").json()
    msgs = build_str_messages(inv)
    assert len(msgs) == 2
    assert {m["role"] for m in msgs} == {"system", "user"}
    user = msgs[1]["content"]
    assert "structuring" in user  # typology grounded
    assert any(cid in user for cid in inv["cited_ids"])  # cites real ids


def test_str_stream_unknown_alert_404():
    r = client.get("/api/alerts/NOPE/str/stream")
    assert r.status_code == 404
