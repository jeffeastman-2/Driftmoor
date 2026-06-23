"""Tests for the CONTENTS.md parser against the echoing_caverns exemplar."""

from __future__ import annotations

from pathlib import Path

import pytest

from models.contents_loader import (
    load_contents,
    load_contents_with_geometry,
    parse_contents_md,
)
from models.geometry_loader import load_geometry
from models.item import Interaction, Item


CONTENTS_PATH = Path("scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md")
GEOMETRY_PATH = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


# ---------------------------------------------------------------------------
# Top-level structure
# ---------------------------------------------------------------------------


class TestParseContentsTopLevel:

    @pytest.fixture
    def parsed(self):
        return parse_contents_md(CONTENTS_PATH.read_text(encoding="utf-8"))

    def test_returns_items_dict(self, parsed):
        assert isinstance(parsed["items"], dict)
        assert all(isinstance(v, Item) for v in parsed["items"].values())

    def test_all_exemplar_items_present(self, parsed):
        expected = {
            "torch_bracket", "wall_scratches",
            "snapped_torch", "old_bloodstain", "discarded_pack", "drag_marks",
            "carved_symbols", "obelisk_fragment",
            "trigger_glyph_top", "trigger_glyph_middle", "trigger_glyph_bottom",
            "secret_burial_vault", "mace_plus_one",
            "companion_remains", "holy_symbol_pelor", "parchment_fragment",
        }
        assert set(parsed["items"]) == expected

    def test_creatures_section_extracted(self, parsed):
        assert "Giant spider" in parsed["creatures_section"]

    def test_zones_section_extracted(self, parsed):
        assert "Entry Chamber" in parsed["zones_section"]
        assert "Echo Chamber" in parsed["zones_section"]

    def test_landmarks_section_extracted(self, parsed):
        assert "first_passage_mouth" in parsed["landmarks_section"]

    def test_dm_notes_section_extracted(self, parsed):
        assert "Secret door" in parsed["dm_notes_section"]


# ---------------------------------------------------------------------------
# Properties parenthetical
# ---------------------------------------------------------------------------


class TestProperties:

    @pytest.fixture(scope="class")
    def items(self):
        return load_contents(CONTENTS_PATH)

    def test_torch_bracket_flavor_not_pickable(self, items):
        item = items["torch_bracket"]
        assert item.pickable is False
        assert item.flavor_only is True
        assert item.pressable is False
        assert item.quest_item_for is None

    def test_mace_plus_one_pickable(self, items):
        item = items["mace_plus_one"]
        assert item.pickable is True

    def test_trigger_glyph_top_pressable(self, items):
        item = items["trigger_glyph_top"]
        assert item.pressable is True
        assert item.pickable is False

    def test_trigger_glyph_middle_inherits_via_ref(self, items):
        item = items["trigger_glyph_middle"]
        assert item.interactions_ref == "trigger_glyph_top"
        # Cross-reference resolution copies trigger_glyph_top's interactions.
        assert item.find_interaction("press") is not None

    def test_companion_remains_quest_item(self, items):
        item = items["companion_remains"]
        # ``Pickup-able with care`` → pickable=True
        assert item.pickable is True
        # ``quest item for Father Elden``
        assert item.quest_item_for is not None
        assert "elden" in item.quest_item_for.lower()

    def test_extra_facts_preserved(self, items):
        # mace_plus_one has unrecognized fact "+1 mace, 1d6+1 bludgeoning..."
        item = items["mace_plus_one"]
        assert any("+1 mace" in fact for fact in item.extra_facts)


# ---------------------------------------------------------------------------
# Description prose
# ---------------------------------------------------------------------------


class TestDescription:

    @pytest.fixture(scope="class")
    def items(self):
        return load_contents(CONTENTS_PATH)

    def test_snapped_torch_description_is_player_facing(self, items):
        desc = items["snapped_torch"].description
        assert "snapped clean" in desc
        # Properties parenthetical and Interactions block stripped.
        assert "Interactions" not in desc

    def test_torch_bracket_description_strips_properties(self, items):
        desc = items["torch_bracket"].description
        assert "Not pickup-able" not in desc
        assert "iron bracket" in desc.lower()


# ---------------------------------------------------------------------------
# Size and apparent-size appearance bands
# ---------------------------------------------------------------------------


class TestAppearanceBands:

    @pytest.fixture(scope="class")
    def items(self):
        return load_contents(CONTENTS_PATH)

    def test_size_keyword_parsed(self, items):
        # small → 2.5 ft, large → 10 ft.
        assert items["snapped_torch"].size_ft == 2.5
        assert items["obelisk_fragment"].size_ft == 10.0
        assert items["drag_marks"].size_ft == 10.0

    def test_named_bands_parsed(self, items):
        bands = items["snapped_torch"].appearance_bands
        assert set(bands) == {"intermediate", "far", "distant"}
        assert "pale" in bands["far"]

    def test_obelisk_bands_parsed(self, items):
        bands = items["obelisk_fragment"].appearance_bands
        assert "intermediate" in bands
        assert "far" in bands

    def test_size_and_band_block_stripped_from_description(self, items):
        desc = items["snapped_torch"].description
        assert "Size:" not in desc
        assert "Appearance by distance" not in desc
        assert "pale length of wood" not in desc

    def test_band_block_does_not_leak_into_interactions(self, items):
        # The authored band text must not be misread as an interaction.
        item = items["snapped_torch"]
        for inter in item.interactions:
            assert "pale length of wood" not in inter.response

    def test_unsized_item_defaults_to_zero(self):
        # An item authored with no *Size:* line reports 0.0 (the engine then
        # treats it as a default medium object).
        md = (
            "## Items\n\n"
            "### plain_item\n"
            "A nondescript thing with no declared size.\n"
        )
        parsed = parse_contents_md(md)
        item = parsed["items"]["plain_item"]
        assert item.size_ft == 0.0
        assert item.appearance_bands == {}


# ---------------------------------------------------------------------------
# Interactions
# ---------------------------------------------------------------------------


class TestInteractions:

    @pytest.fixture(scope="class")
    def items(self):
        return load_contents(CONTENTS_PATH)

    def test_snapped_torch_has_examine_and_pickup(self, items):
        item = items["snapped_torch"]
        assert item.find_interaction("examine") is not None
        assert item.find_interaction("pick up") is not None
        # Alias
        assert item.find_interaction("take") is not None

    def test_alias_canonicalization(self, items):
        item = items["snapped_torch"]
        inter = item.find_interaction("pick up")
        assert inter.verb == "pick up"
        assert "take" in inter.aliases

    def test_condition_captured(self, items):
        item = items["trigger_glyph_top"]
        # Two ``press`` interactions, one for crack-closed and one for
        # crack-open. Both should be present with their conditions captured.
        all_press = item.find_interactions("press")
        assert len(all_press) == 2
        conditions = {i.condition for i in all_press}
        assert any("closed" in c for c in conditions)
        assert any("open" in c for c in conditions)

    def test_response_text_captured(self, items):
        item = items["snapped_torch"]
        inter = item.find_interaction("examine")
        assert "across the grain" in inter.response

    def test_carved_symbols_make_rubbing_with_condition(self, items):
        item = items["carved_symbols"]
        inter = item.find_interaction("make rubbing")
        assert inter is not None
        assert "parchment" in inter.condition.lower()
        assert "carving_rubbing" in inter.response


# ---------------------------------------------------------------------------
# Cross-references
# ---------------------------------------------------------------------------


class TestCrossReferences:

    @pytest.fixture(scope="class")
    def items(self):
        return load_contents(CONTENTS_PATH)

    def test_middle_glyph_inherits_top_interactions(self, items):
        top = items["trigger_glyph_top"]
        middle = items["trigger_glyph_middle"]
        bottom = items["trigger_glyph_bottom"]
        # Top has its own; middle and bottom inherit via "see <id> for interactions".
        assert middle.interactions_ref == "trigger_glyph_top"
        assert bottom.interactions_ref == "trigger_glyph_top"
        # Each inherited verb is reachable.
        for inter in top.interactions:
            assert middle.find_interaction(inter.verb) is not None
            assert bottom.find_interaction(inter.verb) is not None


# ---------------------------------------------------------------------------
# Geometry merge
# ---------------------------------------------------------------------------


class TestLoadWithGeometry:

    @pytest.fixture(scope="class")
    def items(self):
        geometry = load_geometry(GEOMETRY_PATH)
        return load_contents_with_geometry(
            CONTENTS_PATH, GEOMETRY_PATH, scene_geometry=geometry,
        )

    def test_position_populated(self, items):
        item = items["snapped_torch"]
        assert item.position is not None
        assert item.position.x == 132
        assert item.position.y == 268

    def test_label_populated(self, items):
        assert items["mace_plus_one"].label == "Mace +1"

    def test_zone_resolved(self, items):
        # snapped_torch (132, 268) sits in Entry Chamber.
        assert items["snapped_torch"].zone == "Entry Chamber"
        # mace_plus_one (64, 195) sits in Secret Chamber.
        assert items["mace_plus_one"].zone == "Secret Chamber"


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestValidation:

    def test_missing_geometry_raises(self, tmp_path):
        contents = tmp_path / "CONTENTS.md"
        contents.write_text(
            "# CONTENTS.md — Test\n\n## Items\n\n### orphan\nA lonely thing.\n",
            encoding="utf-8",
        )
        geometry = tmp_path / "GEOMETRY.md"
        geometry.write_text(
            "# GEOMETRY.md — Test\n\n## Items\n\n"
            "| id | x | y | label |\n|----|---|---|-------|\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="not in GEOMETRY"):
            load_contents_with_geometry(contents, geometry)

    def test_missing_contents_raises(self, tmp_path):
        contents = tmp_path / "CONTENTS.md"
        contents.write_text(
            "# CONTENTS.md — Test\n\n## Items\n", encoding="utf-8",
        )
        geometry = tmp_path / "GEOMETRY.md"
        geometry.write_text(
            "# GEOMETRY.md — Test\n\n## Items\n\n"
            "| id | x | y | label |\n|----|---|---|-------|\n"
            "| stranded | 1 | 2 | Stranded |\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="not in CONTENTS"):
            load_contents_with_geometry(contents, geometry)

    def test_unknown_cross_reference_raises(self, tmp_path):
        contents = tmp_path / "CONTENTS.md"
        contents.write_text(
            "# CONTENTS.md — Test\n\n## Items\n\n"
            "### thing\nA thing.\n\n*(Pickup-able. See nonexistent for interactions.)*\n",
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="unknown interactions source"):
            load_contents(contents)


class TestWeaponSpec:
    def test_weapon_line_parsed_into_spec(self):
        text = (
            "# CONTENTS.md — Test\n\n## Items\n\n"
            "### banded_mace\n"
            "A heavy mace.\n\n"
            "*(Pickup-able; +1 mace.)*\n\n"
            "*Weapon:* mace+1\n"
            "*Size:* small\n"
        )
        items = parse_contents_md(text)["items"]
        assert items["banded_mace"].weapon_spec == "mace+1"
        # The weapon line is consumed, not left in the description.
        assert "Weapon:" not in items["banded_mace"].description

    def test_no_weapon_line_leaves_spec_none(self):
        text = (
            "# CONTENTS.md — Test\n\n## Items\n\n"
            "### rock\nA plain rock.\n\n*(Pickup-able.)*\n\n*Size:* small\n"
        )
        items = parse_contents_md(text)["items"]
        assert items["rock"].weapon_spec is None
