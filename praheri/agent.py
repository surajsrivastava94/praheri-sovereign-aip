"""Llama investigation pipeline. See BUILD_BIBLE.md §5.

A PIPELINE, not a swarm: one Llama instance does tool-calling across
triage -> investigate (OAG traversal) -> evidence (RAG) -> decide + draft STR.
Model = Llama via Ollama's OpenAI-compatible API. The model never writes data;
it only PROPOSES actions through governance.

TODO(playbook steps 2.1, 2.2, 4.2): implement call_llama + investigate.
"""
from __future__ import annotations

import json
from typing import Any

import requests

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
MODEL = "llama3.1:8b"  # keep in sync with governance.MODEL_NAME

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


def call_llama(messages: list[dict], tools: list[dict] | None = None) -> dict:
    """POST to the local Ollama OpenAI-compatible endpoint. TODO: implement +
    handle the tool-call loop (execute requested tools via store/policy_rag,
    feed results back until the model returns a final answer)."""
    raise NotImplementedError


def investigate(alert_id: str) -> dict[str, Any]:
    """Run the full pipeline for one alert and return a structured Investigation:
    {objects_touched, ring_summary, policy_citations, recommendation, str_narrative}.
    Enforce object_id citations. TODO(playbook 2.2 + 4.2)."""
    raise NotImplementedError
