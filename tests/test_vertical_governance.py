"""U7: vertical actions route through the SAME governance engine as AML —
shared approval queue + audit. AML actions must be untouched."""
import pytest

from praheri import governance
from praheri.governance import Actor


@pytest.fixture
def clean(monkeypatch, tmp_path):
    monkeypatch.setattr(governance, "AUDIT_PATH", tmp_path / "audit.jsonl")
    governance.PENDING.items.clear()


def test_high_stakes_vertical_action_hits_mlro_gate(clean):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.propose_vertical_action(
        analyst, vertical="insurance_siu", action_id="refer_to_siu",
        target_id="GAR-RING-01", reason="FILE")
    assert r["status"] == "PENDING_APPROVAL"
    assert any(i["ref"] == r["ref"] for i in governance.PENDING.list_pending())
    res = governance.approve(r["ref"], mlro)
    assert res["status"] == "EXECUTED"
    assert "refer_to_siu" in res["result"]


def test_routine_vertical_action_executes_immediately(clean):
    analyst = Actor(id="a1", role="analyst")
    r = governance.execute_vertical_action(
        analyst, vertical="lending_ews", action_id="add_watch_note",
        target_id="BOR-00", reason="ESCALATE")
    assert r["status"] == "EXECUTED"
    assert "executed" in r["result"]


def test_vertical_action_writes_audit_entries(clean):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.propose_vertical_action(
        analyst, vertical="corporate", action_id="escalate_kyc_review",
        target_id="CO-A", reason="FILE")
    governance.approve(r["ref"], mlro)
    rows = governance.read_audit()
    events = [row["event"] for row in rows]
    assert "ACTION_PROPOSED" in events
    assert "ACTION_APPROVED_AND_EXECUTED" in events
    # audit carries actor + model name (sovereignty/audit requirement)
    assert any(row.get("actor") for row in rows)


def test_vertical_actions_share_the_aml_executor_registry(clean):
    # the platform thesis at the governance layer: one registry, many verticals
    assert "propose_vertical_action" in governance._EXECUTORS
    assert "execute_vertical_action" in governance._EXECUTORS
    # AML actions still present and untouched
    assert "request_account_freeze" in governance._EXECUTORS
    assert "approve_purchase_order" in governance._EXECUTORS


def test_app_boots_with_wired_vertical_actions():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file("app/streamlit_app.py", default_timeout=30).run()
    assert not at.exception
