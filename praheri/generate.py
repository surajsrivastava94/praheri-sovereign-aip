"""Synthetic data generator with PLANTED fraud rings. See BUILD_BIBLE.md §7.

Because we plant the rings, the demo is deterministic — but the investigation
(traversal + reasoning + narrative) is genuinely done by Llama. SYNTHETIC ONLY.

Run with `python -m praheri.generate`. Seeded for reproducibility so the demo
entry points (planted ring account_ids) are stable across runs.
"""
from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime, timedelta

from faker import Faker

fake = Faker("en_IN")
SEED = 42
fake.seed_instance(SEED)
random.seed(SEED)

DB_PATH = "praheri.db"

# Target volumes
N_CUSTOMERS = 500
N_ACCOUNTS = 1500
N_TXNS = 20_000
N_COUNTERPARTIES = 300
N_DEVICES = 400
STRUCTURING_THRESHOLD = 50_000  # INR; smurfing stays just under this

BASE_DATE = datetime(2026, 1, 1)
CHANNELS = ["UPI", "IMPS", "NEFT", "RTGS", "CASH"]


# --------------------------------------------------------------- schema
def _create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS accounts;
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS counterparties;
        DROP TABLE IF EXISTS devices;
        DROP TABLE IF EXISTS account_devices;
        DROP TABLE IF EXISTS alerts;
        DROP TABLE IF EXISTS cases;

        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY, name TEXT, kyc_risk_rating TEXT,
            pep_flag INTEGER, nationality TEXT, occupation TEXT, onboarding_date TEXT
        );
        CREATE TABLE accounts (
            account_id TEXT PRIMARY KEY, customer_id TEXT, type TEXT, branch TEXT,
            balance REAL, status TEXT, open_date TEXT
        );
        CREATE TABLE transactions (
            txn_id TEXT PRIMARY KEY, from_account TEXT, to_account TEXT,
            counterparty_id TEXT, amount REAL, currency TEXT, channel TEXT, timestamp TEXT
        );
        CREATE TABLE counterparties (
            counterparty_id TEXT PRIMARY KEY, name TEXT, type TEXT, bank TEXT,
            country TEXT, risk_flags TEXT
        );
        CREATE TABLE devices (
            device_id TEXT PRIMARY KEY, ip TEXT, geo TEXT, first_seen TEXT
        );
        CREATE TABLE account_devices (account_id TEXT, device_id TEXT);
        CREATE TABLE alerts (
            alert_id TEXT PRIMARY KEY, account_id TEXT, rule TEXT, score REAL,
            status TEXT, created_at TEXT
        );
        CREATE TABLE cases (
            case_id TEXT PRIMARY KEY, alert_ids TEXT, assigned_to TEXT,
            status TEXT, decision TEXT, narrative TEXT, created_at TEXT
        );
        CREATE INDEX idx_txn_from ON transactions(from_account);
        CREATE INDEX idx_txn_to ON transactions(to_account);
        CREATE INDEX idx_acctdev_acct ON account_devices(account_id);
        CREATE INDEX idx_acctdev_dev ON account_devices(device_id);
        CREATE INDEX idx_alert_acct ON alerts(account_id);
        """
    )


def _ts(days_offset: float) -> str:
    return (BASE_DATE + timedelta(days=days_offset)).isoformat()


# --------------------------------------------------------------- base data
def build_base(conn: sqlite3.Connection) -> None:
    """Create tables and generate baseline customers/accounts/transactions/
    counterparties/devices with realistic-looking Indian data."""
    _create_tables(conn)

    # Customers
    customers = []
    occupations = ["salaried", "self-employed", "business owner", "student",
                   "retired", "trader", "consultant", "homemaker"]
    for i in range(1, N_CUSTOMERS + 1):
        cid = f"CUST-{i:05d}"
        customers.append((
            cid, fake.name(),
            random.choices(["low", "medium", "high"], weights=[70, 25, 5])[0],
            1 if random.random() < 0.03 else 0, "IN",
            random.choice(occupations), _ts(-random.randint(200, 3000)),
        ))
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)", customers)

    # Accounts (each tied to a customer)
    accounts = []
    for i in range(1, N_ACCOUNTS + 1):
        aid = f"ACC-{i:05d}"
        cust = f"CUST-{random.randint(1, N_CUSTOMERS):05d}"
        accounts.append((
            aid, cust, random.choice(["savings", "current", "wallet"]),
            f"MUM-{random.randint(1, 50):03d}", round(random.uniform(1_000, 5_000_000), 2),
            "active", _ts(-random.randint(50, 2500)),
        ))
    conn.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", accounts)
    base_account_ids = [a[0] for a in accounts]

    # Counterparties
    counterparties = []
    for i in range(1, N_COUNTERPARTIES + 1):
        flags = []
        if random.random() < 0.08:
            flags.append("high_risk_jurisdiction")
        if random.random() < 0.05:
            flags.append("sanctions_watch")
        counterparties.append((
            f"CP-{i:04d}", fake.company(),
            random.choice(["internal", "external"]),
            fake.company() + " Bank",
            random.choices(["IN", "AE", "SG", "HK", "KY"], weights=[80, 6, 6, 4, 4])[0],
            json.dumps(flags),
        ))
    conn.executemany("INSERT INTO counterparties VALUES (?,?,?,?,?,?)", counterparties)
    cp_ids = [c[0] for c in counterparties]

    # Devices + random account links
    devices = []
    acct_dev = []
    for i in range(1, N_DEVICES + 1):
        did = f"DEV-{i:05d}"
        devices.append((did, fake.ipv4(), "IN", _ts(-random.randint(10, 2000))))
    conn.executemany("INSERT INTO devices VALUES (?,?,?,?)", devices)
    dev_ids = [d[0] for d in devices]
    # Most accounts use 1 device; ordinary (non-ring) sharing is minimal
    for aid in base_account_ids:
        acct_dev.append((aid, random.choice(dev_ids)))
    conn.executemany("INSERT INTO account_devices VALUES (?,?)", acct_dev)

    # Baseline transactions (noise)
    txns = []
    for i in range(1, N_TXNS + 1):
        frm = random.choice(base_account_ids)
        to = random.choice(base_account_ids)
        use_cp = random.random() < 0.15
        txns.append((
            f"TXN-{i:06d}", frm, to,
            random.choice(cp_ids) if use_cp else None,
            round(random.uniform(100, 200_000), 2), "INR",
            random.choice(CHANNELS), _ts(random.uniform(0, 120)),
        ))
    conn.executemany("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)", txns)

    # Baseline NOISE alerts (low score) so the queue looks realistic
    noise_alerts = []
    noise_rules = ["velocity_spike", "dormant_reactivation", "round_amount",
                   "new_payee_high_value", "cross_border_small"]
    for i in range(1, 21):
        noise_alerts.append((
            f"ALERT-N{i:03d}", random.choice(base_account_ids),
            random.choice(noise_rules), round(random.uniform(20, 58), 1),
            "open", _ts(random.uniform(100, 120)),
        ))
    conn.executemany("INSERT INTO alerts VALUES (?,?,?,?,?,?)", noise_alerts)


# --------------------------------------------------------------- helpers
_txn_counter = {"n": 0}


def _add_txn(conn, frm, to, amount, channel, day, cp=None):
    _txn_counter["n"] += 1
    tid = f"TXN-R{_txn_counter['n']:05d}"  # R = ring txn, easy to spot
    conn.execute(
        "INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?)",
        (tid, frm, to, cp, round(amount, 2), "INR", channel, _ts(day)),
    )


def _add_account(conn, account_id, customer_name, kyc="high", balance=50_000.0):
    cid = f"CUST-{account_id}"
    conn.execute(
        "INSERT INTO customers VALUES (?,?,?,?,?,?,?)",
        (cid, customer_name, kyc, 0, "IN", "self-employed", _ts(-random.randint(30, 400))),
    )
    conn.execute(
        "INSERT INTO accounts VALUES (?,?,?,?,?,?,?)",
        (account_id, cid, "savings", "MUM-007", balance, "active", _ts(-random.randint(20, 200))),
    )


# --------------------------------------------------------------- planted rings
def plant_structuring(conn: sqlite3.Connection) -> list[str]:
    """Typology A — smurfing: many sub-threshold deposits into 7 mule accounts
    funnelling to ONE beneficiary. Return the mule account_ids. (Hero demo.)"""
    beneficiary = "ACC-BENEF-STRUCT"
    _add_account(conn, beneficiary, "Apex Holdings (beneficiary)", kyc="high", balance=10_000.0)

    mules = [f"ACC-MULE-{i:02d}" for i in range(1, 8)]  # 7 mules
    for m in mules:
        _add_account(conn, m, fake.name(), kyc="medium", balance=5_000.0)
        # Each mule receives 10-14 sub-threshold deposits over ~6 days
        n_dep = random.randint(10, 14)
        for _ in range(n_dep):
            amt = random.uniform(0.80, 0.98) * STRUCTURING_THRESHOLD  # just under 50k
            _add_txn(conn, frm=f"ACC-{random.randint(1, N_ACCOUNTS):05d}", to=m,
                     amount=amt, channel=random.choice(["CASH", "UPI"]),
                     day=random.uniform(100, 106))
        # Then mule funnels a lump to the beneficiary
        _add_txn(conn, frm=m, to=beneficiary, amount=random.uniform(300_000, 450_000),
                 channel="IMPS", day=random.uniform(106, 108))
    return mules + [beneficiary]


def plant_circular(conn: sqlite3.Connection) -> list[str]:
    """Typology B — circular layering: A->B->C->A loop. Return account_ids."""
    nodes = [f"ACC-CIRC-{i:02d}" for i in range(1, 4)]  # A, B, C
    for n in nodes:
        _add_account(conn, n, fake.company(), kyc="high", balance=20_000.0)
    amt = 750_000.0
    # A->B->C->A, similar amounts, days apart (little economic substance)
    _add_txn(conn, nodes[0], nodes[1], amt * random.uniform(0.98, 1.0), "RTGS", 110.0)
    _add_txn(conn, nodes[1], nodes[2], amt * random.uniform(0.96, 0.99), "RTGS", 111.0)
    _add_txn(conn, nodes[2], nodes[0], amt * random.uniform(0.95, 0.98), "RTGS", 112.0)
    return nodes


def plant_shared_device(conn: sqlite3.Connection) -> list[str]:
    """Typology C — shared-device ring: 12 'unrelated' accounts on one device_id/IP.
    Return account_ids."""
    device_id = "DEV-RING-001"
    conn.execute("INSERT INTO devices VALUES (?,?,?,?)",
                 (device_id, "203.0.113.77", "IN", _ts(95.0)))
    accts = [f"ACC-DEV-{i:02d}" for i in range(1, 13)]  # 12 accounts
    for a in accts:
        _add_account(conn, a, fake.name(), kyc="medium", balance=8_000.0)
        conn.execute("INSERT INTO account_devices VALUES (?,?)", (a, device_id))
    # They shuffle funds among themselves from the same device in a short window
    for _ in range(20):
        frm, to = random.sample(accts, 2)
        _add_txn(conn, frm, to, random.uniform(20_000, 120_000),
                 random.choice(["UPI", "IMPS"]), random.uniform(113, 115))
    return accts


def create_alerts_for_rings(conn: sqlite3.Connection, ring_accounts: list[str]) -> None:
    """Raise high-score Alerts on ring entry points so triage has something to grab.
    Rule is inferred from the account_id prefix; score is high (top of queue)."""
    rule_for = {
        "ACC-MULE": "structuring_below_threshold",
        "ACC-BENEF": "structuring_funnel_beneficiary",
        "ACC-CIRC": "circular_layering",
        "ACC-DEV": "shared_device_ring",
    }
    n = 0
    for acct in ring_accounts:
        prefix = "-".join(acct.split("-")[:2])
        rule = rule_for.get(prefix, "suspicious_pattern")
        n += 1
        conn.execute(
            "INSERT INTO alerts VALUES (?,?,?,?,?,?)",
            (f"ALERT-R{n:03d}", acct, rule, round(random.uniform(82, 96), 1),
             "open", _ts(random.uniform(116, 119))),
        )


# --------------------------------------------------------------- entrypoint
def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    build_base(conn)
    rings = {
        "structuring": plant_structuring(conn),
        "circular": plant_circular(conn),
        "shared_device": plant_shared_device(conn),
    }
    # Entry points for the queue: beneficiary (hero), one circular node, two device accts.
    entry_points = (
        [a for a in rings["structuring"] if a.startswith("ACC-BENEF")]
        + rings["structuring"][:2]            # a couple of mules too
        + rings["circular"][:1]
        + rings["shared_device"][:2]
    )
    create_alerts_for_rings(conn, entry_points)
    conn.commit()

    print("Planted rings (demo entry points):")
    for name, ids in rings.items():
        print(f"  {name}: {ids}")
    print("\nHigh-score alerts raised on:", entry_points)
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["customers", "accounts", "transactions", "counterparties",
                        "devices", "alerts"]}
    print("Row counts:", counts)
    conn.close()


if __name__ == "__main__":
    main()
