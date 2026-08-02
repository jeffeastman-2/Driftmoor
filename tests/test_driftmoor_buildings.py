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
    _next_zone_toward,
    _place_identity_metadata,
    _waypoint_for_zone,
)
from engine.geometry import _check_impassable
from models.game_init import INITIAL_LOCATIONS
from models.geometry_loader import load_geometry
from models.space_time import Position


ROOT = Path(__file__).parent.parent
DRIFTMOOR = ROOT / "scenario" / "places" / "driftmoor"
NPCS = ROOT / "scenario" / "people" / "npcs"


def _town_buildings():
    """Every first-class building is discovered from Driftmoor's door table."""
    return tuple(_driftmoor_source_doorways("places/driftmoor"))


def test_every_authored_driftmoor_place_is_enterable():
    """A PLACE.md must not advertise a runtime place without geometry."""
    for place_file in DRIFTMOOR.glob("**/PLACE.md"):
        assert (place_file.parent / "GEOMETRY.md").is_file(), (
            f"{place_file.parent.relative_to(DRIFTMOOR)} has PLACE.md but no "
            "GEOMETRY.md; model it as an area in its parent or author an "
            "enterable scene"
        )


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
    assert set(cfg.characters) <= set(cfg.scene_geometry.starting_positions)
    for resident_id in cfg.characters:
        start = cfg.scene_geometry.starting_positions[resident_id]
        assert cfg.scene_geometry.zone_at(start)
        assert not any(
            obstacle.contains(start)
            for obstacle in cfg.scene_geometry.impassable
        )

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


@pytest.mark.parametrize(
    "place_id,connection_name,door_x,door_y",
    _town_buildings(),
    ids=lambda value: str(value),
)
def test_driftmoor_child_origins_are_parent_local(
    place_id, connection_name, door_x, door_y
):
    town = load_geometry(DRIFTMOOR / "GEOMETRY.md")
    child = load_geometry(DRIFTMOOR / place_id / "GEOMETRY.md")

    footprint_name = town.zone_at(Position(door_x, door_y))
    assert footprint_name is not None
    footprint = town.zones[footprint_name]
    expected_x = min(vertex[0] for vertex in footprint.vertices)
    expected_y = min(vertex[1] for vertex in footprint.vertices)

    assert child.origin.x == pytest.approx(expected_x)
    assert child.origin.y == pytest.approx(expected_y)
    assert child.origin.z == pytest.approx(child.z_level - town.z_level)


def test_weary_traveler_upstairs_origin_is_parent_local():
    ground = load_geometry(DRIFTMOOR / "weary_traveler" / "GEOMETRY.md")
    upstairs = load_geometry(
        DRIFTMOOR / "weary_traveler" / "upstairs" / "GEOMETRY.md"
    )

    assert upstairs.origin == Position(0, 0, 9)
    assert upstairs.z_level == pytest.approx(ground.z_level + upstairs.origin.z)


def test_town_building_height_occludes_sight_across_common_ground():
    town = load_geometry(DRIFTMOOR / "GEOMETRY.md")
    # The barber shop stands directly between these two common-ground points.
    assert town.zone_at(Position(414, 340)) == "TOWN_COMMON"
    assert town.zone_at(Position(414, 430)) == "TOWN_COMMON"
    assert town.zone_ceiling_z["BARBER"] > 5
    assert not town.can_see(Position(414, 340), Position(414, 430))
    # The wall itself is visible, but a creature at the interior centroid is not.
    facade = town.zones["BARBER"].nearest_point(Position(414, 340))
    assert town.can_see(Position(414, 340), facade)
    assert not town.can_see(Position(414, 340), Position(414, 390))
    # A short unobstructed line across the street remains visible.
    assert town.can_see(Position(400, 340), Position(500, 340))


def test_broken_lantern_subplaces_have_geometry_and_reciprocal_entries():
    parent_path = "places/driftmoor/broken_lantern"
    parent = configure_from_place_path(parent_path)
    assert parent.scene_geometry is not None
    assert parent.scene_geometry.boundaries == []
    assert {
        "MAIN_ROOM", "STAGE", "BOOTHS", "BAR", "KITCHEN",
        "MEETING_ROOM", "STORAGE_ROOM", "STAIRWAY",
    } <= set(parent.scene_geometry.zones)

    expected = {
        "meeting_room": ("I enter the meeting room", (6.0, 23.0), (0, 23, 0)),
        "storage_room": ("I enter the storage room", (17.0, 23.0), (12.5, 23, 0)),
        "upstairs": ("I go upstairs", (24.5, 27.5), (0, 0, 9)),
    }
    for child_id, (phrase, doorway_xy, expected_origin) in expected.items():
        child_path = f"{parent_path}/{child_id}"
        child = configure_from_place_path(child_path)
        assert child.scene_geometry is not None
        assert child.scene_geometry.origin == Position(*expected_origin)
        assert _infer_driftmoor_venue_transition(
            phrase, parent_path, "MAIN_ROOM"
        ) == child_id
        doorway = _driftmoor_enter_doorway(
            phrase, parent_path, "MAIN_ROOM", parent.scene_geometry
        )
        assert doorway is not None
        assert doorway[0] == child_id
        assert doorway[1][:2] == doorway_xy
        assert _entry_point_from_target_geometry(
            child_path, parent_path, child.scene_geometry
        ) is not None
        assert _infer_driftmoor_venue_transition(
            "I exit", child_path, next(iter(child.scene_geometry.zones))
        ) == "broken_lantern"


def test_dustcloaks_living_loft_is_an_enterable_second_story():
    parent_path = "places/driftmoor/dustcloaks_curios"
    child_path = f"{parent_path}/living_loft"
    parent = configure_from_place_path(parent_path)
    child = configure_from_place_path(child_path)

    assert child.scene_geometry.origin == Position(6.5, 13, 9)
    assert child.scene_geometry.z_level == pytest.approx(
        parent.scene_geometry.z_level + 9
    )
    assert _infer_driftmoor_venue_transition(
        "I go upstairs", parent_path, "BACKROOM"
    ) == "living_loft"
    assert _entry_point_from_target_geometry(
        child_path, parent_path, child.scene_geometry
    ) is not None


def test_broken_lantern_items_live_in_their_physical_subplaces():
    base = "places/driftmoor/broken_lantern"
    main = configure_from_place_path(base)
    meeting = configure_from_place_path(f"{base}/meeting_room")
    storage = configure_from_place_path(f"{base}/storage_room")

    assert {"ledger_book", "sealed_letter"}.isdisjoint(main.items)
    assert set(meeting.items) == {"ledger_book", "sealed_letter"}
    assert {
        "spare_blanket", "crate_saltfish", "candle_stub_bundle"
    }.isdisjoint(main.items)
    assert set(storage.items) == {
        "spare_blanket", "crate_saltfish", "candle_stub_bundle"
    }


@pytest.mark.parametrize(
    "start",
    [
        (24.5, 27.5, "STAIRWAY"),
        (17.0, 27.0, "STORAGE_ROOM"),
        (15.0, 10.0, "MAIN_ROOM"),
        (7.0, 17.0, "STAGE"),
    ],
)
def test_broken_lantern_meeting_room_has_a_clear_routed_approach(start):
    geometry = load_geometry(DRIFTMOOR / "broken_lantern" / "GEOMETRY.md")
    position = start

    for _ in range(3):
        if position[2] == "MEETING_ROOM":
            break
        next_zone = _next_zone_toward(
            geometry, position[2], "MEETING_ROOM"
        ) or "MEETING_ROOM"
        waypoint = _waypoint_for_zone(
            character_id="visitor",
            current_positions={"visitor": position},
            scene_geometry=geometry,
            target_zone=next_zone,
        )
        assert waypoint is not None
        allowed, log, _stop = _check_impassable(
            "visitor",
            position,
            (waypoint[0], waypoint[1], next_zone),
            geometry.impassable,
            geometry.zones,
        )
        assert allowed, log
        position = (waypoint[0], waypoint[1], next_zone)

    assert position[2] == "MEETING_ROOM"
