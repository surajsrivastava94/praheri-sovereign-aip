"""Deterministic, explainable confidence for the AML recommendation.

Lives in server/ — the engine stays frozen. A faithful port of the Streamlit
`_confidence`/`_signal_count` (app/streamlit_app.py), re-implemented here rather
than imported (the Streamlit app is the frozen fallback). Pure function of the
cached investigation dict; no model call. Server-side so the math is testable and
the term-by-term breakdown is authoritative ("how is confidence computed?").
"""
from __future__ import annotations

import re
from typing import Any


def signal_count(detail: str, evidence_ids: list[str]) -> int:
    """Headline count from a signal: the leading integer in `detail`
    ('7 mule account(s)…'), else the number of ACC- evidence ids."""
    m = re.match(r"\s*(\d+)", detail or "")
    if m:
        return int(m.group(1))
    return sum(1 for i in evidence_ids if i.startswith("ACC-"))


def confidence(inv: dict[str, Any]) -> dict[str, Any]:
    """Return {score 0-100, band, reasons[]} — explainable term-by-term."""
    rec = inv.get("recommendation", "ESCALATE")
    score = {"FILE": 60, "ESCALATE": 35, "CLEAR": 15}.get(rec, 35)
    reasons = [f"base {rec} = {score}"]
    typ_seen: set[str] = set()
    for s in inv.get("signals", []):
        typ = s["typology"]
        typ_seen.add(typ)
        n = signal_count(s.get("detail", ""), s.get("evidence_ids", []))
        if typ == "structuring":
            add = min(15 + 3 * max(0, n - 1), 30)
            reasons.append(f"structuring ({n} mules) +{add}")
        elif typ == "circular_layering":
            add = 20
            reasons.append(f"circular layering +{add}")
        elif typ == "shared_device_ring":
            add = min(15 + 2 * max(0, n - 5), 25)
            reasons.append(f"shared-device ring ({n} accts) +{add}")
        else:
            add = 10
            reasons.append(f"{typ} +{add}")
        score += add
    if len(typ_seen) >= 2:
        score += 10
        reasons.append(f"{len(typ_seen)} typologies corroborate +10")
    if inv.get("policy_citations"):
        score += 5
        reasons.append("policy-grounded +5")
    score = max(0, min(100, score))
    band = "High" if score >= 75 else "Medium" if score >= 45 else "Low"
    return {"score": score, "band": band, "reasons": reasons}
