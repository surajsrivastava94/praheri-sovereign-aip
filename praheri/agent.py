"""Llama investigation pipeline. See BUILD_BIBLE.md §5.

A PIPELINE, not a swarm: one Llama instance does tool-calling across
triage -> investigate (OAG traversal) -> evidence (RAG) -> decide + draft STR.
Model = Llama via Ollama's OpenAI-compatible API. The model never writes data;
it only PROPOSES actions through governance.

TODO(playbook steps 2.1, 2.2, 4.2): implement call_llama + investigate.
"""
from __future__ import annotations

import json
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


def investigate(alert_id: str) -> dict[str, Any]:
    """Run the full pipeline for one alert and return a structured Investigation:
    {objects_touched, ring_summary, policy_citations, recommendation, str_narrative}.
    Enforce object_id citations. TODO(playbook 2.2 + 4.2)."""
    raise NotImplementedError
