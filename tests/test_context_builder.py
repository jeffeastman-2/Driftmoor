"""Tests for the context_builder module."""

import pytest
from pathlib import Path

from models.game_init import initialize_game_state
from models.game_state import GameState
from models.character import PlayerCharacter, NPC
from models.place import Place
from models.scene import Scene
from engine.context_builder import build_player_context, PlayerContext

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenario"


@pytest.fixture(scope="module")
def gs():
    return initialize_game_state(SCENARIO_DIR)


# ---- PlayerContext structure tests ----

class TestPlayerContextStructure:
    def test_returns_player_context(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert isinstance(ctx, PlayerContext)

    def test_has_game_overview(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.game_overview
        assert "Driftmoor" in ctx.game_overview

    def test_has_character_name(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.character_name == "Kaelin Brightspark"

    def test_has_character_brief(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.character_brief
        assert "Halfling" in ctx.character_brief or "Bard" in ctx.character_brief

    def test_has_character_soul(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.character_soul
        assert len(ctx.character_soul) > 50

    def test_has_location_description(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.location_name
        assert ctx.location_description
        assert "Broken Lantern" in ctx.location_name

    def test_has_scene_characters(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert len(ctx.scene_characters) > 0
        # Tess is at the Broken Lantern with Kaelin
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Tess Malwin" in names

    def test_scene_characters_excludes_self(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Kaelin Brightspark" not in names

    def test_has_available_items(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        # Broken Lantern has food/drink/lodging items
        assert len(ctx.available_items) > 0

    def test_has_backstory(self, gs: GameState):
        ctx = build_player_context(gs, "kaelin")
        assert ctx.backstory
        assert "Kaelin" in ctx.backstory

    def test_unknown_character_raises(self, gs: GameState):
        with pytest.raises(KeyError, match="Unknown character"):
            build_player_context(gs, "nonexistent")

    def test_npc_raises(self, gs: GameState):
        with pytest.raises(ValueError, match="not a player character"):
            build_player_context(gs, "tess")


# ---- Per-player context tests ----

class TestEachPlayerContext:
    @pytest.fixture(scope="class")
    def all_contexts(self, gs):
        players = gs.get_players()
        return {pc.id: build_player_context(gs, pc.id) for pc in players}

    def test_all_players_have_context(self, all_contexts):
        # Scenario content evolves as new PCs are introduced.
        assert len(all_contexts) >= 7

    def test_all_have_game_overview(self, all_contexts):
        for pid, ctx in all_contexts.items():
            assert ctx.game_overview, f"{pid} missing game_overview"

    def test_all_have_character_brief(self, all_contexts):
        for pid, ctx in all_contexts.items():
            assert ctx.character_brief, f"{pid} missing character_brief"

    def test_all_have_location(self, all_contexts):
        for pid, ctx in all_contexts.items():
            assert ctx.location_name, f"{pid} missing location_name"
            assert ctx.location_description, f"{pid} missing location_description"

    def test_aeliana_at_fey_glade(self, all_contexts):
        ctx = all_contexts["aeliana"]
        assert "Fey Glade" in ctx.location_name
        # Aeliana is with Fennel and the Shadowbeast
        assert len(ctx.scene_characters) == 2

    def test_aeliana_no_items(self, all_contexts):
        ctx = all_contexts["aeliana"]
        assert len(ctx.available_items) == 0

    def test_lilar_at_old_mill(self, all_contexts):
        ctx = all_contexts["lilar"]
        assert "Old Mill" in ctx.location_name
        # Haversteads are there
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Gregan Haverstead" in names

    def test_thorgrim_at_forge(self, all_contexts):
        ctx = all_contexts["thorgrim"]
        assert "Ironhoof" in ctx.location_name or "Forge" in ctx.location_name
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Darrin Stonebrook" in names

    def test_seraphina_at_pawnshop(self, all_contexts):
        ctx = all_contexts["seraphina"]
        assert "Gilded Trinket" in ctx.location_name
        names = [sc["name"] for sc in ctx.scene_characters]
        assert any("Tavian" in n or "Tav" in n for n in names)
        # Should have items including magical ones
        assert len(ctx.available_items) > 0

    def test_amara_at_church(self, all_contexts):
        ctx = all_contexts["amara"]
        assert "Beacon" in ctx.location_name
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Father Elden Greybeard" in names

    def test_varrak_at_salt_iron(self, all_contexts):
        ctx = all_contexts["varrak"]
        assert "Salt" in ctx.location_name
        names = [sc["name"] for sc in ctx.scene_characters]
        assert "Jorgen Hallowtide" in names

    def test_all_have_backstory(self, all_contexts):
        for pid, ctx in all_contexts.items():
            # New player onboarding can temporarily omit backstory while
            # IDENTITY/SOUL specs are being completed.
            assert ctx.backstory or ctx.character_soul, (
                f"{pid} missing both backstory and soul context"
            )

    def test_render_text_not_empty(self, all_contexts):
        for pid, ctx in all_contexts.items():
            text = ctx.render()
            assert len(text) > 200, f"{pid} render too short"
            assert ctx.character_name in text
