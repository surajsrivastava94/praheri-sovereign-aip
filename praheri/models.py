"""Ontology object types (the nouns). See BUILD_BIBLE.md §3.1.

These are the typed objects the agent reasons over. Retrieval ALWAYS returns
structured objects built from these — never free text about them (OAG, not RAG).
This file is intended to be fairly complete; extend properties as needed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

RiskRating = Literal["low", "medium", "high"]
Channel = Literal["UPI", "IMPS", "NEFT", "RTGS", "CASH", "CARD"]


class Customer(BaseModel):
    customer_id: str
    name: str
    kyc_risk_rating: RiskRating = "low"
    pep_flag: bool = False
    nationality: str = "IN"
    occupation: Optional[str] = None
    onboarding_date: datetime


class Account(BaseModel):
    account_id: str
    customer_id: str  # link -> Customer
    type: Literal["savings", "current", "wallet"] = "savings"
    branch: str = "MUM-001"
    balance: float = 0.0
    status: Literal["active", "frozen", "closed"] = "active"
    open_date: datetime


class Transaction(BaseModel):
    txn_id: str
    from_account: str             # link -> Account
    to_account: str               # link -> Account
    counterparty_id: Optional[str] = None  # link -> Counterparty
    amount: float
    currency: str = "INR"
    channel: Channel = "UPI"
    timestamp: datetime


class Counterparty(BaseModel):
    counterparty_id: str
    name: str
    type: Literal["internal", "external"] = "external"
    bank: Optional[str] = None
    country: str = "IN"
    risk_flags: list[str] = Field(default_factory=list)


class Device(BaseModel):
    device_id: str
    ip: str
    geo: str = "IN"
    first_seen: datetime
    linked_accounts: list[str] = Field(default_factory=list)  # link -> Account


class Alert(BaseModel):
    alert_id: str
    account_id: str               # link -> Account
    rule: str                     # e.g. "structuring_below_threshold"
    score: float                  # 0..100, queue is sorted by this
    status: Literal["open", "in_review", "closed"] = "open"
    created_at: datetime


class Case(BaseModel):
    case_id: str
    alert_ids: list[str] = Field(default_factory=list)   # link -> Alert
    assigned_to: Optional[str] = None
    status: Literal["open", "filed", "cleared"] = "open"
    decision: Optional[Literal["clear", "escalate", "file"]] = None
    narrative: Optional[str] = None
    created_at: datetime


# Documents the graph edges for store.build_graph() and get_linked_objects().
LINKS = {
    "Customer": [("owns", "Account")],
    "Account": [("held_by", "Customer"), ("sends", "Transaction"),
                ("receives", "Transaction"), ("used_on", "Device")],
    "Transaction": [("from", "Account"), ("to", "Account"), ("to_cp", "Counterparty")],
    "Device": [("used_by", "Account")],
    "Alert": [("raised_on", "Account"), ("bundled_in", "Case")],
    "Case": [("bundles", "Alert")],
}

OBJECT_TYPES = {
    "Customer": Customer, "Account": Account, "Transaction": Transaction,
    "Counterparty": Counterparty, "Device": Device, "Alert": Alert, "Case": Case,
}
