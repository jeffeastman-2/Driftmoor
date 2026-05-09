"""Phase 3b.1 tests: examined-tag and out-of-zone interaction guard."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.session import _build_perception
from engine.verb_resolver import resolve_item_interaction
from models.contents_loader import load_contents_with_geometry
from models.geometry_loader import load_geometry


CONTENTS = Path("scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md")
GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


@pytest.fixture
def geometry():
    return load_geometry(GEOMETRY)


@pytest.fixture
def items(geometry):
    # Fresh load each test so discovered_by mutations don't leak.
    return load_contents_with_geometry(CONTENTS, GEOMETRY, scene_geometry=geometry)


class TestExaminedTag:
    def test_unexamined_has_no_tag(self, geometry, items):
        positions = {"t": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "t", geometry, positions, set(), items=items,
        )
        assert "(already examined)" not in perception

    def test_examined_item_is_tagged(self, geometry, items):
        # Mark drag_marks as discovered.
        items["drag_marks"].discovered_by.add("seraphina")
        positions = {"t": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "t", geometry, positions, set(), items=items,
        )
        # Find the drag-marks line and confirm it carries the tag while
        # an unexamined item (Snapped torch) does not.
        drag_line = next(
            line for line in perception.splitlines()
            if "Drag marks" in line
        )
        torch_line = next(
            line for line in perception.splitlines()
            if "Snapped torch" in line
        )
        assert "(already examined)" in drag_line
        assert "(already examined)" not in torch_line


class TestOutOfZoneGuard:
    def test_match_in_actor_zone_succeeds(self, items):
        result = resolve_item_interaction(
            intent_text="examine the drag marks",
            interaction_target="Drag marks",
            items=items,
            character_zone="ENTRY CHAMBER",
        )
        assert result is not None
        item, _ = result
        assert item.id == "drag_marks"

    def test_match_in_other_zone_fails(self, items):
        # Actor in First Passage cannot resolve Entry-Chamber items.
        result = resolve_item_interaction(
            intent_text="examine the drag marks",
            interaction_target="Drag marks",
            items=items,
            character_zone="FIRST PASSAGE",
        )
        assert result is None

    def test_zoneless_match_finds_item_for_diagnostic(self, items):
        # The session uses a second pass with character_zone=None to
        # produce an "out of reach" message that names the item's actual
        # zone — confirm that pass succeeds.
        result = resolve_item_interaction(
            intent_text="examine the drag marks",
            interaction_target="Drag marks",
            items=items,
            character_zone=None,
        )
        assert result is not None
        item, _ = result
        assert item.id == "drag_marks"
        assert item.zone and "Entry" in item.zone
