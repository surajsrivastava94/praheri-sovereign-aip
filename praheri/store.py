"""Ontology store: SQLite persistence + networkx graph. See BUILD_BIBLE.md §3, §6.

The FIRST design decision that makes this OAG: every read returns a structured
object dict {type, id, properties, linked_ids} — NEVER a text blob. The agent
walks fraud rings via get_linked_objects, the core OAG primitive.

Writes happen ONLY via governance.actions (see governance.py), never here directly,
EXCEPT the guarded mutators at the bottom which those actions call.
"""
from __future__ import annotations

import sqlite3
from typing import Any

import networkx as nx

DB_PATH = "praheri.db"

# Each object type -> (table, primary-key column).
_TABLE = {
    "Customer": ("customers", "customer_id"),
    "Account": ("accounts", "account_id"),
    "Transaction": ("transactions", "txn_id"),
    "Counterparty": ("counterparties", "counterparty_id"),
    "Device": ("devices", "device_id"),
    "Alert": ("alerts", "alert_id"),
    "Case": ("cases", "case_id"),
}

# Map an account_id prefix back to its object type for id-based lookups.
def _type_of(object_id: str) -> str | None:
    if object_id.startswith(("CUST-",)):
        return "Customer"
    if object_id.startswith("ACC-"):
        return "Account"
    if object_id.startswith(("TXN-",)):
        return "Transaction"
    if object_id.startswith("CP-"):
        return "Counterparty"
    if object_id.startswith("DEV-"):
        return "Device"
    if object_id.startswith("ALERT-"):
        return "Alert"
    if object_id.startswith("CASE-"):
        return "Case"
    return None


# Synonyms the LLM tends to emit, normalised to real edge semantics. The 8B model
# fabricates link_type values (e.g. "transactions" for what is sends/receives),
# so get_linked_objects must tolerate loose input rather than assume an exact enum.
_LINK_SYNONYMS = {
    "transactions": "all_txns", "txn": "all_txns", "txns": "all_txns",
    "sent": "sends", "outgoing": "sends", "out": "sends",
    "received": "receives", "incoming": "receives", "in": "receives",
    "device": "used_on", "devices": "used_on",
    "customer": "held_by", "owner": "held_by", "account": "held_by",
    "counterparty": "to_cp", "counterparties": "to_cp",
}


class OntologyStore:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    # ------------------------------------------------ structured-object builder
    def _structured(self, type: str, row: sqlite3.Row) -> dict:
        props = dict(row)
        oid = props.get(_TABLE[type][1])
        return {"type": type, "id": oid, "properties": props,
                "linked_ids": self._linked_ids(type, oid)}

    def _linked_ids(self, type: str, oid: str) -> dict[str, list[str]]:
        """Lightweight neighbour-id map (no recursion) for the structured dict."""
        c = self.conn
        out: dict[str, list[str]] = {}
        if type == "Account":
            out["sends"] = [r[0] for r in c.execute(
                "SELECT txn_id FROM transactions WHERE from_account=?", (oid,))]
            out["receives"] = [r[0] for r in c.execute(
                "SELECT txn_id FROM transactions WHERE to_account=?", (oid,))]
            out["used_on"] = [r[0] for r in c.execute(
                "SELECT device_id FROM account_devices WHERE account_id=?", (oid,))]
            held = c.execute("SELECT customer_id FROM accounts WHERE account_id=?",
                             (oid,)).fetchone()
            out["held_by"] = [held[0]] if held else []
        elif type == "Transaction":
            r = c.execute("SELECT from_account, to_account, counterparty_id "
                          "FROM transactions WHERE txn_id=?", (oid,)).fetchone()
            if r:
                out["from"] = [r[0]] if r[0] else []
                out["to"] = [r[1]] if r[1] else []
                out["to_cp"] = [r[2]] if r[2] else []
        elif type == "Device":
            out["used_by"] = [r[0] for r in c.execute(
                "SELECT account_id FROM account_devices WHERE device_id=?", (oid,))]
        elif type == "Customer":
            out["owns"] = [r[0] for r in c.execute(
                "SELECT account_id FROM accounts WHERE customer_id=?", (oid,))]
        elif type == "Alert":
            r = c.execute("SELECT account_id FROM alerts WHERE alert_id=?",
                          (oid,)).fetchone()
            out["raised_on"] = [r[0]] if r else []
        return out

    # ------------------------------------------------ reads (structured, not text)
    def query_objects(self, type: str, **filters: Any) -> list[dict]:
        """Return objects of `type` matching equality filters, as
        {type, id, properties, linked_ids} dicts."""
        if type not in _TABLE:
            raise ValueError(f"unknown object type: {type}")
        table = _TABLE[type][0]
        sql = f"SELECT * FROM {table}"
        params: list[Any] = []
        if filters:
            clauses = [f"{k}=?" for k in filters]
            sql += " WHERE " + " AND ".join(clauses)
            params = list(filters.values())
        return [self._structured(type, r) for r in self.conn.execute(sql, params)]

    def get_object(self, type: str, object_id: str) -> dict | None:
        """Single object as a structured dict, or None if not found."""
        if type not in _TABLE:
            raise ValueError(f"unknown object type: {type}")
        table, pk = _TABLE[type]
        row = self.conn.execute(
            f"SELECT * FROM {table} WHERE {pk}=?", (object_id,)).fetchone()
        return self._structured(type, row) if row else None

    def get_linked_objects(self, object_id: str,
                           link_type: str | None = None) -> list[dict]:
        """Traverse links from object_id (see models.LINKS). The core OAG primitive.
        `link_type` is normalised — invalid/None means 'all links'. Never raises on
        a bad link_type (the LLM emits loose values)."""
        otype = _type_of(object_id)
        if not otype:
            return []
        norm = _LINK_SYNONYMS.get((link_type or "").lower().strip(),
                                  (link_type or "").lower().strip())
        results: list[dict] = []

        def add(type, oid):
            obj = self.get_object(type, oid)
            if obj:
                results.append(obj)

        if otype == "Account":
            sends = [r[0] for r in self.conn.execute(
                "SELECT txn_id FROM transactions WHERE from_account=?", (object_id,))]
            recvs = [r[0] for r in self.conn.execute(
                "SELECT txn_id FROM transactions WHERE to_account=?", (object_id,))]
            devs = [r[0] for r in self.conn.execute(
                "SELECT device_id FROM account_devices WHERE account_id=?", (object_id,))]
            cust = self.conn.execute(
                "SELECT customer_id FROM accounts WHERE account_id=?",
                (object_id,)).fetchone()
            if norm in ("sends",):
                tids = sends
            elif norm in ("receives",):
                tids = recvs
            elif norm in ("used_on",):
                for d in devs:
                    add("Device", d)
                return results
            elif norm in ("held_by",):
                if cust:
                    add("Customer", cust[0])
                return results
            else:  # all_txns / unknown / None -> everything linked
                tids = sends + recvs
                for d in devs:
                    add("Device", d)
                if cust:
                    add("Customer", cust[0])
            for t in tids:
                add("Transaction", t)
        elif otype == "Transaction":
            r = self.conn.execute(
                "SELECT from_account, to_account, counterparty_id "
                "FROM transactions WHERE txn_id=?", (object_id,)).fetchone()
            if r:
                if norm not in ("to", "to_cp"):
                    add("Account", r["from_account"])
                if norm not in ("from", "to_cp"):
                    add("Account", r["to_account"])
                if r["counterparty_id"] and norm not in ("from", "to"):
                    add("Counterparty", r["counterparty_id"])
        elif otype == "Device":
            for a in self.conn.execute(
                    "SELECT account_id FROM account_devices WHERE device_id=?",
                    (object_id,)):
                add("Account", a[0])
        elif otype == "Customer":
            for a in self.conn.execute(
                    "SELECT account_id FROM accounts WHERE customer_id=?", (object_id,)):
                add("Account", a[0])
        elif otype == "Alert":
            r = self.conn.execute(
                "SELECT account_id FROM alerts WHERE alert_id=?", (object_id,)).fetchone()
            if r:
                add("Account", r["account_id"])
        return results

    # ------------------------------------------------ graph for the viz
    def build_graph(self, account_ids: list[str] | None = None) -> nx.Graph:
        """networkx graph of accounts/txns/devices/counterparties, optionally scoped
        to a ring's accounts (1 hop out: their txns, counterparties, shared devices)."""
        g = nx.Graph()
        c = self.conn
        if account_ids is None:
            account_ids = [r[0] for r in c.execute("SELECT account_id FROM accounts")]
        scope = set(account_ids)

        for aid in scope:
            g.add_node(aid, kind="account", label=aid)

        # Transactions touching the scope
        qmarks = ",".join("?" * len(scope))
        if scope:
            rows = c.execute(
                f"SELECT txn_id, from_account, to_account, counterparty_id, amount "
                f"FROM transactions WHERE from_account IN ({qmarks}) "
                f"OR to_account IN ({qmarks})",
                (*scope, *scope)).fetchall()
            for r in rows:
                # bring in the counterpart account even if outside scope
                for end in (r["from_account"], r["to_account"]):
                    if end and end not in g:
                        g.add_node(end, kind="account", label=end)
                g.add_edge(r["from_account"], r["to_account"],
                           kind="txn", label=f"₹{r['amount']:,.0f}", txn_id=r["txn_id"])
                if r["counterparty_id"]:
                    cp = r["counterparty_id"]
                    g.add_node(cp, kind="counterparty", label=cp)
                    g.add_edge(r["to_account"], cp, kind="to_cp")

            # Shared devices among scope accounts
            dev_rows = c.execute(
                f"SELECT account_id, device_id FROM account_devices "
                f"WHERE account_id IN ({qmarks})", tuple(scope)).fetchall()
            for r in dev_rows:
                d = r["device_id"]
                g.add_node(d, kind="device", label=d)
                g.add_edge(r["account_id"], d, kind="used_on")
        return g


# ---------------------------------------------------- guarded mutators (U10)
# The ONLY write path. governance.@action functions call these; nothing else should.
def freeze_account(store: OntologyStore, account_id: str) -> bool:
    cur = store.conn.execute(
        "UPDATE accounts SET status='frozen' WHERE account_id=?", (account_id,))
    store.conn.commit()
    return cur.rowcount > 0
