"""U12 tests — procurement vertical reuses the SAME governance engine."""
import pytest

from praheri import governance, models_procurement as proc
from praheri.governance import Actor


@pytest.fixture
def clean(monkeypatch, tmp_path):
    monkeypatch.setattr(governance, "AUDIT_PATH", tmp_path / "audit.jsonl")
    governance.PENDING.items.clear()


def test_models_are_valid(clean):
    assert set(proc.PROC_OBJECT_TYPES) == {"Vendor", "Budget", "Requisition", "Contract"}
    assert len(proc.DEMO_REQUISITIONS) == 2


def test_over_budget_po_hits_approval_gate(clean):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    remaining = proc.DEMO_BUDGET.cap - proc.DEMO_BUDGET.spent
    over = proc.DEMO_REQUISITIONS[1]
    assert over.amount > remaining  # precondition
    r = governance.approve_purchase_order(
        analyst, requisition_id=over.requisition_id, amount=over.amount,
        budget_remaining=remaining)
    assert r["status"] == "PENDING_APPROVAL"
    res = governance.approve(r["ref"], mlro)
    assert res["status"] == "EXECUTED"


def test_reuses_same_executor_registry(clean):
    """The platform thesis, asserted: procurement action lives in the SAME registry
    as the AML actions — one engine, many verticals."""
    assert "approve_purchase_order" in governance._EXECUTORS
    assert "request_account_freeze" in governance._EXECUTORS  # AML, same registry


def test_audit_is_shared(clean):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.approve_purchase_order(
        analyst, requisition_id="REQ-02", amount=900_000, budget_remaining=380_000)
    governance.approve(r["ref"], mlro)
    events = [x["event"] for x in governance.read_audit()]
    assert "ACTION_PROPOSED" in events and "ACTION_APPROVED_AND_EXECUTED" in events
