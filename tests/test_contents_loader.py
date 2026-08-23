"""Tests for legacy CONTENTS parsing and current zone-content loading."""

from pathlib import Path

import pytest

from models.contents_loader import (
    load_contents_with_geometry,
    load_zone_contents_with_geometry,
    load_zone_puzzles,
    parse_contents_md,
    parse_zone_md,
)
from models.geometry_loader import load_geometry


SCENE = Path("scenario/places/obelisk_reach/echoing_caverns")
GEOMETRY = SCENE / "GEOMETRY.md"
ZONES = SCENE / "zones"


def test_legacy_contents_parser_remains_available():
    parsed = parse_contents_md(
        "# CONTENTS.md — Test\n\n## Items\n\n### old_key\n"
        "An old iron key.\n\n*Properties:*\n- Pickable: yes\n"
    )
    assert "old iron key" in parsed["items"]["old_key"].description


def test_zone_parser_reads_affordances_and_interactions():
    parsed = parse_zone_md(
        "# Room\n\n## Items\n### lever\n- label: Lever\n"
        "- size: small\n- pickable: false\n- flavor_only: false\n"
        "- description: A bronze lever.\n- interactions:\n"
        "  - examine: Its hinge is clean.\n  - press: It moves.\n"
    )
    lever = parsed["lever"]
    assert not lever.pickable
    assert lever.pressable
    assert {i.verb for i in lever.interactions} == {"examine", "press"}


def test_echoing_caverns_zone_items_match_geometry():
    geometry = load_geometry(GEOMETRY)
    items = load_zone_contents_with_geometry(
        ZONES, GEOMETRY, scene_geometry=geometry
    )
    assert len(items) == 16
    assert items["mace_plus_one"].label == "Mace +1"
    assert items["mace_plus_one"].zone == "Secret Chamber"
    assert items["trigger_glyph_top"].pressable


def test_echoing_caverns_puzzle_lives_in_zone_content():
    puzzle = load_zone_puzzles(ZONES)["west_wall_glyph_sequence"]
    assert puzzle.solution == [
        "trigger_glyph_top", "trigger_glyph_bottom", "trigger_glyph_middle"
    ]


def test_zone_loader_rejects_geometry_item_mismatch(tmp_path):
    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text(
        "# GEOMETRY.md — Test\n\n## Items\n\n"
        "| id | x | y | label |\n|---|---|---|---|\n"
        "| placed | 1 | 1 | Placed |\n", encoding="utf-8",
    )
    zones = tmp_path / "zones"
    zones.mkdir()
    (zones / "room.md").write_text(
        "# Room\n\n## Items\n\n### other\n"
        "- label: Other\n- description: Other.\n", encoding="utf-8",
    )
    with pytest.raises(ValueError, match="not in GEOMETRY"):
        load_zone_contents_with_geometry(zones, geometry)


def test_legacy_geometry_merge_still_supported(tmp_path):
    contents = tmp_path / "CONTENTS.md"
    contents.write_text(
        "# CONTENTS.md — Test\n\n## Items\n\n### key\nAn iron key.\n",
        encoding="utf-8",
    )
    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text(
        "# GEOMETRY.md — Test\n\n## Items\n\n"
        "| id | x | y | label |\n|---|---|---|---|\n"
        "| key | 2 | 3 | Iron key |\n", encoding="utf-8",
    )
    items = load_contents_with_geometry(contents, geometry)
    assert items["key"].position.x == 2
    assert items["key"].label == "Iron key"
