"""Phase 2a tests: items surfaced into per-turn perception.

Validates that when a CONTENTS.md is present, items in the acting
character's current zone are listed under an ``Items in this zone:``
sub-block in the perception string, and items in other zones are not.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.session import _build_perception
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


class TestPerceptionWithItems:

    def test_entry_chamber_items_listed(self, geometry, items):
        # Thorgrim starts in Entry Chamber (138, 295).
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        assert "Items in this zone:" in perception
        # Each Entry-Chamber item should appear by its label.
        for label in ("Snapped torch", "Dark stain", "Discarded pack",
                      "Drag marks", "Torch bracket", "Tally scratches"):
            assert label in perception, f"missing {label} in:\n{perception}"

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
        assert "Items in this zone:" in perception
        assert "Mace +1" in perception
        assert "Burial vault" in perception

    def test_no_items_dict_omits_subblock(self, geometry):
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=None,
        )
        assert "Items in this zone" not in perception

    def test_distance_format(self, geometry, items):
        # snapped_torch is at (132, 268); thorgrim at (138, 295) → ~28 ft.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", geometry, positions, set(),
            items=items,
        )
        # Format: "- Snapped torch (~25 ft away)" or similar (rounded to 5).
        import re
        m = re.search(r"- Snapped torch \(~(\d+) ft away\)", perception)
        assert m is not None, f"snapped_torch line not found:\n{perception}"
        dist = int(m.group(1))
        # Actual dist = sqrt(36 + 729) ≈ 27.7 → rounded to 25 or 30.
        assert dist in (25, 30)

    def test_no_geometry_returns_empty(self, items):
        # Without geometry, perception falls back to empty string regardless.
        positions = {"thorgrim": (138.0, 295.0, "ENTRY CHAMBER")}
        perception = _build_perception(
            "thorgrim", None, positions, set(),
            items=items,
        )
        assert perception == ""
