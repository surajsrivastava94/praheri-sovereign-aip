"""U10 tests — actions mutate the store, gated actions require approval."""
import sqlite3

import pytest

from praheri import generate, governance, store as store_mod
from praheri.governance import Actor
from praheri.store import OntologyStore


@pytest.fixture
def wired(tmp_path, monkeypatch):
    db = tmp_path / "gov.db"
    generate.fake.seed_instance(generate.SEED)
    generate.random.seed(generate.SEED)
    generate._txn_counter["n"] = 0
    c = sqlite3.connect(db)
    generate.build_base(c)
    generate.plant_structuring(c)
    generate.plant_shared_device(c)
    generate.create_alerts_for_rings(c, ["ACC-BENEF-STRUCT", "ACC-DEV-01"])
    c.commit()
    c.close()
    s = OntologyStore(str(db))
    monkeypatch.setattr(store_mod, "_DEFAULT", s)  # actions mutate this store
    # clean audit + pending for deterministic assertions
    monkeypatch.setattr(governance, "AUDIT_PATH", tmp_path / "audit.jsonl")
    governance.PENDING.items.clear()
    return s


def test_clear_alert_closes_alert(wired):
    analyst = Actor(id="a1", role="analyst")
    governance.clear_alert(analyst, alert_id="ALERT-R001", rationale="benign")
    a = wired.get_object("Alert", "ALERT-R001")
    assert a["properties"]["status"] == "closed"


def test_freeze_requires_approval_then_executes(wired):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.request_account_freeze(analyst, account_id="ACC-DEV-01", reason="ring")
    assert r["status"] == "PENDING_APPROVAL"
    # not frozen yet
    assert wired.get_object("Account", "ACC-DEV-01")["properties"]["status"] == "active"
    # approve -> executes -> frozen
    governance.approve(r["ref"], mlro)
    assert wired.get_object("Account", "ACC-DEV-01")["properties"]["status"] == "frozen"


def test_file_str_persists_case_after_approval(wired):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.file_str(analyst, case_id="CASE-001", narrative="smurfing via mules")
    assert r["status"] == "PENDING_APPROVAL"
    governance.approve(r["ref"], mlro)
    case = wired.get_object("Case", "CASE-001")
    assert case is not None
    assert case["properties"]["status"] == "filed"
    assert "smurfing" in case["properties"]["narrative"]


def test_audit_records_propose_and_execute(wired):
    analyst = Actor(id="a1", role="analyst")
    mlro = Actor(id="m1", role="mlro")
    r = governance.request_account_freeze(analyst, account_id="ACC-DEV-02", reason="ring")
    governance.approve(r["ref"], mlro)
    events = [x["event"] for x in governance.read_audit()]
    assert "ACTION_PROPOSED" in events
    assert "ACTION_APPROVED_AND_EXECUTED" in events
