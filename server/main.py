"""Praheri FastAPI layer — a thin wrapper over the existing Python engine.

Phase 0: health, alerts list, alert ring-graph (JSON), and the SSE streaming
spike. The engine (praheri/*) and the Streamlit console (app/streamlit_app.py)
are NOT touched — this server only imports and calls them.

State note: praheri.governance.PENDING, store.default_store(), and the audit log
are module-level singletons, so this app MUST run single-worker:
    uvicorn server.main:app --workers 1 --port 8000
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from praheri import agent, governance
from praheri.agent import LlamaUnavailable
from praheri.governance import Actor
from praheri.store import OntologyStore, _type_of
from server.models import ActionRequest, ApproveRequest
from server.serialize import graph_json
from server.str_prompt import build_str_messages
from server.stream import stream_chat

app = FastAPI(title="Praheri API", version="0.1")

# One store for the process (sqlite opened check_same_thread=False, so the
# threadpool is safe). Mirrors the engine's single-process demo posture.
_store = OntologyStore()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "model": agent.MODEL, "single_worker": True}


@app.get("/api/alerts")
def list_alerts() -> list[dict[str, Any]]:
    """Open alerts, highest-risk first (matches the Streamlit queue ordering)."""
    alerts = _store.query_objects("Alert")
    alerts.sort(key=lambda a: a["properties"]["score"], reverse=True)
    return alerts


@app.get("/api/alerts/{alert_id}/graph")
def alert_graph(alert_id: str) -> dict[str, Any]:
    """The fraud-ring graph as {nodes, edges}. Uses the cached investigation to
    scope the ring + glow the cited evidence nodes."""
    alert = _store.get_object("Alert", alert_id)
    if not alert:
        raise HTTPException(404, f"no such alert: {alert_id}")
    inv = agent.investigate(alert_id, store=_store, use_cache=True)
    ring_accounts = [i for i in inv["objects_touched"] if i.startswith("ACC-")]
    g = _store.build_graph(ring_accounts)
    return graph_json(g, highlight=inv.get("cited_ids", []))


@app.get("/api/alerts/{alert_id}/investigate")
def alert_investigate(alert_id: str) -> dict[str, Any]:
    """The full cached investigation dict (signals, typology, recommendation,
    rationale, cited_ids, policy_citations, str_narrative, source). Read-only —
    a thin pass-through of agent.investigate(); ALERT-R001 is golden-cached, so
    this returns instantly without touching Ollama."""
    if not _store.get_object("Alert", alert_id):
        raise HTTPException(404, f"no such alert: {alert_id}")
    return agent.investigate(alert_id, store=_store, use_cache=True)


@app.get("/api/objects/{object_id}")
def inspect_object(object_id: str) -> dict[str, Any]:
    """Drill-down: a single ontology object's real properties + linked ids.
    Proves the ontology is a queryable graph, not a chatbot. Read-only."""
    otype = _type_of(object_id)
    if not otype:
        raise HTTPException(404, f"unknown object id: {object_id}")
    obj = _store.get_object(otype, object_id)
    if not obj:
        raise HTTPException(404, f"no such object: {object_id}")
    return obj


@app.get("/api/alerts/{alert_id}/rag")
def alert_rag(alert_id: str) -> dict[str, Any]:
    """The RAG comparison answer (flattened text, links stripped). LIVE and
    UNCACHED by design — the contrast with OAG is the point. 503 if Ollama down."""
    if not _store.get_object("Alert", alert_id):
        raise HTTPException(404, f"no such alert: {alert_id}")
    try:
        return agent.investigate_rag(alert_id, store=_store)
    except LlamaUnavailable as e:
        raise HTTPException(503, str(e))


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/api/ask/stream")
def ask_stream(q: str) -> StreamingResponse:
    """SPIKE: stream Llama tokens to the browser over SSE. Proves the live
    token feed end-to-end (Ollama -> FastAPI -> EventSource)."""
    def gen():
        messages = [{"role": "user", "content": q}]
        try:
            for tok in stream_chat(messages):
                yield _sse("token", {"t": tok})
            yield _sse("done", {"ok": True})
        except LlamaUnavailable as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


# --------------------------------------------------------- governance loop (P3)
# The model never writes data — all mutations route through governance @actions.
# This layer only CALLS them and builds the Actor from the request role; the
# engine enforces the role gate. State (PENDING, audit log, praheri.db) is
# module-global => single worker only.
_ACTIONS = {
    "clear_alert": governance.clear_alert,
    "escalate_alert_to_case": governance.escalate_alert_to_case,
    "request_account_freeze": governance.request_account_freeze,
    "file_str": governance.file_str,
}


@app.post("/api/actions/{name}")
def run_action(name: str, body: ActionRequest) -> dict[str, Any]:
    """Invoke a governed AML action. Low-stakes execute immediately; high-stakes
    return PENDING_APPROVAL and land in the MLRO queue."""
    fn = _ACTIONS.get(name)
    if not fn:
        raise HTTPException(404, f"unknown action: {name}")
    actor = Actor(id=f"demo_{body.role}", role=body.role)
    try:
        return fn(actor, **body.params)
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.get("/api/approvals")
def list_approvals() -> list[dict[str, Any]]:
    return governance.PENDING.list_pending()


@app.post("/api/approvals/{ref}/approve")
def approve_action(ref: str, body: ApproveRequest) -> dict[str, Any]:
    """MLRO approves a pending action; it executes and is audited."""
    actor = Actor(id=f"demo_{body.role}", role=body.role)
    try:
        return governance.approve(ref, actor)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.get("/api/audit")
def get_audit() -> list[dict[str, Any]]:
    return governance.read_audit()


@app.get("/api/alerts/{alert_id}/str/stream")
def str_stream(alert_id: str) -> StreamingResponse:
    """Stream a freshly-drafted STR token-by-token. The prompt is built from the
    cached structured investigation (typology + cited ids + rationale), so the
    narrative is grounded in real object_ids. Engine zero-diff — uses stream_chat
    over agent constants, never agent.call_llama."""
    if not _store.get_object("Alert", alert_id):
        raise HTTPException(404, f"no such alert: {alert_id}")
    inv = agent.investigate(alert_id, store=_store, use_cache=True)
    messages = build_str_messages(inv)

    def gen():
        try:
            for tok in stream_chat(messages):
                yield _sse("token", {"t": tok})
            yield _sse("done", {"ok": True})
        except LlamaUnavailable as e:
            yield _sse("error", {"message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })
