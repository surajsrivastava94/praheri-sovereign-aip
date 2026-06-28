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


# --------------------------------------------------------------- insurance SIU
def build_insurance() -> tuple[list[dict], list[dict]]:
    """Planted SHARED-GARAGE ring: 6 motor claims, all serviced by one garage that
    also shares a phone with the claimants — a classic staged-accident cluster.
    Mirrors AML's shared-device ring, different nouns (detector reused)."""
    nodes: list[dict] = []
    edges: list[dict] = []

    garage = "GAR-RING-01"
    nodes.append({"type": "Garage", "id": garage,
                  "properties": {"name": "QuickFix Motors", "city": "Surat",
                                 "empanelled": False}})
    # one alert raised on the garage (the ring hub) — traversal fans out to claims
    nodes.append({"type": "Alert", "id": "ALERT-INS-01",
                  "properties": {"score": 88, "rule": "garage_concentration",
                                 "root_id": garage}})
    edges.append({"from": "ALERT-INS-01", "to": garage, "link_type": "raised_on"})

    # 6 claims through the one garage (>=5 fires shared_attribute_ring)
    for i in range(6):
        clm, clt, pol = f"CLM-{i:02d}", f"CLT-{i:02d}", f"POL-{i:02d}"
        nodes.append({"type": "Claim", "id": clm,
                      "properties": {"amount": 90_000 + i * 5_000,
                                     "type": "motor", "status": "pending"}})
        nodes.append({"type": "Claimant", "id": clt,
                      "properties": {"name": f"Claimant {i}", "phone": "+91-99999-00000"}})
        nodes.append({"type": "Policy", "id": pol,
                      "properties": {"sum_insured": 300_000, "product": "motor"}})
        edges.append({"from": clm, "to": garage, "link_type": "serviced_by"})
        edges.append({"from": clm, "to": clt, "link_type": "filed_by"})
        edges.append({"from": clm, "to": pol, "link_type": "under_policy"})

    # a couple of clean claims through a real garage (control group / noise)
    nodes.append({"type": "Garage", "id": "GAR-OK-01",
                  "properties": {"name": "City Auto Care", "city": "Pune",
                                 "empanelled": True}})
    for i in range(2):
        clm = f"CLM-OK-{i:02d}"
        nodes.append({"type": "Claim", "id": clm,
                      "properties": {"amount": 40_000, "type": "motor",
                                     "status": "settled"}})
        edges.append({"from": clm, "to": "GAR-OK-01", "link_type": "serviced_by"})
    return nodes, edges


# --------------------------------------------------------------- lending EWS
def build_lending() -> tuple[list[dict], list[dict]]:
    """Planted EARLY-WARNING cluster: 5 borrowers all linked to one common director
    (shared_attribute_ring) AND a stressed borrower with >=5 bounced/sub-threshold
    EMI inflows (threshold_cluster). The shared director is the contagion hub."""
    nodes: list[dict] = []
    edges: list[dict] = []

    director = "DIR-RING-01"
    nodes.append({"type": "Director", "id": director,
                  "properties": {"name": "S. Mehta", "din": "00123456"}})
    nodes.append({"type": "Alert", "id": "ALERT-LEND-01",
                  "properties": {"score": 82, "rule": "common_director_stress",
                                 "root_id": director}})
    edges.append({"from": "ALERT-LEND-01", "to": director, "link_type": "raised_on"})

    # 5 borrowers sharing one director (>=5 fires shared_attribute_ring)
    for i in range(5):
        bor, loan = f"BOR-{i:02d}", f"LOAN-{i:02d}"
        nodes.append({"type": "Borrower", "id": bor,
                      "properties": {"name": f"Acme {i} Pvt Ltd", "rating": "BBB"}})
        nodes.append({"type": "Loan", "id": loan,
                      "properties": {"exposure": 1_00_00_000, "dpd": 0}})
        edges.append({"from": bor, "to": director, "link_type": "governed_by"})
        edges.append({"from": loan, "to": bor, "link_type": "lent_to"})

    # BOR-00 is stressed: >=5 bounced/sub-threshold EMI inflows (threshold_cluster)
    for i in range(6):
        emi = f"EMI-{i:02d}"
        nodes.append({"type": "Inflow", "id": emi,
                      "properties": {"amount": 8_000, "kind": "partial_emi"}})
        edges.append({"from": emi, "to": "BOR-00", "link_type": "credited_to"})
    return nodes, edges


_BUILDERS = {
    "procurement": build_procurement,
    "insurance": build_insurance,
    "lending": build_lending,
}


def main() -> None:
    for key, builder in _BUILDERS.items():
        nodes, edges = builder()
        path = _write(key, nodes, edges)
        print(f"wrote {path} ({len(nodes)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    main()
