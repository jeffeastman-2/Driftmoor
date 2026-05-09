"""Phase 2b tests: verb resolver maps player intent to authored Interactions."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.verb_resolver import (
    _detect_verb,
    _match_item,
    _normalize_target,
    resolve_item_interaction,
)
from models.contents_loader import load_contents_with_geometry
from models.geometry_loader import load_geometry


CONTENTS = Path("scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md")
GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


@pytest.fixture(scope="module")
def geometry():
    return load_geometry(GEOMETRY)


@pytest.fixture(scope="module")
def items(geometry):
    return load_contents_with_geometry(CONTENTS, GEOMETRY, scene_geometry=geometry)


class TestVerbDetection:
    def test_examine(self):
        assert _detect_verb("I examine the snapped torch carefully") == "examine"

    def test_inspect_maps_to_examine(self):
        assert _detect_verb("Inspect the drag marks for clues") == "examine"

    def test_look_at_phrase(self):
        assert _detect_verb("I look at the bracket") == "examine"

    def test_search(self):
        assert _detect_verb("I will search the discarded pack") == "search"

    def test_investigate_maps_to_search(self):
        assert _detect_verb("Investigate the area for fragments") == "search"

    def test_no_match(self):
        assert _detect_verb("I draw my axe and swing wildly") is None

    def test_empty(self):
        assert _detect_verb("") is None
        assert _detect_verb(None) is None  # type: ignore[arg-type]


class TestNormalizeTarget:
    def test_strips_articles(self):
        assert _normalize_target("the Snapped torch") == "snapped torch"
        assert _normalize_target("A Discarded Pack") == "discarded pack"

    def test_strips_trailing_punct(self):
        assert _normalize_target("Drag marks.") == "drag marks"
        assert _normalize_target("Mace +1!") == "mace +1"


class TestMatchItem:
    def test_exact_label(self, items):
        it = _match_item("Drag marks", items, "Entry Chamber")
        assert it is not None and it.id == "drag_marks"

    def test_exact_id(self, items):
        it = _match_item("snapped_torch", items, "Entry Chamber")
        assert it is not None and it.id == "snapped_torch"

    def test_with_article(self, items):
        it = _match_item("the Drag marks", items, "Entry Chamber")
        assert it is not None and it.id == "drag_marks"

    def test_zone_filters(self, items):
        # Mace +1 is in Secret Chamber; should not match from Entry Chamber.
        assert _match_item("Mace +1", items, "Entry Chamber") is None
        assert _match_item("Mace +1", items, "Secret Chamber") is not None

    def test_no_zone_searches_all(self, items):
        assert _match_item("Mace +1", items, None) is not None

    def test_substring_label(self, items):
        # Player narration sometimes adds qualifiers.
        it = _match_item("the discarded pack on the floor", items, "Entry Chamber")
        assert it is not None and it.id == "discarded_pack"

    def test_unknown(self, items):
        assert _match_item("nonexistent thing", items, "Entry Chamber") is None


class TestResolveInteraction:
    def test_examine_drag_marks(self, items):
        result = resolve_item_interaction(
            intent_text="Examine the drag marks closely",
            interaction_target="Drag marks",
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is not None
        item, interaction = result
        assert item.id == "drag_marks"
        assert interaction.verb == "examine"
        assert interaction.response  # non-empty DM-authored text

    def test_search_falls_back_to_search_alias(self, items):
        # discarded_pack lists "examine without disturbing" — the resolver
        # should match by verb-prefix when an exact verb hit fails.
        result = resolve_item_interaction(
            intent_text="I search the discarded pack for valuables",
            interaction_target="Discarded pack",
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is not None
        _, interaction = result
        # Multi-word verb: starts with examine (search falls back to examine).
        assert interaction.verb.lower().startswith("examine")

    def test_no_verb_defaults_to_examine(self, items):
        # Player just declares "Interact: Drag marks" with vague intent.
        result = resolve_item_interaction(
            intent_text="Move forward and check what's on the floor",
            interaction_target="Drag marks",
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is not None
        _, interaction = result
        assert interaction.matches("examine")

    def test_zone_gating_blocks_far_items(self, items):
        # Cannot examine Mace +1 from Entry Chamber.
        result = resolve_item_interaction(
            intent_text="Examine the mace",
            interaction_target="Mace +1",
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is None

    def test_no_target_returns_none(self, items):
        result = resolve_item_interaction(
            intent_text="Examine the drag marks",
            interaction_target=None,
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is None

    def test_no_items_returns_none(self):
        result = resolve_item_interaction(
            intent_text="Examine the drag marks",
            interaction_target="Drag marks",
            items=None,
            character_zone="Entry Chamber",
        )
        assert result is None

    def test_unknown_target_returns_none(self, items):
        result = resolve_item_interaction(
            intent_text="Examine the unicorn",
            interaction_target="Unicorn",
            items=items,
            character_zone="Entry Chamber",
        )
        assert result is None

    def test_attack_intent_no_examine_match(self, items):
        # Pure combat intent on an item with no attack interaction returns
        # None (we still need a verb match in lexicon -> falls back to
        # examine -> examine exists -> match. So this should still match
        # via the default-to-examine fallback). Verify expected behaviour.
        result = resolve_item_interaction(
            intent_text="I swing my axe at it",
            interaction_target="Drag marks",
            items=items,
            character_zone="Entry Chamber",
        )
        # Falls back to examine; drag_marks has examine -> should resolve.
        assert result is not None
        _, interaction = result
        assert interaction.matches("examine")
