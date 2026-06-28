"""Governance layer: audit log + actions + approval gate. See BUILD_BIBLE.md §4.

The SECOND design decision that makes this "AIP, not a chatbot": the model never
writes data directly. All mutations go through @action. High-stakes actions require
human approval before they execute. Everything is audited (append-only).

This module is intended to be fairly complete and runnable.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

AUDIT_PATH = Path("audit_log.jsonl")
MODEL_NAME = "llama3.1:8b"  # surfaced in every audit row; keep in sync with agent.py


@dataclass
class Actor:
    id: str
    role: str  # "analyst" | "mlro"


# ---------------------------------------------------------------- audit log
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(event: str, actor: Actor, action: str = "", params: dict | None = None,
        result: Any = None) -> str:
    """Append one immutable audit row. Returns the row id."""
    row_id = uuid.uuid4().hex[:12]
    row = {
        "id": row_id, "ts": _now(), "event": event, "actor": actor.id,
        "role": actor.role, "action": action, "params": params or {},
        "result": result, "model": MODEL_NAME,
    }
    with AUDIT_PATH.open("a") as f:
        f.write(json.dumps(row, default=str) + "\n")
    return row_id


def read_audit() -> list[dict]:
    if not AUDIT_PATH.exists():
        return []
    return [json.loads(line) for line in AUDIT_PATH.read_text().splitlines() if line.strip()]


# ------------------------------------------------------- pending approvals
@dataclass
class Pending:
    items: dict[str, dict] = field(default_factory=dict)

    def add(self, ref: str, action: str, params: dict, proposed_by: str) -> None:
        self.items[ref] = {"ref": ref, "action": action, "params": params,
                           "proposed_by": proposed_by, "ts": _now(), "status": "pending"}

    def list_pending(self) -> list[dict]:
        return [i for i in self.items.values() if i["status"] == "pending"]


PENDING = Pending()
# Registry so the approver can re-invoke the underlying function on approval.
_EXECUTORS: dict[str, Callable] = {}


# ------------------------------------------------------------ @action
def action(requires_role: str, requires_approval: bool = False):
    """Decorator. Enforces role, logs proposal, gates high-stakes actions."""
    def wrap(fn: Callable):
        _EXECUTORS[fn.__name__] = fn

        def inner(actor: Actor, **params):
            if actor.role not in (requires_role, "mlro"):
                raise PermissionError(f"{actor.role} cannot {fn.__name__}")
            ref = log("ACTION_PROPOSED", actor, fn.__name__, params)
            if requires_approval:
                PENDING.add(ref, fn.__name__, params, actor.id)
                return {"status": "PENDING_APPROVAL", "ref": ref}
            result = fn(actor=actor, **params)
            log("ACTION_EXECUTED", actor, fn.__name__, params, result=result)
            return {"status": "EXECUTED", "ref": ref, "result": result}
        inner.__name__ = fn.__name__
        return inner
    return wrap


def approve(ref: str, mlro: Actor) -> dict:
    """MLRO approves a pending action; it executes and is audited."""
    item = PENDING.items.get(ref)
    if not item or item["status"] != "pending":
        raise ValueError("no such pending action")
    fn = _EXECUTORS[item["action"]]
    result = fn(actor=mlro, **item["params"])
    item["status"] = "approved"
    log("ACTION_APPROVED_AND_EXECUTED", mlro, item["action"], item["params"], result=result)
    return {"status": "EXECUTED", "ref": ref, "result": result}


# --------------------------------------------------------------- the actions
# Mutations go ONLY through store.py guarded mutators — never direct SQL here.
from praheri import store as _store  # noqa: E402


@action(requires_role="analyst")
def clear_alert(actor: Actor, alert_id: str, rationale: str):
    _store.set_alert_status(alert_id, "closed")
    return f"alert {alert_id} cleared"


@action(requires_role="analyst")
def escalate_alert_to_case(actor: Actor, alert_id: str, reason: str):
    _store.set_alert_status(alert_id, "in_review")
    return f"alert {alert_id} escalated to case"


@action(requires_role="analyst")
def add_case_note(actor: Actor, case_id: str, note: str):
    _store.add_note(case_id, note)
    return f"note added to {case_id}"


@action(requires_role="analyst", requires_approval=True)
def request_account_freeze(actor: Actor, account_id: str, reason: str):
    ok = _store.freeze_account(account_id)
    return f"account {account_id} FROZEN" if ok else f"account {account_id} not found"


@action(requires_role="analyst", requires_approval=True)
def file_str(actor: Actor, case_id: str, narrative: str):
    _store.file_str_record(case_id, narrative)
    return f"STR filed for {case_id}"


# --------------------------------------------------- procurement vertical (U12)
# Same @action engine, new vertical. Over-budget POs hit the SAME approval gate as
# request_account_freeze — proving the governance layer is workflow-agnostic.
@action(requires_role="analyst", requires_approval=True)
def approve_purchase_order(actor: Actor, requisition_id: str, amount: float,
                           budget_remaining: float):
    over = amount > budget_remaining
    return (f"PO {requisition_id} approved for INR{amount:,.0f}"
            if not over else
            f"PO {requisition_id} (INR{amount:,.0f}) EXCEEDS budget — escalated")


# ----------------------------------------------- generic vertical actions (U7)
# The shallow verticals (insurance/lending/wealth/corporate) propose their
# governed actions through the SAME @action engine, queue and audit log as AML —
# one approval gate for every sector. High-stakes actions route to MLRO; the few
# routine ones execute immediately. AML's own actions above are untouched.
@action(requires_role="analyst", requires_approval=True)
def propose_vertical_action(actor: Actor, vertical: str, action_id: str,
                            target_id: str, reason: str):
    return f"{action_id} on {target_id} ({vertical}) approved"


@action(requires_role="analyst")
def execute_vertical_action(actor: Actor, vertical: str, action_id: str,
                            target_id: str, reason: str):
    return f"{action_id} on {target_id} ({vertical}) executed"
