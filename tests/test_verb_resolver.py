"""Phase 2b tests: verb resolver maps player intent to authored Interactions."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.verb_resolver import (
    _detect_verb,
    _match_item,
    _normalize_target,
    detect_transfer_verb,
    infer_interaction_target,
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

    def test_open_and_read_are_distinct_interactions(self):
        assert _detect_verb("I open the sealed letter") == "open"
        assert _detect_verb("I read the sealed letter") == "read"


class TestTransferVerbDetection:
    def test_take_phrases(self):
        assert detect_transfer_verb("pick up the torch") == "take"
        assert detect_transfer_verb("I grab the mace") == "take"

    def test_drop_puts_it_on_the_ground(self):
        assert detect_transfer_verb("drop the torch") == "drop"
        assert detect_transfer_verb("set down the torch") == "drop"

    def test_stow_puts_it_in_the_pack(self):
        # "save"/"stow"/"put away" mean stow-to-pack, distinct from "drop".
        assert detect_transfer_verb("save the torch") == "stow"
        assert detect_transfer_verb("stow the torch") == "stow"
        assert detect_transfer_verb("put away the torch") == "stow"

    def test_give_outranks_take(self):
        assert detect_transfer_verb("give the torch to Amara") == "give"

    def test_none_when_no_transfer(self):
        assert detect_transfer_verb("examine the torch") is None
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


class TestTransferTargetInference:
    """infer_interaction_target must resolve the object of a possession verb
    (take/drop/give/stow) — not just examine-class verbs — so the take/drop can
    fire, and disambiguate a shared word toward the real (non-flavor) item."""

    def test_pick_up_resolves_takeable_item(self, items):
        # "pick up" is a transfer verb, not in _VERB_LEXICON; inference still
        # resolves the object (regression: it returned None and the take no-op'd).
        assert infer_interaction_target(
            "I pick up the torch", items, "Entry Chamber") == "Snapped torch"

    def test_drop_and_save_resolve_object(self, items):
        assert infer_interaction_target(
            "drop the torch", items, "Entry Chamber") == "Snapped torch"
        assert infer_interaction_target(
            "save the torch", items, "Entry Chamber") == "Snapped torch"

    def test_torch_disambiguates_to_takeable_over_flavor(self, items):
        # "the torch" token-ties snapped_torch and the flavor "Torch bracket";
        # the decoration loses the tie.
        item = _match_item("pick up the torch", items, "Entry Chamber")
        assert item is not None and item.id == "snapped_torch"

    def test_flavor_item_still_matches_when_named(self, items):
        # Naming the bracket explicitly still resolves it (exact/substring pass).
        item = _match_item("examine the bracket", items, "Entry Chamber")
        assert item is not None and item.id == "torch_bracket"

    def test_non_interaction_text_still_none(self, items):
        # No verb (interaction or transfer) -> no target.
        assert infer_interaction_target(
            "the torch is over there", items, "Entry Chamber") is None
