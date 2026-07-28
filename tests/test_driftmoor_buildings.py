"""Data-driven integration audit for every enterable Driftmoor building."""

import re
from pathlib import Path

import pytest

from engine.md_loader import configure_from_place_path, parse_scene_introductions
from engine.session import (
    _driftmoor_enter_doorway,
    _driftmoor_source_doorways,
    _entry_point_from_target_geometry,
    _infer_driftmoor_venue_transition,
    _place_identity_metadata,
)
from models.game_init import INITIAL_LOCATIONS


ROOT = Path(__file__).parent.parent
DRIFTMOOR = ROOT / "scenario" / "places" / "driftmoor"
NPCS = ROOT / "scenario" / "people" / "npcs"


def _town_buildings():
    """Every first-class building is discovered from Driftmoor's door table."""
    return tuple(_driftmoor_source_doorways("places/driftmoor"))


@pytest.mark.parametrize(
    "place_id,connection_name,door_x,door_y",
    _town_buildings(),
    ids=lambda value: str(value),
)
def test_driftmoor_building_is_enterable_and_loads_its_npcs(
    place_id, connection_name, door_x, door_y
):
    place_dir = DRIFTMOOR / place_id
    assert (place_dir / "PLACE.md").is_file()
    assert (place_dir / "GEOMETRY.md").is_file()
    place_type, aliases = _place_identity_metadata(place_dir / "PLACE.md")
    assert place_type
    assert aliases

    # Connection names are the public generic aliases used on the map:
    # to_fishmonger -> "enter the fishmonger", etc.
    alias = connection_name.removeprefix("to_").replace("_", " ")
    phrase = f"I enter the {alias}"
    assert _infer_driftmoor_venue_transition(
        phrase, "places/driftmoor", "TOWN_COMMON"
    ) == place_id
    assert _driftmoor_enter_doorway(
        phrase, "places/driftmoor", "TOWN_COMMON", None
    ) == (place_id, (door_x, door_y, ""))

    cfg = configure_from_place_path(f"places/driftmoor/{place_id}")
    assert cfg.scene_geometry is not None
    assert cfg.scene_geometry.place_path == f"places/driftmoor/{place_id}"

    # The interior must author a reciprocal exit/arrival point back to town.
    assert _entry_point_from_target_geometry(
        f"places/driftmoor/{place_id}",
        "places/driftmoor",
        cfg.scene_geometry,
    ) is not None

    # Every initialized NPC assigned to this building must be instantiated by
    # its PLACE.md. Player starting locations are intentionally excluded.
    expected_npcs = {
        npc_dir.name
        for npc_dir in NPCS.iterdir()
        if npc_dir.is_dir() and INITIAL_LOCATIONS.get(npc_dir.name) == place_id
    }
    assert expected_npcs <= set(cfg.characters)

    introductions = parse_scene_introductions(
        (place_dir / "PLACE.md").read_text(encoding="utf-8")
    )
    assert expected_npcs <= set(introductions)

    # Every bold name under "Who Is Normally Here" must correspond to a
    # structured resident. This catches prose-only characters that disappear
    # when the place is loaded.
    text = (place_dir / "PLACE.md").read_text(encoding="utf-8")
    who_match = re.search(
        r"^## Who Is Normally Here\s*$\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    named_here = (
        re.findall(r"^\s*-\s*\*\*(.+?)\*\*", who_match.group(1), re.MULTILINE)
        if who_match
        else []
    )
    accepted_names = set()
    for resident_id, session in cfg.characters.items():
        accepted_names.add(resident_id.lower())
        display_name = session.character.name.lower()
        accepted_names.add(display_name)
        accepted_names.add(display_name.split()[0])
    for display_name in named_here:
        assert display_name.lower() in accepted_names
