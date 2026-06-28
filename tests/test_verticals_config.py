"""U1: VerticalConfig schema + registry. Pure schema unit — no engine, no app."""
import pytest
from pydantic import ValidationError

from praheri import verticals
from praheri.verticals import (
    ActionSpec, KPI, ObjectTypeSpec, SignalSpec, VerticalConfig,
    get_config, register,
)


def _minimal() -> VerticalConfig:
    return VerticalConfig(
        key="demo_vertical",
        name="Demo — Vertical",
        icon="🧪",
        accent_color="#36B37E",
        tagline="A tiny test cartridge.",
        regulator="N/A",
        object_types=[ObjectTypeSpec(name="Claim")],
        link_types=["filed_by"],
    )


def test_minimal_config_constructs_and_round_trips():
    cfg = _minimal()
    dumped = cfg.model_dump()
    assert dumped["key"] == "demo_vertical"
    assert dumped["object_types"][0]["name"] == "Claim"
    # round-trip back into the model
    assert VerticalConfig(**dumped) == cfg


def test_missing_required_field_raises():
    with pytest.raises(ValidationError):
        VerticalConfig(  # type: ignore[call-arg]
            name="No key", icon="x", accent_color="#000",
            tagline="t", regulator="r", object_types=[], link_types=[],
        )


def test_specs_accept_their_shapes():
    cfg = VerticalConfig(
        key="k", name="n", icon="i", accent_color="#abcdef",
        tagline="t", regulator="r",
        object_types=[ObjectTypeSpec(name="Policy", icon="P", color="#FFAB00",
                                     key_props=["sum_insured"])],
        link_types=["insures"],
        kpi_cards=[KPI(label="At risk", value="₹4.2 Cr", delta="+3")],
        signals=[SignalSpec(id="shared_attribute_ring", label="Ring",
                            why="Many claims, one garage.")],
        actions=[ActionSpec(id="refer_to_siu", label="Refer to SIU",
                            requires_approval=True)],
    )
    assert cfg.signals[0].id == "shared_attribute_ring"
    assert cfg.actions[0].requires_approval is True
    assert cfg.kpi_cards[0].value == "₹4.2 Cr"


def test_register_and_get_config_round_trip():
    # work on a clean registry so the test is order-independent
    saved = dict(verticals.REGISTRY)
    verticals.REGISTRY.clear()
    try:
        cfg = _minimal()
        returned = register(cfg)
        assert returned is cfg
        assert get_config("demo_vertical") is cfg
        # re-register same key overwrites, not duplicates
        register(cfg)
        assert len(verticals.REGISTRY) == 1
    finally:
        verticals.REGISTRY.clear()
        verticals.REGISTRY.update(saved)


def test_get_config_absent_raises_keyerror():
    with pytest.raises(KeyError):
        get_config("definitely-not-registered")
