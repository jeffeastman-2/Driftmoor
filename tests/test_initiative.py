"""Tests for engine/initiative.py — d20 + DEX modifier rolling."""

import random

import pytest

from engine.initiative import InitiativeEntry, dex_modifier, roll_initiative
from models.character import Character, Creature, NPC, PlayerCharacter


# ---------------------------------------------------------------------------
# dex_modifier
# ---------------------------------------------------------------------------

class TestDexModifier:
    def test_player_character(self):
        pc = PlayerCharacter(id="a", name="A", race="Elf", character_type="player", dexterity=16)
        assert dex_modifier(pc) == 3

    def test_npc_with_stats(self):
        npc = NPC(id="f", name="F", race="Human", character_type="npc", dexterity=12)
        assert dex_modifier(npc) == 1

    def test_npc_default(self):
        npc = NPC(id="n", name="N", race="Human", character_type="npc")
        assert dex_modifier(npc) == 0  # default dexterity=10

    def test_creature(self):
        c = Creature(id="sb", name="SB", race="Monstrosity", character_type="creature", dexterity=14)
        assert dex_modifier(c) == 2

    def test_base_character(self):
        c = Character(id="x", name="X", race="?", character_type="npc")
        assert dex_modifier(c) == 0  # no dexterity attr → default


# ---------------------------------------------------------------------------
# roll_initiative
# ---------------------------------------------------------------------------

class TestRollInitiative:
    @pytest.fixture()
    def fey_glade_chars(self):
        return [
            PlayerCharacter(id="aeliana", name="Aeliana", race="Elf",
                            character_type="player", dexterity=16),
            Creature(id="shadowbeast", name="Shadowbeast", race="Monstrosity",
                     character_type="creature", dexterity=14),
            NPC(id="fennel", name="Fennel", race="Human",
                character_type="npc", dexterity=12),
        ]

    def test_returns_all_characters(self, fey_glade_chars):
        entries = roll_initiative(fey_glade_chars, rng=random.Random(42))
        ids = {e.character_id for e in entries}
        assert ids == {"aeliana", "shadowbeast", "fennel"}

    def test_sorted_descending(self, fey_glade_chars):
        entries = roll_initiative(fey_glade_chars, rng=random.Random(42))
        totals = [e.total for e in entries]
        assert totals == sorted(totals, reverse=True)

    def test_total_equals_roll_plus_modifier(self, fey_glade_chars):
        entries = roll_initiative(fey_glade_chars, rng=random.Random(42))
        for e in entries:
            assert e.total == e.roll + e.modifier

    def test_rolls_are_1_to_20(self, fey_glade_chars):
        entries = roll_initiative(fey_glade_chars, rng=random.Random(42))
        for e in entries:
            assert 1 <= e.roll <= 20

    def test_modifiers_match_dex(self, fey_glade_chars):
        entries = roll_initiative(fey_glade_chars, rng=random.Random(42))
        expected = {"aeliana": 3, "shadowbeast": 2, "fennel": 1}
        for e in entries:
            assert e.modifier == expected[e.character_id]

    def test_deterministic_with_same_seed(self, fey_glade_chars):
        e1 = roll_initiative(fey_glade_chars, rng=random.Random(99))
        e2 = roll_initiative(fey_glade_chars, rng=random.Random(99))
        assert [e.total for e in e1] == [e.total for e in e2]

    def test_different_seeds_differ(self, fey_glade_chars):
        e1 = roll_initiative(fey_glade_chars, rng=random.Random(1))
        e2 = roll_initiative(fey_glade_chars, rng=random.Random(2))
        # Very unlikely to match across all three
        assert [e.roll for e in e1] != [e.roll for e in e2]

    def test_repr(self):
        entry = InitiativeEntry(character_id="aeliana", roll=14, modifier=3, total=17)
        assert "aeliana: 17" in repr(entry)
        assert "d20=14" in repr(entry)

    def test_empty_list(self):
        entries = roll_initiative([], rng=random.Random(1))
        assert entries == []

    def test_single_character(self):
        pc = PlayerCharacter(id="solo", name="Solo", race="Human",
                             character_type="player", dexterity=10)
        entries = roll_initiative([pc], rng=random.Random(1))
        assert len(entries) == 1
        assert entries[0].modifier == 0


# ---------------------------------------------------------------------------
# Loaded characters get correct DEX
# ---------------------------------------------------------------------------

class TestLoadedDex:
    @pytest.fixture(scope="class")
    def gs(self):
        from pathlib import Path
        from models.game_init import initialize_game_state
        scenario_dir = Path(__file__).resolve().parent.parent / "scenario"
        return initialize_game_state(scenario_dir)

    def test_fennel_dex_loaded(self, gs):
        fennel = gs.get_character("fennel")
        assert fennel is not None
        assert fennel.dexterity == 12
        assert dex_modifier(fennel) == 1

    def test_aeliana_dex_loaded(self, gs):
        aeliana = gs.get_character("aeliana")
        assert aeliana is not None
        assert aeliana.dexterity == 16
        assert dex_modifier(aeliana) == 3

    def test_shadowbeast_dex_loaded(self, gs):
        sb = gs.get_character("shadowbeast_fey_glade")
        assert sb is not None
        assert sb.dexterity == 14
        assert dex_modifier(sb) == 2

    def test_roll_with_loaded_chars(self, gs):
        chars = [
            gs.get_character("aeliana"),
            gs.get_character("shadowbeast_fey_glade"),
            gs.get_character("fennel"),
        ]
        entries = roll_initiative(chars, rng=random.Random(42))
        assert len(entries) == 3
        for e in entries:
            assert 1 <= e.roll <= 20
