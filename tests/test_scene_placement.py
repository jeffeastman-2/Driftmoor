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
    """End-to-end: the migrated scene places exactly its authored cast, from the
    scene's own ``position`` bullets (no hardcoded coords — they're read from the
    file so re-authoring placement doesn't break this) and with no stray keys."""
    from engine.md_loader import _load, _parse_all_char_sections
    path = Path("scenes/echoing_caverns.md")
    authored = {cid: m["position"]
                for cid, m in _parse_all_char_sections(_load(path)).items()
                if m.get("position")}
    assert authored, "scene should author placement bullets"

    cfg = configure_from_md(path)
    sp = cfg.scene_geometry.starting_positions
    # Only the authored cast is seeded — geometry no longer contributes keys.
    assert set(sp) == set(authored)
    for cid, pos_str in authored.items():
        x, y = (float(n) for n in pos_str.split(",")[:2])
        assert (sp[cid].x, sp[cid].y) == (x, y)               # scene coord seeded
        # Zone is derived from the coordinate, not authored.
        assert cfg.scene_geometry.zone_at(sp[cid]) == cfg.scene_geometry.zone_at(
            Position(x, y))
