"""Tests: items surfaced into per-turn perception.

Validates that when zone content is present, items the acting character
can perceive are listed under an ``Items in view:`` sub-block in the
perception string. Perception is gated by the observer's sight range —
the scene's ambient (light) range for caverns, extended by darkvision —
plus line of sight, spans zone boundaries (a character at a seam perceives
nearby items in the adjoining zone), and always recalls previously examined
items regardless of distance.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.session import _build_perception
from models.contents_loader import load_zone_contents_with_geometry
from models.geometry_loader import load_geometry


ZONES = Path("scenario/places/obelisk_reach/echoing_caverns/zones")
GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


def _observer(cid, *, race="Human", senses=None, features=None):
    """Minimal characters dict so _build_perception can read observer senses."""
    char = SimpleNamespace(
        race=race, senses=senses or [], features=features or [],
        faction="party",
    )
    return {cid: SimpleNamespace(character=char, scene_handle="")}


@pytest.fixture(scope="module")
def geometry():
    return load_geometry(GEOMETRY)


@pytest.fixture(scope="module")
def items(geometry):
    return load_zone_contents_with_geometry(ZONES, GEOMETRY, scene_geometry=geometry)


class TestPerceptionWithItems:

    def test_entry_chamber_items_listed(self, geometry, items):
        # Thorgrim is a Mountain Dwarf (darkvision 60 ft) starting in the
        # Entry Chamber (138, 295). The item cluster sits ~28-35 ft north,
        # well within his darkvision, so it is perceived.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Mountain Dwarf"),
            items=items,
        )
        assert "Items in view:" in perception
        # Drag marks (large) at ~28 ft fall in the "intermediate" band; they
        # author an intermediate description, so that vague text shows (not the
        # bare label).
        assert "twin scored lines" in perception, perception
        # The snapped torch (small) at ~28 ft falls in the "far" band, so it
        # reads as its vague distant appearance, not its label.
        assert "pale streak" in perception, perception
        assert "Snapped torch" not in perception, perception

    def test_torchless_observer_limited_to_light_radius(self, geometry, items):
        # A torchless observer with no darkvision sees only ~25 ft (scene
        # ambient). From the start, every Entry item sits beyond 25 ft, so
        # nothing is in view until the character moves closer or makes light.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Human"),
            items=items,
        )
        assert "Items in view" not in perception, perception

    def test_cross_zone_item_visible_at_boundary(self, geometry, items):
        # Standing in First Passage near the seam, the snapped torch in the
        # adjoining Entry Chamber (~19 ft, with LOS) should be perceived and
        # tagged with its zone. At that range a small torch is in the "far"
        # band, so it reads by its vague appearance, prefixed with its zone.
        positions = {"thorgrim": (137.0, 250.0, "FIRST PASSAGE")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        assert "pale streak" in perception, perception
        assert "(Entry Chamber," in perception, perception

    def test_remembered_item_bypasses_radius(self, geometry, items):
        # An item previously examined by anyone in the party is recalled even
        # when far beyond the torch radius, under "Items remembered or examined:"
        # (a separate section from "Items in view:").
        items["torch_bracket"].discovered_by.add("thorgrim")
        try:
            positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
            perception = _build_perception(
                "thorgrim", geometry, positions, set(),
                items=items,
            )
            assert "Torch bracket" in perception, perception
            assert "Items remembered or examined:" in perception, perception
            # And it must NOT be under the currently-visible header.
            view = perception.split("Items remembered or examined:")[0]
            assert "Torch bracket" not in view, perception
        finally:
            items["torch_bracket"].discovered_by.discard("thorgrim")

    def test_secret_chamber_items_not_visible_from_entry(self, geometry, items):
        # Mace (64,195) and burial vault are in Secret Chamber, not Entry.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        assert "Mace +1" not in perception
        assert "Burial vault" not in perception

    def test_secret_chamber_perception_shows_secret_items(self, geometry, items):
        # Standing inside the Secret Chamber.
        positions = {"thorgrim": (64.0, 195.0, "SECRET CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        assert "Items in view:" in perception
        assert "Mace +1" in perception
        assert "Burial vault" in perception

    def test_held_item_not_listed_as_loose(self, geometry, items):
        # Once carried, the mace is in someone's pack and must not surface
        # as a loose scene item, even when the observer is right on top of it.
        mace = next(
            it for it in items.values()
            if (it.label or "").lower().startswith("mace")
        )
        mace.holder = "thorgrim"
        positions = {"thorgrim": (64.0, 195.0, "SECRET CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        assert "Mace +1" not in perception

    def test_no_items_dict_omits_subblock(self, geometry):
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=None,
        )
        assert "Items in view" not in perception
        assert "Items in this zone" not in perception

    def test_distance_format(self, geometry, items):
        # Drag marks at (130, 268); thorgrim at (138, 295) ≈ 28 ft. At that
        # range (intermediate band) they render their authored band text with
        # a rounded distance suffix.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Mountain Dwarf"),
            items=items,
        )
        # Format uses the zone-authored appearance and rounds to nearest 5.
        import re
        m = re.search(r"- twin scored lines[^\n]*\(~(\d+) ft away\)", perception)
        assert m is not None, f"drag_marks line not found:\n{perception}"
        dist = int(m.group(1))
        # Actual dist = sqrt(64 + 729) ≈ 28.2 → rounded to 25 or 30.
        assert dist in (25, 30)

    def test_no_geometry_falls_back_to_copresent(self, items):
        # Without geometry, perception should still expose other active
        # participants as co-present so social scenes do not become mute.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", None, positions, {"thorgrim", "aeliana"},
            items=items,
        )
        assert "aeliana" in perception
        assert "co-present" in perception


class TestDistantItemAppearance:
    """Apparent size (size / distance) selects the perception band."""

    def test_authored_band_used_at_distance(self, geometry, items):
        # Dwarf (darkvision 60) at entry start; the small snapped_torch ~28 ft
        # away falls in the "far" band → its authored vague text, not its label.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Mountain Dwarf"),
            items=items,
        )
        assert "pale streak" in perception, perception
        assert "Snapped torch" not in perception

    def test_authored_item_identified_when_close(self, geometry, items):
        # Standing on top of the snapped torch (apparent size huge → "near"):
        # it is identified by its label, not the vague band text.
        positions = {"thorgrim": (132.0, 270.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Mountain Dwarf"),
            items=items,
        )
        assert "Snapped torch" in perception, perception
        assert "pale streak" not in perception

    def test_examined_item_keeps_identity_at_distance(self, geometry, items):
        # Once examined, identity is known regardless of apparent size.
        items["snapped_torch"].discovered_by.add("seraphina")
        try:
            positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
            perception = _build_perception(
                "thorgrim", geometry, positions, set(),
                characters=_observer("thorgrim", race="Mountain Dwarf"),
                items=items,
            )
            torch_line = next(
                l for l in perception.splitlines() if "Snapped torch" in l
            )
            assert "examined" in torch_line, torch_line
            assert "pale streak" not in perception
        finally:
            items["snapped_torch"].discovered_by.discard("seraphina")

    def test_unauthored_far_item_is_omitted_as_visual_clutter(self, geometry, items):
        # An item with no authored far silhouette should not become a generic
        # "indistinct shape"; that flooded populated interiors with implausible
        # mystery objects. It appears once close enough to identify.
        from models.item import Item
        from models.space_time import Position

        # Medium (5 ft) object ~50 ft north of the observer → ratio 0.1 → far.
        mystery = Item(
            id="mystery_lump",
            label="Mystery lump",
            description="A nondescript lump.",
            size_ft=5.0,
            position=Position(138.0, 245.0),
            zone="Entry Chamber",
        )
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            characters=_observer("thorgrim", race="Mountain Dwarf"),
            items={"mystery_lump": mystery},
        )
        assert "indistinct shape" not in perception, perception
        assert "Mystery lump" not in perception, perception


class TestCreatureSightRange:
    """Creatures are gated by the same ambient + darkvision sight model."""
    def test_darkvision_sees_distant_creature_in_dark(self, geometry):
        # Two creatures ~40 ft apart in the Entry Chamber. A torchless human
        # (ambient 25) cannot see the other; a dwarf (darkvision 60) can.
        positions = {
            "watcher": (138.0, 295.0, "ENTRY CHAMBER"),
            "other": (130.0, 268.0, "ENTRY CHAMBER"),  # ~28 ft
        }
        active = {"watcher", "other"}
        chars = {
            **_observer("watcher", race="Human"),
            "other": SimpleNamespace(
                character=SimpleNamespace(
                    race="Human", senses=[], features=[], faction="party",
                ),
                scene_handle="the other",
            ),
        }
        torchless = _build_perception(
            "watcher", geometry, positions, active,
            characters=chars, items=None,
        )
        assert "the other" not in torchless

        chars_dwarf = {
            **_observer("watcher", race="Mountain Dwarf"),
            "other": chars["other"],
        }
        with_darkvision = _build_perception(
            "watcher", geometry, positions, active,
            characters=chars_dwarf, items=None,
        )
        assert "the other" in with_darkvision

    def test_nonvisual_sense_surfaces_unseen_creature(self, geometry):
        # A torchless observer with keen hearing/smell senses (but does not
        # see) a creature just beyond visual range.
        positions = {
            "watcher": (138.0, 295.0, "ENTRY CHAMBER"),
            "other": (130.0, 268.0, "ENTRY CHAMBER"),  # ~28 ft, beyond 25
        }
        active = {"watcher", "other"}
        chars = {
            "watcher": SimpleNamespace(
                character=SimpleNamespace(
                    race="Human", senses=[],
                    features=["Keen Hearing and Smell"], faction="party",
                ),
                scene_handle="",
            ),
            "other": SimpleNamespace(
                character=SimpleNamespace(
                    race="Human", senses=[], features=[], faction="party",
                ),
                scene_handle="the other",
            ),
        }
        perception = _build_perception(
            "watcher", geometry, positions, active,
            characters=chars, items=None,
        )
        assert "the other" in perception
        assert "sensed" in perception and "not seen" in perception


class TestApparentSizeBand:
    """The perspective model: apparent size ≈ size / distance picks the band."""

    def test_near_when_close_relative_to_size(self):
        from models.item import apparent_size_band
        # A 5 ft object at 5 ft (ratio 1.0) is near.
        assert apparent_size_band(5.0, 5.0) == "near"

    def test_bands_progress_with_distance(self):
        from models.item import apparent_size_band
        # A 10 ft object: identifiable up close, vaguer with distance.
        assert apparent_size_band(10.0, 10.0) == "near"
        assert apparent_size_band(10.0, 40.0) == "intermediate"
        assert apparent_size_band(10.0, 100.0) == "far"
        assert apparent_size_band(10.0, 200.0) == "distant"

    def test_small_item_drops_out_sooner_than_large(self):
        from models.item import apparent_size_band
        # At the same 60 ft, a tiny torch is unidentifiable while a large
        # obelisk is still discernible.
        assert apparent_size_band(2.5, 80.0) is None        # torch: too small
        assert apparent_size_band(20.0, 80.0) is not None    # obelisk: visible

    def test_zero_size_treated_as_medium(self):
        from models.item import apparent_size_band
        # Unspecified size behaves like a 5 ft medium object.
        assert apparent_size_band(0.0, 20.0) == apparent_size_band(5.0, 20.0)


class TestExaminationStateReseed:
    """item.discovered_by is not checkpointed; on resume it must be rebuilt
    from the persisted party_examination_state, or the "Items remembered or
    examined" perception section silently empties out after every restart."""

    def test_reseed_repopulates_discovered_by(self, items):
        from engine.session import _reseed_discovered_from_examination_state
        # Fresh load -> nothing discovered (the resume starting condition).
        assert not items["wall_scratches"].discovered_by
        assert not items["obelisk_fragment"].discovered_by
        # Deserialized examination state: keys are (ZONE, normalized target).
        pes = {
            ("ENTRY CHAMBER", "tally scratches"): {"by": "seraphina"},
            ("ECHO CHAMBER", "obelisk fragment"): {"by": "amara"},
        }
        try:
            _reseed_discovered_from_examination_state(items, pes)
            assert items["wall_scratches"].discovered_by == {"seraphina"}
            assert items["obelisk_fragment"].discovered_by == {"amara"}
        finally:
            items["wall_scratches"].discovered_by.clear()
            items["obelisk_fragment"].discovered_by.clear()

    def test_reseed_respects_zone_to_avoid_cross_pollination(self, items):
        from engine.session import _reseed_discovered_from_examination_state
        # Same target name but a zone where that item does not live: must NOT
        # mark the Entry Chamber item.
        pes = {("ECHO CHAMBER", "tally scratches"): {"by": "amara"}}
        try:
            _reseed_discovered_from_examination_state(items, pes)
            assert not items["wall_scratches"].discovered_by
        finally:
            items["wall_scratches"].discovered_by.clear()

    def test_reseed_noops_without_state(self, items):
        from engine.session import _reseed_discovered_from_examination_state
        _reseed_discovered_from_examination_state(items, None)
        _reseed_discovered_from_examination_state(items, {})
        assert not any(it.discovered_by for it in items.values())
