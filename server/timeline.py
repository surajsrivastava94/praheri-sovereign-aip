"""Chronological evidence timeline for a fraud ring.

Lives in server/ — the engine stays frozen. A faithful port of the Streamlit
`_ring_timeline`. Scoped to the ring via per-account indexed queries — never a
full-table scan of the 20k+ transactions. Each row carries a `sub_threshold` flag
(amount < INR 50,000 — the structuring tell). Read-only.
"""
from __future__ import annotations

from typing import Any

_THRESHOLD = 50_000


def ring_timeline(store, ring_accounts: list[str], cap: int = 40) -> dict[str, Any]:
    """Return {rows, total}: ring transactions in chronological order, capped."""
    seen: dict[str, dict] = {}
    for acct in ring_accounts:
        for direction in ("from_account", "to_account"):
            for t in store.query_objects("Transaction", **{direction: acct}):
                seen[t["id"]] = t["properties"]
    rows = sorted(seen.values(), key=lambda p: str(p.get("timestamp", "")))
    flagged = [
        {**r, "sub_threshold": float(r.get("amount", 0) or 0) < _THRESHOLD}
        for r in rows[:cap]
    ]
    return {"rows": flagged, "total": len(rows)}
