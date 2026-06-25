"""Procurement ontology — vertical #2. See BUILD_BIBLE.md §8 (platform thesis).

The POINT of this file: prove the Sovereign AIP engine (agent + governance + store)
is workflow-agnostic. Swap the ontology nouns + one action, reuse everything else.
Deliberately tiny — Requisition, Vendor, Contract, Budget — with one budget-gated
action. This is a stub that demonstrates reuse, NOT a second product.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Vendor(BaseModel):
    vendor_id: str
    name: str
    country: str = "IN"
    risk_rating: str = "low"  # low | medium | high


class Budget(BaseModel):
    budget_id: str
    department: str
    cap: float                # approval threshold in INR
    spent: float = 0.0


class Requisition(BaseModel):
    requisition_id: str
    vendor_id: str            # link -> Vendor
    budget_id: str            # link -> Budget
    amount: float
    description: str
    status: str = "pending"   # pending | approved | rejected
    created_at: datetime


class Contract(BaseModel):
    contract_id: str
    requisition_id: str       # link -> Requisition
    vendor_id: str            # link -> Vendor
    value: float
    signed: bool = False


PROC_OBJECT_TYPES = {
    "Vendor": Vendor, "Budget": Budget,
    "Requisition": Requisition, "Contract": Contract,
}

# Demo seed data — one PO under budget, one over (triggers the approval gate).
DEMO_VENDORS = [
    Vendor(vendor_id="VEN-01", name="Reliance Digital Supplies", risk_rating="low"),
    Vendor(vendor_id="VEN-02", name="Offshore Logistics Ltd", country="AE",
           risk_rating="high"),
]
DEMO_BUDGET = Budget(budget_id="BUD-IT", department="IT", cap=500_000, spent=120_000)
DEMO_REQUISITIONS = [
    Requisition(requisition_id="REQ-01", vendor_id="VEN-01", budget_id="BUD-IT",
                amount=180_000, description="Laptops for analyst team",
                created_at=datetime(2026, 6, 1)),
    Requisition(requisition_id="REQ-02", vendor_id="VEN-02", budget_id="BUD-IT",
                amount=900_000, description="Datacenter expansion (over budget)",
                created_at=datetime(2026, 6, 10)),
]
