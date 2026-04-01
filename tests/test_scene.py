"""Tests for the Scene model and scene-related GameState features."""

import pytest

from models.scene import Scene
from models.character import Character, PlayerCharacter, NPC
from models.place import Place
from models.game_state import GameState


# ---- Scene dataclass unit tests ----

class TestScene:
    def test_create_scene(self):
        scene = Scene(
            id="scene_broken_lantern",
            place_id="broken_lantern",
            character_ids=["kaelin", "tess"],
        )
        assert scene.id == "scene_broken_lantern"
        assert scene.place_id == "broken_lantern"
        assert scene.character_ids == ["kaelin", "tess"]
        assert scene.status == "active"
        assert scene.turn_started == 0
        assert scene.narrative == []

    def test_scene_defaults(self):
        scene = Scene(id="s1", place_id="p1")
        assert scene.character_ids == []
        assert scene.status == "active"
        assert scene.turn_started == 0
        assert scene.narrative == []

    def test_scene_custom_status(self):
        scene = Scene(id="s1", place_id="p1", status="paused")
        assert scene.status == "paused"

    def test_scene_with_narrative(self):
        scene = Scene(id="s1", place_id="p1", narrative=["The party enters."])
        assert len(scene.narrative) == 1

    def test_scene_add_narrative(self):
        scene = Scene(id="s1", place_id="p1")
        scene.narrative.append("A stranger approaches.")
        assert scene.narrative == ["A stranger approaches."]

    def test_scene_add_character(self):
        scene = Scene(id="s1", place_id="p1", character_ids=["kaelin"])
        scene.character_ids.append("thorgrim")
        assert "thorgrim" in scene.character_ids

    def test_scene_remove_character(self):
        scene = Scene(id="s1", place_id="p1", character_ids=["kaelin", "thorgrim"])
        scene.character_ids.remove("kaelin")
        assert scene.character_ids == ["thorgrim"]


# ---- GameState scene integration tests ----

def _make_game_state():
    """Build a small GameState with 2 places, 2 PCs, and 1 NPC."""
    characters = [
        PlayerCharacter(id="kaelin", name="Kaelin", race="Halfling", character_type="player"),
        PlayerCharacter(id="thorgrim", name="Thorgrim", race="Dwarf", character_type="player"),
        NPC(id="tess", name="Tess", race="Human", character_type="npc", role="Tavern owner"),
    ]
    places = [
        Place(id="broken_lantern", name="The Broken Lantern"),
        Place(id="old_mill", name="The Old Mill"),
    ]
    gs = GameState(characters=characters, places=places)
    gs.move_character("kaelin", "broken_lantern")
    gs.move_character("thorgrim", "broken_lantern")
    gs.move_character("tess", "broken_lantern")
    return gs


class TestGameStateScenes:
    def test_create_scene(self):
        gs = _make_game_state()
        scene = gs.create_scene("broken_lantern")
        assert scene.place_id == "broken_lantern"
        assert scene.id == "scene_broken_lantern"
        assert set(scene.character_ids) == {"kaelin", "thorgrim", "tess"}

    def test_create_scene_records_turn(self):
        gs = _make_game_state()
        gs.advance_turn()
        gs.advance_turn()
        scene = gs.create_scene("broken_lantern")
        assert scene.turn_started == 2

    def test_create_scene_unknown_place_raises(self):
        gs = _make_game_state()
        with pytest.raises(KeyError, match="Unknown place"):
            gs.create_scene("nonexistent")

    def test_create_scene_stored_in_scenes_list(self):
        gs = _make_game_state()
        gs.create_scene("broken_lantern")
        assert len(gs.scenes) == 1

    def test_get_scene(self):
        gs = _make_game_state()
        gs.create_scene("broken_lantern")
        scene = gs.get_scene("scene_broken_lantern")
        assert scene is not None
        assert scene.place_id == "broken_lantern"

    def test_get_scene_not_found(self):
        gs = _make_game_state()
        assert gs.get_scene("scene_nowhere") is None

    def test_get_scene_at_place(self):
        gs = _make_game_state()
        gs.create_scene("broken_lantern")
        scene = gs.get_scene_at("broken_lantern")
        assert scene is not None
        assert scene.id == "scene_broken_lantern"

    def test_get_scene_at_no_scene(self):
        gs = _make_game_state()
        assert gs.get_scene_at("old_mill") is None

    def test_get_active_scenes(self):
        gs = _make_game_state()
        gs.create_scene("broken_lantern")
        gs.create_scene("old_mill")
        active = gs.get_active_scenes()
        assert len(active) == 2

    def test_get_active_scenes_excludes_resolved(self):
        gs = _make_game_state()
        s1 = gs.create_scene("broken_lantern")
        gs.create_scene("old_mill")
        s1.status = "resolved"
        active = gs.get_active_scenes()
        assert len(active) == 1
        assert active[0].place_id == "old_mill"

    def test_create_scenes_from_players(self):
        gs = _make_game_state()
        gs.move_character("thorgrim", "old_mill")
        scenes = gs.create_scenes_for_players()
        assert len(scenes) == 2
        place_ids = {s.place_id for s in scenes}
        assert place_ids == {"broken_lantern", "old_mill"}

    def test_create_scenes_for_players_includes_npcs(self):
        gs = _make_game_state()
        scenes = gs.create_scenes_for_players()
        assert len(scenes) == 1
        scene = scenes[0]
        assert "tess" in scene.character_ids

    def test_create_scenes_for_players_skips_npc_only_places(self):
        """Places with only NPCs should not generate scenes."""
        gs = _make_game_state()
        gs.move_character("tess", "old_mill")
        # Only PCs at broken_lantern, only NPC at old_mill
        scenes = gs.create_scenes_for_players()
        assert len(scenes) == 1
        assert scenes[0].place_id == "broken_lantern"

    def test_no_duplicate_scene_for_same_place(self):
        gs = _make_game_state()
        gs.create_scene("broken_lantern")
        gs.create_scene("broken_lantern")
        assert len(gs.scenes) == 2  # allows multiple (new scene each time)

    def test_scene_character_ids_match_location(self):
        gs = _make_game_state()
        scene = gs.create_scene("broken_lantern")
        at_place = gs.get_characters_at("broken_lantern")
        assert set(scene.character_ids) == {c.id for c in at_place}
