"""U1 tests — synthetic data + 3 planted rings are structurally sound & deterministic."""
import sqlite3

import pytest

from praheri import generate


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    db = tmp_path_factory.mktemp("data") / "test.db"
    c = sqlite3.connect(db)
    generate.build_base(c)
    rings = {
        "structuring": generate.plant_structuring(c),
        "circular": generate.plant_circular(c),
        "shared_device": generate.plant_shared_device(c),
    }
    entry = ([a for a in rings["structuring"] if a.startswith("ACC-BENEF")]
             + rings["structuring"][:2] + rings["circular"][:1]
             + rings["shared_device"][:2])
    generate.create_alerts_for_rings(c, entry)
    c.commit()
    return c, rings


def test_volumes_within_tolerance(conn):
    c, _ = conn
    n_acct = c.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    n_txn = c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    assert n_acct >= generate.N_ACCOUNTS          # base + ring accounts
    assert n_txn >= generate.N_TXNS               # base + ring txns


def test_structuring_ring(conn):
    c, rings = conn
    mules = [a for a in rings["structuring"] if a.startswith("ACC-MULE")]
    assert 6 <= len(mules) <= 8
    beneficiary = "ACC-BENEF-STRUCT"
    for m in mules:
        # sub-threshold inbound deposits
        deposits = c.execute(
            "SELECT amount FROM transactions WHERE to_account=? AND amount < ?",
            (m, generate.STRUCTURING_THRESHOLD)).fetchall()
        assert len(deposits) >= 10, f"{m} has too few sub-threshold deposits"
        # funnels to the ONE beneficiary
        funnel = c.execute(
            "SELECT COUNT(*) FROM transactions WHERE from_account=? AND to_account=?",
            (m, beneficiary)).fetchone()[0]
        assert funnel >= 1, f"{m} does not funnel to beneficiary"


def test_circular_ring_forms_cycle(conn):
    c, rings = conn
    a, b, cc = rings["circular"]
    edges = {(r[0], r[1]) for r in c.execute(
        "SELECT from_account, to_account FROM transactions "
        "WHERE from_account LIKE 'ACC-CIRC-%'").fetchall()}
    assert (a, b) in edges and (b, cc) in edges and (cc, a) in edges  # closed loop


def test_shared_device_ring(conn):
    c, rings = conn
    accts = rings["shared_device"]
    assert len(accts) >= 10
    dev = c.execute(
        "SELECT device_id FROM account_devices WHERE account_id=?",
        (accts[0],)).fetchone()[0]
    shared = c.execute(
        "SELECT COUNT(DISTINCT account_id) FROM account_devices WHERE device_id=?",
        (dev,)).fetchone()[0]
    assert shared >= 10, "device not shared by enough accounts"


def test_ring_alerts_top_the_queue(conn):
    c, rings = conn
    top = c.execute(
        "SELECT account_id, score FROM alerts ORDER BY score DESC LIMIT 6").fetchall()
    # All top-6 alerts should be on planted ring accounts (ring scores 82-96 > noise 20-58)
    ring_accts = set(sum(rings.values(), []))
    for account_id, score in top:
        assert account_id in ring_accts, f"{account_id} unexpectedly high score {score}"
        assert score > 60


def test_determinism():
    """Two fresh builds with the same seed yield identical ring account_ids."""
    def build():
        generate.fake.seed_instance(generate.SEED)
        generate.random.seed(generate.SEED)
        generate._txn_counter["n"] = 0
        c = sqlite3.connect(":memory:")
        generate.build_base(c)
        return generate.plant_structuring(c)
    assert build() == build()
