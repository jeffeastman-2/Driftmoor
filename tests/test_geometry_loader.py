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
        assert fey_glade_data["width"] == 325.0
        assert fey_glade_data["height"] == 325.0

    def test_scene_z_level(self, fey_glade_data):
        assert fey_glade_data["z_level"] == 0.65

    def test_scene_origin(self, fey_glade_data):
        origin = fey_glade_data["origin"]
        assert origin.x == 3971.5
        assert origin.y == 8476.0
        assert origin.z == 0.65

    def test_landmarks_count(self, fey_glade_data):
        assert len(fey_glade_data["landmarks"]) == 6

    def test_landmark_trail_entrance(self, fey_glade_data):
        pos = fey_glade_data["landmarks"]["trail_entrance"]
        assert pos.x == 191.0
        assert pos.y == 146.0

    def test_landmark_carved_stone(self, fey_glade_data):
        pos = fey_glade_data["landmarks"]["carved_stone"]
        assert pos.x == 136.0
        assert pos.y == 169.0

    def test_zones_count(self, fey_glade_data):
        assert len(fey_glade_data["zones"]) == 4

    def test_zone_names(self, fey_glade_data):
        assert set(fey_glade_data["zones"].keys()) == {
            "POOL", "GLADE", "TRAIL", "FOREST"
        }

    def test_zone_trail_vertices(self, fey_glade_data):
        trail = fey_glade_data["zones"]["TRAIL"]
        assert trail.vertices == [(191.0, 146.0, 0.33), (195.0, 146.0, 0.33), (325.0, 13.0, 0.0), (321.0, 9.0, 0.0)]

    def test_zone_z_elevation(self, fey_glade_data):
        zones = fey_glade_data["zones"]
        assert zones["FOREST"].z == pytest.approx(0.0)
        assert zones["GLADE"].z == pytest.approx(0.65)
        assert zones["POOL"].z == pytest.approx(0.97)

    def test_impassable_count(self, fey_glade_data):
        assert len(fey_glade_data["impassable"]) == 1

    def test_connections_count(self, fey_glade_data):
        assert len(fey_glade_data["connections"]) == 1

    def test_connection_trail_exit(self, fey_glade_data):
        pos = fey_glade_data["connections"]["trail_exit"]
        assert pos.x == 321.0
        assert pos.y == 13.0

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
        assert "fey resonance" in boundary.effect

    def test_boundary_vertices(self, fey_glade_data):
        boundary = fey_glade_data["boundaries"][0]
        assert len(boundary.perimeter.vertices) == 4

    def test_geometry_carries_no_placement(self, fey_glade_data):
        # Placement is a scene concern now; GEOMETRY.md is a pure stage.
        assert "starting_positions" not in fey_glade_data


class TestLoadGeometry:
    """Test loading from file to SceneGeometry."""

    def test_load_returns_scene_geometry(self):
        geo = load_geometry(FEY_GLADE_PATH)
        assert isinstance(geo, SceneGeometry)
        assert geo.name == "The Fey Glade"

    def test_load_zones_work(self):
        geo = load_geometry(FEY_GLADE_PATH)
        assert geo.zone_at(Position(256.0, 81.0)) == "TRAIL"
        assert geo.zone_at(Position(162.0, 162.0)) == "GLADE"
        assert geo.zone_at(Position(32.0, 32.0)) == "FOREST"


    def test_load_full_returns_tuple(self):
        geo, boundaries = load_geometry_full(FEY_GLADE_PATH)
        assert isinstance(geo, SceneGeometry)
        assert len(boundaries) == 1

    def test_loaded_boundary_blocks_shadowbeast(self):
        _, boundaries = load_geometry_full(FEY_GLADE_PATH)
        boundary = boundaries[0]
        assert boundary.is_blocked("shadowbeast") is True
        assert boundary.is_blocked("human") is False

    def test_loaded_zone_z_elevations(self):
        geo, _ = load_geometry_full(FEY_GLADE_PATH)
        assert geo.zones["POOL"].z == pytest.approx(0.97)
        assert geo.zones["FOREST"].z == pytest.approx(0.0)
