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
    # Ambient (light-limited) sight range in ft. None = unlimited (e.g. a lit
    # or open-air scene). Set for dark scenes (caverns) where, absent another
    # light source, a creature only sees a short distance. Darkvision extends
    # this; mist/occlusion (visibility_rules) does not yield to it.
    ambient_visibility_ft: Optional[float] = None
    # Per-zone ambient override (zone name → range ft). Wins over the scene
    # default for an observer standing in that zone.
    zone_visibility_ft: dict[str, float] = field(default_factory=dict)
    # character_id → starting Position. Resolved from the scene file by
    # md_loader (authored `position` bullet), with the zone derived from the
    # coordinate. Geometry may still seed this as a migration fallback until the
    # GEOMETRY `## Starting Positions` table is retired.
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

    def floor_z_at(self, point: Position) -> float:
        """Local floor z at (point.x, point.y): the containing zone's vertex z
        interpolated across the polygon. Flat zones return their constant z;
        sloping passages return a least-squares plane fit, so the floor follows
        the slope as a creature descends. 0.0 when the point is outside every
        zone or the zone carries no z. Relative to the scene floor (matches the
        GEOMETRY vertex z); add ``z_level`` for world z. Distances within a scene
        only need this relative value (z_level cancels)."""
        for polygon in self.zones.values():
            if polygon.contains(point):
                return _interpolate_vertex_z(
                    getattr(polygon, "vertices", None) or [], point.x, point.y)
        return 0.0

    def ambient_sight_range(self, zone: Optional[str]) -> Optional[float]:
        """Ambient (light-limited) sight range in ft for an observer in ``zone``.

        Resolution: a per-zone override (``zone_visibility_ft``) wins over the
        scene default (``ambient_visibility_ft``). ``None`` means unlimited —
        no light-based cap applies (e.g. an open-air or lit scene). This is the
        ambient/light component only; mist and occlusion are handled separately
        by ``visibility_rules`` in ``can_see`` and are not affected by senses.
        """
        if zone:
            z = zone.upper()
            for name, rng in self.zone_visibility_ft.items():
                if name.upper() == z:
                    return rng
        return self.ambient_visibility_ft

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
        """Return True if pos_a has line-of-sight to pos_b.

        Resolution order:

        1. If an explicit ``visibility_rules`` entry exists for the
           ``(zone_a, zone_b)`` pair, it wins. ``0`` means blocked;
           otherwise the value is a max-range cap in feet. This lets
           open-air scenes (e.g. Fey Glade) opt into range-based fall-off
           without changing the underlying geometric model.
        2. Within the same zone, visibility is presumed (returns True).
        3. Between different zones, the segment from a→b is ray-traced
           through the union of all zone polygons. Every interior sample
           must lie inside (or on the edge of) some zone polygon. A
           sample landing in non-zoned space — i.e. "Solid Rock" / void
           between zones — blocks LOS.

        If the scene has no zones at all, no spatial constraint is applied
        and the function returns True.
        """
        import math

        # No spatial structure: no LOS constraint.
        if not self.zones:
            return True

        zone_a = (self.zone_at(pos_a) or "").upper()
        zone_b = (self.zone_at(pos_b) or "").upper()

        # 1. Explicit rules win.
        key = (zone_a, zone_b)
        if key in self.visibility_rules:
            max_range = self.visibility_rules[key]
            if max_range == 0:
                return False
            dist = math.hypot(pos_b.x - pos_a.x, pos_b.y - pos_a.y)
            return dist <= max_range

        # 2. Same zone: presumed visible.
        if zone_a and zone_a == zone_b:
            return True

        # 3. Different zones: ray-trace through zone-polygon union.
        dx = pos_b.x - pos_a.x
        dy = pos_b.y - pos_a.y
        length = math.hypot(dx, dy)
        if length == 0:
            return True
        # ~1 ft sample resolution; minimum 4 samples even for tiny segments.
        n_steps = max(4, int(length))
        edge_tol = 0.5  # tolerate samples sitting exactly on a zone seam
        # Skip endpoints — the observer can always "see" their own position
        # and the target's position is what we're testing reachability TO.
        for i in range(1, n_steps):
            t = i / n_steps
            sample = Position(pos_a.x + t * dx, pos_a.y + t * dy)
            in_zone = False
            for poly in self.zones.values():
                if poly.contains(sample):
                    in_zone = True
                    break
            if not in_zone:
                # Polygons sharing an edge may both fail .contains() on the
                # seam due to floating-point inclusivity. Allow samples
                # within edge_tol of any zone polygon's boundary.
                for poly in self.zones.values():
                    if poly.boundary_distance(sample) <= edge_tol:
                        in_zone = True
                        break
            if not in_zone:
                return False
        return True


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


def _solve3(a11, a12, a13, a21, a22, a23, a31, a32, a33, b1, b2, b3):
    """Solve a 3x3 linear system by Cramer's rule; None if singular."""
    det = (a11 * (a22 * a33 - a23 * a32)
           - a12 * (a21 * a33 - a23 * a31)
           + a13 * (a21 * a32 - a22 * a31))
    if abs(det) < 1e-12:
        return None
    dx = (b1 * (a22 * a33 - a23 * a32)
          - a12 * (b2 * a33 - a23 * b3)
          + a13 * (b2 * a32 - a22 * b3))
    dy = (a11 * (b2 * a33 - a23 * b3)
          - b1 * (a21 * a33 - a23 * a31)
          + a13 * (a21 * b3 - b2 * a31))
    dz = (a11 * (a22 * b3 - b2 * a32)
          - a12 * (a21 * b3 - b2 * a31)
          + b1 * (a21 * a32 - a22 * a31))
    return (dx / det, dy / det, dz / det)


def _interpolate_vertex_z(vertices, px: float, py: float) -> float:
    """Interpolate the floor z at (px, py) from a zone polygon's vertices.

    Flat polygons (all vertex z equal) return that constant; sloped ones fit a
    least-squares plane z = a*x + b*y + c over the vertices (exact for the
    planar quads that encode sloping passages) and evaluate it at (px, py).
    Returns 0.0 if the vertices carry no z (2D polygon)."""
    pts = [(v[0], v[1], v[2]) for v in vertices if len(v) > 2]
    if not pts:
        return 0.0
    zs = [p[2] for p in pts]
    if max(zs) - min(zs) < 1e-9:
        return zs[0]  # flat floor
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    n = float(len(pts))
    coeffs = _solve3(
        sum(p[0] * p[0] for p in pts), sum(p[0] * p[1] for p in pts), sx,
        sum(p[0] * p[1] for p in pts), sum(p[1] * p[1] for p in pts), sy,
        sx, sy, n,
        sum(p[0] * p[2] for p in pts), sum(p[1] * p[2] for p in pts), sum(zs),
    )
    if coeffs is None:
        return sum(zs) / len(zs)  # degenerate (collinear) -> average
    a, b, c = coeffs
    return a * px + b * py + c
