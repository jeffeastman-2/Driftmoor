"""Tests for the structured spellcasting parser (specs/SPELLCASTING.md step 1).

Uses real ``IDENTITY.md`` files from ``scenario/people/players/`` as fixtures.
The parser is telemetry-only: these tests verify it extracts the right
counters, classifies cantrips vs leveled spells, marks concentration and
Cleric domain ("always-prepared") spells correctly, and gracefully returns
``None`` for legacy free-form sections (e.g. Aeliana the Ranger).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from models.character_loader import load_player_character
from models.spellcasting import (
    Spell,
    SpellcastingProfile,
    parse_spellcasting,
    validate_spellcasting,
)


PLAYERS_DIR = Path(__file__).parent.parent / "scenario" / "people" / "players"


def _spell_names(spells: list[Spell]) -> set[str]:
    return {s.name for s in spells}


# ---------------------------------------------------------------------------
# Parser unit tests against real character fixtures
# ---------------------------------------------------------------------------


class TestAmaraLifeCleric:
    @pytest.fixture
    def pc(self):
        return load_player_character(PLAYERS_DIR / "amara")

    def test_profile_present(self, pc):
        assert pc.spellcasting is not None

    def test_header_fields(self, pc):
        p = pc.spellcasting
        assert p.ability == "WIS"
        assert p.save_dc == 13
        assert p.attack_bonus == 5

    def test_cantrip_count(self, pc):
        assert len(pc.spellcasting.cantrips) == 3

    def test_cantrip_names(self, pc):
        names = _spell_names(pc.spellcasting.cantrips)
        assert {"Sacred Flame", "Spare the Dying", "Light"} <= names

    def test_slot_count(self, pc):
        assert pc.spellcasting.spell_slots_max == {1: 2}
        assert pc.spellcasting.spell_slots_used == {1: 0}

    def test_prepared_includes_domain_and_personal(self, pc):
        names = _spell_names(pc.spellcasting.prepared)
        assert "Bless" in names
        assert "Cure Wounds" in names
        assert "Guiding Bolt" in names
        assert "Healing Word" in names

    def test_domain_spells_flagged(self, pc):
        prepared_by_name = {s.name: s for s in pc.spellcasting.prepared}
        assert prepared_by_name["Bless"].is_domain
        assert prepared_by_name["Cure Wounds"].is_domain
        assert not prepared_by_name["Guiding Bolt"].is_domain

    def test_concentration_flagged(self, pc):
        prepared_by_name = {s.name: s for s in pc.spellcasting.prepared}
        assert prepared_by_name["Bless"].concentration
        assert prepared_by_name["Shield of Faith"].concentration
        assert not prepared_by_name["Sanctuary"].concentration
        assert not prepared_by_name["Cure Wounds"].concentration

    def test_action_economy_parsed(self, pc):
        prepared_by_name = {s.name: s for s in pc.spellcasting.prepared}
        assert "bonus action" in prepared_by_name["Healing Word"].action.lower()
        assert prepared_by_name["Guiding Bolt"].action.lower() == "1 action"

    def test_validator_clean(self, pc):
        assert validate_spellcasting(pc.spellcasting, pc.character_class, pc.level) == []


class TestLilarLightCleric:
    @pytest.fixture
    def pc(self):
        return load_player_character(PLAYERS_DIR / "lilar")

    def test_profile_present(self, pc):
        assert pc.spellcasting is not None
        assert pc.spellcasting.ability == "WIS"

    def test_cantrip_count(self, pc):
        assert len(pc.spellcasting.cantrips) == 3

    def test_slot_count(self, pc):
        assert pc.spellcasting.spell_slots_max == {1: 2}

    def test_domain_spells(self, pc):
        prepared_by_name = {s.name: s for s in pc.spellcasting.prepared}
        assert prepared_by_name["Burning Hands"].is_domain
        assert prepared_by_name["Faerie Fire"].is_domain
        assert not prepared_by_name["Healing Word"].is_domain

    def test_validator_clean(self, pc):
        assert validate_spellcasting(pc.spellcasting, pc.character_class, pc.level) == []


class TestKaelinBard:
    @pytest.fixture
    def pc(self):
        return load_player_character(PLAYERS_DIR / "kaelin")

    def test_profile_present(self, pc):
        assert pc.spellcasting is not None
        assert pc.spellcasting.ability == "CHA"

    def test_cantrip_count(self, pc):
        assert len(pc.spellcasting.cantrips) == 3

    def test_slot_count(self, pc):
        assert pc.spellcasting.spell_slots_max == {1: 4, 2: 3}

    def test_known_spells_not_prepared(self, pc):
        """Bards use 'Spells known', not 'Prepared spells'."""
        assert pc.spellcasting.prepared == []
        assert len(pc.spellcasting.known) == 7

    def test_known_names(self, pc):
        names = _spell_names(pc.spellcasting.known)
        assert names == {
            "Detect Magic", "Faerie Fire", "Healing Word", "Dissonant Whispers",
            "Calm Emotions", "Detect Thoughts", "Invisibility",
        }

    def test_known_spell_levels(self, pc):
        levels = {s.name: s.level for s in pc.spellcasting.known}
        assert levels["Detect Magic"] == 1
        assert levels["Faerie Fire"] == 1
        assert levels["Calm Emotions"] == 2
        assert levels["Detect Thoughts"] == 2
        assert levels["Invisibility"] == 2

    def test_faerie_fire_concentration(self, pc):
        ff = next(s for s in pc.spellcasting.known if s.name == "Faerie Fire")
        assert ff.concentration

    def test_validator_clean(self, pc):
        assert validate_spellcasting(pc.spellcasting, pc.character_class, pc.level) == []


class TestVarrakSorcerer:
    @pytest.fixture
    def pc(self):
        return load_player_character(PLAYERS_DIR / "varrak")

    def test_profile_present(self, pc):
        assert pc.spellcasting is not None
        assert pc.spellcasting.ability == "CHA"

    def test_cantrip_count(self, pc):
        assert len(pc.spellcasting.cantrips) == 4

    def test_known_spells(self, pc):
        names = _spell_names(pc.spellcasting.known)
        assert names == {"Shield", "Burning Hands"}
        assert pc.spellcasting.prepared == []

    def test_validator_clean(self, pc):
        assert validate_spellcasting(pc.spellcasting, pc.character_class, pc.level) == []


class TestAeliana:
    """Aeliana's IDENTITY.md uses the legacy free-form Spells list (Ranger
    L1 has no spellcasting under RAW). Parser must return ``None``."""

    @pytest.fixture
    def pc(self):
        return load_player_character(PLAYERS_DIR / "aeliana")

    def test_no_profile(self, pc):
        assert pc.spellcasting is None

    def test_validator_silent_when_none(self, pc):
        assert validate_spellcasting(None, "Ranger", 1) == []


# ---------------------------------------------------------------------------
# parse_spellcasting unit tests on synthetic snippets
# ---------------------------------------------------------------------------


class TestParseSpellcastingSnippets:
    def test_empty_returns_none(self):
        assert parse_spellcasting("") is None

    def test_no_header_returns_none(self):
        text = "- Some flavor spell\n- Another one\n"
        assert parse_spellcasting(text) is None

    def test_minimal_header(self):
        text = (
            "**Spellcasting ability:** INT | **Spell save DC:** 13 "
            "| **Spell attack:** +5\n"
        )
        p = parse_spellcasting(text)
        assert p is not None
        assert (p.ability, p.save_dc, p.attack_bonus) == ("INT", 13, 5)
        assert p.spell_slots_max == {}

    def test_slot_line_parsed(self):
        text = (
            "**Spellcasting ability:** WIS | **Spell save DC:** 13 "
            "| **Spell attack:** +5\n\n"
            "**1st-level spell slots:** 2 per long rest\n"
        )
        p = parse_spellcasting(text)
        assert p.spell_slots_max == {1: 2}
        assert p.spell_slots_used == {1: 0}


# ---------------------------------------------------------------------------
# validate_spellcasting unit tests
# ---------------------------------------------------------------------------


class TestValidator:
    def _profile(self, cantrips: int, slots_l1: int) -> SpellcastingProfile:
        return SpellcastingProfile(
            ability="WIS",
            save_dc=13,
            attack_bonus=5,
            cantrips=[Spell(name=f"C{i}") for i in range(cantrips)],
            spell_slots_max={1: slots_l1},
            spell_slots_used={1: 0},
        )

    def test_cleric_l1_clean(self):
        assert validate_spellcasting(self._profile(3, 2), "Cleric (Life Domain)", 1) == []

    def test_cleric_wrong_cantrip_count(self):
        warnings = validate_spellcasting(self._profile(2, 2), "Cleric", 1)
        assert any("cantrips" in w for w in warnings)

    def test_cleric_wrong_slot_count(self):
        warnings = validate_spellcasting(self._profile(3, 1), "Cleric", 1)
        assert any("first-level" in w for w in warnings)

    def test_bard_l1_clean(self):
        assert validate_spellcasting(self._profile(2, 2), "Bard", 1) == []

    def test_non_caster_unchecked(self):
        assert validate_spellcasting(self._profile(0, 0), "Fighter", 1) == []

    def test_above_level_one_unchecked(self):
        assert validate_spellcasting(self._profile(0, 0), "Cleric", 2) == []


class TestSpacedHyphenSuffixStripped:
    """Spellbook bullets like '- Teleport - 1 action' keep only the name."""

    SECTION = (
        "## Spells\n"
        "**Spellcasting ability:** INT | **Spell save DC:** 16 | "
        "**Spell attack:** +8\n\n"
        "**Spells known (spellbook):**\n"
        "- Disguise Self - 1 action\n"
        "- Silent Image - 1 action, concentration up to 10 minutes\n"
        "- Teleport - 1 action\n"
    )

    def test_names_have_no_casting_time_suffix(self):
        profile = parse_spellcasting(self.SECTION)
        assert profile is not None
        names = _spell_names(profile.known)
        assert names == {"Disguise Self", "Silent Image", "Teleport"}

    def test_concentration_still_flagged(self):
        profile = parse_spellcasting(self.SECTION)
        si = next(s for s in profile.known if s.name == "Silent Image")
        assert si.concentration
