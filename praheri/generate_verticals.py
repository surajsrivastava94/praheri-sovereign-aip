"""Deterministic synthetic data for the shallow verticals.

Mirrors praheri/generate.py's philosophy (seeded, planted patterns) but emits
generic {nodes, edges} JSON under data/verticals/<key>.json for GenericOntologyStore.
Each vertical plants exactly ONE ring so the demo beat is crisp. Regenerate with:

    python -m praheri.generate_verticals

Output is gitignored (like the AML DB) — it is synthetic and reproducible.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT_DIR = Path("data/verticals")


def _write(key: str, nodes: list[dict], edges: list[dict]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{key}.json"
    path.write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2,
                               sort_keys=True))
    return path


# --------------------------------------------------------------- procurement
def build_procurement() -> tuple[list[dict], list[dict]]:
    """Reuse the existing procurement demo objects (models_procurement) as the
    cartridge dataset — one PO under budget, one over (the approval-gate beat)."""
    from praheri import models_procurement as proc

    nodes: list[dict] = []
    edges: list[dict] = []

    b = proc.DEMO_BUDGET
    nodes.append({"type": "Budget", "id": b.budget_id,
                  "properties": {"department": b.department, "cap": b.cap,
                                 "spent": b.spent,
                                 "remaining": b.cap - b.spent}})
    for v in proc.DEMO_VENDORS:
        nodes.append({"type": "Vendor", "id": v.vendor_id,
                      "properties": {"name": v.name, "country": v.country,
                                     "risk_rating": v.risk_rating}})
    for r in proc.DEMO_REQUISITIONS:
        nodes.append({"type": "Requisition", "id": r.requisition_id,
                      "properties": {"amount": r.amount, "description": r.description,
                                     "status": r.status}})
        edges.append({"from": r.requisition_id, "to": r.vendor_id,
                      "link_type": "from_vendor"})
        edges.append({"from": r.requisition_id, "to": r.budget_id,
                      "link_type": "against_budget"})
    return nodes, edges


_BUILDERS = {
    "procurement": build_procurement,
}


def main() -> None:
    for key, builder in _BUILDERS.items():
        nodes, edges = builder()
        path = _write(key, nodes, edges)
        print(f"wrote {path} ({len(nodes)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    main()
