"""Tests for character model classes."""

import pytest

from models.character import Character, PlayerCharacter, NPC


class TestCharacter:
    def test_create_with_required_fields(self):
        c = Character(id="test", name="Test", race="Human", character_type="npc")
        assert c.id == "test"
        assert c.name == "Test"
        assert c.race == "Human"
        assert c.character_type == "npc"

    def test_defaults(self):
        c = Character(id="test", name="Test", race="Human", character_type="npc")
        assert c.location is None
        assert c.physical_description == ""
        assert c.identity_raw == ""
        assert c.soul_raw == ""
        assert c.mood == ""
        assert c.disposition == ""

    def test_missing_required_field_raises(self):
        with pytest.raises(TypeError):
            Character(id="test", name="Test")


class TestPlayerCharacter:
    def test_is_character(self):
        assert issubclass(PlayerCharacter, Character)

    def test_create_with_stats(self):
        pc = PlayerCharacter(
            id="sera",
            name="Seraphina",
            race="Half-Elf",
            character_type="player",
            player="Kristin",
            character_class="Rogue",
            level=1,
            hp=9,
            ac=11,
            strength=8,
            dexterity=16,
            constitution=12,
            intelligence=14,
            wisdom=10,
            charisma=15,
        )
        assert pc.player == "Kristin"
        assert pc.hp == 9
        assert pc.dexterity == 16
        assert pc.character_type == "player"

    def test_mutable_dynamic_state(self):
        pc = PlayerCharacter(
            id="t", name="T", race="R", character_type="player",
            hp=10, current_hp=10,
        )
        pc.current_hp -= 3
        assert pc.current_hp == 7
        pc.conditions.append("poisoned")
        assert "poisoned" in pc.conditions

    def test_list_defaults_are_independent(self):
        pc1 = PlayerCharacter(id="a", name="A", race="R", character_type="player")
        pc2 = PlayerCharacter(id="b", name="B", race="R", character_type="player")
        pc1.equipment.append("sword")
        assert pc2.equipment == []

    def test_defaults(self):
        pc = PlayerCharacter(id="t", name="T", race="R", character_type="player")
        assert pc.abilities == []
        assert pc.spells == []
        assert pc.equipment == []
        assert pc.conditions == []
        assert pc.current_hp == 0
        assert pc.level == 1

    def test_modifier(self):
        pc = PlayerCharacter(
            id="t", name="T", race="R", character_type="player",
            strength=16, dexterity=12, constitution=10, intelligence=8,
            wisdom=15, charisma=1,
        )
        assert pc.modifier("strength") == 3
        assert pc.modifier("dexterity") == 1
        assert pc.modifier("constitution") == 0
        assert pc.modifier("intelligence") == -1
        assert pc.modifier("wisdom") == 2
        assert pc.modifier("charisma") == -5


class TestNPC:
    def test_is_character(self):
        assert issubclass(NPC, Character)

    def test_create_npc(self):
        npc = NPC(
            id="aldren",
            name="Aldren Thorne",
            race="Human",
            character_type="npc",
            role="Mayor of Driftmoor",
        )
        assert npc.role == "Mayor of Driftmoor"
        assert npc.character_type == "npc"

    def test_defaults(self):
        npc = NPC(id="t", name="T", race="R", character_type="npc")
        assert npc.relationships == {}
        assert npc.knowledge == []
        assert npc.hooks == []
        assert npc.active_concerns == []

    def test_dict_defaults_are_independent(self):
        npc1 = NPC(id="a", name="A", race="R", character_type="npc")
        npc2 = NPC(id="b", name="B", race="R", character_type="npc")
        npc1.relationships["X"] = "friend"
        assert npc2.relationships == {}

    def test_list_defaults_are_independent(self):
        npc1 = NPC(id="a", name="A", race="R", character_type="npc")
        npc2 = NPC(id="b", name="B", race="R", character_type="npc")
        npc1.knowledge.append("secret")
        assert npc2.knowledge == []
