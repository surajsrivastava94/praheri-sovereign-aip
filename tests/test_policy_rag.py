"""U8 tests — local policy RAG retrieves the right clause per typology query.

Live (needs Ollama for embeddings); skipped offline.
"""
import pytest
import requests

from praheri import policy_rag


def _ollama_up() -> bool:
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2).raise_for_status()
        return True
    except Exception:
        return False


live = pytest.mark.skipif(not _ollama_up(), reason="Ollama not running")


@pytest.fixture(scope="module")
def store():
    s = policy_rag.PolicyStore(collection="test_aml_policy")
    n = s.ingest()
    assert n >= 3, f"expected >=3 policy chunks, got {n}"
    return s


@live
def test_structuring_query_retrieves_structuring_clause(store):
    hits = store.search("many sub-threshold cash deposits to several accounts", k=3)
    assert hits
    joined = " ".join(h["text"].lower() for h in hits)
    assert "structuring" in joined or "smurfing" in joined


@live
def test_circular_query_retrieves_layering_clause(store):
    hits = store.search("funds moved in a loop A to B to C to A", k=3)
    joined = " ".join(h["text"].lower() for h in hits)
    assert "layering" in joined or "circular" in joined


@live
def test_shared_device_query_retrieves_device_clause(store):
    hits = store.search("multiple accounts using the same device or IP", k=3)
    joined = " ".join(h["text"].lower() for h in hits)
    assert "device" in joined or "linked-identity" in joined


@live
def test_search_returns_scored_snippets(store):
    hits = store.search("reporting threshold", k=2)
    assert len(hits) <= 2
    for h in hits:
        assert set(h) == {"source", "text", "score"}


@live
def test_ingest_is_idempotent():
    s = policy_rag.PolicyStore(collection="test_idem")
    first = s.ingest()
    second = s.ingest()
    assert first == second
    assert s.collection.count() == first  # upsert, no duplicates
