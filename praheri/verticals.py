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
    """A typology check to run. `id` dispatches to a detector in vertical_engine;
    `params` tunes that detector (hub/member types, thresholds) for this vertical."""
    id: str                        # e.g. "shared_attribute_ring" (detector id)
    label: str                     # e.g. "Shared-garage ring"
    why: str                       # plain-English explanation shown in the UI
    params: dict = {}              # detector-specific knobs (e.g. {"hub_type":"Garage"})


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


# --------------------------------------------------------------------------- #
# Cartridge definitions. Each vertical is just data. The engine never changes. #
# --------------------------------------------------------------------------- #

PROCUREMENT = register(VerticalConfig(
    key="procurement",
    name="Procurement — Maverick Spend",
    icon="📦",
    accent_color="#6554C0",
    tagline="Same engine, a non-financial ontology — the platform thesis, proven.",
    regulator="Internal controls · DoA policy",
    object_types=[
        ObjectTypeSpec(name="Requisition", icon="📝", color="#6554C0",
                       key_props=["amount", "description", "status"]),
        ObjectTypeSpec(name="Vendor", icon="🏭", color="#FFAB00",
                       key_props=["name", "country", "risk_rating"]),
        ObjectTypeSpec(name="Budget", icon="💰", color="#36B37E",
                       key_props=["department", "cap", "spent", "remaining"]),
    ],
    link_types=["from_vendor", "against_budget"],
    kpi_cards=[
        KPI(label="Open requisitions", value="2"),
        KPI(label="Budget cap (IT)", value="₹5,00,000"),
        KPI(label="Over-budget POs", value="1", delta="needs MLRO"),
    ],
    signals=[],  # procurement gate is a budget rule, not a fraud-ring typology
    actions=[ActionSpec(id="approve_purchase_order", label="Submit PO",
                        requires_approval=True)],
    sample_data_path="data/verticals/procurement.json",
    golden_cache_key="procurement",
))


INSURANCE_SIU = register(VerticalConfig(
    key="insurance_siu",
    name="Insurance — Claims Fraud (SIU)",
    icon="🛡",
    accent_color="#FF5630",
    tagline="Staged-accident rings, same graph engine as AML — different nouns.",
    regulator="IRDAI · DPDP Act 2023",
    object_types=[
        ObjectTypeSpec(name="Claim", icon="📄", color="#FF5630",
                       key_props=["amount", "type", "status"]),
        ObjectTypeSpec(name="Garage", icon="🔧", color="#FFAB00",
                       key_props=["name", "city", "empanelled"]),
        ObjectTypeSpec(name="Claimant", icon="👤", color="#4C9AFF",
                       key_props=["name", "phone"]),
        ObjectTypeSpec(name="Policy", icon="📋", color="#998DD9",
                       key_props=["sum_insured", "product"]),
    ],
    link_types=["serviced_by", "filed_by", "under_policy", "raised_on"],
    kpi_cards=[
        KPI(label="Open SIU cases", value="1", delta="₹5.6L exposure"),
        KPI(label="Claims in ring", value="6"),
        KPI(label="Suspect garages", value="1"),
    ],
    signals=[SignalSpec(
        id="shared_attribute_ring", label="Shared-garage ring",
        why="Many ostensibly unrelated claims routed through one non-empanelled garage.",
        params={"hub_type": "Garage", "min_members": 5,
                "typology": "shared_garage_ring"})],
    actions=[ActionSpec(id="refer_to_siu", label="Refer to SIU",
                        requires_approval=True)],
    sample_data_path="data/verticals/insurance.json",
    golden_cache_key="insurance_siu",
))


LENDING_EWS = register(VerticalConfig(
    key="lending_ews",
    name="Lending — Early Warning Signals",
    icon="🏦",
    accent_color="#00B8D9",
    tagline="Predict NPA stress before DPD — common-director contagion + EMI bounces.",
    regulator="RBI EWS (>₹5 Cr) · Digital Lending 2022",
    object_types=[
        ObjectTypeSpec(name="Borrower", icon="🏢", color="#00B8D9",
                       key_props=["name", "rating"]),
        ObjectTypeSpec(name="Loan", icon="💳", color="#36B37E",
                       key_props=["exposure", "dpd"]),
        ObjectTypeSpec(name="Director", icon="👔", color="#FFAB00",
                       key_props=["name", "din"]),
        ObjectTypeSpec(name="Inflow", icon="💧", color="#998DD9",
                       key_props=["amount", "kind"]),
    ],
    link_types=["governed_by", "lent_to", "credited_to", "raised_on"],
    kpi_cards=[
        KPI(label="Stressed exposures", value="₹5 Cr"),
        KPI(label="Borrowers in cluster", value="5"),
        KPI(label="Common directors", value="1", delta="contagion hub"),
    ],
    signals=[
        SignalSpec(id="shared_attribute_ring", label="Common-director cluster",
                   why="Multiple borrowers governed by one director — correlated stress.",
                   params={"hub_type": "Director", "min_members": 5,
                           "typology": "common_director_cluster"}),
        SignalSpec(id="threshold_cluster", label="EMI-bounce stress",
                   why="A borrower receiving many sub-threshold partial EMIs — distress.",
                   params={"member_type": "Borrower", "link_type": "credited_to_in",
                           "amount_prop": "amount", "threshold": 10_000,
                           "min_count": 5, "typology": "emi_bounce_stress"}),
    ],
    actions=[
        ActionSpec(id="margin_call", label="Issue margin call",
                   requires_approval=True),
        ActionSpec(id="downgrade_rating", label="Downgrade rating",
                   requires_approval=True),
    ],
    sample_data_path="data/verticals/lending.json",
    golden_cache_key="lending_ews",
))
