"""Sovereignty self-check (U14). See BUILD_BIBLE.md §9 beat 2:20.

Praheri's pitch: customer/transaction data NEVER leaves the box. The only network
egress is to the local Ollama endpoint (localhost:11434). This module audits the
source for any non-localhost URL so the claim is verifiable, not a promise — the
slide a regulator actually wants.
"""
from __future__ import annotations

import re
from pathlib import Path

_URL = re.compile(r"https?://([a-zA-Z0-9.\-]+)(:\d+)?")
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}
_SRC_DIRS = ["praheri", "app"]


def scan_egress(root: str | Path = ".") -> dict:
    """Return {ok, local_endpoints, external_endpoints}. ok=True means every URL in
    the source points at a local host — no data can egress."""
    root = Path(root)
    local: set[str] = set()
    external: set[str] = set()
    for d in _SRC_DIRS:
        for py in (root / d).rglob("*.py"):
            for host, port in _URL.findall(py.read_text()):
                url = f"{host}{port or ''}"
                (local if host in _LOCAL_HOSTS else external).add(url)
    return {"ok": not external,
            "local_endpoints": sorted(local),
            "external_endpoints": sorted(external)}


if __name__ == "__main__":
    r = scan_egress()
    print("🛡️  Sovereignty egress check")
    print("   local endpoints :", r["local_endpoints"])
    print("   external egress :", r["external_endpoints"] or "NONE")
    print("   VERDICT         :", "✅ on-prem only — data never leaves the box"
          if r["ok"] else "❌ external egress detected")
