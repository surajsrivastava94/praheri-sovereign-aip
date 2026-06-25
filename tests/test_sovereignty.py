"""U14 — the sovereignty claim is verifiable: no external egress in source."""
from praheri.sovereignty import scan_egress


def test_no_external_egress():
    rep = scan_egress()
    assert rep["ok"], f"external egress found: {rep['external_endpoints']}"
    # the only endpoints are the local Ollama ones
    assert all("11434" in e or "localhost" in e for e in rep["local_endpoints"])


def test_local_endpoints_present():
    rep = scan_egress()
    assert rep["local_endpoints"], "expected at least the local Ollama endpoint"
