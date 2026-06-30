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
from server.verticals_api import root_id_for

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


# --- P3: governance loop (offline — pure governance + SQLite, no Ollama) ---
# These mutate process-global state (PENDING, audit log, praheri.db). Assert on
# status strings + append-only audit so the suite stays re-runnable.

def test_low_stakes_action_executes_immediately():
    r = client.post("/api/actions/clear_alert",
                    json={"role": "analyst",
                          "params": {"alert_id": "ALERT-R001", "rationale": "test"}})
    assert r.status_code == 200
    assert r.json()["status"] == "EXECUTED"


def test_unknown_action_404():
    r = client.post("/api/actions/nonesuch", json={"role": "analyst", "params": {}})
    assert r.status_code == 404


def test_high_stakes_propose_then_approve_flow():
    # propose (analyst) -> PENDING_APPROVAL
    r = client.post("/api/actions/request_account_freeze",
                    json={"role": "analyst",
                          "params": {"account_id": "ACC-MULE-07", "reason": "test"}})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "PENDING_APPROVAL"
    ref = body["ref"]

    # it shows up in the queue
    pending = client.get("/api/approvals").json()
    assert any(p["ref"] == ref and p["action"] == "request_account_freeze"
               for p in pending)

    # MLRO approves -> EXECUTED, leaves the queue
    a = client.post(f"/api/approvals/{ref}/approve", json={"role": "mlro"})
    assert a.status_code == 200
    assert a.json()["status"] == "EXECUTED"
    assert not any(p["ref"] == ref for p in client.get("/api/approvals").json())


def test_approve_unknown_ref_404():
    r = client.post("/api/approvals/BADREF/approve", json={"role": "mlro"})
    assert r.status_code == 404


def test_audit_log_records_actions():
    # an action was run above; the audit trail is non-empty with the right shape
    rows = client.get("/api/audit").json()
    assert isinstance(rows, list) and rows
    for key in ("actor", "role", "action", "event", "model"):
        assert key in rows[-1]


# --- P4: verticals + platform (offline — golden caches committed) ---

def test_root_id_for_resolves_link_or_prop():
    assert root_id_for({"linked_ids": {"raised_on": ["X"]}, "properties": {}}) == "X"
    assert root_id_for({"linked_ids": {}, "properties": {"root_id": "Y"}}) == "Y"


def test_verticals_list_and_counters():
    body = client.get("/api/verticals").json()
    assert body["counters"]["ontologies"] == 6
    assert len(body["verticals"]) == 5
    first = body["verticals"][0]
    for key in ("key", "name", "signals"):
        assert key in first


def test_vertical_alerts():
    r = client.get("/api/verticals/insurance_siu/alerts")
    assert r.status_code == 200
    assert r.json()  # non-empty


def test_vertical_investigate_file_cached():
    r = client.get("/api/verticals/insurance_siu/investigate",
                   params={"root_id": "GAR-RING-01"})
    assert r.status_code == 200
    inv = r.json()
    assert inv["recommendation"] == "FILE"
    assert inv["source"] == "cached"
    assert inv["signals"]


def test_vertical_graph_has_highlights():
    r = client.get("/api/verticals/insurance_siu/graph",
                   params={"root_id": "GAR-RING-01"})
    assert r.status_code == 200
    g = r.json()
    assert g["nodes"]
    assert any(n["highlight"] for n in g["nodes"])


def test_vertical_unknown_key_404():
    r = client.get("/api/verticals/nope/alerts")
    assert r.status_code == 404


def test_sector_action_routes_to_shared_queue():
    r = client.post("/api/actions/propose_vertical_action",
                    json={"role": "analyst",
                          "params": {"vertical": "insurance_siu",
                                     "action_id": "refer_to_siu",
                                     "target_id": "GAR-RING-01", "reason": "ring"}})
    assert r.status_code == 200
    assert r.json()["status"] == "PENDING_APPROVAL"
