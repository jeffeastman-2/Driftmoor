"""Tests for sense-range resolution and ambient visibility."""

from __future__ import annotations

from pathlib import Path

from models.geometry_loader import load_geometry
from models.senses import resolve_senses


GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


class TestRacialDarkvision:
    def test_dwarf_has_darkvision(self):
        assert resolve_senses(race="Mountain Dwarf").darkvision_ft == 60.0

    def test_elf_has_darkvision(self):
        assert resolve_senses(race="Wood Elf").darkvision_ft == 60.0

    def test_half_elf_has_darkvision(self):
        assert resolve_senses(race="Half-Elf").darkvision_ft == 60.0

    def test_human_has_none(self):
        assert resolve_senses(race="Human").darkvision_ft == 0.0

    def test_halfling_has_none(self):
        assert resolve_senses(race="Lightfoot Halfling").darkvision_ft == 0.0


class TestExplicitSenses:
    def test_explicit_darkvision_overrides_race(self):
        prof = resolve_senses(race="Human", senses=["Darkvision 120 ft."])
        assert prof.darkvision_ft == 120.0

    def test_blindsight_and_tremorsense_parsed(self):
        prof = resolve_senses(senses=["Blindsight 10 ft.", "Tremorsense 30 ft."])
        assert prof.blindsight_ft == 10.0
        assert prof.tremorsense_ft == 30.0
        assert prof.nonvisual_range_ft == 30.0

    def test_keen_senses_from_features(self):
        prof = resolve_senses(features=["Keen Hearing and Smell"])
        assert prof.keen_senses is True
        assert prof.nonvisual_range_ft == 30.0

    def test_no_senses_means_zero(self):
        prof = resolve_senses()
        assert prof.darkvision_ft == 0.0
        assert prof.nonvisual_range_ft == 0.0


class TestAmbientVisibility:
    def test_cavern_ambient_parsed(self):
        geo = load_geometry(GEOMETRY)
        assert geo.ambient_visibility_ft == 25.0

    def test_ambient_sight_range_falls_back_to_default(self):
        geo = load_geometry(GEOMETRY)
        # No per-zone override → scene default applies for any zone.
        assert geo.ambient_sight_range("Entry Chamber") == 25.0
        assert geo.ambient_sight_range("Echo Chamber") == 25.0

    def test_unset_ambient_is_unlimited(self):
        from models.space_time import SceneGeometry, Position
        geo = SceneGeometry(
            name="x", place_path="x", z_level=0, width=1, height=1,
            origin=Position(0, 0),
        )
        assert geo.ambient_sight_range("anything") is None
