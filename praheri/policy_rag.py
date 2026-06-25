"""Policy/threshold retrieval (the evidence step). See BUILD_BIBLE.md §5.

Small Chroma store over policies/*.md so the agent grounds thresholds and
typologies in actual policy text. This is the ONE place text-RAG is appropriate
— for policy lookup, not for the entities (those come from the ontology as OAG).

TODO(playbook step 4.1): implement.
"""
from __future__ import annotations

from pathlib import Path

POLICY_DIR = Path("policies")


class PolicyStore:
    def __init__(self, collection: str = "aml_policy"):
        # TODO: init chromadb client + collection
        ...

    def ingest(self, folder: Path = POLICY_DIR) -> int:
        """Chunk + embed every .md in folder. Return count. TODO."""
        raise NotImplementedError

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Return top-k policy snippets {source, text, score}. TODO."""
        raise NotImplementedError


def search_policy(query: str) -> list[dict]:
    """Module-level helper wired as the agent's search_policy tool. TODO."""
    raise NotImplementedError
