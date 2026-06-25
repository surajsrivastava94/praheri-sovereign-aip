"""U4 tests — call_llama drives a real tool-calling loop against local Llama.

These are INTEGRATION tests: they hit the live Ollama endpoint. Skipped if it's
not reachable so the suite stays green offline, but the demo path requires them.
"""
import json

import pytest
import requests

from praheri import agent
from praheri.store import OntologyStore


def _ollama_up() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2).raise_for_status()
        return True
    except Exception:
        return False


live = pytest.mark.skipif(not _ollama_up(), reason="Ollama not running")


@live
def test_agent_calls_read_tool_and_returns_structured_objects():
    """The core OAG claim: asked to investigate a ring account, the model issues a
    read tool call and gets real structured objects back (not invented text)."""
    store = OntologyStore()
    messages = [
        {"role": "system", "content": agent.SYSTEM_PROMPT},
        {"role": "user", "content": "Investigate account ACC-DEV-01. "
         "Use get_linked_objects to pull its linked objects before answering."},
    ]
    out = agent.call_llama(messages, agent.TOOLS, store=store)
    assert out["trace"], "model made no tool calls"
    tools_used = {t["tool"] for t in out["trace"]}
    assert "get_linked_objects" in tools_used or "query_objects" in tools_used
    # at least one call returned real linked objects
    assert any(t["result_count"] > 0 for t in out["trace"])


@live
def test_loop_terminates_with_final_message():
    store = OntologyStore()
    out = agent.call_llama(
        [{"role": "system", "content": agent.SYSTEM_PROMPT},
         {"role": "user", "content": "List two open alerts using query_objects."}],
        agent.TOOLS, store=store)
    assert out["message"].get("content") is not None  # got a final answer


def test_bogus_link_type_does_not_crash_dispatch():
    """The model fabricated link_type='transactions' in the probe — dispatch must cope."""
    store = OntologyStore()
    result = agent._dispatch_tool(
        "get_linked_objects", {"object_id": "ACC-MULE-01", "link_type": "transactions"}, store)
    assert isinstance(result, list)  # normalised, not an exception


def test_unknown_tool_returns_error_not_raise():
    store = OntologyStore()
    result = agent._dispatch_tool("nonexistent_tool", {}, store)
    assert isinstance(result, dict) and "error" in result


def test_ollama_unreachable_raises_clean_error(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("refused")
    monkeypatch.setattr(agent.requests, "post", boom)
    with pytest.raises(agent.LlamaUnavailable):
        agent._post([{"role": "user", "content": "hi"}], None)
