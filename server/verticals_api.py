"""Vertical-cartridge helpers for the FastAPI layer.

Lives in server/ — the engine stays frozen. Re-implements the root-id resolution
that lives inside app/streamlit_app.py (which must NOT be imported) from the
verified contract, and memoizes a GenericOntologyStore per vertical key (the data
is static).
"""
from __future__ import annotations

import json
from typing import Any

from praheri.verticals import get_config
from praheri.vertical_store import GenericOntologyStore

_STORES: dict[str, GenericOntologyStore] = {}


def get_store(key: str) -> GenericOntologyStore:
    """Memoized store for a vertical. Raises FileNotFoundError if the cartridge's
    synthetic data hasn't been generated (`python -m praheri.generate_verticals`)."""
    if key not in _STORES:
        config = get_config(key)  # raises KeyError on unknown key
        data = json.loads(open(config.sample_data_path).read())
        _STORES[key] = GenericOntologyStore(data)
    return _STORES[key]


def root_id_for(alert: dict[str, Any]) -> str:
    """The investigation entry point for a vertical alert: the `raised_on` link
    (a list) or the `root_id` property. Mirrors the Streamlit render_vertical logic."""
    root = alert.get("linked_ids", {}).get("raised_on") or \
        alert.get("properties", {}).get("root_id", "")
    if isinstance(root, list):
        root = root[0] if root else ""
    return root
