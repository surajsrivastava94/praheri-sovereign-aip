"""U1 tests — the FastAPI layer's read-only endpoints.

These exercise server/main.py against the real seeded praheri.db and the
committed golden cache (demo_cache/ALERT-R001.json), so they run fully offline:
the investigate path is a cache hit and never calls Ollama.
"""
from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


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
