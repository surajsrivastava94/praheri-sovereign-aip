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
    use_case: str = ""             # plain-English real-world problem (for a cold reader)
    what_you_see: str = ""         # one line: what to watch happen on this tab

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


def platform_counters() -> dict[str, int]:
    """Live counters for the Platform dashboard, derived from REGISTRY so they can
    never drift from what is actually wired. `+1` ontology is AML — the bespoke
    hero that is NOT a cartridge but is still a sector the one engine serves."""
    return {
        "ontologies": len(REGISTRY) + 1,
        "object_types": sum(len(c.object_types) for c in REGISTRY.values()),
        "link_types": sum(len(c.link_types) for c in REGISTRY.values()),
        "actions": sum(len(c.actions) for c in REGISTRY.values()),
    }


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
    use_case=("Enterprises lose margin and invite collusion when staff buy "
              "off-contract or split orders to dodge approval limits. The same "
              "engine checks each requisition against budget and the "
              "Delegation-of-Authority matrix — a completely different ontology, "
              "zero engine code changed."),
    what_you_see=("Below: open purchase requisitions. Submitting one that exceeds "
                  "the remaining budget is routed to the MLRO approval queue — the "
                  "exact same governance gate as an AML account freeze."),
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
    use_case=("A single insurance claim looks legitimate in isolation — organized "
              "fraud only shows up in the links between claims. The engine "
              "traverses from a suspicious claim to its garage, claimant and "
              "policy, surfacing entities that recur across supposedly unrelated "
              "claims. The signal is shared-node density: one workshop at the "
              "centre of many 'accidents'."),
    what_you_see=("Click an alert to investigate. Watch the engine light up a "
                  "ring of claims all routed through one garage, then recommend "
                  "referring the case to the Special Investigation Unit (SIU)."),
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
    use_case=("Loans rarely go bad overnight; stress is visible months before an "
              "account is classified a Non-Performing Asset (NPA), but the signals "
              "sit scattered across systems. The engine traverses from a borrower "
              "to its loans, directors and repayment history to assemble a live "
              "risk picture — catching distress spreading through a shared-control "
              "network before it surfaces in the books."),
    what_you_see=("Click an alert to investigate. Watch the engine cluster "
                  "borrowers under one common director and flag EMI-bounce stress, "
                  "then propose a margin call or a credit-rating downgrade."),
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


WEALTH = register(VerticalConfig(
    key="wealth",
    name="Wealth — Suitability & Mis-selling",
    icon="📈",
    accent_color="#36B37E",
    tagline="SEBI suitability breaches — the audit log IS the compliance artifact.",
    regulator="SEBI IA Regs 2013 · SCORES",
    use_case=("Advisers face incentives to push high-commission products onto "
              "clients they don't fit, exposing the firm to regulator action and "
              "restitution. The engine traverses from a client to their "
              "suitability profile, sales, products and adviser, comparing what "
              "was sold against the client's documented risk appetite — and flags "
              "advisers who breach repeatedly across a book."),
    what_you_see=("Click an alert to investigate. Watch the engine surface an "
                  "adviser who sold a high-risk product to many low-risk-profile "
                  "clients, then propose flagging the mis-selling for compliance."),
    object_types=[
        ObjectTypeSpec(name="Adviser", icon="🧑‍💼", color="#36B37E",
                       key_props=["name", "arn"]),
        ObjectTypeSpec(name="Sale", icon="🧾", color="#FF5630",
                       key_props=["amount", "product"]),
        ObjectTypeSpec(name="Client", icon="👤", color="#4C9AFF",
                       key_props=["name"]),
        ObjectTypeSpec(name="SuitabilityProfile", icon="📊", color="#998DD9",
                       key_props=["risk_appetite", "horizon"]),
        ObjectTypeSpec(name="Product", icon="📦", color="#FFAB00",
                       key_props=["name", "risk"]),
    ],
    link_types=["sold_by", "sold_to", "of_product", "has_profile", "raised_on"],
    kpi_cards=[
        KPI(label="Mis-sold value", value="₹1 Cr", delta="5 clients"),
        KPI(label="Suitability breaches", value="5"),
        KPI(label="Advisers flagged", value="1"),
    ],
    signals=[SignalSpec(
        id="shared_attribute_ring", label="Adviser mis-selling cluster",
        why="One adviser sold a high-risk product to many low-risk-profile clients.",
        params={"hub_type": "Adviser", "min_members": 5,
                "typology": "suitability_mismatch"})],
    actions=[ActionSpec(id="flag_misselling", label="Flag mis-selling",
                        requires_approval=True)],
    sample_data_path="data/verticals/wealth.json",
    golden_cache_key="wealth",
))


CORPORATE = register(VerticalConfig(
    key="corporate",
    name="Corporate — UBO / Ownership",
    icon="🏢",
    accent_color="#998DD9",
    tagline="Unwind circular ownership to the true beneficial owner — pure OAG.",
    regulator="RBI CDD/EDD · FATF Rec 24",
    use_case=("Regulators require knowing the real human Ultimate Beneficial "
              "Owner (UBO) behind a corporate customer, but ownership is "
              "deliberately obscured through layered holdings across "
              "jurisdictions. The engine traverses the company-owns-company graph "
              "through multiple layers to compute effective control and resolve "
              "the true UBO — here the signal is the shape of the ownership graph "
              "itself."),
    what_you_see=("Click an alert to investigate. Watch the engine unwind a loop "
                  "of companies that own each other (hiding the owner) and a "
                  "cluster sharing one UBO, then propose escalating to Enhanced "
                  "Due Diligence (KYC review)."),
    object_types=[
        ObjectTypeSpec(name="Company", icon="🏢", color="#998DD9",
                       key_props=["name", "jurisdiction"]),
        ObjectTypeSpec(name="UBO", icon="👑", color="#FF5630",
                       key_props=["name", "nationality"]),
    ],
    link_types=["owns", "declares_ubo", "raised_on"],
    kpi_cards=[
        KPI(label="Companies in loop", value="3", delta="circular"),
        KPI(label="Shared UBO", value="1"),
        KPI(label="Offshore shells", value="2"),
    ],
    signals=[
        SignalSpec(id="circular_flow", label="Circular ownership",
                   why="Holding companies own each other in a loop, obscuring the UBO.",
                   params={"node_type": "Company", "link_type": "owns",
                           "typology": "circular_ownership"}),
        SignalSpec(id="shared_attribute_ring", label="Shared-UBO cluster",
                   why="Many companies declare one common ultimate beneficial owner.",
                   params={"hub_type": "UBO", "min_members": 5,
                           "typology": "shared_ubo_cluster"}),
    ],
    actions=[ActionSpec(id="escalate_kyc_review", label="Escalate KYC review",
                        requires_approval=True)],
    sample_data_path="data/verticals/corporate.json",
    golden_cache_key="corporate",
))
