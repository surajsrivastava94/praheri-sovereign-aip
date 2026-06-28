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


# --------------------------------------------------------------- wealth
def build_wealth() -> tuple[list[dict], list[dict]]:
    """Planted MIS-SELLING cluster: one adviser sold a high-risk product to 5
    low-risk-profile clients (SEBI suitability breach). The adviser is the hub —
    shared_attribute_ring over the mis-sold sales."""
    nodes: list[dict] = []
    edges: list[dict] = []

    adviser = "ADV-RING-01"
    nodes.append({"type": "Adviser", "id": adviser,
                  "properties": {"name": "R. Kapoor", "arn": "ARN-99887"}})
    nodes.append({"type": "Alert", "id": "ALERT-WEALTH-01",
                  "properties": {"score": 79, "rule": "suitability_mismatch",
                                 "root_id": adviser}})
    edges.append({"from": "ALERT-WEALTH-01", "to": adviser, "link_type": "raised_on"})

    # high-risk product sold to 5 low-risk clients (>=5 fires shared_attribute_ring)
    nodes.append({"type": "Product", "id": "PRD-AIF-01",
                  "properties": {"name": "High-Yield AIF", "risk": "high"}})
    for i in range(5):
        sale, client, prof = f"SALE-{i:02d}", f"CLI-{i:02d}", f"PROF-{i:02d}"
        nodes.append({"type": "Sale", "id": sale,
                      "properties": {"amount": 20_00_000, "product": "PRD-AIF-01"}})
        nodes.append({"type": "Client", "id": client,
                      "properties": {"name": f"Investor {i}"}})
        nodes.append({"type": "SuitabilityProfile", "id": prof,
                      "properties": {"risk_appetite": "low", "horizon": "short"}})
        edges.append({"from": sale, "to": adviser, "link_type": "sold_by"})
        edges.append({"from": sale, "to": client, "link_type": "sold_to"})
        edges.append({"from": sale, "to": "PRD-AIF-01", "link_type": "of_product"})
        edges.append({"from": client, "to": prof, "link_type": "has_profile"})
    return nodes, edges


# --------------------------------------------------------------- corporate
def build_corporate() -> tuple[list[dict], list[dict]]:
    """Planted CIRCULAR OWNERSHIP: A->B->C->A holding loop obscuring the true UBO,
    plus a common UBO across the loop. circular_flow + shared_attribute_ring."""
    nodes: list[dict] = []
    edges: list[dict] = []

    ubo = "UBO-01"
    nodes.append({"type": "UBO", "id": ubo,
                  "properties": {"name": "V. Singh", "nationality": "IN"}})
    nodes.append({"type": "Alert", "id": "ALERT-CORP-01",
                  "properties": {"score": 85, "rule": "circular_ownership",
                                 "root_id": "CO-A"}})
    edges.append({"from": "ALERT-CORP-01", "to": "CO-A", "link_type": "raised_on"})

    # circular ownership loop A->B->C->A
    loop = ["CO-A", "CO-B", "CO-C"]
    for i, co in enumerate(loop):
        nodes.append({"type": "Company", "id": co,
                      "properties": {"name": f"Holdco {co[-1]}", "jurisdiction": "IN"}})
        nxt = loop[(i + 1) % len(loop)]
        edges.append({"from": co, "to": nxt, "link_type": "owns"})
        # each loop company also declares the same UBO (shared_attribute_ring on UBO)
        edges.append({"from": co, "to": ubo, "link_type": "declares_ubo"})

    # two more shells declaring the same UBO -> >=5 members fires the ring
    for j in range(2):
        sh = f"CO-SHELL-{j:02d}"
        nodes.append({"type": "Company", "id": sh,
                      "properties": {"name": f"Shell {j}", "jurisdiction": "AE"}})
        edges.append({"from": sh, "to": ubo, "link_type": "declares_ubo"})
    return nodes, edges


_BUILDERS = {
    "procurement": build_procurement,
    "insurance": build_insurance,
    "lending": build_lending,
    "wealth": build_wealth,
    "corporate": build_corporate,
}


def main() -> None:
    for key, builder in _BUILDERS.items():
        nodes, edges = builder()
        path = _write(key, nodes, edges)
        print(f"wrote {path} ({len(nodes)} nodes, {len(edges)} edges)")


if __name__ == "__main__":
    main()
