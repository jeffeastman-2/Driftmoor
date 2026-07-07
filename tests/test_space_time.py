"""Tests for spatial coordinate system and time tracking."""

from __future__ import annotations

import pytest
from pathlib import Path
from math import sqrt

from models.space_time import (
    Position, Polygon, GameTime, SceneGeometry, MagicalBoundary, Portal,
)
from models.geometry_loader import load_geometry, load_geometry_full



# =========================================================================
# Position
# =========================================================================


class TestPosition:
    """Position dataclass with distance methods."""

    def test_create_position(self):
        p = Position(10.0, 20.0, 0.5)
        assert p.x == 10.0
        assert p.y == 20.0
        assert p.z == 0.5

    def test_default_z_is_zero(self):
        p = Position(5.0, 5.0)
        assert p.z == 0.0

    def test_distance_to_same_point(self):
        p = Position(0, 0, 0)
        assert p.distance_to(p) == 0.0

    def test_distance_to_horizontal(self):
        a = Position(0, 0)
        b = Position(3, 4)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_distance_to_with_z(self):
        a = Position(0, 0, 0)
        b = Position(3, 4, 12)
        # sqrt(9 + 16 + 144) = sqrt(169) = 13
        assert a.distance_to(b) == pytest.approx(13.0)

    def test_horizontal_distance_ignores_z(self):
        a = Position(0, 0, 0)
        b = Position(3, 4, 100)
        assert a.horizontal_distance_to(b) == pytest.approx(5.0)

    def test_distance_is_symmetric(self):
        a = Position(1, 2, 3)
        b = Position(4, 6, 8)
        assert a.distance_to(b) == pytest.approx(b.distance_to(a))

    def test_horizontal_distance_same_point(self):
        p = Position(7, 3, 5)
        assert p.horizontal_distance_to(p) == 0.0


# =========================================================================
# Polygon
# =========================================================================


class TestPolygon:
    """Polygon with point-in-polygon and nearest point."""

    def test_create_polygon(self):
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert len(poly.vertices) == 4

    def test_contains_center(self):
        """Point clearly inside a square."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert poly.contains(Position(5, 5)) is True

    def test_contains_outside(self):
        """Point clearly outside."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert poly.contains(Position(15, 5)) is False

    def test_contains_negative_coords(self):
        poly = Polygon([(-5, -5), (5, -5), (5, 5), (-5, 5)])
        assert poly.contains(Position(0, 0)) is True
        assert poly.contains(Position(-6, 0)) is False

    def test_contains_non_square(self):
        """Triangle."""
        poly = Polygon([(0, 0), (10, 0), (5, 10)])
        assert poly.contains(Position(5, 3)) is True
        assert poly.contains(Position(9, 9)) is False

    def test_boundary_distance_inside(self):
        """Distance from interior point to nearest edge."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        # Point (5, 2) — nearest edge is bottom (y=0), distance = 2
        assert poly.boundary_distance(Position(5, 2)) == pytest.approx(2.0)

    def test_boundary_distance_centered(self):
        """Center of 10x10 square — distance to nearest edge is 5."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        assert poly.boundary_distance(Position(5, 5)) == pytest.approx(5.0)

    def test_boundary_distance_close_to_edge(self):
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        # Point (1, 5) — nearest edge is left (x=0), distance = 1
        assert poly.boundary_distance(Position(1, 5)) == pytest.approx(1.0)

    def test_nearest_point_outside(self):
        """Nearest point on polygon boundary from outside."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        # Point at (15, 5) — nearest boundary point is (10, 5)
        nearest = poly.nearest_point(Position(15, 5))
        assert nearest.x == pytest.approx(10.0)
        assert nearest.y == pytest.approx(5.0)

    def test_nearest_point_outside_corner(self):
        """Nearest to a corner region."""
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        # Point at (12, 12) — nearest boundary point is corner (10, 10)
        nearest = poly.nearest_point(Position(12, 12))
        assert nearest.x == pytest.approx(10.0)
        assert nearest.y == pytest.approx(10.0)

    def test_centroid_square(self):
        poly = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        c = poly.centroid()
        assert c.x == pytest.approx(5.0)
        assert c.y == pytest.approx(5.0)

    def test_centroid_triangle(self):
        poly = Polygon([(0, 0), (6, 0), (3, 6)])
        c = poly.centroid()
        assert c.x == pytest.approx(3.0)
        assert c.y == pytest.approx(2.0)


# =========================================================================
# GameTime
# =========================================================================


class TestGameTime:
    """Time tracking with period and advance."""

    def test_create_game_time(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.hour == 14
        assert t.minute == 30

    def test_period_afternoon(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "afternoon"

    def test_period_dawn(self):
        t = GameTime(hour=5, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "dawn"

    def test_period_morning(self):
        t = GameTime(hour=9, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "morning"

    def test_period_midday(self):
        t = GameTime(hour=12, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "midday"

    def test_period_dusk(self):
        t = GameTime(hour=18, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "dusk"

    def test_period_evening(self):
        t = GameTime(hour=21, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "evening"

    def test_period_night(self):
        t = GameTime(hour=2, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "night"

    def test_is_dark_evening(self):
        t = GameTime(hour=21, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.is_dark is True

    def test_is_dark_afternoon(self):
        t = GameTime(hour=14, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.is_dark is False

    def test_advance_one_turn(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        t.advance(1)
        assert t.hour == 14
        assert t.minute == 40
        assert t.absolute_turn == 1

    def test_advance_rolls_hour(self):
        t = GameTime(hour=14, minute=50, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        t.advance(2)
        assert t.hour == 15
        assert t.minute == 10
        assert t.absolute_turn == 2

    def test_advance_rolls_day(self):
        t = GameTime(hour=23, minute=50, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        t.advance(2)
        assert t.hour == 0
        assert t.minute == 10
        assert t.day == 2

    def test_advance_multiple_turns(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=5)
        t.advance(6)
        assert t.hour == 15
        assert t.minute == 30
        assert t.absolute_turn == 11

    def test_minutes_until_later_hour(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.minutes_until(18) == 210  # 3.5 hours

    def test_minutes_until_wraps_next_day(self):
        t = GameTime(hour=20, minute=0, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        # 6 AM next day = 10 hours = 600 minutes
        assert t.minutes_until(6) == 600

    def test_turns_until(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        # 210 minutes / 10 min per turn = 21 turns until dusk (18:00)
        assert t.turns_until(18) == 21

    def test_fey_glade_starting_time(self):
        """Fey Glade starts at 2:30 PM, dusk at 6 PM = ~3.5 hours."""
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=10, absolute_turn=0)
        assert t.period == "afternoon"
        assert t.minutes_until(18) == 210
        assert t.turns_until(18) == 21

    def test_combat_turn_duration(self):
        t = GameTime(hour=14, minute=30, day=1, season="autumn",
                     turn_duration=1, absolute_turn=0)
        t.advance(6)
        assert t.minute == 36
        assert t.absolute_turn == 6


# =========================================================================
# SceneGeometry
# =========================================================================


class TestSceneGeometry:
    """Scene geometry with zones, landmarks, and coordinate conversion."""

    @pytest.fixture
    def simple_scene(self):
        return SceneGeometry(
            name="Test Scene",
            place_path="test/scene",
            z_level=0.0,
            width=20.0,
            height=20.0,
            origin=Position(100, 200, 0),
            landmarks={
                "center": Position(10, 10),
                "corner": Position(0, 0),
            },
            zones={
                "north": Polygon([(0, 10), (20, 10), (20, 20), (0, 20)]),
                "south": Polygon([(0, 0), (20, 0), (20, 10), (0, 10)]),
            },
            impassable=[
                Polygon([(8, 8), (12, 8), (12, 12), (8, 12)]),
            ],
            connections={
                "exit_south": Position(10, 0),
            },
        )

    def test_absolute_position(self, simple_scene):
        local = Position(5, 5, 0)
        absolute = simple_scene.absolute_position(local)
        assert absolute.x == 105.0
        assert absolute.y == 205.0

    def test_absolute_position_preserves_z(self, simple_scene):
        local = Position(5, 5, 3)
        absolute = simple_scene.absolute_position(local)
        assert absolute.z == 3.0

    def test_zone_at_north(self, simple_scene):
        assert simple_scene.zone_at(Position(10, 15)) == "north"

    def test_zone_at_south(self, simple_scene):
        assert simple_scene.zone_at(Position(10, 5)) == "south"

    def test_zone_at_outside(self, simple_scene):
        assert simple_scene.zone_at(Position(50, 50)) is None

    def test_nearest_landmark(self, simple_scene):
        name, pos = simple_scene.nearest_landmark(Position(1, 1))
        assert name == "corner"

    def test_nearest_landmark_center(self, simple_scene):
        name, pos = simple_scene.nearest_landmark(Position(9, 11))
        assert name == "center"


# =========================================================================
# MagicalBoundary
# =========================================================================


class TestMagicalBoundary:
    """Magical boundary that blocks certain entity types."""

    def test_create_boundary(self):
        boundary = MagicalBoundary(
            name="Test Boundary",
            perimeter=Polygon([(0, 9), (20, 9), (20, 11), (0, 11)]),
            blocks=["shadowbeast", "undead"],
            effect="cannot cross",
        )
        assert boundary.name == "Test Boundary"
        assert "shadowbeast" in boundary.blocks

    def test_boundary_is_blocked(self):
        boundary = MagicalBoundary(
            name="Test",
            perimeter=Polygon([(0, 9), (20, 9), (20, 11), (0, 11)]),
            blocks=["shadowbeast"],
            effect="stopped",
        )
        assert boundary.is_blocked("shadowbeast") is True
        assert boundary.is_blocked("human") is False

    def test_boundary_contains_position(self):
        boundary = MagicalBoundary(
            name="Test",
            perimeter=Polygon([(0, 9), (20, 9), (20, 11), (0, 11)]),
            blocks=["shadowbeast"],
            effect="stopped",
        )
        assert boundary.perimeter.contains(Position(10, 10)) is True
        assert boundary.perimeter.contains(Position(10, 5)) is False


# =========================================================================
# Portal
# =========================================================================


class TestPortal:
    """Portal connecting two scenes."""

    def test_create_portal(self):
        portal = Portal(
            from_scene="scene_a",
            from_position=Position(10, 0),
            to_scene="scene_b",
            to_position=Position(10, 20),
            traversal_cost=1.5,
            conditions=[],
            direction_label="north through the gate",
        )
        assert portal.from_scene == "scene_a"
        assert portal.to_scene == "scene_b"
        assert portal.traversal_cost == 1.5

    def test_portal_with_conditions(self):
        portal = Portal(
            from_scene="dungeon_entrance",
            from_position=Position(5, 0),
            to_scene="dungeon_level_1",
            to_position=Position(5, 0),
            traversal_cost=9.0,
            conditions=["requires_key"],
            direction_label="down the shaft",
        )
        assert "requires_key" in portal.conditions


# =========================================================================
# Fey Glade Integration
# =========================================================================


class TestFeyGladeGeometry:
    """Validate the Fey Glade geometry loaded from GEOMETRY.md."""

    FEY_GLADE_PATH = Path("scenario/places/mistwood_hills/fey_glade/GEOMETRY.md")

    @pytest.fixture
    def fey_glade(self):
        return load_geometry(self.FEY_GLADE_PATH)

    def test_aeliana_starts_in_trail(self, fey_glade):
        aeliana_pos = Position(256.75, 81.25)
        assert fey_glade.zone_at(aeliana_pos) == "TRAIL"

    def test_fennel_starts_in_glade(self, fey_glade):
        fennel_pos = Position(190.0, 162.5)
        assert fey_glade.zone_at(fennel_pos) == "GLADE"

    def test_shadowbeast_starts_in_forest(self, fey_glade):
        shadowbeast_pos = Position(37, 50)
        assert fey_glade.zone_at(shadowbeast_pos) == "FOREST"

    def test_absolute_position_of_glade_center(self, fey_glade):
        abs_pos = fey_glade.absolute_position(Position(162.5, 162.5))
        assert abs_pos.x == pytest.approx(4134.0)
        assert abs_pos.y == pytest.approx(8638.5)
        assert abs_pos.z == pytest.approx(0.65)

    def test_nearest_landmark_to_fennel(self, fey_glade):
        fennel_pos = Position(190.0, 162.5)
        name, _ = fey_glade.nearest_landmark(fennel_pos)
        # oak_east (185.25,162.5) is ~4.75 ft away
        assert name == "oak_east"

    def test_nearest_landmark_to_aeliana(self, fey_glade):
        aeliana_pos = Position(256.75, 81.25)
        name, _ = fey_glade.nearest_landmark(aeliana_pos)
        assert name == "trail_entrance"

    def test_pool_surface_is_impassable(self, fey_glade):
        """The pool interior (136.5,169.0)-(139.75,172.25) is impassable."""
        pool_center = Position(138.12, 170.62)
        blocked = any(
            poly.contains(pool_center) for poly in fey_glade.impassable
        )
        assert blocked is True

    def test_glade_center_is_passable(self, fey_glade):
        glade_center = Position(50, 50)
        blocked = any(
            poly.contains(glade_center) for poly in fey_glade.impassable
        )
        assert blocked is False

    def test_fey_glade_boundary(self):
        """Repulsion boundary is 1m outside glade perimeter."""
        _, boundaries = load_geometry_full(self.FEY_GLADE_PATH)
        boundary = boundaries[0]
        assert boundary.is_blocked("shadowbeast") is True
        assert boundary.is_blocked("human") is False
        # Shadowbeast in forest (37,50) ft is outside boundary rect (126.75-198.25, 143-182)
        assert boundary.perimeter.contains(Position(37, 50)) is False
        # Inside glade (162.5,162.5) ft is inside boundary rect
        assert boundary.perimeter.contains(Position(162.5, 162.5)) is True
