"""Spatial coordinate system and time tracking for the Driftmoor engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from typing import Optional


@dataclass
class Position:
    """3D position in feet."""

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Position) -> float:
        """Euclidean distance in 3D."""
        return sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )

    def horizontal_distance_to(self, other: Position) -> float:
        """Euclidean distance ignoring z (for movement cost on same level)."""
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass
class Polygon:
    """Polygon defined by vertices with optional z elevation. Used for zones and boundaries."""

    vertices: list[tuple[float, ...]]

    @property
    def z(self) -> float:
        """Average z of all vertices (0.0 if vertices are 2D)."""
        zs = [v[2] if len(v) > 2 else 0.0 for v in self.vertices]
        return sum(zs) / len(zs) if zs else 0.0

    def contains(self, point: Position) -> bool:
        """Point-in-polygon test using ray casting algorithm."""
        x, y = point.x, point.y
        n = len(self.vertices)
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = self.vertices[i][0], self.vertices[i][1]
            xj, yj = self.vertices[j][0], self.vertices[j][1]
            if ((yi > y) != (yj > y)) and (
                x < (xj - xi) * (y - yi) / (yj - yi) + xi
            ):
                inside = not inside
            j = i
        return inside

    def boundary_distance(self, point: Position) -> float:
        """Distance from point to nearest edge of the polygon."""
        min_dist = float("inf")
        n = len(self.vertices)
        for i in range(n):
            j = (i + 1) % n
            dist = _point_to_segment_distance(
                point.x, point.y,
                self.vertices[i][0], self.vertices[i][1],
                self.vertices[j][0], self.vertices[j][1],
            )
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def nearest_point(self, point: Position) -> Position:
        """Nearest point on polygon boundary to the given point."""
        min_dist = float("inf")
        nearest = Position(0, 0)
        n = len(self.vertices)
        for i in range(n):
            j = (i + 1) % n
            px, py = _nearest_point_on_segment(
                point.x, point.y,
                self.vertices[i][0], self.vertices[i][1],
                self.vertices[j][0], self.vertices[j][1],
            )
            dist = sqrt((point.x - px) ** 2 + (point.y - py) ** 2)
            if dist < min_dist:
                min_dist = dist
                nearest = Position(px, py)
        return nearest

    def centroid(self) -> Position:
        """Average of vertices (simple centroid)."""
        n = len(self.vertices)
        cx = sum(v[0] for v in self.vertices) / n
        cy = sum(v[1] for v in self.vertices) / n
        return Position(cx, cy)


def _point_to_segment_distance(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
) -> float:
    """Distance from point (px, py) to line segment (ax,ay)-(bx,by)."""
    nx, ny = _nearest_point_on_segment(px, py, ax, ay, bx, by)
    return sqrt((px - nx) ** 2 + (py - ny) ** 2)


def _nearest_point_on_segment(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float,
) -> tuple[float, float]:
    """Nearest point on segment (ax,ay)-(bx,by) to point (px,py)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ax, ay
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    return ax + t * dx, ay + t * dy


@dataclass
class GameTime:
    """Tracks in-game time with period-of-day and advance logic."""

    hour: int
    minute: int
    day: int
    season: str
    turn_duration: int  # minutes per turn
    absolute_turn: int  # total turns elapsed

    @property
    def period(self) -> str:
        if 4 <= self.hour < 6:
            return "dawn"
        elif 6 <= self.hour < 12:
            return "morning"
        elif 12 <= self.hour < 14:
            return "midday"
        elif 14 <= self.hour < 18:
            return "afternoon"
        elif 18 <= self.hour < 20:
            return "dusk"
        elif 20 <= self.hour < 23:
            return "evening"
        else:
            return "night"

    @property
    def is_dark(self) -> bool:
        return self.period in ("evening", "night", "dawn")

    def advance(self, turns: int = 1) -> None:
        """Advance time by the given number of turns."""
        minutes = self.turn_duration * turns
        self.minute += minutes
        while self.minute >= 60:
            self.minute -= 60
            self.hour += 1
        while self.hour >= 24:
            self.hour -= 24
            self.day += 1
        self.absolute_turn += turns

    def minutes_until(self, target_hour: int) -> int:
        """Minutes until a target hour (wraps to next day if needed)."""
        current_minutes = self.hour * 60 + self.minute
        target_minutes = target_hour * 60
        if target_minutes <= current_minutes:
            target_minutes += 24 * 60
        return target_minutes - current_minutes

    def turns_until(self, target_hour: int) -> int:
        """Turns until a target hour."""
        return self.minutes_until(target_hour) // self.turn_duration


@dataclass
class SceneGeometry:
    """Spatial geometry for a scene — zones, landmarks, boundaries."""

    name: str
    place_path: str
    z_level: float
    width: float
    height: float
    origin: Position
    landmarks: dict[str, Position] = field(default_factory=dict)
    zones: dict[str, Polygon] = field(default_factory=dict)
    impassable: list[Polygon] = field(default_factory=list)
    connections: dict[str, Position] = field(default_factory=dict)
    # zone-pair → max visible range in ft; missing pair = unlimited
    visibility_rules: dict[tuple[str, str], float] = field(default_factory=dict)
    # character_id → starting Position parsed from GEOMETRY.md
    starting_positions: dict[str, Position] = field(default_factory=dict)
    # magical and physical boundaries
    boundaries: list["MagicalBoundary"] = field(default_factory=list)

    def absolute_position(self, local: Position) -> Position:
        """Convert local scene coordinates to world coordinates."""
        return Position(
            x=self.origin.x + local.x,
            y=self.origin.y + local.y,
            z=self.origin.z + local.z,
        )

    def zone_at(self, point: Position) -> Optional[str]:
        """Return the zone name containing the given point, or None."""
        for name, polygon in self.zones.items():
            if polygon.contains(point):
                return name
        return None

    def nearest_landmark(self, point: Position) -> tuple[str, Position]:
        """Return (name, position) of the nearest landmark."""
        best_name = ""
        best_pos = Position(0, 0)
        best_dist = float("inf")
        for name, pos in self.landmarks.items():
            dist = point.horizontal_distance_to(pos)
            if dist < best_dist:
                best_dist = dist
                best_name = name
                best_pos = pos
        return best_name, best_pos

    def can_see(self, pos_a: Position, pos_b: Position) -> bool:
        """Return True if pos_a has line-of-sight to pos_b per visibility_rules.

        If no rule exists for the zone pair, sight is unrestricted (returns True).
        """
        import math
        zone_a = (self.zone_at(pos_a) or "FOREST").upper()
        zone_b = (self.zone_at(pos_b) or "FOREST").upper()
        key = (zone_a, zone_b)
        if key not in self.visibility_rules:
            return True  # no rule → no restriction
        max_range = self.visibility_rules[key]
        if max_range == 0:
            return False
        dist = math.hypot(pos_b.x - pos_a.x, pos_b.y - pos_a.y)
        return dist <= max_range


@dataclass
class MagicalBoundary:
    """A boundary with magical blocking properties."""

    name: str
    perimeter: Polygon
    blocks: list[str]
    effect: str
    # Ability check to cross ("wisdom", "dexterity", etc.)
    save: str = "wisdom"
    # period → DC; if period absent, crossing is absolutely blocked
    crossing_dc: dict[str, int] = field(default_factory=dict)
    # period → dice expression dealt on a successful crossing (e.g. "2d6")
    crossing_damage_success: dict[str, str] = field(default_factory=dict)

    def is_blocked(self, entity_type: str) -> bool:
        """Check if an entity type is blocked by this boundary."""
        return entity_type.lower() in [b.lower() for b in self.blocks]


@dataclass
class Portal:
    """A connection between two scenes."""

    from_scene: str
    from_position: Position
    to_scene: str
    to_position: Position
    traversal_cost: float
    conditions: list[str] = field(default_factory=list)
    direction_label: str = ""
