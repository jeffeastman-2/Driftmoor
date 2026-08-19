import shutil
from pathlib import Path

from engine.map_renderer import parse_geometry
from engine.regional_compiler import compile_regional_geometry
from models.geometry_loader import load_geometry
from scene_editor import (
    EDITOR_HTML, load_regions, load_rivers, materialize_geometry,
    write_regions, write_rivers,
)


def test_regional_compiler_builds_runtime_geometry_from_all_authoring_layers(tmp_path):
    source = Path("scenario/places")
    for name in ("GEOMETRY.md", "REGIONS.md", "RIVERS.md", "ROADS.md", "SUBZONES.md", "LANDMARKS.md"):
        shutil.copy2(source / name, tmp_path / name)

    geometry_path = compile_regional_geometry(tmp_path)
    parsed = parse_geometry(geometry_path.read_text(encoding="utf-8"))
    runtime = load_geometry(geometry_path)

    assert "DRIFTMOOR_TOWN" in runtime.zones
    assert "GREYWATER_VALLEY" in runtime.zones
    assert "MISTWOOD_FOREST" in runtime.zones
    assert not {
        "FEY_GLADE", "ECHOING_CAVERNS", "OLD_MILL_SITE", "SHATTERED_OBELISK",
    } & set(runtime.zones)
    assert set(runtime.landmarks) == {"old_mill"}
    assert runtime.impassable == []
    assert runtime.boundaries == []
    assert set(runtime.connections) == {
        "to_driftmoor", "to_azure_sea", "to_greywater_valley",
        "to_mistwood_hills", "to_obelisk_reach", "to_plains",
    }
    assert {name for name, _kind, _vertices in parsed["routes"]} >= {
        "Greywater River", "Gold Run", "Blackwater River", "Fanghorn", "Misty",
        "Obelisk Trail", "Greywater Road",
    }
    assert parsed["map_styles"]["AZURE_SEA"] == "#7897a3"


def test_shared_region_mesh_has_six_faces_and_reused_boundary_points():
    data = load_regions(Path("scenario/places/REGIONS.md"))
    assert len(data["regions"]) == 6
    uses = [
        region["name"] for region in data["regions"]
        if "valley_north_1" in region["points"]
    ]
    assert set(uses) == {"GREYWATER_VALLEY", "MISTWOOD_HILLS"}
    uses = [
        region["name"] for region in data["regions"]
        if "valley_south_1" in region["points"]
    ]
    assert set(uses) == {"GREYWATER_VALLEY", "PLAINS_OF_STONEHEARTH"}
    uses = [
        region["name"] for region in data["regions"]
        if "driftmoor_east" in region["points"]
    ]
    assert set(uses) == {"DRIFTMOOR", "GREYWATER_VALLEY", "MISTWOOD_HILLS"}


def test_region_round_trip_and_geometry_materialization(tmp_path):
    data = load_regions(Path("scenario/places/REGIONS.md"))
    regions_path = tmp_path / "REGIONS.md"
    write_regions(regions_path, data)
    assert load_regions(regions_path) == data

    geometry_path = tmp_path / "GEOMETRY.md"
    geometry_path.write_text(
        Path("scenario/places/GEOMETRY.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    materialize_geometry(geometry_path, data)
    rendered = geometry_path.read_text(encoding="utf-8")
    assert "| GREYWATER_VALLEY " in rendered
    east = data["points"]["driftmoor_east"]
    north = data["points"]["valley_north_1"]
    assert f"({east[0]:g},{east[1]:g}) ({north[0]:g},{north[1]:g})" in rendered


def test_five_editable_rivers_round_trip(tmp_path):
    rivers = load_rivers(Path("scenario/places/RIVERS.md"))
    assert [river["name"] for river in rivers] == [
        "Greywater", "Gold", "Blackwater", "Fanghorn", "Misty",
    ]
    assert all(len(river["vertices"]) >= 2 for river in rivers)
    target = tmp_path / "RIVERS.md"
    write_rivers(target, rivers)
    assert load_rivers(target) == rivers


def test_editor_supports_river_vertex_insert_delete_and_undo():
    assert "r.vertices.splice(best.i,0,q)" in EDITOR_HTML
    assert "r.vertices.splice(selected,1)" in EDITOR_HTML
    assert "Delete this endpoint?" in EDITOR_HTML
    assert "id=\"undo\"" in EDITOR_HTML
    for mode in ("regions", "rivers", "roads", "subzones", "landmarks"):
        assert f'value="{mode}"' in EDITOR_HTML
    assert "function insertRegion" in EDITOR_HTML
    assert "Delete this shared boundary point" in EDITOR_HTML
    assert "insert(z,P(e),true)" in EDITOR_HTML
