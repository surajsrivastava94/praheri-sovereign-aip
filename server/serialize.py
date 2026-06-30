"""networkx Graph -> JSON for the Next.js graph canvas.

Lives in server/ (NOT praheri/) so the engine stays byte-for-byte frozen. Reads
only the node/edge attributes the engine already sets in store.build_graph():
  AML nodes  -> {kind: account|device|counterparty, label}
  AML edges  -> {kind: txn|to_cp|used_on, label (e.g. "₹50,000"), txn_id}
  vertical   -> nodes {kind: <type>, label}, edges {label: link_type}
"""
from __future__ import annotations

from typing import Any, Iterable

import networkx as nx


def graph_json(g: nx.Graph, highlight: Iterable[str] = ()) -> dict[str, Any]:
    """Convert a built graph to {nodes, edges}. `highlight` ids glow in the UI
    (the cited evidence objects), so the frontend needs no second round-trip."""
    hl = set(highlight)
    nodes = [
        {
            "id": n,
            "kind": data.get("kind", "node"),
            "label": data.get("label", n),
            "highlight": n in hl,
        }
        for n, data in g.nodes(data=True)
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "kind": data.get("kind", "link"),
            "label": data.get("label", ""),
            "txn_id": data.get("txn_id"),
        }
        for u, v, data in g.edges(data=True)
    ]
    return {"nodes": nodes, "edges": edges}
