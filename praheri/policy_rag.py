"""Policy/threshold retrieval (the evidence step). See BUILD_BIBLE.md §5.

Local Chroma store over policies/*.md so the agent grounds thresholds and
typologies in actual policy text. This is the ONE place text-RAG is appropriate
— for policy lookup, not for the entities (those come from the ontology as OAG).

Embeddings come from the LOCAL Ollama embed model (nomic-embed-text) — no network
egress, keeping the airplane-mode sovereignty story intact (U14).
"""
from __future__ import annotations

import re
from pathlib import Path

import chromadb
import requests
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

POLICY_DIR = Path("policies")
EMBED_MODEL = "nomic-embed-text"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"


class OllamaEmbedding(EmbeddingFunction):
    """Chroma embedding function backed by the local Ollama embed endpoint."""

    def __init__(self, model: str = EMBED_MODEL):
        self.model = model

    @staticmethod
    def name() -> str:
        return "ollama-nomic-embed-text"

    def __call__(self, input: Documents) -> Embeddings:
        r = requests.post(OLLAMA_EMBED_URL,
                          json={"model": self.model, "input": list(input)},
                          timeout=120)
        r.raise_for_status()
        return r.json()["embeddings"]


def _chunk_markdown(text: str, source: str) -> list[dict]:
    """Split a policy doc into chunks by '##' heading — each clause is one chunk."""
    parts = re.split(r"\n(?=##\s)", text)
    chunks = []
    for i, part in enumerate(parts):
        part = part.strip()
        if len(part) < 20:
            continue
        chunks.append({"id": f"{source}::{i}", "text": part, "source": source})
    return chunks


class PolicyStore:
    def __init__(self, collection: str = "aml_policy"):
        self.client = chromadb.Client()
        self.embed = OllamaEmbedding()
        # get_or_create so re-init is idempotent within a process
        self.collection = self.client.get_or_create_collection(
            name=collection, embedding_function=self.embed)

    def ingest(self, folder: Path = POLICY_DIR) -> int:
        """Chunk + embed every .md in folder. Idempotent (upsert by id). Returns count."""
        chunks: list[dict] = []
        for md in sorted(Path(folder).glob("*.md")):
            chunks.extend(_chunk_markdown(md.read_text(), md.name))
        if not chunks:
            return 0
        self.collection.upsert(
            ids=[c["id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[{"source": c["source"]} for c in chunks],
        )
        return len(chunks)

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Return top-k policy snippets {source, text, score}."""
        if self.collection.count() == 0:
            self.ingest()
        res = self.collection.query(query_texts=[query], n_results=k)
        out = []
        for text, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                                    res["distances"][0]):
            out.append({"source": meta["source"], "text": text,
                        "score": round(1.0 - dist, 3)})  # cosine sim-ish
        return out


# Module-level singleton wired as the agent's search_policy tool.
_STORE: PolicyStore | None = None


def search_policy(query: str) -> list[dict]:
    """Retrieve relevant AML policy/threshold/typology clauses (top-3)."""
    global _STORE
    if _STORE is None:
        _STORE = PolicyStore()
        _STORE.ingest()
    return _STORE.search(query, k=3)
