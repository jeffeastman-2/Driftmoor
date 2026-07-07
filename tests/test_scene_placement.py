"""Character placement lives on the scene, not GEOMETRY.

Placement is authored as a raw ``- **position:** x, y[, z]`` bullet on each
``### <char_id>`` block in ``scenes/<scene>.md``; the zone is always *derived*
from the coordinate via ``zone_at`` (never authored). GEOMETRY.md is a pure
stage and carries no positions.
"""
from pathlib import Path

from engine.md_loader import _resolve_start_position, configure_from_md
from models.space_time import Polygon, Position, SceneGeometry


def _geo():
    # Two disjoint square zones so zone_at is unambiguous.
    return SceneGeometry(
        name="test", place_path="", z_level=0.0, width=200, height=200,
        origin=Position(0, 0),
        zones={
            "Entry Chamber": Polygon(vertices=[(0, 0), (10, 0), (10, 10), (0, 10)]),
            "Secret Chamber": Polygon(vertices=[(100, 100), (110, 100), (110, 110), (100, 110)]),
        },
    )


def test_scene_position_seeds_and_zone_is_derived():
    g = _geo()
    pos, zone = _resolve_start_position("hero", "5, 5", g)
    assert (pos.x, pos.y, pos.z) == (5.0, 5.0, 0.0)
    assert zone == "ENTRY CHAMBER"                 # derived from the coordinate


def test_optional_z_is_parsed():
    g = _geo()
    pos, _zone = _resolve_start_position("hero", "5, 5, 3.5", g)
    assert (pos.x, pos.y, pos.z) == (5.0, 5.0, 3.5)


def test_zone_derived_for_second_zone():
    g = _geo()
    pos, zone = _resolve_start_position("hero", "105, 105", g)
    assert (pos.x, pos.y) == (105.0, 105.0)
    assert zone == "SECRET CHAMBER"


def test_position_outside_all_zones_has_empty_zone():
    pos, zone = _resolve_start_position("hero", "500, 500", _geo())
    assert (pos.x, pos.y) == (500.0, 500.0)
    assert zone == ""


def test_no_position_returns_none():
    assert _resolve_start_position("ghost", "", _geo()) is None


def test_malformed_position_returns_none():
    assert _resolve_start_position("hero", "nope", _geo()) is None
    assert _resolve_start_position("hero", "5", _geo()) is None   # needs x and y


def test_echoing_caverns_seeds_from_scene():
    """End-to-end: the migrated scene places the whole cast; zones derive."""
    cfg = configure_from_md(Path("scenes/echoing_caverns.md"))
    sp = cfg.scene_geometry.starting_positions
    assert (sp["seraphina"].x, sp["seraphina"].y) == (155.0, 285.0)
    assert (sp["giant_spider"].x, sp["giant_spider"].y) == (64.0, 195.0)
    assert cfg.scene_geometry.zone_at(sp["seraphina"]) == "Entry Chamber"
    assert cfg.scene_geometry.zone_at(sp["giant_spider"]) == "Secret Chamber"
    # Geometry no longer seeds stray keys — only the authored cast is present.
    assert set(sp) == {"seraphina", "thorgrim", "amara", "gilthaness", "giant_spider"}
