from __future__ import annotations

from pathlib import Path

from engine.session import (
    _all_zone_items_examined,
    _build_puzzle_pressure_block,
    _choose_exploration_waypoint,
    _exploration_redirect_intent,
    _should_block_backtrack,
    _waypoint_for_zone,
    _choose_puzzle_focus_item,
    _zone_has_unresolved_puzzle,
)
from engine.puzzles import build_registry
from models.contents_loader import load_zone_contents_with_geometry, load_zone_puzzles
from models.geometry_loader import load_geometry
from models.space_time import Position


ZONES = Path("scenario/places/obelisk_reach/echoing_caverns/zones")
GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


def _load_items_and_geometry():
    geometry = load_geometry(GEOMETRY)
    items = load_zone_contents_with_geometry(ZONES, GEOMETRY, scene_geometry=geometry)
    return geometry, items


def test_all_zone_items_examined_false_until_discovered():
    _, items = _load_items_and_geometry()
    pos = {"seraphina": (138.0, 295.0, "ENTRY CHAMBER")}
    assert not _all_zone_items_examined(
        character_id="seraphina",
        current_positions=pos,
        items=items,
    )


def test_all_zone_items_examined_true_after_marking_zone_items():
    _, items = _load_items_and_geometry()
    pos = {"seraphina": (138.0, 295.0, "ENTRY CHAMBER")}

    for item in items.values():
        if (item.zone or "").upper() == "ENTRY CHAMBER":
            item.discovered_by.add("seraphina")

    assert _all_zone_items_examined(
        character_id="seraphina",
        current_positions=pos,
        items=items,
    )


def test_choose_exploration_waypoint_prefers_unvisited_zone():
    geometry, _ = _load_items_and_geometry()
    pos = {"seraphina": (138.0, 295.0, "ENTRY CHAMBER")}

    waypoint = _choose_exploration_waypoint(
        character_id="seraphina",
        current_positions=pos,
        scene_geometry=geometry,
        visited={"ENTRY CHAMBER"},
    )

    assert waypoint is not None
    zone, x, y = waypoint
    assert zone != "ENTRY CHAMBER"
    assert isinstance(x, float)
    assert isinstance(y, float)


def test_first_passage_redirect_prefers_echo_chamber_over_nonadjacent_branch():
    geometry, _ = _load_items_and_geometry()
    pos = {"seraphina": (137.5, 243.5, "FIRST PASSAGE")}

    waypoint = _choose_exploration_waypoint(
        character_id="seraphina",
        current_positions=pos,
        scene_geometry=geometry,
        visited={"ENTRY CHAMBER", "FIRST PASSAGE"},
    )

    assert waypoint is not None
    zone, x, y = waypoint
    assert zone == "ECHO CHAMBER"
    resolved = geometry.zone_at(Position(x, y))
    assert (resolved or "").upper() == "ECHO CHAMBER"


def test_echo_chamber_puzzle_pressure_block_appears():
    geometry, items = _load_items_and_geometry()
    pos = {"seraphina": (222.0, 200.0, "Echo Chamber")}
    puzzles = build_registry(load_zone_puzzles(ZONES))

    assert _zone_has_unresolved_puzzle(
        current_zone="Echo Chamber",
        items=items,
        puzzles=puzzles,
    )

    block = _build_puzzle_pressure_block(
        current_zone="Echo Chamber",
        items=items,
        puzzles=puzzles,
    )
    assert "Unresolved puzzle" in block
    assert "trigger_glyph" in block or "glyph" in block.lower()


def test_puzzle_focus_prefers_glyphs_over_exit_when_live():
    geometry, items = _load_items_and_geometry()
    pos = {"seraphina": (222.0, 200.0, "Echo Chamber")}
    puzzles = build_registry(load_zone_puzzles(ZONES))

    focus = _choose_puzzle_focus_item(
        character_id="seraphina",
        current_positions=pos,
        items=items,
        puzzles=puzzles,
        current_target_norm="snapped torch",
    )

    assert focus is not None
    label, x, y, zone = focus
    assert zone.upper() == "ECHO CHAMBER"
    assert "glyph" in label.lower()
    assert isinstance(x, float)
    assert isinstance(y, float)


def test_exploration_redirect_hides_unseen_zone_name():
    text = _exploration_redirect_intent(
        zone_name="Rocky Passage",
        known_zones={"ENTRY CHAMBER", "FIRST PASSAGE"},
    )
    assert "Rocky Passage" not in text
    assert "move deeper" in text.lower()


def test_exploration_redirect_names_seen_zone():
    text = _exploration_redirect_intent(
        zone_name="First Passage",
        known_zones={"ENTRY CHAMBER", "FIRST PASSAGE"},
    )
    assert "First Passage" in text


def test_waypoint_for_zone_returns_point_inside_target_zone():
    geometry, _ = _load_items_and_geometry()
    pos = {"seraphina": (137.5, 243.5, "FIRST PASSAGE")}

    wp = _waypoint_for_zone(
        character_id="seraphina",
        current_positions=pos,
        scene_geometry=geometry,
        target_zone="Echo Chamber",
    )

    assert wp is not None
    x, y = wp
    resolved = geometry.zone_at(Position(x, y))
    assert (resolved or "").upper() == "ECHO CHAMBER"


def test_should_block_backtrack_when_leaving_focus_to_seen_zone():
    assert _should_block_backtrack(
        current_zone="First Passage",
        target_zone="Entry Chamber",
        visited={"ENTRY CHAMBER", "FIRST PASSAGE"},
        party_focus_zone="FIRST PASSAGE",
    )


def test_should_not_block_move_to_unseen_zone_from_focus():
    assert not _should_block_backtrack(
        current_zone="First Passage",
        target_zone="Echo Chamber",
        visited={"ENTRY CHAMBER", "FIRST PASSAGE"},
        party_focus_zone="FIRST PASSAGE",
    )


def test_only_explicit_companions_follow_party_focus():
    from types import SimpleNamespace as NS
    from engine.session import _follows_party_focus

    resident = NS(character=NS(character_type="npc", follows_party=False))
    companion = NS(character=NS(character_type="npc", follows_party=True))
    player = NS(character=NS(character_type="player", follows_party=True))

    assert not _follows_party_focus(resident)
    assert _follows_party_focus(companion)
    assert not _follows_party_focus(player)
