"""Builds the Suspicious Transaction Report prompt for live token streaming.

Lives in server/ (NOT praheri/) so the engine stays byte-for-byte frozen. Pure
string assembly over the cached investigation dict — no model call, no engine
import. The resulting STR is grounded in STRUCTURED objects (typology + cited
object_ids + rationale), which is the whole point: the narrative cites real ids.
"""
from __future__ import annotations

from typing import Any


def build_str_messages(inv: dict[str, Any]) -> list[dict[str, str]]:
    """A system+user message pair instructing Llama to draft a concise STR
    grounded in the investigation's typology, cited object ids, and rationale."""
    cited = ", ".join(inv.get("cited_ids", [])) or "(none)"
    system = (
        "You are an AML analyst drafting a Suspicious Transaction Report (STR). "
        "Write a concise, formal narrative. Cite the specific object ids you are "
        "given verbatim — every claim must reference a real account or transaction id."
    )
    user = (
        f"Draft an STR for this case.\n"
        f"Typology: {inv.get('typology', 'unknown')}\n"
        f"Recommendation: {inv.get('recommendation', 'ESCALATE')}\n"
        f"Cited object ids (use these verbatim): {cited}\n"
        f"Analyst rationale: {inv.get('rationale', '')}\n\n"
        f"Write 4-6 sentences. Reference the cited ids; do not invent new ones."
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
