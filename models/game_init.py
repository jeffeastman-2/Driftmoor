"""Initialize a GameState from scenario files with starting locations."""

from __future__ import annotations

from pathlib import Path

from models.character_loader import load_all_characters
from models.place_loader import load_all_places
from models.game_state import GameState


# ---------------------------------------------------------------------------
# Initial location mapping
#
# Derived from scenario/README.md backstory and NPC IDENTITY.md files.
# Players converge at the Broken Lantern tavern.
# NPCs start at their home workplaces.
# ---------------------------------------------------------------------------

INITIAL_LOCATIONS: dict[str, str] = {
    # Players — all converge at the tavern per README backstory
    "kaelin": "broken_lantern",
    "thorgrim": "broken_lantern",
    "seraphina": "broken_lantern",
    "aeliana": "broken_lantern",
    "lilar": "broken_lantern",

    # Named NPCs — at their home locations
    "aldren": "mayors_hall",
    "elyssa": "elyssa_cottage",
    "kelem": "dustcloaks_curios",
    "jorgen": "salt_and_iron",
    "tess": "broken_lantern",
    "lytha": "bitter_remedy",
    "elden": "beacon_church",
    "darrin": "ironhoof_forge",
    "kara": "ironhoof_forge",
    "tavian": "gilded_trinket",
    "arlan": "rusty_razor",
    "martha": "weary_traveler",
    "mira": "beacon_church",

    # Haverstead family — Old Mill on Greywater River
    "gregan": "old_mill",
    "mara": "old_mill",
    "davin": "old_mill",
    "isla": "old_mill",
    "tessa": "old_mill",

    # Background NPCs — at their workplaces
    "alina": "schoolhouse",
    "boren": "tannery",
    "darwin": "watchtower",
    "eadric": "weavers_cottage",
    "gran_lorie": "midwifes_home",
    "hilda": "carpenters_workshop",
    "jedrin": "general_store",
    "kessla": "fishmongers_shack",
    "maribel": "bakery",
    "marta": "cobblers_shop",
    "tomas": "coopers_shed",
    "vindra": "tailors_shop",
}


def initialize_game_state(scenario_dir: Path) -> GameState:
    """Load all scenario data and return a GameState with initial locations set."""
    characters = load_all_characters(scenario_dir / "people")
    places = load_all_places(scenario_dir / "places")

    gs = GameState(characters=characters, places=places)

    for character in gs.characters:
        location = INITIAL_LOCATIONS.get(character.id)
        if location is not None:
            gs.move_character(character.id, location)

    return gs
