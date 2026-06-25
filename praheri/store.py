"""Ontology store: SQLite persistence + networkx graph. See BUILD_BIBLE.md §3, §6.

The FIRST design decision that makes this OAG: every read returns a structured
object dict {type, id, properties, linked_ids} — NEVER a text blob.

TODO(playbook step 1.3): implement the bodies below.
"""
from __future__ import annotations

import sqlite3
from typing import Any

import networkx as nx

DB_PATH = "praheri.db"


class OntologyStore:
    def __init__(self, db_path: str = DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # --- reads (return structured objects, not text) ---
    def query_objects(self, type: str, **filters: Any) -> list[dict]:
        """Return objects of `type` matching filters, as
        {type, id, properties, linked_ids} dicts. TODO."""
        raise NotImplementedError

    def get_object(self, type: str, object_id: str) -> dict | None:
        """Single object as a structured dict. TODO."""
        raise NotImplementedError

    def get_linked_objects(self, object_id: str, link_type: str | None = None) -> list[dict]:
        """Traverse links from object_id (see models.LINKS). The core OAG primitive
        the agent uses to walk a fraud ring. Return structured object dicts. TODO."""
        raise NotImplementedError

    def build_graph(self, account_ids: list[str] | None = None) -> nx.Graph:
        """Build a networkx graph (accounts/txns/devices/counterparties) for the
        pyvis visualization, optionally scoped to a ring. TODO."""
        raise NotImplementedError

    # --- writes happen ONLY via governance.actions, never here directly ---
