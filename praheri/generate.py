"""Synthetic data generator with PLANTED fraud rings. See BUILD_BIBLE.md §7.

Because we plant the rings, the demo is deterministic — but the investigation
(traversal + reasoning + narrative) is genuinely done by Llama. SYNTHETIC ONLY.

TODO(playbook step 1.2): implement the bodies. Run with `python -m praheri.generate`.
"""
from __future__ import annotations

import sqlite3

from faker import Faker

fake = Faker("en_IN")
DB_PATH = "praheri.db"

# Target volumes
N_CUSTOMERS = 500
N_ACCOUNTS = 1500
N_TXNS = 20_000
STRUCTURING_THRESHOLD = 50_000  # INR; smurfing stays just under this


def build_base(conn: sqlite3.Connection) -> None:
    """Create tables and generate baseline customers/accounts/transactions/
    counterparties/devices with realistic-looking Indian data. TODO."""
    raise NotImplementedError


def plant_structuring(conn: sqlite3.Connection) -> list[str]:
    """Typology A — smurfing: many sub-threshold deposits into 6-8 mule accounts
    funnelling to ONE beneficiary. Return the mule account_ids. (Hero demo.) TODO."""
    raise NotImplementedError


def plant_circular(conn: sqlite3.Connection) -> list[str]:
    """Typology B — circular layering: A->B->C->A loops. Return account_ids. TODO."""
    raise NotImplementedError


def plant_shared_device(conn: sqlite3.Connection) -> list[str]:
    """Typology C — shared-device ring: 10+ 'unrelated' accounts on one device_id/IP.
    Return account_ids. TODO."""
    raise NotImplementedError


def create_alerts_for_rings(conn: sqlite3.Connection, ring_accounts: list[str]) -> None:
    """Raise high-score Alerts on ring entry points so triage has something to grab. TODO."""
    raise NotImplementedError


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    build_base(conn)
    rings = {
        "structuring": plant_structuring(conn),
        "circular": plant_circular(conn),
        "shared_device": plant_shared_device(conn),
    }
    all_ring_accounts = [a for ids in rings.values() for a in ids]
    create_alerts_for_rings(conn, all_ring_accounts)
    conn.commit()
    print("Planted rings (demo entry points):")
    for name, ids in rings.items():
        print(f"  {name}: {ids}")


if __name__ == "__main__":
    main()
