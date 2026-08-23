from pathlib import Path

from models.contents_loader import (
    load_contents_with_geometry,
    load_zone_contents_with_geometry,
)
from models.geometry_loader import load_geometry


def test_echoing_caverns_zone_loader_matches_geometry_ids():
    scene_dir = Path("scenario/places/obelisk_reach/echoing_caverns")
    zones_dir = scene_dir / "zones"
    geometry_path = scene_dir / "GEOMETRY.md"

    geometry = load_geometry(geometry_path)
    items = load_zone_contents_with_geometry(
        zones_dir, geometry_path, scene_geometry=geometry
    )

    # Echoing Caverns GEOMETRY.md defines 16 item ids.
    assert len(items) == 16
    assert "mace_plus_one" in items
    assert items["mace_plus_one"].label == "Mace +1"
    assert items["mace_plus_one"].zone == "Secret Chamber"


def test_fey_glade_zone_loader_matches_legacy_id_set():
    scene_dir = Path("scenario/places/mistwood_hills/fey_glade")
    zones_dir = scene_dir / "zones"
    geometry_path = scene_dir / "GEOMETRY.md"
    contents_path = scene_dir / "CONTENTS.md"

    geometry = load_geometry(geometry_path)
    zone_items = load_zone_contents_with_geometry(
        zones_dir, geometry_path, scene_geometry=geometry
    )
    legacy_items = load_contents_with_geometry(
        contents_path, geometry_path, scene_geometry=geometry
    )

    # New zones path should fully cover the same geometry-bound id set.
    assert set(zone_items.keys()) == set(legacy_items.keys())
    assert zone_items["fey_herbs"].zone == "GLADE"


def test_sleeping_city_loads_from_zones_without_contents_file():
    scene_dir = Path(
        "scenario/places/obelisk_reach/echoing_caverns/sleeping_city"
    )
    geometry_path = scene_dir / "GEOMETRY.md"

    assert not (scene_dir / "CONTENTS.md").exists()
    geometry = load_geometry(geometry_path)
    items = load_zone_contents_with_geometry(
        scene_dir / "zones", geometry_path, scene_geometry=geometry
    )

    assert len(geometry.zones) == 8
    assert len(items) == 20
    assert items["living_lock_depression"].zone == "Crypt of Seven Chains"
