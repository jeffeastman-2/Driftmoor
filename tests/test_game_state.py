"""Tests for GameState — the central registry and lookup for all entities."""

import pytest

from models.character import Character, PlayerCharacter, NPC
from models.place import Place
from models.game_state import GameState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_pc(id: str, name: str, location: str | None = None) -> PlayerCharacter:
    return PlayerCharacter(id=id, name=name, race="Human", character_type="player", location=location)


def _make_npc(id: str, name: str, location: str | None = None) -> NPC:
    return NPC(id=id, name=name, race="Human", character_type="npc", location=location)


def _make_place(id: str, name: str, parent_id: str | None = None, children: list[str] | None = None) -> Place:
    return Place(id=id, name=name, parent_id=parent_id, children=children or [])


@pytest.fixture
def state() -> GameState:
    """A small game state with 2 players, 2 NPCs, and a place hierarchy."""
    characters = [
        _make_pc("sera", "Seraphina", location="tavern"),
        _make_pc("thor", "Thorgrim", location="tavern"),
        _make_npc("aldren", "Aldren", location="mayors_hall"),
        _make_npc("tess", "Tess", location="tavern"),
    ]
    places = [
        _make_place("region", "Region", children=["driftmoor"]),
        _make_place("driftmoor", "Driftmoor", parent_id="region", children=["tavern", "mayors_hall"]),
        _make_place("tavern", "The Broken Lantern", parent_id="driftmoor"),
        _make_place("mayors_hall", "Mayor's Hall", parent_id="driftmoor"),
    ]
    return GameState(characters=characters, places=places)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_empty_state(self):
        gs = GameState()
        assert gs.turn == 0
        assert gs.characters == []
        assert gs.places == []

    def test_from_lists(self, state: GameState):
        assert len(state.characters) == 4
        assert len(state.places) == 4
        assert state.turn == 0


# ---------------------------------------------------------------------------
# Character lookups
# ---------------------------------------------------------------------------


class TestCharacterLookups:
    def test_get_character(self, state: GameState):
        c = state.get_character("sera")
        assert c.name == "Seraphina"

    def test_get_character_missing(self, state: GameState):
        assert state.get_character("nobody") is None

    def test_get_players(self, state: GameState):
        players = state.get_players()
        assert len(players) == 2
        assert all(isinstance(p, PlayerCharacter) for p in players)

    def test_get_npcs(self, state: GameState):
        npcs = state.get_npcs()
        assert len(npcs) == 2
        assert all(isinstance(n, NPC) for n in npcs)

    def test_get_characters_at(self, state: GameState):
        at_tavern = state.get_characters_at("tavern")
        assert len(at_tavern) == 3
        names = {c.name for c in at_tavern}
        assert names == {"Seraphina", "Thorgrim", "Tess"}

    def test_get_characters_at_empty(self, state: GameState):
        at_region = state.get_characters_at("region")
        assert at_region == []


# ---------------------------------------------------------------------------
# Place lookups
# ---------------------------------------------------------------------------


class TestPlaceLookups:
    def test_get_place(self, state: GameState):
        p = state.get_place("tavern")
        assert p.name == "The Broken Lantern"

    def test_get_place_missing(self, state: GameState):
        assert state.get_place("nowhere") is None

    def test_get_parent(self, state: GameState):
        parent = state.get_parent("tavern")
        assert parent.id == "driftmoor"

    def test_get_parent_of_root(self, state: GameState):
        assert state.get_parent("region") is None

    def test_get_children(self, state: GameState):
        children = state.get_children("driftmoor")
        ids = {p.id for p in children}
        assert ids == {"tavern", "mayors_hall"}

    def test_get_children_of_leaf(self, state: GameState):
        assert state.get_children("tavern") == []


# ---------------------------------------------------------------------------
# State mutations
# ---------------------------------------------------------------------------


class TestMutations:
    def test_move_character(self, state: GameState):
        state.move_character("sera", "mayors_hall")
        assert state.get_character("sera").location == "mayors_hall"
        at_tavern = state.get_characters_at("tavern")
        assert not any(c.id == "sera" for c in at_tavern)
        at_hall = state.get_characters_at("mayors_hall")
        assert any(c.id == "sera" for c in at_hall)

    def test_move_character_bad_character(self, state: GameState):
        with pytest.raises(KeyError):
            state.move_character("nobody", "tavern")

    def test_move_character_bad_place(self, state: GameState):
        with pytest.raises(KeyError):
            state.move_character("sera", "nowhere")

    def test_advance_turn(self, state: GameState):
        assert state.turn == 0
        state.advance_turn()
        assert state.turn == 1
        state.advance_turn()
        assert state.turn == 2


# ---------------------------------------------------------------------------
# Integration: load from scenario files
# ---------------------------------------------------------------------------


class TestLoadFromScenario:
    def test_from_scenario(self):
        from pathlib import Path
        from models.character_loader import load_all_characters
        from models.place_loader import load_all_places

        base = Path(__file__).parent.parent / "scenario"
        characters = load_all_characters(base / "people")
        places = load_all_places(base / "places")
        gs = GameState(characters=characters, places=places)

        assert gs.get_character("seraphina") is not None
        assert gs.get_place("driftmoor") is not None
        assert len(gs.get_players()) == 7
        assert len(gs.places) == 54

    def test_all_character_locations_valid(self):
        """If a character has a location set, it should be a known place."""
        from pathlib import Path
        from models.character_loader import load_all_characters
        from models.place_loader import load_all_places

        base = Path(__file__).parent.parent / "scenario"
        gs = GameState(
            characters=load_all_characters(base / "people"),
            places=load_all_places(base / "places"),
        )
        place_ids = {p.id for p in gs.places}
        for c in gs.characters:
            if c.location is not None:
                assert c.location in place_ids, (
                    f"Character {c.id} has location={c.location!r} which is not a known place"
                )
