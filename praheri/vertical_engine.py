"""Vertical engine — the config-driven half of the investigation pipeline.

This is the generalisation of praheri/agent.py's hybrid (KTD-2): Python does the
deterministic detection, the model would narrate. Here we provide the DETECTION
for the shallow verticals, parameterised by a VerticalConfig's SignalSpec list.

It is ADDITIVE: agent.compute_signals() (the AML detector) is left untouched. The
cycle primitive is REUSED, not copied — we import agent._has_cycle so there is one
implementation. The detectors below are the generic analogues of AML's three
typologies, keyed by node/edge type via SignalSpec.params:

  shared_attribute_ring  ~ AML shared-device ring  (>=N members share one hub node)
  circular_flow          ~ AML circular layering    (a directed cycle in the graph)
  threshold_cluster      ~ AML structuring          (>=N sub-threshold inbound edges)

Each detector returns the SAME signal dict shape AML emits:
    {"typology", "detail", "evidence_ids"}
so render_vertical and the decision panel are detector-agnostic.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from praheri.agent import _has_cycle  # reuse the one cycle implementation
from praheri.vertical_store import GenericOntologyStore
from praheri.verticals import VerticalConfig

CACHE_DIR = Path("demo_cache")


# --------------------------------------------------------------------------- #
# Detectors. Each: (store, root_id, params) -> signal dict | None             #
# --------------------------------------------------------------------------- #

def _detect_shared_attribute_ring(store: GenericOntologyStore, root_id: str,
                                  params: dict) -> dict | None:
    """>=N members linked to a single hub node (e.g. claims sharing one garage,
    accounts sharing one device). Generalises AML's shared-device ring."""
    hub_type = params.get("hub_type")
    min_members = params.get("min_members", 5)
    best: dict | None = None
    for hub in store.query_objects(hub_type) if hub_type else []:
        members: list[str] = []
        for ids in hub["linked_ids"].values():
            members.extend(ids)
        members = sorted(set(members))
        if len(members) >= min_members and (best is None
                                            or len(members) > len(best["_members"])):
            best = {
                "typology": params.get("typology", "shared_attribute_ring"),
                "detail": (f"{len(members)} ostensibly unrelated parties link to one "
                           f"{hub_type} ({hub['id']}) — linked-identity ring."),
                "evidence_ids": [hub["id"]] + members[:8],
                "_members": members,
            }
    if best:
        best.pop("_members", None)
    return best


def _detect_circular_flow(store: GenericOntologyStore, root_id: str,
                         params: dict) -> dict | None:
    """A directed cycle among nodes of `node_type` over edges of `link_type`.
    Reuses agent._has_cycle. Generalises AML's circular layering."""
    node_type = params.get("node_type")
    link_type = params.get("link_type")
    members = store.query_objects(node_type) if node_type else []
    nodes = {o["id"] for o in members}
    # DIRECTED edges only: use linked_ids[link_type] (outgoing), not the
    # direction-blind get_linked_objects, else A->B reads back as B->A (false cycle).
    edges: set[tuple[str, str]] = set()
    for obj in members:
        for tgt in obj["linked_ids"].get(link_type, []):
            if tgt in nodes:
                edges.add((obj["id"], tgt))
    if len(nodes) >= 3 and _has_cycle(edges, nodes):
        cycle_nodes = sorted({a for e in edges for a in e})[:6]
        return {
            "typology": params.get("typology", "circular_flow"),
            "detail": ("Closed loop detected among these parties "
                       "(A->B->C->A) with little economic substance."),
            "evidence_ids": cycle_nodes,
        }
    return None


def _detect_threshold_cluster(store: GenericOntologyStore, root_id: str,
                             params: dict) -> dict | None:
    """>=N inbound edges whose `amount_prop` sits below `threshold`. Generalises
    AML's structuring/smurfing. Counts members of `member_type` exceeding the count."""
    member_type = params.get("member_type")
    link_type = params.get("link_type")          # inbound link to count
    amount_prop = params.get("amount_prop", "amount")
    threshold = params.get("threshold", 50_000)
    min_count = params.get("min_count", 5)
    flagged: list[str] = []
    for member in store.query_objects(member_type) if member_type else []:
        # inbound ids are grouped in linked_ids under the (possibly reversed) key
        inbound_ids = member["linked_ids"].get(link_type, [])
        sub = []
        for iid in inbound_ids:
            obj = store._structured(iid)  # noqa: SLF001 — resolve neighbour object
            if obj and obj["properties"].get(amount_prop, threshold) < threshold:
                sub.append(iid)
        if len(sub) >= min_count:
            flagged.append(member["id"])
    if flagged:
        return {
            "typology": params.get("typology", "threshold_cluster"),
            "detail": (f"{len(flagged)} party(ies) each received >={min_count} "
                       f"sub-threshold ({threshold:,}) inflows — classic structuring."),
            "evidence_ids": sorted(flagged)[:8],
        }
    return None


DETECTORS: dict[str, Callable[[GenericOntologyStore, str, dict], dict | None]] = {
    "shared_attribute_ring": _detect_shared_attribute_ring,
    "circular_flow": _detect_circular_flow,
    "threshold_cluster": _detect_threshold_cluster,
}


def compute_signals_for(config: VerticalConfig, store: GenericOntologyStore,
                        root_id: str) -> list[dict]:
    """Run each of the vertical's configured signal detectors; return those that
    fired, in config order. Mirrors agent.compute_signals' output contract.
    Raises KeyError on an unknown detector id (fail fast, not silent)."""
    signals: list[dict] = []
    for spec in config.signals:
        detector = DETECTORS[spec.id]  # KeyError if config names a bad detector
        hit = detector(store, root_id, spec.params)
        if hit:
            signals.append(hit)
    return signals


# --------------------------------------------------------------------------- #
# Investigation: real traverse + signals; narrative golden-cached (KTD-5).    #
# --------------------------------------------------------------------------- #

def traverse_generic(store: GenericOntologyStore, root_id: str,
                     max_hops: int = 2) -> list[dict]:
    """BFS over the generic ontology from the root, assembling the ring as
    structured objects. Mirrors agent.traverse_ring, store-agnostic."""
    seen: set[str] = {root_id}
    touched: list[dict] = []
    # root can be any type; resolve it generically (the store is keyed by id).
    root_obj = store._structured(root_id)  # noqa: SLF001
    if root_obj:
        touched.append(root_obj)
    frontier = [(root_id, 0)]
    while frontier:
        oid, hop = frontier.pop(0)
        if hop >= max_hops:
            continue
        for obj in store.get_linked_objects(oid):
            if obj["id"] in seen:
                continue
            seen.add(obj["id"])
            touched.append(obj)
            frontier.append((obj["id"], hop + 1))
    return touched


def compute_vertical_investigation(config: VerticalConfig,
                                   store: GenericOntologyStore,
                                   root_id: str,
                                   use_cache: bool = True) -> dict[str, Any]:
    """Real traversal + real signal detection over the cartridge's data; narrative
    served from the golden cache when present (honest Live/Cached source flag)."""
    touched = traverse_generic(store, root_id)
    signals = compute_signals_for(config, store, root_id)
    recommendation = "FILE" if signals else "CLEAR"
    cited = sorted({eid for s in signals for eid in s["evidence_ids"]})

    narrative, source = "", "live"
    cache_file = CACHE_DIR / f"{config.golden_cache_key}__{root_id}.json"
    if use_cache and cache_file.exists():
        cached = json.loads(cache_file.read_text())
        narrative = cached.get("narrative", "")
        source = "cached"

    return {
        "vertical": config.key,
        "root_id": root_id,
        "objects_touched": [o["id"] for o in touched],
        "signals": signals,
        "recommendation": recommendation,
        "cited_ids": cited,
        "narrative": narrative,
        "source": source,
    }
