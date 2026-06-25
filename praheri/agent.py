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

ASK_SYSTEM = """\
You are Praheri, an AML investigation copilot. Answer the analyst's question by
READING the ontology with your tools (query_objects, get_linked_objects,
search_policy). Always call a tool to ground your answer in real objects before
responding. Cite object_ids. Never invent data.
"""


def flatten_to_text(touched: list[dict]) -> str:
    """Flatten structured objects into naive text chunks with LINKS STRIPPED — what
    a plain text-RAG system would feed the model. This is the OAG-vs-RAG handicap:
    same facts, but the relationships (who sent to whom, shared device) are gone, so
    the model can't traverse the ring. Used for the side-by-side demo (U13)."""
    lines = []
    for o in touched:
        p = o["properties"]
        if o["type"] == "Account":
            lines.append(f"Account {o['id']} is a {p.get('type','')} account at "
                         f"{p.get('branch','')} with balance {p.get('balance','')}.")
        elif o["type"] == "Transaction":
            lines.append(f"There was a transaction of {p.get('amount','')} "
                         f"{p.get('currency','')} via {p.get('channel','')}.")
        elif o["type"] == "Device":
            lines.append(f"A device with IP {p.get('ip','')} was seen.")
        elif o["type"] == "Customer":
            lines.append(f"Customer {p.get('name','')} has KYC rating "
                         f"{p.get('kyc_risk_rating','')}.")
    # Shuffle-free but link-free: the model sees facts, not the graph.
    return "\n".join(lines)


RAG_PROMPT = """\
You are an AML analyst. Based ONLY on these case notes, is there a fraud ring, and
what is the typology? Recommend CLEAR, ESCALATE, or FILE in 2-3 sentences.

Case notes:
{notes}"""


def investigate_rag(alert_id: str, store: OntologyStore | None = None) -> dict[str, Any]:
    """The RAG comparison path: same ring, flattened to text (links stripped). Shows
    why OAG wins — the model gets facts but cannot reconstruct the relationships."""
    store = store or OntologyStore()
    alert = store.get_object("Alert", alert_id)
    if not alert:
        raise ValueError(f"no such alert: {alert_id}")
    touched = traverse_ring(store, alert["properties"]["account_id"])
    notes = flatten_to_text(touched)[:6000]
    resp = call_llama(
        [{"role": "system", "content": "You are an AML analyst working from text notes."},
         {"role": "user", "content": RAG_PROMPT.format(notes=notes)}],
        tools=None, store=store)
    return {"answer": (resp["message"].get("content") or "").strip(), "mode": "RAG"}


def ask(question: str, store: OntologyStore | None = None) -> dict[str, Any]:
    """Free-form analyst Q&A — a GENUINE model-driven tool-calling loop (KTD-1).
    Unlike investigate() (Python-orchestrated), here Llama itself decides which
    tools to call. Returns {answer, trace} so the UI can show the live tool calls.
    """
    store = store or OntologyStore()
    out = call_llama(
        [{"role": "system", "content": ASK_SYSTEM},
         {"role": "user", "content": question}],
        tools=TOOLS, store=store)
    return {"answer": out["message"].get("content", ""), "trace": out["trace"]}


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


# Threshold for "structuring" sub-threshold deposits — mirrors generate + policy.
STRUCTURING_THRESHOLD = 50_000


def compute_signals(store: OntologyStore, account_id: str,
                    touched: list[dict]) -> list[dict]:
    """[Python] Deterministically detect typology signatures over the ring objects.

    This is the engine half of the hybrid (KTD-1): a real AML system computes the
    rule hits — it does not hand an analyst raw rows and hope they spot the pattern.
    The 8B model reliably *confirms and narrates* a computed signal, but is unreliable
    at *deriving* it (e.g. aggregating that each sender is a mule fed by sub-threshold
    deposits). We compute; the model judges. Each signal cites real object_ids.
    """
    signals: list[dict] = []
    ring_accounts = {o["id"] for o in touched if o["type"] == "Account"}
    devices = [o for o in touched if o["type"] == "Device"]

    # --- Signal A: structuring / smurfing -------------------------------------
    # Query the store directly for each ring account's sub-threshold inbound
    # deposits — these sit beyond the traversal horizon, so we must look them up,
    # not rely on what BFS happened to reach.
    mules: dict[str, list[str]] = {}
    for acct in ring_accounts:
        deposits = [t["id"] for t in store.query_objects("Transaction", to_account=acct)
                    if t["properties"]["amount"] < STRUCTURING_THRESHOLD]
        if len(deposits) >= 5:
            mules[acct] = deposits
    if mules:
        evidence = sorted(mules)[:6]
        sample_txns = [tid for tids in list(mules.values())[:3] for tid in tids[:2]]
        signals.append({
            "typology": "structuring",
            "detail": f"{len(mules)} mule account(s) each received >=5 sub-"
                      f"INR{STRUCTURING_THRESHOLD:,} deposits then funnelled lumps onward "
                      f"— classic smurfing.",
            "evidence_ids": evidence + sample_txns,
        })

    # --- Signal B: circular layering ------------------------------------------
    # Gather ALL transactions among the ring accounts (query, don't depend on BFS
    # depth) and detect a directed cycle (A->B->C->A).
    edges: set[tuple[str, str]] = set()
    for acct in ring_accounts:
        for t in store.query_objects("Transaction", from_account=acct):
            to = t["properties"]["to_account"]
            if to in ring_accounts:
                edges.add((acct, to))
    if len(ring_accounts) >= 3 and _has_cycle(edges, ring_accounts):
        cycle_nodes = sorted({a for e in edges for a in e})[:6]
        signals.append({
            "typology": "circular_layering",
            "detail": "Funds move in a closed loop among these accounts "
                      "(A->B->C->A) with little economic substance.",
            "evidence_ids": cycle_nodes,
        })

    # --- Signal C: shared-device ring -----------------------------------------
    for d in devices:
        users = d["linked_ids"].get("used_by", [])
        if len(users) >= 5:
            signals.append({
                "typology": "shared_device_ring",
                "detail": f"{len(users)} ostensibly unrelated accounts transact from "
                          f"one device ({d['id']}) — linked-identity ring.",
                "evidence_ids": [d["id"]] + sorted(users)[:8],
            })

    # Lead with the most distinctive typology so the headline matches the demo beat.
    _priority = {"shared_device_ring": 0, "structuring": 1, "circular_layering": 2}
    signals.sort(key=lambda s: _priority.get(s["typology"], 9))
    return signals


def _has_cycle(edges: set[tuple[str, str]], nodes: set[str]) -> bool:
    """True if a directed cycle exists within `nodes` given `edges`."""
    adj: dict[str, list[str]] = {}
    for a, b in edges:
        if a in nodes and b in nodes:
            adj.setdefault(a, []).append(b)
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}

    def dfs(n: str) -> bool:
        color[n] = GREY
        for m in adj.get(n, []):
            if color[m] == GREY:
                return True
            if color[m] == WHITE and dfs(m):
                return True
        color[n] = BLACK
        return False

    return any(color[n] == WHITE and dfs(n) for n in nodes)


DECIDE_PROMPT = """\
You are reviewing a potential AML fraud ring assembled from a bank's ontology.

The bank's detection engine has ALREADY COMPUTED the following typology signals
from the structured objects (these are confirmed rule hits, not speculation):

DETECTED SIGNALS:
{signals}

Supporting ring objects (JSON, for reference): {objects}
Policy evidence: {policy}

Your job is to CONFIRM and NARRATE these signals — not to re-derive them. The
signals above are computed facts; treat them as established evidence.

Tasks:
1. State the typology (use the detected signal; if multiple, pick the strongest).
2. Recommend a disposition: FILE if a signal clearly matches a money-laundering
   typology, ESCALATE if signals are weak/ambiguous, CLEAR only if no signal fired.
3. Justify in 2-3 sentences, CITING the specific object_ids from the signals.

Respond as STRICT JSON only:
{{"typology": "...", "recommendation": "CLEAR|ESCALATE|FILE",
  "rationale": "... cite object_ids ...", "cited_ids": ["..."]}}"""


STR_PROMPT = """\
Draft a concise Suspicious Transaction Report (STR) narrative for a compliance file.

Typology: {typology}
Detected signals: {signals}
Matched policy clause: {policy}
Key object_ids (cite these): {cited}

Write 4-6 sentences in formal regulatory tone. You MUST:
- Describe the suspicious pattern factually.
- Cite the specific object_ids (accounts, transactions, devices) as evidence.
- Reference the matched policy/typology by name.
- State why the activity lacks apparent lawful purpose.
Do NOT invent ids or evidence beyond those listed. Do NOT mention tool names,
internal function names, or "not specified" placeholders. Output the narrative
text only (no preamble, no 'Propose' line)."""


def _draft_str_narrative(typology: str, signals: list[dict], policy: list[dict],
                         cited: list[str], store: OntologyStore) -> str:
    """[Llama] Draft the STR narrative grounded in cited object_ids + policy clause."""
    signal_text = "; ".join(s["detail"] for s in signals) or "n/a"
    policy_text = policy[0]["text"][:600] if policy else "n/a"
    prompt = STR_PROMPT.format(
        typology=typology, signals=signal_text, policy=policy_text,
        cited=", ".join(cited[:12]))
    resp = call_llama(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": prompt}], tools=None, store=store)
    return (resp["message"].get("content") or "").strip()


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

    # [Python] deterministically detect typology signals (the engine half of KTD-1)
    signals = compute_signals(store, account_id, touched)

    # [Evidence] policy lookup (search_policy degrades gracefully pre-U8)
    policy = _dispatch_tool("search_policy",
                            {"query": alert["properties"]["rule"]}, store)

    # [Llama] confirm + narrate over the COMPUTED signals + structured objects
    signal_text = "\n".join(
        f"- [{s['typology']}] {s['detail']} (object_ids: {', '.join(s['evidence_ids'])})"
        for s in signals) or "- No typology signals fired."
    prompt = DECIDE_PROMPT.format(
        signals=signal_text,
        objects=json.dumps(_compact_objects(touched), default=str)[:6000],
        policy=json.dumps(policy, default=str)[:1500])
    resp = call_llama(
        [{"role": "system", "content": SYSTEM_PROMPT},
         {"role": "user", "content": prompt}], tools=None, store=store)
    decision = _parse_json_block(resp["message"].get("content", ""))

    # Enforce object_id citations: keep only ids that actually exist in the ring.
    cited = [i for i in decision.get("cited_ids", []) if i in valid_ids]
    # Always include the signal evidence ids so the narrative is grounded even if
    # the model under-cites.
    signal_ids = [i for s in signals for i in s["evidence_ids"] if i in valid_ids]
    cited = list(dict.fromkeys(cited + signal_ids))[:12]

    rec = decision.get("recommendation", "ESCALATE").upper()
    if rec not in ("CLEAR", "ESCALATE", "FILE"):
        rec = "ESCALATE"
    # Deterministic floor: a fired signal is a confirmed typology — never CLEAR it,
    # and a strong signal warrants FILE. The model can escalate FILE->ESCALATE in
    # ambiguity but cannot downgrade a real ring to CLEAR (golden rule #4 posture).
    typology = signals[0]["typology"] if signals else decision.get("typology", "none")
    if signals and rec == "CLEAR":
        rec = "FILE"

    # [Llama] draft the STR narrative when the case warrants filing/escalation (U9).
    str_narrative = None
    if rec in ("FILE", "ESCALATE") and signals:
        str_narrative = _draft_str_narrative(typology, signals, policy, cited, store)

    result = {
        "alert_id": alert_id,
        "account_id": account_id,
        "objects_touched": [o["id"] for o in touched],
        "ring_summary": summary,
        "signals": signals,
        "typology": typology,
        "recommendation": rec,
        "rationale": decision.get("rationale", ""),
        "cited_ids": cited,
        "policy_citations": policy,
        "str_narrative": str_narrative,
        "source": "live",
    }

    if use_cache:
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file.write_text(json.dumps(result, indent=2, default=str))
    return result
