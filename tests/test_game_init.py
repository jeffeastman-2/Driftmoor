"""Tests for game state initialization from scenario files."""

import pytest
from pathlib import Path

from models.game_state import GameState
from models.character import PlayerCharacter, NPC
from models.game_init import initialize_game_state

SCENARIO_DIR = Path(__file__).parent.parent / "scenario"


@pytest.fixture
def state() -> GameState:
    return initialize_game_state(SCENARIO_DIR)


class TestInitialization:
    def test_returns_game_state(self, state: GameState):
        assert isinstance(state, GameState)

    def test_turn_starts_at_zero(self, state: GameState):
        assert state.turn == 0

    def test_all_characters_loaded(self, state: GameState):
        assert len(state.characters) >= 35

    def test_all_places_loaded(self, state: GameState):
        assert len(state.places) == 54

    def test_five_players(self, state: GameState):
        assert len(state.get_players()) == 5


class TestPlayerInitialLocations:
    """Players placed per scenario README backstory."""

    def test_kaelin_at_tavern(self, state: GameState):
        """Kaelin was performing at the tavern."""
        c = state.get_character("kaelin")
        assert c.location == "broken_lantern"

    def test_thorgrim_at_tavern(self, state: GameState):
        """Thorgrim was staying at the same tavern."""
        c = state.get_character("thorgrim")
        assert c.location == "broken_lantern"

    def test_seraphina_at_tavern(self, state: GameState):
        """Seraphina heard rumors of adventurers at the tavern."""
        c = state.get_character("seraphina")
        assert c.location == "broken_lantern"

    def test_aeliana_at_tavern(self, state: GameState):
        """Aeliana's tracking brought her to the tavern."""
        c = state.get_character("aeliana")
        assert c.location == "broken_lantern"

    def test_lilar_at_tavern(self, state: GameState):
        """Lilar (Amara in README) arrived at the tavern."""
        c = state.get_character("lilar")
        assert c.location == "broken_lantern"


class TestNPCInitialLocations:
    """Named NPCs placed at their home locations."""

    def test_aldren_at_mayors_hall(self, state: GameState):
        assert state.get_character("aldren").location == "mayors_hall"

    def test_elyssa_at_cottage(self, state: GameState):
        assert state.get_character("elyssa").location == "elyssa_cottage"

    def test_kelem_at_curios(self, state: GameState):
        assert state.get_character("kelem").location == "dustcloaks_curios"

    def test_jorgen_at_mercantile(self, state: GameState):
        assert state.get_character("jorgen").location == "salt_and_iron"

    def test_tess_at_tavern(self, state: GameState):
        assert state.get_character("tess").location == "broken_lantern"

    def test_lytha_at_apothecary(self, state: GameState):
        assert state.get_character("lytha").location == "bitter_remedy"

    def test_elden_at_church(self, state: GameState):
        assert state.get_character("elden").location == "beacon_church"

    def test_darrin_at_forge(self, state: GameState):
        assert state.get_character("darrin").location == "ironhoof_forge"

    def test_kara_at_stables(self, state: GameState):
        assert state.get_character("kara").location == "ironhoof_forge"

    def test_tavian_at_pawnshop(self, state: GameState):
        assert state.get_character("tavian").location == "gilded_trinket"

    def test_arlan_at_barbershop(self, state: GameState):
        assert state.get_character("arlan").location == "rusty_razor"

    def test_martha_at_rooming_house(self, state: GameState):
        assert state.get_character("martha").location == "weary_traveler"

    def test_mira_at_church(self, state: GameState):
        assert state.get_character("mira").location == "beacon_church"


class TestFamilyInitialLocations:
    """Haverstead family at the Old Mill."""

    def test_gregan_at_mill(self, state: GameState):
        assert state.get_character("gregan").location == "old_mill"

    def test_davin_at_mill(self, state: GameState):
        assert state.get_character("davin").location == "old_mill"

    def test_mara_at_mill(self, state: GameState):
        assert state.get_character("mara").location == "old_mill"

    def test_isla_at_mill(self, state: GameState):
        assert state.get_character("isla").location == "old_mill"

    def test_tessa_at_mill(self, state: GameState):
        assert state.get_character("tessa").location == "old_mill"


class TestBackgroundNPCLocations:
    """Background NPCs placed at their workplaces."""

    def test_alina_at_schoolhouse(self, state: GameState):
        assert state.get_character("alina").location == "schoolhouse"

    def test_boren_at_tannery(self, state: GameState):
        assert state.get_character("boren").location == "tannery"

    def test_darwin_at_watchtower(self, state: GameState):
        assert state.get_character("darwin").location == "watchtower"

    def test_eadric_at_weavers(self, state: GameState):
        assert state.get_character("eadric").location == "weavers_cottage"

    def test_gran_lorie_at_midwife(self, state: GameState):
        assert state.get_character("gran_lorie").location == "midwifes_home"

    def test_hilda_at_carpenters(self, state: GameState):
        assert state.get_character("hilda").location == "carpenters_workshop"

    def test_jedrin_at_general_store(self, state: GameState):
        assert state.get_character("jedrin").location == "general_store"

    def test_kessla_at_fishmonger(self, state: GameState):
        assert state.get_character("kessla").location == "fishmongers_shack"

    def test_maribel_at_bakery(self, state: GameState):
        assert state.get_character("maribel").location == "bakery"

    def test_marta_at_cobbler(self, state: GameState):
        assert state.get_character("marta").location == "cobblers_shop"

    def test_tomas_at_coopers(self, state: GameState):
        assert state.get_character("tomas").location == "coopers_shed"

    def test_vindra_at_tailors(self, state: GameState):
        assert state.get_character("vindra").location == "tailors_shop"


class TestAllLocationsValid:
    def test_every_character_has_location(self, state: GameState):
        for c in state.characters:
            assert c.location is not None, f"Character {c.id} has no location"

    def test_every_location_is_valid_place(self, state: GameState):
        place_ids = {p.id for p in state.places}
        for c in state.characters:
            assert c.location in place_ids, (
                f"Character {c.id} has location={c.location!r} not in places"
            )
