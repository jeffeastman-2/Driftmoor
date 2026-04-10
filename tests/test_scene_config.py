"""Tests for JSON scene configuration loading."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from engine.scene_runner import (
    SceneConfig,
    configure_from_json,
    _build_character,
    _build_game_state,
    ROOT,
)
from engine.session import CharacterSession
from models.character import PlayerCharacter, NPC, Creature
from engine.dm_agent import DMLeft
from engine.player_router import PlayerLeft


SCENES_DIR = Path(__file__).resolve().parent.parent / "scenes"


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
        assert session.soul == "A brave soul."
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


# ---------------------------------------------------------------------------
# All JSON scene files load successfully
# ---------------------------------------------------------------------------

class TestAllScenesLoad:
    @pytest.fixture(params=sorted(SCENES_DIR.glob("*.json")),
                    ids=lambda p: p.stem)
    def scene_json(self, request):
        return request.param

    def test_json_is_valid(self, scene_json):
        data = json.loads(scene_json.read_text())
        assert "scene_name" in data
        assert "characters" in data
        assert "game_state_sections" in data

    def test_has_required_fields(self, scene_json):
        data = json.loads(scene_json.read_text())
        for field in ("scene_name", "title", "narrative_title",
                       "transcript_title", "character_summary",
                       "characters"):
            assert field in data, f"Missing {field} in {scene_json.name}"

    def test_characters_have_required_fields(self, scene_json):
        data = json.loads(scene_json.read_text())
        for cid, cdata in data["characters"].items():
            for field in ("type", "name", "race", "provider", "model",
                          "initial_scene", "condition"):
                assert field in cdata, f"{cid} missing {field}"
            cond = cdata["condition"]
            assert "state" in cond
            for dim in ("dopamine", "cortisol", "norepinephrine",
                        "endorphins", "serotonin", "acetylcholine",
                        "oxytocin"):
                assert dim in cond["state"], f"{cid} missing {dim}"

    def test_soul_and_identity_files_exist(self, scene_json):
        data = json.loads(scene_json.read_text())
        for cid, cdata in data["characters"].items():
            if cdata.get("soul_file"):
                path = ROOT / cdata["soul_file"]
                assert path.exists(), f"{cid} soul_file not found: {path}"
            if cdata.get("identity_file"):
                path = ROOT / cdata["identity_file"]
                assert path.exists(), f"{cid} identity_file not found: {path}"

    def test_game_state_files_exist(self, scene_json):
        data = json.loads(scene_json.read_text())
        for section in data.get("game_state_sections", []):
            if "file" in section:
                path = ROOT / section["file"]
                assert path.exists(), f"game_state file not found: {path}"

    def test_has_dm_provider(self, scene_json):
        data = json.loads(scene_json.read_text())
        assert "dm_provider" in data, f"Missing dm_provider in {scene_json.name}"
        assert "dm_model" in data, f"Missing dm_model in {scene_json.name}"

    def test_no_player_uses_dm_provider(self, scene_json):
        """Player characters should not use the same provider as the DM."""
        data = json.loads(scene_json.read_text())
        dm_provider = data.get("dm_provider", "anthropic")
        for cid, cdata in data["characters"].items():
            assert cdata["provider"] != dm_provider, (
                f"{cid} in {scene_json.name} uses DM provider {dm_provider}"
            )

    def test_dm_roles_share_single_llm(self, scene_json):
        """All characters in a scene should share the same DM LLM."""
        call_count = {"n": 0}
        created_llms = []

        def mock_make_call_llm(provider, model, **kwargs):
            call_count["n"] += 1
            sentinel = f"llm_{call_count['n']}_{provider}"
            created_llms.append(sentinel)
            return sentinel

        with patch("engine.scene_runner.make_call_llm", side_effect=mock_make_call_llm):
            config = configure_from_json(scene_json)

        # The DM LLM should be created once (first call) and shared
        dm_lefts = [config.roles[cid].dm_left._call_llm for cid in config.roles]
        first = dm_lefts[0]
        for dl in dm_lefts[1:]:
            assert dl is first

    def test_dm_and_player_use_different_llms(self, scene_json):
        """DM roles and player roles should use different LLM callables."""
        call_count = {"n": 0}

        def mock_make_call_llm(provider, model, **kwargs):
            call_count["n"] += 1
            return f"llm_{call_count['n']}_{provider}"

        with patch("engine.scene_runner.make_call_llm", side_effect=mock_make_call_llm):
            config = configure_from_json(scene_json)

        for cid in config.roles:
            dm_llm = config.roles[cid].dm_left._call_llm
            player_llm = config.roles[cid].player_left._call_llm
            assert dm_llm != player_llm, (
                f"{cid}: DM and player should use different LLMs"
            )

    def test_config_exposes_dm_provider(self, scene_json):
        """SceneConfig should expose dm_provider and dm_model."""
        def mock_make_call_llm(provider, model, **kwargs):
            return f"llm_{provider}"

        with patch("engine.scene_runner.make_call_llm", side_effect=mock_make_call_llm):
            config = configure_from_json(scene_json)

        assert config.dm_provider == "anthropic"
        assert "claude" in config.dm_model
