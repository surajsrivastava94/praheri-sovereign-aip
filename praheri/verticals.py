"""Vertical cartridges — the config that turns the engine into a new sector.

This is the load-bearing file for the "Sovereign AIP OS" thesis (see
docs/superpowers/specs/2026-06-28-praheri-multi-vertical-os-design.md). The
engine (traverse -> detect signals -> decide -> govern -> audit) never changes;
a new vertical swaps three things, all captured here as a VerticalConfig:

  1. the ontology   -> object_types + link_types (the nouns and how they link)
  2. the signals    -> SignalSpec list (the typology checks to run)
  3. the actions    -> ActionSpec list (the governed actions a human approves)

plus theming/copy and pointers to its synthetic data + golden-cached narrative.

AML stays bespoke (praheri/agent.py + the AML tab) and does NOT use this file.
These cartridges drive the shallow verticals via the shared render_vertical().
"""
from __future__ import annotations

from pydantic import BaseModel


class ObjectTypeSpec(BaseModel):
    """One ontology noun and how it should look in the ring graph."""
    name: str                      # e.g. "Claim"
    icon: str = "•"                # node glyph hint
    color: str = "#4C9AFF"         # node colour in the ring graph
    key_props: list[str] = []      # properties surfaced on the object card


class SignalSpec(BaseModel):
    """A typology check to run. `id` dispatches to a detector in vertical_engine."""
    id: str                        # e.g. "shared_attribute_ring" (detector id)
    label: str                     # e.g. "Shared-garage ring"
    why: str                       # plain-English explanation shown in the UI


class ActionSpec(BaseModel):
    """A governed action. High-stakes ones route to the MLRO approval queue."""
    id: str                        # e.g. "refer_to_siu"
    label: str                     # button label
    requires_approval: bool = False


class KPI(BaseModel):
    """A headline metric card for the sector hero band."""
    label: str                     # e.g. "₹ at risk"
    value: str                     # e.g. "₹4.2 Cr"
    delta: str | None = None


class VerticalConfig(BaseModel):
    """One swappable cartridge. The shared renderer + Platform dashboard read this."""
    # identity / theming
    key: str                       # stable slug, e.g. "insurance_siu"
    name: str                      # e.g. "Insurance — Claims Fraud (SIU)"
    icon: str                      # e.g. "🛡"
    accent_color: str              # hex — drives KPI cards + ring-graph palette
    tagline: str                   # sector hero copy
    regulator: str                 # e.g. "IRDAI · DPDP Act 2023" — shown as a chip

    # ontology cartridge
    object_types: list[ObjectTypeSpec]
    link_types: list[str]

    # domain content
    kpi_cards: list[KPI] = []
    signals: list[SignalSpec] = []
    actions: list[ActionSpec] = []

    # demo data + cached narrative
    sample_data_path: str = ""     # synthetic objects for this vertical
    golden_cache_key: str = ""     # narrative cache namespace (per vertical)


# The cartridge registry. Populated as verticals are built (U4-U6); the Platform
# dashboard (U8) derives its live counters from exactly this dict, so the counts
# can never drift from what is actually wired.
REGISTRY: dict[str, VerticalConfig] = {}


def register(config: VerticalConfig) -> VerticalConfig:
    """Add a cartridge to the registry (idempotent on key). Returns it for reuse."""
    REGISTRY[config.key] = config
    return config


def get_config(key: str) -> VerticalConfig:
    """Look up a cartridge by key. Raises KeyError if absent (fail fast)."""
    return REGISTRY[key]
