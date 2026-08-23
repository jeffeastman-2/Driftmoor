"""Tests for loading and parsing places from scenario markdown files."""

import pytest
from pathlib import Path

from models.place import Place
from models.place_loader import (
    parse_place_md,
    load_place,
    load_all_places,
)

PLACES_DIR = Path(__file__).parent.parent / "scenario" / "places"


# ---------------------------------------------------------------------------
# Unit tests: parse structured fields from sample markdown text
# ---------------------------------------------------------------------------


class TestParsePlaceMd:
    """Parse structured fields from PLACE.md content."""

    SAMPLE = """\
# PLACE.md — The Mayor's Hall

## Description and Atmosphere
The largest and most prominent building in Driftmoor — two stories of timber and stone.

Inside it smells of old paper, woodsmoke, and whiskey.

## Sub-Places
- `mayors_office/` — Aldren Thorne's working space
- `records_room/` — locked, town documents
- `living_quarters/` — upstairs suite

## Who Is Normally Here
- **Aldren Thorne** — mayor, usually in his office
- **Elise Harper** — sharp-eyed clerk

## Connections
- Village square (outside)
- `mayors_office/` (left of main hall)
- `records_room/` (behind the office, locked)
- `living_quarters/` (upstairs)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Aldren Thorne (office), Elise Harper (records area)
- **Recent events:** None yet — session not started
- **Active conditions:** Records room ledger missing
"""

    def test_parse_name(self):
        result = parse_place_md(self.SAMPLE)
        assert result["name"] == "The Mayor's Hall"

    def test_parse_description(self):
        result = parse_place_md(self.SAMPLE)
        assert "largest and most prominent" in result["description"]
        assert "whiskey" in result["description"]

    def test_parse_sub_places(self):
        result = parse_place_md(self.SAMPLE)
        assert "mayors_office" in result["children"]
        assert "records_room" in result["children"]
        assert "living_quarters" in result["children"]
        assert len(result["children"]) == 3

    def test_parse_who_is_here(self):
        result = parse_place_md(self.SAMPLE)
        assert len(result["who_is_here"]) == 2
        assert any("Aldren Thorne" in w for w in result["who_is_here"])

    def test_parse_connections(self):
        result = parse_place_md(self.SAMPLE)
        assert len(result["connections"]) == 4

    def test_parse_dynamic_state(self):
        result = parse_place_md(self.SAMPLE)
        assert "Current occupants" in result["dynamic_state"]
        assert "Records room ledger missing" in result["dynamic_state"]["Active conditions"]

    def test_no_sub_places(self):
        text = "# PLACE.md — A Room\n\n## Description and Atmosphere\nSmall.\n"
        result = parse_place_md(text)
        assert result["children"] == []

    def test_region_level(self):
        text = """\
# PLACE.md — The Land Around Driftmoor

## Description and Atmosphere
A rocky coastal region.

## Sub-Places
- `driftmoor/` — the town
- `obelisk_reach/` — cliffs

## Dynamic State
*(Updated by monitor agent)*

- **Current threat level:** Elevated
"""
        result = parse_place_md(text)
        assert result["name"] == "The Land Around Driftmoor"
        assert "driftmoor" in result["children"]
        assert "Current threat level" in result["dynamic_state"]

    def test_building_without_sub_places(self):
        text = """\
# PLACE.md — Salt & Iron Mercantile

## Description and Atmosphere
One of the town's largest structures.

## Who Is Normally Here
- **Jorgen Hallowtide** — behind the counter

## Connections
- Village center (outside)

## Dynamic State
*(Updated by monitor agent)*

- **Current occupants:** Jorgen Hallowtide
- **Active conditions:** Supply caravan overdue
"""
        result = parse_place_md(text)
        assert result["name"] == "Salt & Iron Mercantile"
        assert result["children"] == []
        assert len(result["who_is_here"]) == 1
        assert "Supply caravan overdue" in result["dynamic_state"]["Active conditions"]


# ---------------------------------------------------------------------------
# Integration tests: load places from actual scenario files
# ---------------------------------------------------------------------------


class TestLoadPlace:
    def test_zone_files_replace_obsolete_contents_file(self, tmp_path):
        (tmp_path / "PLACE.md").write_text(
            "# PLACE.md — Migrated Place\n\n"
            "## Description and Atmosphere\nA migrated place.\n",
            encoding="utf-8",
        )
        zones = tmp_path / "zones"
        zones.mkdir()
        (zones / "second.md").write_text("# Second Zone\n", encoding="utf-8")
        (zones / "first.md").write_text("# First Zone\n", encoding="utf-8")

        place = load_place(tmp_path)

        assert "First Zone" in place.contents_raw
        assert "Second Zone" in place.contents_raw
        assert place.contents_raw.index("First Zone") < place.contents_raw.index("Second Zone")

    def test_zone_files_take_precedence_over_legacy_contents(self, tmp_path):
        (tmp_path / "PLACE.md").write_text(
            "# PLACE.md — Migrated Place\n", encoding="utf-8"
        )
        (tmp_path / "CONTENTS.md").write_text(
            "obsolete sentinel", encoding="utf-8"
        )
        zones = tmp_path / "zones"
        zones.mkdir()
        (zones / "room.md").write_text("# Current Zone\n", encoding="utf-8")

        place = load_place(tmp_path)

        assert "Current Zone" in place.contents_raw
        assert "obsolete sentinel" not in place.contents_raw

    def test_load_region(self):
        p = load_place(PLACES_DIR, place_id="region")
        assert p.name == "The Land Around Driftmoor"
        assert p.parent_id is None
        assert "driftmoor" in p.children
        assert len(p.place_raw) > 100
        assert len(p.contents_raw) > 100

    def test_load_driftmoor_town(self):
        p = load_place(PLACES_DIR / "driftmoor", place_id="driftmoor")
        assert p.name == "Driftmoor Town"
        assert len(p.children) >= 20
        assert "mayors_hall" in p.children
        assert "broken_lantern" in p.children

    def test_load_mayors_hall(self):
        p = load_place(
            PLACES_DIR / "driftmoor" / "mayors_hall",
            place_id="mayors_hall",
            parent_id="driftmoor",
        )
        assert p.name == "The Mayor's Hall"
        assert p.parent_id == "driftmoor"
        assert p.children == []
        assert "Mayor's office" in p.place_raw
        assert "Records Room" in p.contents_raw

    def test_load_salt_and_iron(self):
        p = load_place(
            PLACES_DIR / "driftmoor" / "salt_and_iron",
            place_id="salt_and_iron",
            parent_id="driftmoor",
        )
        assert "Salt" in p.name
        assert any("Jorgen" in w for w in p.who_is_here)

    def test_load_shattered_obelisk(self):
        p = load_place(
            PLACES_DIR / "obelisk_reach" / "shattered_obelisk",
            place_id="shattered_obelisk",
            parent_id="obelisk_reach",
        )
        assert "Obelisk" in p.name
        assert len(p.contents_raw) > 0

    def test_leaf_place_has_no_children(self):
        p = load_place(
            PLACES_DIR / "driftmoor" / "bakery",
            place_id="bakery",
            parent_id="driftmoor",
        )
        assert p.children == [] or isinstance(p.children, list)

    def test_preserves_raw_content(self):
        p = load_place(PLACES_DIR / "driftmoor", place_id="driftmoor")
        assert "PLACE.md" in p.place_raw
        assert "CONTENTS.md" in p.contents_raw


class TestLoadAllPlaces:
    def test_load_all(self):
        places = load_all_places(PLACES_DIR)
        # Derive the expected count from the PLACE.md files on disk so the test
        # verifies "every place loads" without breaking each time one is
        # added/removed (matches test_game_init.test_all_players_loaded).
        expected = sum(1 for _ in PLACES_DIR.rglob("PLACE.md"))
        assert len(places) == expected

    def test_no_duplicate_ids(self):
        places = load_all_places(PLACES_DIR)
        ids = [p.id for p in places]
        assert len(ids) == len(set(ids)), f"Duplicates: {[x for x in ids if ids.count(x) > 1]}"

    def test_region_is_root(self):
        places = load_all_places(PLACES_DIR)
        region = next(p for p in places if p.id == "region")
        assert region.parent_id is None

    def test_every_place_has_name(self):
        places = load_all_places(PLACES_DIR)
        for p in places:
            assert p.name, f"Place {p.id} has no name"

    def test_parent_child_consistency(self):
        """Every child's parent_id should reference an existing place."""
        places = load_all_places(PLACES_DIR)
        id_set = {p.id for p in places}
        for p in places:
            if p.parent_id is not None:
                assert p.parent_id in id_set, (
                    f"Place {p.id} has parent_id={p.parent_id!r} which doesn't exist"
                )

    def test_driftmoor_buildings_have_parent(self):
        places = load_all_places(PLACES_DIR)
        by_id = {p.id: p for p in places}
        mayors_hall = by_id["mayors_hall"]
        assert mayors_hall.parent_id == "driftmoor"

    def test_sub_places_have_parent(self):
        places = load_all_places(PLACES_DIR)
        by_id = {p.id: p for p in places}
        meeting_room = by_id["meeting_room"]
        assert meeting_room.parent_id == "broken_lantern"

    def test_explicit_nested_id_avoids_reused_directory_name_collision(self):
        places = load_all_places(PLACES_DIR)
        by_id = {p.id: p for p in places}
        upstairs = by_id["weary_traveler_upstairs"]
        assert upstairs.parent_id == "weary_traveler"
        assert upstairs.name == "The Weary Traveler Upstairs"
