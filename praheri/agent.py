"""Llama investigation pipeline. See BUILD_BIBLE.md §5.

A PIPELINE, not a swarm: one Llama instance does tool-calling across
triage -> investigate (OAG traversal) -> evidence (RAG) -> decide + draft STR.
Model = Llama via Ollama's OpenAI-compatible API. The model never writes data;
it only PROPOSES actions through governance.

TODO(playbook steps 2.1, 2.2, 4.2): implement call_llama + investigate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import requests

from praheri.store import OntologyStore

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "llama3.1:8b"  # keep in sync with governance.MODEL_NAME
MAX_TOOL_ITERS = 6     # cap the tool-call loop so a confused 8B can't spin forever
REQUEST_TIMEOUT = 120  # seconds


class LlamaUnavailable(RuntimeError):
    """Raised when the local Ollama endpoint can't be reached or errors out."""

SYSTEM_PROMPT = """\
You are an AML investigation copilot operating inside a bank's secure, on-prem environment.

You can ONLY read data with these tools: query_objects, get_linked_objects, search_policy.
You can ONLY act by PROPOSING these actions: clear_alert, escalate_alert_to_case,
request_account_freeze, file_str. You may NEVER write data directly.

Rules:
1. Always query objects and traverse links BEFORE forming a conclusion.
2. Ground every claim in specific object_ids. Cite them in your narrative.
3. Recommend exactly one of: CLEAR, ESCALATE, FILE.
4. request_account_freeze and file_str require human approval — propose, never assume.
5. If evidence is insufficient or ambiguous, escalate to a human. Do not guess.
"""

# OpenAI-style tool specs the model is allowed to call. TODO: complete the schemas.
TOOLS: list[dict] = [
    {"type": "function", "function": {
        "name": "query_objects",
        "description": "Return ontology objects of a type matching filters (structured, not text).",
        "parameters": {"type": "object", "properties": {
            "type": {"type": "string"}, "filters": {"type": "object"}}, "required": ["type"]}}},
    {"type": "function", "function": {
        "name": "get_linked_objects",
        "description": "Traverse links from an object_id to walk the ring. Returns structured objects.",
        "parameters": {"type": "object", "properties": {
            "object_id": {"type": "string"}, "link_type": {"type": "string"}},
            "required": ["object_id"]}}},
    {"type": "function", "function": {
        "name": "search_policy",
        "description": "Retrieve relevant AML policy/threshold/typology clauses.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}},
                       "required": ["query"]}}},
    # TODO: add the 4 action-proposer tools (they route through governance).
]


def _post(messages: list[dict], tools: list[dict] | None) -> dict:
    """Single POST to Ollama's OpenAI-compatible endpoint. Raises LlamaUnavailable
    on connection/HTTP errors so callers can surface a clean message."""
    payload: dict[str, Any] = {"model": MODEL, "messages": messages, "stream": False}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:  # connection refused, timeout, 5xx, ...
        raise LlamaUnavailable(f"Ollama call failed: {e}") from e
    return r.json()


# ---- tool dispatch: the read tools the model is allowed to execute ----
def _dispatch_tool(name: str, args: dict, store: OntologyStore) -> Any:
    """Execute one tool call against the real store/policy. Defensive: the 8B model
    emits loose/invalid args, so we normalise and never let a bad call crash the loop."""
    try:
        if name == "query_objects":
            otype = args.get("type") or args.get("object_type") or ""
            filters = args.get("filters") or {}
            if not isinstance(filters, dict):
                filters = {}
            return store.query_objects(otype, **filters)
        if name == "get_linked_objects":
            oid = args.get("object_id") or args.get("id") or ""
            return store.get_linked_objects(oid, args.get("link_type"))
        if name == "search_policy":
            # policy_rag is wired in U8; degrade gracefully until then.
            try:
                from praheri.policy_rag import search_policy
                return search_policy(args.get("query", ""))
            except (ImportError, NotImplementedError):
                return [{"source": "policies/aml_thresholds.md",
                         "text": "(policy retrieval available after U8)", "score": 0.0}]
        return {"error": f"unknown tool {name}"}
    except Exception as e:  # never crash the loop on a malformed tool call
        return {"error": f"{name} failed: {e}"}


def call_llama(messages: list[dict], tools: list[dict] | None = None,
               store: OntologyStore | None = None) -> dict:
    """Drive a tool-calling loop against the local Llama. If the model returns
    tool_calls, execute the read tools via the store, append tool-role results, and
    re-call until the model returns a final text answer or MAX_TOOL_ITERS is hit.

    Returns {message, trace} where trace is the list of tool calls made (tool name,
    args, result count) — surfaced in the UI so the loop is visible (U6)."""
    store = store or OntologyStore()
    convo = list(messages)
    trace: list[dict] = []

    for _ in range(MAX_TOOL_ITERS):
        data = _post(convo, tools)
        msg = data["choices"][0]["message"]
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return {"message": msg, "trace": trace}
        # Append the assistant turn that requested the tools, then each result.
        convo.append(msg)
        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            result = _dispatch_tool(fn, args, store)
            n = len(result) if isinstance(result, list) else 1
            trace.append({"tool": fn, "args": args, "result_count": n})
            convo.append({
                "role": "tool",
                "tool_call_id": tc.get("id", fn),
                "name": fn,
                "content": json.dumps(result, default=str)[:8000],  # bound payload
            })
    # Hit the cap — ask for a final answer with no more tools.
    data = _post(convo + [{"role": "user",
                           "content": "Give your final answer now; do not call tools."}], None)
    return {"message": data["choices"][0]["message"], "trace": trace}


CACHE_DIR = Path("demo_cache")


# ---- [Python] deterministic triage + traversal (the orchestrated half of KTD-1) ----
def traverse_ring(store: OntologyStore, account_id: str,
                  max_hops: int = 2) -> list[dict]:
    """BFS over the ontology from the alerted account, assembling the ring as
    STRUCTURED OBJECTS. Deterministic and reproducible — a real AML system has a
    defined traversal procedure; this is it. Returns the touched objects."""
    seen: set[str] = set()
    touched: list[dict] = []
    frontier = [(account_id, 0)]
    seen.add(account_id)
    start = store.get_object("Account", account_id)
    if start:
        touched.append(start)

    while frontier:
        oid, hop = frontier.pop(0)
        if hop >= max_hops:
            continue
        for obj in store.get_linked_objects(oid):
            if obj["id"] in seen:
                continue
            seen.add(obj["id"])
            touched.append(obj)
            # Expand through the ring backbone: accounts, devices, AND transactions —
            # a transaction is the bridge between two accounts (mule -> beneficiary),
            # so we must walk through it to reach the counterpart account.
            # Customers/counterparties are leaves. max_hops bounds the explosion.
            if obj["type"] in ("Account", "Device", "Transaction"):
                frontier.append((obj["id"], hop + 1))
    return touched


def _ring_summary(touched: list[dict]) -> dict:
    """Cheap structured stats Python can assert on (no LLM needed)."""
    by_type: dict[str, int] = {}
    for o in touched:
        by_type[o["type"]] = by_type.get(o["type"], 0) + 1
    accounts = [o["id"] for o in touched if o["type"] == "Account"]
    devices = [o["id"] for o in touched if o["type"] == "Device"]
    return {"counts": by_type, "accounts": accounts, "devices": devices,
            "n_objects": len(touched)}


def _compact_objects(touched: list[dict], limit: int = 40) -> list[dict]:
    """Trim objects for the prompt: id, type, key properties, links. Still STRUCTURED
    (OAG) — not flattened text."""
    out = []
    for o in touched[:limit]:
        out.append({"type": o["type"], "id": o["id"],
                    "properties": o["properties"], "linked_ids": o["linked_ids"]})
    return out


DECIDE_PROMPT = """\
You are reviewing a potential AML fraud ring assembled from a bank's ontology.
Below are the STRUCTURED OBJECTS (accounts, transactions, devices, counterparties)
reachable from the alerted account, with their links.

Alert: {alert}
Ring objects (JSON): {objects}
Policy evidence: {policy}

Tasks:
1. Classify the typology: one of structuring, circular_layering, shared_device_ring, none.
2. Recommend exactly one disposition: CLEAR, ESCALATE, or FILE.
3. Justify in 2-3 sentences, CITING specific object_ids from the ring above.

Respond as STRICT JSON only:
{{"typology": "...", "recommendation": "CLEAR|ESCALATE|FILE",
  "rationale": "... cite object_ids ...", "cited_ids": ["..."]}}"""


def _parse_json_block(text: str) -> dict:
    """Pull the first JSON object out of a model response (8B often wraps it)."""
    text = (text or "").strip()
    start, depth = text.find("{"), 0
    if start == -1:
        return {}
    for i in range(start, len(text)):
        depth += (text[i] == "{") - (text[i] == "}")
        if depth == 0:
            try:
                return json.loads(text[start:i + 1])
            except json.JSONDecodeError:
                return {}
    return {}


def investigate(alert_id: str, store: OntologyStore | None = None,
                use_cache: bool = True) -> dict[str, Any]:
    """The hybrid hero pipeline. Python triages + traverses; Llama classifies the
    typology and decides CLEAR/ESCALATE/FILE over the structured objects. Returns
    a structured Investigation. Cites object_ids (enforced). Golden-cached per
    alert_id for demo stability (KTD-2)."""
    cache_file = CACHE_DIR / f"{alert_id}.json"
    if use_cache and cache_file.exists():
        result = json.loads(cache_file.read_text())
        result["source"] = "cached"
        return result

    store = store or OntologyStore()

    # [Python] triage: resolve the alerted account
    alert = store.get_object("Alert", alert_id)
    if not alert:
        raise ValueError(f"no such alert: {alert_id}")
    account_id = alert["properties"]["account_id"]

    # [Python] traverse the ring as structured objects
    touched = traverse_ring(store, account_id)
    summary = _ring_summary(touched)
    valid_ids = {o["id"] for o in touched}

    # [Evidence] policy lookup (search_policy degrades gracefully pre-U8)
    policy = _dispatch_tool("search_policy",
                            {"query": alert["properties"]["rule"]}, store)

    # [Llama] classify + decide over the STRUCTURED objects
    prompt = DECIDE_PROMPT.format(
        alert=json.dumps(alert["properties"], default=str),
        objects=json.dumps(_compact_objects(touched), default=str)[:9000],
        policy=json.dumps(policy, default=str)[:1500])
    resp = call_llama(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": prompt}], tools=None, store=store)
    decision = _parse_json_block(resp["message"].get("content", ""))

    # Enforce object_id citations: keep only ids that actually exist in the ring.
    cited = [i for i in decision.get("cited_ids", []) if i in valid_ids]
    rec = decision.get("recommendation", "ESCALATE").upper()
    if rec not in ("CLEAR", "ESCALATE", "FILE"):
        rec = "ESCALATE"

    result = {
        "alert_id": alert_id,
        "account_id": account_id,
        "objects_touched": [o["id"] for o in touched],
        "ring_summary": summary,
        "typology": decision.get("typology", "unknown"),
        "recommendation": rec,
        "rationale": decision.get("rationale", ""),
        "cited_ids": cited,
        "policy_citations": policy,
        "str_narrative": None,   # drafted in U9
        "source": "live",
    }

    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file.write_text(json.dumps(result, indent=2, default=str))
    return result
