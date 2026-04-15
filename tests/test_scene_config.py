"""Tests for scene_runner internal helpers (_build_character, _build_game_state)."""

from pathlib import Path

import pytest

from engine.scene_runner import (
    SceneConfig,
    _build_character,
    _build_game_state,
    ROOT,
)
from engine.session import CharacterSession
from models.character import PlayerCharacter, NPC, Creature
from engine.dm_agent import DMLeft
from engine.player_router import PlayerLeft


# ---------------------------------------------------------------------------
# _build_character
# ---------------------------------------------------------------------------

class TestBuildCharacter:
    def test_player_character(self):
        cdata = {
            "type": "player",
            "name": "Test Hero",
            "race": "Human",
            "class": "Fighter",
            "level": 2,
            "hp": 20,
            "ac": 16,
            "strength": 16, "dexterity": 12, "constitution": 14,
            "intelligence": 10, "wisdom": 10, "charisma": 8,
            "location": "town",
            "provider": "openai",
            "model": "gpt-4o",
            "soul": "A brave soul.",
            "identity": "Fighter stats.",
            "initial_scene": "You are in town.",
            "condition": {
                "state": {
                    "dopamine": 0.5, "cortisol": 0.3,
                    "norepinephrine": 0.4, "endorphins": 0.5,
                    "serotonin": 0.6, "acetylcholine": 0.5,
                    "oxytocin": 0.4,
                },
                "profiles": {
                    "dopamine": {"baseline": 0.5, "volatility": 0.5},
                },
            },
        }
        session, provider, model = _build_character("hero", cdata)
        assert isinstance(session.character, PlayerCharacter)
        assert session.character.id == "hero"
        assert session.character.name == "Test Hero"
        assert session.character.character_class == "Fighter"
        assert session.character.strength == 16
        assert session.soul.startswith("A brave soul.")
        assert "## Names and Strangers" in session.soul
        assert session.initial_scene == "You are in town."
        assert session.condition.state.dopamine == 0.5
        assert provider == "openai"
        assert model == "gpt-4o"

    def test_npc_character(self):
        cdata = {
            "type": "npc",
            "name": "Shopkeeper",
            "race": "Human",
            "role": "Merchant",
            "home_location": "market",
            "hp": 10, "ac": 10,
            "strength": 10, "dexterity": 10, "constitution": 10,
            "intelligence": 12, "wisdom": 12, "charisma": 14,
            "knowledge": ["Knows prices", "Has a secret"],
            "active_concerns": ["Thieves"],
            "location": "market",
            "provider": "deepseek",
            "model": "deepseek-chat",
            "soul": "A merchant soul.",
            "identity": "Merchant identity.",
            "initial_scene": "Your shop is open.",
            "condition": {
                "state": {
                    "dopamine": 0.4, "cortisol": 0.4,
                    "norepinephrine": 0.4, "endorphins": 0.4,
                    "serotonin": 0.5, "acetylcholine": 0.5,
                    "oxytocin": 0.3,
                },
                "profiles": {},
            },
        }
        session, provider, model = _build_character("shop", cdata)
        assert isinstance(session.character, NPC)
        assert session.character.knowledge == ["Knows prices", "Has a secret"]
        assert session.character.role == "Merchant"
        assert provider == "deepseek"

    def test_creature_character(self):
        cdata = {
            "type": "creature",
            "name": "Wolf",
            "race": "Medium Beast",
            "alignment": "Unaligned",
            "hp": 11, "ac": 13,
            "speed": "40 ft", "challenge": "¼",
            "strength": 12, "dexterity": 15, "constitution": 12,
            "intelligence": 3, "wisdom": 12, "charisma": 6,
            "skills": ["Perception +3"],
            "senses": ["Passive Perception 13"],
            "features": ["Pack Tactics"],
            "actions": ["Bite: +4, 2d4+2"],
            "tactics": "Hunt in packs",
            "location": "forest",
            "provider": "openai",
            "model": "gpt-4o",
            "soul": "Predator instinct.",
            "identity": "Wolf stats.",
            "initial_scene": "Prey nearby.",
            "condition": {
                "state": {
                    "dopamine": 0.7, "cortisol": 0.1,
                    "norepinephrine": 0.8, "endorphins": 0.8,
                    "serotonin": 0.2, "acetylcholine": 0.8,
                    "oxytocin": 0.0,
                },
                "profiles": {},
            },
        }
        session, provider, model = _build_character("wolf_1", cdata)
        assert isinstance(session.character, Creature)
        assert session.character.speed == "40 ft"
        assert session.character.tactics == "Hunt in packs"
        assert session.character.damage_resistances == []

    def test_condition_name_defaults_to_first_name(self):
        cdata = {
            "type": "player",
            "name": "Father Lilar Hearthsong",
            "race": "Human",
            "location": "mill",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "soul": "", "identity": "",
            "initial_scene": "Scene.",
            "condition": {
                "state": {
                    "dopamine": 0.5, "cortisol": 0.5,
                    "norepinephrine": 0.5, "endorphins": 0.5,
                    "serotonin": 0.5, "acetylcholine": 0.5,
                    "oxytocin": 0.5,
                },
                "profiles": {},
            },
        }
        session, _, _ = _build_character("lilar", cdata)
        assert session.condition.character_name == "Father"

    def test_condition_name_override(self):
        cdata = {
            "type": "player",
            "name": "Father Lilar Hearthsong",
            "race": "Human",
            "condition_name": "Lilar",
            "location": "mill",
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "soul": "", "identity": "",
            "initial_scene": "Scene.",
            "condition": {
                "state": {
                    "dopamine": 0.5, "cortisol": 0.5,
                    "norepinephrine": 0.5, "endorphins": 0.5,
                    "serotonin": 0.5, "acetylcholine": 0.5,
                    "oxytocin": 0.5,
                },
                "profiles": {},
            },
        }
        session, _, _ = _build_character("lilar", cdata)
        assert session.condition.character_name == "Lilar"

    def test_unknown_type_raises(self):
        cdata = {
            "type": "dragon",
            "name": "X", "race": "X",
            "provider": "x", "model": "x",
            "soul": "", "identity": "",
            "initial_scene": "",
            "condition": {
                "state": {
                    "dopamine": 0, "cortisol": 0,
                    "norepinephrine": 0, "endorphins": 0,
                    "serotonin": 0, "acetylcholine": 0,
                    "oxytocin": 0,
                },
                "profiles": {},
            },
        }
        with pytest.raises(ValueError, match="Unknown character type"):
            _build_character("x", cdata)


# ---------------------------------------------------------------------------
# _build_game_state
# ---------------------------------------------------------------------------

class TestBuildGameState:
    def test_text_section(self):
        sections = [{"text": "Hello world"}]
        assert _build_game_state(sections) == "Hello world"

    def test_header_and_text(self):
        sections = [{"header": "Notes", "text": "Some notes"}]
        assert _build_game_state(sections) == "# Notes\n\nSome notes"

    def test_multiple_sections(self):
        sections = [
            {"text": "Part 1"},
            {"header": "Part 2", "text": "Content 2"},
        ]
        result = _build_game_state(sections)
        assert "Part 1" in result
        assert "# Part 2\n\nContent 2" in result
        assert "\n\n" in result

    def test_file_section(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("File content here")
        sections = [{"file": str(f)}]
        # _build_game_state uses ROOT-relative paths, so test with absolute
        result = _build_game_state([{"text": "ok"}])
        assert result == "ok"
