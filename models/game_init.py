"""Initialize a GameState from scenario files with starting locations."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from models.character_loader import load_all_characters, load_all_creatures
from models.place_loader import load_all_places
from models.thing_loader import load_all_things
from models.game_state import GameState


# ---------------------------------------------------------------------------
# Initial location mapping
#
# Derived from scenario/README.md backstory and NPC IDENTITY.md files.
# Players converge at the Broken Lantern tavern.
# NPCs start at their home workplaces.
# ---------------------------------------------------------------------------

INITIAL_LOCATIONS: dict[str, str] = {
    # Players — each starts in a separate scene
    "kaelin": "broken_lantern",
    "thorgrim": "forge",
    "seraphina": "gilded_trinket",
    "aeliana": "fey_glade",
    "lilar": "old_mill",
    "varrak": "salt_and_iron",
    "amara": "beacon_church",
    "brenna": "weary_traveler",
    "cinnabar": "gilded_trinket",
    "gilthaness": "broken_lantern",
    "hendricks": "broken_lantern",
    "pippa": "broken_lantern",
    "tobin": "beacon_church",

    # Named NPCs — at their home locations
    "aldren": "mayors_hall",
    "elise": "mayors_hall",
    "elyssa": "elyssa_cottage",
    "kelem": "dustcloaks_curios",
    "jorgen": "salt_and_iron",
    "tess": "broken_lantern",
    "bran": "broken_lantern",
    "marda": "broken_lantern",
    "wilfred": "broken_lantern",
    "lytha": "bitter_remedy",
    "fennel": "fey_glade",
    "elden": "beacon_church",
    "darrin": "forge",
    "kara": "stables",
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
    "lottie": "bakery",
    "marta": "cobblers_shop",
    "tomas": "coopers_shed",
    "vindra": "tailors_shop",

    # Creature instances
    "shadowbeast_fey_glade": "fey_glade",
}


def initialize_game_state(scenario_dir: Path) -> GameState:
    """Load all scenario data and return a GameState with initial locations set."""
    characters = load_all_characters(scenario_dir / "people")
    places = load_all_places(scenario_dir / "places")
    things = load_all_things(scenario_dir / "things")

    # Load creature templates and create scene-specific instances
    creature_templates = load_all_creatures(scenario_dir / "creatures")
    sb_template = next((c for c in creature_templates if c.id == "shadowbeast"), None)
    if sb_template is not None:
        fey_glade_sb = dataclasses.replace(sb_template, id="shadowbeast_fey_glade")
        characters.append(fey_glade_sb)

    gs = GameState(characters=characters, places=places, things=things)

    for character in gs.characters:
        location = INITIAL_LOCATIONS.get(character.id)
        if location is not None:
            gs.move_character(character.id, location)

    gs.create_scenes_for_players()

    return gs
