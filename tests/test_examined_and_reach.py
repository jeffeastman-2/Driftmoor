"""Phase 3b.1 tests: examined-tag and out-of-zone interaction guard."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.session import _build_perception
from engine.verb_resolver import resolve_item_interaction
from models.contents_loader import load_contents_with_geometry
from models.geometry_loader import load_geometry


CONTENTS = Path("scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md")
GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


def _dwarf_observer(cid):
    """Minimal characters dict for an observer with darkvision (Dwarf)."""
    char = SimpleNamespace(
        race="Mountain Dwarf", senses=[], features=[], faction="party",
    )
    return {cid: SimpleNamespace(character=char, scene_handle="")}


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
            "t", geometry, positions, set(),
            characters=_dwarf_observer("t"), items=items,
        )
        assert "(already examined)" not in perception

    def test_examined_item_is_tagged(self, geometry, items):
        # Mark drag_marks as discovered.
        items["drag_marks"].discovered_by.add("seraphina")
        positions = {"t": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "t", geometry, positions, set(),
            characters=_dwarf_observer("t"), items=items,
        )
        # Find the drag-marks line and confirm it carries the tag while
        # an unexamined item (the snapped torch, shown by its far-band text)
        # does not.
        drag_line = next(
            line for line in perception.splitlines()
            if "Drag marks" in line
        )
        torch_line = next(
            line for line in perception.splitlines()
            if "pale streak" in line
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


class TestDescriptionFallback:
    def test_flavor_only_item_falls_back_to_description(self, items):
        # torch_bracket has no *Interactions* block — examine should
        # still return a synthetic Interaction built from the description
        # so discovered_by gets populated and the item is tagged
        # already-examined in subsequent perception ticks.
        result = resolve_item_interaction(
            intent_text="examine the torch bracket",
            interaction_target="Torch bracket",
            items=items,
            character_zone="ENTRY CHAMBER",
        )
        assert result is not None
        item, interaction = result
        assert item.id == "torch_bracket"
        assert interaction.verb == "examine"
        # Description text should have flowed into the response.
        assert interaction.response
        assert "iron" in interaction.response.lower() or "bracket" in interaction.response.lower()

    def test_authored_interaction_still_wins(self, items):
        # drag_marks DOES have an authored examine response; fallback
        # must not shadow it.
        result = resolve_item_interaction(
            intent_text="examine the drag marks",
            interaction_target="Drag marks",
            items=items,
            character_zone="ENTRY CHAMBER",
        )
        assert result is not None
        _, interaction = result
        assert "body dragged south" in interaction.response.lower() or \
               "passage" in interaction.response.lower()
