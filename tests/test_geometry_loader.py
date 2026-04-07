"""Tests for geometry loader — parses GEOMETRY.md into SceneGeometry."""

from __future__ import annotations

import pytest
from pathlib import Path

from models.geometry_loader import parse_geometry_md, load_geometry, load_geometry_full
from models.space_time import Position, Polygon, SceneGeometry, MagicalBoundary


FEY_GLADE_PATH = Path("scenario/places/mistwood_hills/fey_glade/GEOMETRY.md")


class TestParseGeometryMd:
    """Test markdown parsing of GEOMETRY.md content."""

    @pytest.fixture
    def fey_glade_data(self):
        text = FEY_GLADE_PATH.read_text(encoding="utf-8")
        return parse_geometry_md(text)

    def test_scene_name(self, fey_glade_data):
        assert fey_glade_data["name"] == "The Fey Glade"

    def test_scene_place_path(self, fey_glade_data):
        assert fey_glade_data["place_path"] == "places/mistwood_hills/fey_glade"

    def test_scene_dimensions(self, fey_glade_data):
        assert fey_glade_data["width"] == 100.0
        assert fey_glade_data["height"] == 100.0

    def test_scene_z_level(self, fey_glade_data):
        assert fey_glade_data["z_level"] == 0.2

    def test_scene_origin(self, fey_glade_data):
        origin = fey_glade_data["origin"]
        assert origin.x == 1222.0
        assert origin.y == 2608.0
        assert origin.z == 0.2

    def test_landmarks_count(self, fey_glade_data):
        assert len(fey_glade_data["landmarks"]) == 6

    def test_landmark_trail_entrance(self, fey_glade_data):
        pos = fey_glade_data["landmarks"]["trail_entrance"]
        assert pos.x == 59.0
        assert pos.y == 45.0

    def test_landmark_carved_stone(self, fey_glade_data):
        pos = fey_glade_data["landmarks"]["carved_stone"]
        assert pos.x == 42.0
        assert pos.y == 52.0

    def test_zones_count(self, fey_glade_data):
        assert len(fey_glade_data["zones"]) == 4

    def test_zone_names(self, fey_glade_data):
        assert set(fey_glade_data["zones"].keys()) == {
            "POOL", "GLADE", "TRAIL", "FOREST"
        }

    def test_zone_trail_vertices(self, fey_glade_data):
        trail = fey_glade_data["zones"]["TRAIL"]
        assert trail.vertices == [(59, 45), (60, 45), (100, 4), (99, 3)]

    def test_render_z_values(self, fey_glade_data):
        rz = fey_glade_data["render_z"]
        assert rz["FOREST"] == 0
        assert rz["GLADE"] == 1
        assert rz["TRAIL"] == 1
        assert rz["POOL"] == 2

    def test_render_z_count(self, fey_glade_data):
        assert len(fey_glade_data["render_z"]) == 4

    def test_impassable_count(self, fey_glade_data):
        assert len(fey_glade_data["impassable"]) == 1

    def test_connections_count(self, fey_glade_data):
        assert len(fey_glade_data["connections"]) == 1

    def test_connection_trail_exit(self, fey_glade_data):
        pos = fey_glade_data["connections"]["trail_exit"]
        assert pos.x == 99.0
        assert pos.y == 4.0

    def test_boundaries_count(self, fey_glade_data):
        assert len(fey_glade_data["boundaries"]) == 1

    def test_boundary_name(self, fey_glade_data):
        boundary = fey_glade_data["boundaries"][0]
        assert boundary.name == "Fey Glade Repulsion Boundary"

    def test_boundary_blocks(self, fey_glade_data):
        boundary = fey_glade_data["boundaries"][0]
        assert "shadowbeast" in boundary.blocks
        assert "undead" in boundary.blocks

    def test_boundary_effect(self, fey_glade_data):
        boundary = fey_glade_data["boundaries"][0]
        assert "wrongness" in boundary.effect

    def test_boundary_vertices(self, fey_glade_data):
        boundary = fey_glade_data["boundaries"][0]
        assert len(boundary.perimeter.vertices) == 4

    def test_starting_positions_count(self, fey_glade_data):
        assert len(fey_glade_data["starting_positions"]) == 3

    def test_starting_aeliana(self, fey_glade_data):
        pos = fey_glade_data["starting_positions"]["aeliana"]
        assert pos.x == 79.0
        assert pos.y == 25.0

    def test_starting_fennel(self, fey_glade_data):
        pos = fey_glade_data["starting_positions"]["fennel"]
        assert pos.x == 44.0
        assert pos.y == 52.0

    def test_starting_shadowbeast(self, fey_glade_data):
        pos = fey_glade_data["starting_positions"]["shadowbeast"]
        assert pos.x == 37.0
        assert pos.y == 50.0


class TestLoadGeometry:
    """Test loading from file to SceneGeometry."""

    def test_load_returns_scene_geometry(self):
        geo = load_geometry(FEY_GLADE_PATH)
        assert isinstance(geo, SceneGeometry)
        assert geo.name == "The Fey Glade"

    def test_load_zones_work(self):
        geo = load_geometry(FEY_GLADE_PATH)
        assert geo.zone_at(Position(79, 25)) == "TRAIL"
        assert geo.zone_at(Position(50, 50)) == "GLADE"
        assert geo.zone_at(Position(10, 10)) == "FOREST"

    def test_load_full_returns_tuple(self):
        geo, boundaries, starting, render_z = load_geometry_full(FEY_GLADE_PATH)
        assert isinstance(geo, SceneGeometry)
        assert len(boundaries) == 1
        assert len(starting) == 3
        assert isinstance(render_z, dict)

    def test_loaded_boundary_blocks_shadowbeast(self):
        _, boundaries, _, _ = load_geometry_full(FEY_GLADE_PATH)
        boundary = boundaries[0]
        assert boundary.is_blocked("shadowbeast") is True
        assert boundary.is_blocked("human") is False

    def test_loaded_starting_positions_in_correct_zones(self):
        geo, _, starting, _ = load_geometry_full(FEY_GLADE_PATH)
        assert geo.zone_at(starting["aeliana"]) == "TRAIL"
        assert geo.zone_at(starting["fennel"]) == "GLADE"
        assert geo.zone_at(starting["shadowbeast"]) == "FOREST"

    def test_loaded_render_z(self):
        _, _, _, render_z = load_geometry_full(FEY_GLADE_PATH)
        assert render_z["POOL"] == 2
        assert render_z["FOREST"] == 0
