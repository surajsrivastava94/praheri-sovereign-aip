"""Token-streaming helper for Ollama (the new capability the Streamlit console
lacked). Lives in server/ and imports the endpoint/model constants from
praheri.agent READ-ONLY — agent.call_llama is never touched, so the AML hero
pipeline stays byte-for-byte the demo fallback.

Ollama's /v1/chat/completions with stream:True emits Server-Sent-Events-style
lines: `data: {json}\n` per chunk, ending with `data: [DONE]`. Each chunk carries
choices[0].delta.content (the new token(s))."""
from __future__ import annotations

import json
from typing import Any, Iterator

import requests

from praheri.agent import MODEL, OLLAMA_URL, REQUEST_TIMEOUT, LlamaUnavailable


def stream_chat(messages: list[dict[str, Any]]) -> Iterator[str]:
    """Yield content tokens from Ollama as they arrive. Raises LlamaUnavailable
    if the connection fails before any token (caller decides the fallback)."""
    payload = {"model": MODEL, "messages": messages, "stream": True}
    try:
        with requests.post(OLLAMA_URL, json=payload, stream=True,
                           timeout=REQUEST_TIMEOUT) as r:
            r.raise_for_status()
            for raw in r.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                if line.startswith("data: "):
                    line = line[6:]
                if line.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                tok = delta.get("content")
                if tok:
                    yield tok
    except requests.RequestException as e:
        raise LlamaUnavailable(f"Ollama stream failed: {e}") from e
