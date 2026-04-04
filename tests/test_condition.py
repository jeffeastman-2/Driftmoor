"""Tests for the neurochemical condition model, renderer, and CONDITION.md I/O."""

import pytest
from pathlib import Path

from models.condition import (
    NeurochemicalState,
    DimensionProfile,
    CharacterCondition,
    render_condition,
    write_condition_md,
    read_condition_md,
    DIMENSIONS,
)


# ---------------------------------------------------------------------------
# NeurochemicalState
# ---------------------------------------------------------------------------

class TestNeurochemicalState:
    def test_default_values(self):
        ns = NeurochemicalState()
        assert ns.dopamine == 0.5
        assert ns.cortisol == 0.5
        assert ns.norepinephrine == 0.5
        assert ns.endorphins == 0.5
        assert ns.serotonin == 0.5
        assert ns.acetylcholine == 0.5
        assert ns.oxytocin == 0.5

    def test_custom_values(self):
        ns = NeurochemicalState(dopamine=0.85, cortisol=0.25)
        assert ns.dopamine == 0.85
        assert ns.cortisol == 0.25

    def test_to_dict(self):
        ns = NeurochemicalState(dopamine=0.8, cortisol=0.3)
        d = ns.to_dict()
        assert d["dopamine"] == 0.8
        assert d["cortisol"] == 0.3
        assert len(d) == 7

    def test_from_dict(self):
        d = {"dopamine": 0.9, "cortisol": 0.1, "norepinephrine": 0.6,
             "endorphins": 0.7, "serotonin": 0.5, "acetylcholine": 0.8,
             "oxytocin": 0.4}
        ns = NeurochemicalState.from_dict(d)
        assert ns.dopamine == 0.9
        assert ns.oxytocin == 0.4

    def test_clamp_values(self):
        ns = NeurochemicalState(dopamine=1.5, cortisol=-0.3)
        ns = ns.clamped()
        assert ns.dopamine == 1.0
        assert ns.cortisol == 0.0

    def test_dimensions_list(self):
        assert DIMENSIONS == [
            "dopamine", "cortisol", "norepinephrine",
            "endorphins", "serotonin", "acetylcholine", "oxytocin",
        ]


# ---------------------------------------------------------------------------
# DimensionProfile
# ---------------------------------------------------------------------------

class TestDimensionProfile:
    def test_defaults(self):
        dp = DimensionProfile()
        assert dp.baseline == 0.5
        assert dp.volatility == 0.5

    def test_custom(self):
        dp = DimensionProfile(baseline=0.65, volatility=0.8)
        assert dp.baseline == 0.65
        assert dp.volatility == 0.8


# ---------------------------------------------------------------------------
# CharacterCondition
# ---------------------------------------------------------------------------

class TestCharacterCondition:
    def test_create_with_defaults(self):
        cc = CharacterCondition(character_id="aeliana", character_name="Aeliana Moonglade")
        assert cc.character_id == "aeliana"
        assert cc.state.dopamine == 0.5
        assert len(cc.profiles) == 0
        assert len(cc.extensions) == 0

    def test_apply_delta_with_volatility(self):
        cc = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            state=NeurochemicalState(dopamine=0.65),
            profiles={"dopamine": DimensionProfile(baseline=0.65, volatility=0.8)},
        )
        cc.apply_delta({"dopamine": +0.20})
        # new = 0.65 + (0.20 * 0.8) = 0.65 + 0.16 = 0.81
        assert abs(cc.state.dopamine - 0.81) < 0.001

    def test_apply_delta_clamps(self):
        cc = CharacterCondition(
            character_id="test",
            character_name="Test",
            state=NeurochemicalState(dopamine=0.95),
            profiles={"dopamine": DimensionProfile(baseline=0.5, volatility=1.0)},
        )
        cc.apply_delta({"dopamine": +0.20})
        assert cc.state.dopamine == 1.0

    def test_apply_delta_no_profile_uses_default_volatility(self):
        cc = CharacterCondition(
            character_id="test",
            character_name="Test",
            state=NeurochemicalState(cortisol=0.5),
        )
        cc.apply_delta({"cortisol": +0.20})
        # no profile → volatility defaults to 1.0 → raw delta applied
        assert abs(cc.state.cortisol - 0.7) < 0.001

    def test_delta_for_baseline(self):
        cc = CharacterCondition(
            character_id="test",
            character_name="Test",
            state=NeurochemicalState(dopamine=0.85),
            profiles={"dopamine": DimensionProfile(baseline=0.65, volatility=0.8)},
        )
        delta = cc.delta("dopamine")
        assert abs(delta - 0.20) < 0.001

    def test_extensions(self):
        cc = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            extensions={"obelisk_dopamine_response": 0.70},
        )
        assert cc.extensions["obelisk_dopamine_response"] == 0.70


# ---------------------------------------------------------------------------
# Condition renderer
# ---------------------------------------------------------------------------

class TestRenderCondition:
    def test_render_returns_string(self):
        cc = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            state=NeurochemicalState(
                dopamine=0.85, cortisol=0.25, norepinephrine=0.55,
                endorphins=0.75, serotonin=0.70, acetylcholine=0.75,
                oxytocin=0.55,
            ),
            profiles={
                "dopamine": DimensionProfile(baseline=0.65, volatility=0.7),
                "cortisol": DimensionProfile(baseline=0.40, volatility=0.6),
                "norepinephrine": DimensionProfile(baseline=0.60, volatility=0.7),
                "endorphins": DimensionProfile(baseline=0.70, volatility=0.4),
                "serotonin": DimensionProfile(baseline=0.65, volatility=0.5),
                "acetylcholine": DimensionProfile(baseline=0.75, volatility=0.8),
                "oxytocin": DimensionProfile(baseline=0.55, volatility=0.6),
            },
        )
        text = render_condition(cc)
        assert "CURRENT STATE:" in text
        assert "dopamine" in text
        assert "0.85" in text

    def test_render_has_all_seven_dimensions(self):
        cc = CharacterCondition(
            character_id="test", character_name="Test",
            state=NeurochemicalState(),
        )
        text = render_condition(cc)
        for dim in DIMENSIONS:
            assert dim in text

    def test_render_annotations_present(self):
        cc = CharacterCondition(
            character_id="test", character_name="Test",
            state=NeurochemicalState(dopamine=0.10, cortisol=0.90),
        )
        text = render_condition(cc)
        # dopamine 0.10 should match the lowest band
        assert "disengaged" in text or "apathetic" in text
        # cortisol 0.90 should match the highest band
        assert "acute stress" in text or "tunnel vision" in text

    def test_render_shows_baseline_comparison(self):
        cc = CharacterCondition(
            character_id="test", character_name="Test",
            state=NeurochemicalState(dopamine=0.85),
            profiles={"dopamine": DimensionProfile(baseline=0.65, volatility=0.7)},
        )
        text = render_condition(cc)
        assert "above baseline" in text.lower() or "well above baseline" in text.lower()


# ---------------------------------------------------------------------------
# CONDITION.md writer/reader round-trip
# ---------------------------------------------------------------------------

class TestConditionMdIO:
    def test_write_creates_file(self, tmp_path):
        cc = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            turn=0,
            situation="Approaching the Fey Glade",
            state=NeurochemicalState(
                dopamine=0.85, cortisol=0.25, norepinephrine=0.55,
                endorphins=0.75, serotonin=0.70, acetylcholine=0.75,
                oxytocin=0.55,
            ),
            profiles={
                "dopamine": DimensionProfile(baseline=0.65, volatility=0.7),
                "cortisol": DimensionProfile(baseline=0.40, volatility=0.6),
                "norepinephrine": DimensionProfile(baseline=0.60, volatility=0.7),
                "endorphins": DimensionProfile(baseline=0.70, volatility=0.4),
                "serotonin": DimensionProfile(baseline=0.65, volatility=0.5),
                "acetylcholine": DimensionProfile(baseline=0.75, volatility=0.8),
                "oxytocin": DimensionProfile(baseline=0.55, volatility=0.6),
            },
        )
        filepath = tmp_path / "CONDITION.md"
        write_condition_md(cc, filepath)
        assert filepath.exists()
        content = filepath.read_text()
        assert "Aeliana Moonglade" in content
        assert "Turn 0" in content
        assert "dopamine" in content

    def test_round_trip(self, tmp_path):
        original = CharacterCondition(
            character_id="aeliana",
            character_name="Aeliana Moonglade",
            turn=3,
            situation="Examining the carved stone",
            state=NeurochemicalState(
                dopamine=0.85, cortisol=0.25, norepinephrine=0.55,
                endorphins=0.75, serotonin=0.70, acetylcholine=0.75,
                oxytocin=0.55,
            ),
            profiles={
                "dopamine": DimensionProfile(baseline=0.65, volatility=0.7),
                "cortisol": DimensionProfile(baseline=0.40, volatility=0.6),
                "norepinephrine": DimensionProfile(baseline=0.60, volatility=0.7),
                "endorphins": DimensionProfile(baseline=0.70, volatility=0.4),
                "serotonin": DimensionProfile(baseline=0.65, volatility=0.5),
                "acetylcholine": DimensionProfile(baseline=0.75, volatility=0.8),
                "oxytocin": DimensionProfile(baseline=0.55, volatility=0.6),
            },
            extensions={"obelisk_dopamine_response": 0.70},
        )
        filepath = tmp_path / "CONDITION.md"
        write_condition_md(original, filepath)
        loaded = read_condition_md(filepath)

        assert loaded.character_name == "Aeliana Moonglade"
        assert loaded.turn == 3
        assert loaded.situation == "Examining the carved stone"
        # State values preserved to 2 decimal places
        assert abs(loaded.state.dopamine - 0.85) < 0.01
        assert abs(loaded.state.cortisol - 0.25) < 0.01
        assert abs(loaded.state.oxytocin - 0.55) < 0.01
        # Baselines preserved
        assert abs(loaded.profiles["dopamine"].baseline - 0.65) < 0.01
        assert abs(loaded.profiles["dopamine"].volatility - 0.70) < 0.01
        # Extensions preserved
        assert abs(loaded.extensions["obelisk_dopamine_response"] - 0.70) < 0.01

    def test_write_includes_rendered_condition(self, tmp_path):
        cc = CharacterCondition(
            character_id="test", character_name="Test Character",
            state=NeurochemicalState(dopamine=0.10, cortisol=0.90),
        )
        filepath = tmp_path / "CONDITION.md"
        write_condition_md(cc, filepath)
        content = filepath.read_text()
        assert "Rendered Condition" in content

    def test_write_includes_delta_column(self, tmp_path):
        cc = CharacterCondition(
            character_id="test", character_name="Test Character",
            state=NeurochemicalState(dopamine=0.85),
            profiles={"dopamine": DimensionProfile(baseline=0.65, volatility=0.7)},
        )
        filepath = tmp_path / "CONDITION.md"
        write_condition_md(cc, filepath)
        content = filepath.read_text()
        assert "+0.20" in content
