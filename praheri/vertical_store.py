"""Generic ontology store — the schema-free sibling of OntologyStore.

The AML store (praheri/store.py) is deliberately AML-hardcoded: its _TABLE,
prefix-based _type_of(), and per-type SQL bind it to accounts/transactions/
devices. Generalising *it* would touch the hero's read path. So instead this
file adds a separate, schema-free store backed by an in-memory networkx graph,
built from a cartridge's node/edge lists.

It exposes the SAME structured-object contract as OntologyStore —
query_objects / get_object / get_linked_objects / build_graph, all returning the
identical {type, id, properties, linked_ids} dict — so every downstream consumer
(traversal, signal detection, render_ring_graph) is store-agnostic. AML keeps
using OntologyStore; the shallow verticals use this. Nothing here imports or
changes store.py.

Data shape it loads:
    {"nodes": [{"type": "Claim", "id": "CLM-1", "properties": {...}}, ...],
     "edges": [{"from": "CLM-1", "to": "GAR-1", "link_type": "serviced_by"}, ...]}

linked_ids convention: an outgoing edge with link_type "X" lists the neighbour
under key "X"; the same edge seen from the other endpoint lists it under "X_in"
(a mechanical reverse name — the generic store has no semantic reverse pairs the
way AML has sends/receives).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx


class GenericOntologyStore:
    def __init__(self, data: dict[str, Any]):
        # id -> {"type", "properties"}
        self._nodes: dict[str, dict[str, Any]] = {}
        # adjacency: id -> list of (link_type, neighbour_id, direction)
        #   direction "out" => self --link_type--> neighbour
        #   direction "in"  => neighbour --link_type--> self
        self._adj: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
        self._edges: list[dict[str, str]] = []

        for n in data.get("nodes", []):
            self._nodes[n["id"]] = {"type": n["type"],
                                    "properties": dict(n.get("properties", {}))}
        for e in data.get("edges", []):
            frm, to, lt = e["from"], e["to"], e.get("link_type", "linked")
            self._edges.append({"from": frm, "to": to, "link_type": lt})
            self._adj[frm].append((lt, to, "out"))
            self._adj[to].append((lt, frm, "in"))

    # ------------------------------------------------ structured-object builder
    def _structured(self, oid: str) -> dict | None:
        node = self._nodes.get(oid)
        if node is None:
            return None
        return {"type": node["type"], "id": oid,
                "properties": dict(node["properties"]),
                "linked_ids": self._linked_ids(oid)}

    def _linked_ids(self, oid: str) -> dict[str, list[str]]:
        """Neighbour-id map grouped by link_type. Incoming edges use 'X_in'."""
        out: dict[str, list[str]] = defaultdict(list)
        for lt, neighbour, direction in self._adj.get(oid, []):
            key = lt if direction == "out" else f"{lt}_in"
            out[key].append(neighbour)
        return dict(out)

    # ------------------------------------------------ reads (structured, not text)
    def query_objects(self, type: str, **filters: Any) -> list[dict]:
        """Objects of `type` matching property-equality filters, as structured dicts."""
        results = []
        for oid, node in self._nodes.items():
            if node["type"] != type:
                continue
            props = node["properties"]
            if all(props.get(k) == v for k, v in filters.items()):
                results.append(self._structured(oid))
        return results

    def get_object(self, type: str, object_id: str) -> dict | None:
        """Single object as a structured dict, or None if missing / wrong type."""
        node = self._nodes.get(object_id)
        if node is None or node["type"] != type:
            return None
        return self._structured(object_id)

    def get_linked_objects(self, object_id: str,
                           link_type: str | None = None) -> list[dict]:
        """Traverse links from object_id. The core OAG primitive. `link_type` None
        or unknown means 'all links' — never raises on a bad value (mirrors the AML
        store, which tolerates the loose values the LLM emits)."""
        if object_id not in self._nodes:
            return []
        want = (link_type or "").lower().strip()
        seen: set[str] = set()
        results: list[dict] = []
        for lt, neighbour, _direction in self._adj.get(object_id, []):
            if want and want != lt.lower():
                continue
            if neighbour in seen:
                continue
            obj = self._structured(neighbour)
            if obj:
                seen.add(neighbour)
                results.append(obj)
        return results

    # ------------------------------------------------ graph for the viz
    def build_graph(self, ids: list[str] | None = None) -> nx.Graph:
        """Undirected networkx graph (same shape as OntologyStore.build_graph): nodes
        carry `kind` (object type) + `label`; edges carry `label` (link_type). Scoped
        to `ids` plus one hop out when given, else the whole graph."""
        g = nx.Graph()
        if ids is None:
            scope = set(self._nodes)
        else:
            scope = set(ids)
            # one hop out: pull in direct neighbours of the scoped nodes
            for oid in list(scope):
                for _lt, neighbour, _d in self._adj.get(oid, []):
                    scope.add(neighbour)

        for oid in scope:
            node = self._nodes.get(oid)
            if node is None:
                continue
            label = (node["properties"].get("name")
                     or node["properties"].get("label") or oid)
            g.add_node(oid, kind=node["type"], label=label)

        for e in self._edges:
            if e["from"] in g and e["to"] in g:
                g.add_edge(e["from"], e["to"],
                           kind=e["link_type"], label=e["link_type"])
        return g
