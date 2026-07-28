"""Spatial geometry helpers for movement resolution.

Extracted from engine.session (low-risk refactor): pure-ish geometry —
point/segment distance, polygon adjacency, zone entry points, speed clamping,
and the impassable / magical-boundary crossing checks. Depends only on stdlib,
models.space_time.Position, and the shared dice roller. session.py re-exports
these so the turn loop and other callers are unchanged.
"""

from __future__ import annotations

from engine.game_rng import rng
import re
from typing import Optional

from models.space_time import Position

from engine.dice import _roll_damage_expr


def _point_to_segment_distance_2d(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    """Distance from point (px, py) to segment (ax, ay)-(bx, by)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-9:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    qx, qy = ax + t * dx, ay + t * dy
    return ((px - qx) ** 2 + (py - qy) ** 2) ** 0.5


def _polygons_are_adjacent(poly_a, poly_b, tol: float = 0.75) -> bool:
    """True when two zone polygons share/touch an edge (or near-edge)."""
    va = list(getattr(poly_a, "vertices", []) or [])
    vb = list(getattr(poly_b, "vertices", []) or [])
    if not va or not vb:
        return False

    for v in va:
        ax, ay = float(v[0]), float(v[1])
        for i in range(len(vb)):
            x1, y1 = float(vb[i][0]), float(vb[i][1])
            x2, y2 = float(vb[(i + 1) % len(vb)][0]), float(vb[(i + 1) % len(vb)][1])
            if _point_to_segment_distance_2d(ax, ay, x1, y1, x2, y2) <= tol:
                return True

    for v in vb:
        bx, by = float(v[0]), float(v[1])
        for i in range(len(va)):
            x1, y1 = float(va[i][0]), float(va[i][1])
            x2, y2 = float(va[(i + 1) % len(va)][0]), float(va[(i + 1) % len(va)][1])
            if _point_to_segment_distance_2d(bx, by, x1, y1, x2, y2) <= tol:
                return True

    return False


def _entry_point_inside_zone(
    *,
    actor_x: float,
    actor_y: float,
    target_poly,
    inset: float = 3.0,
) -> tuple[float, float]:
    """Pick a point just inside target_poly near the actor-facing boundary."""
    actor_pos = Position(actor_x, actor_y)
    boundary = target_poly.nearest_point(actor_pos)
    center = target_poly.centroid()

    vx = center.x - boundary.x
    vy = center.y - boundary.y
    mag = (vx * vx + vy * vy) ** 0.5
    if mag <= 1e-9:
        return float(center.x), float(center.y)

    step = min(inset, mag * 0.95)
    ux, uy = vx / mag, vy / mag
    tx = boundary.x + ux * step
    ty = boundary.y + uy * step
    if target_poly.contains(Position(tx, ty)):
        return float(tx), float(ty)

    # Fallback: walk from boundary toward center until we are inside.
    for frac in (0.65, 0.8, 1.0):
        cx = boundary.x + vx * frac
        cy = boundary.y + vy * frac
        if target_poly.contains(Position(cx, cy)):
            return float(cx), float(cy)
    return float(center.x), float(center.y)


def _clamp_position(
    proposed: tuple[float, float, str],
    origin: tuple[float, float, str],
    max_feet: float,
) -> tuple[float, float, str]:
    """Clamp *proposed* to within *max_feet* of *origin*.

    If the proposed displacement exceeds max_feet, scales it back along
    the same direction so the character moves at most max_feet.
    The zone from *proposed* is preserved — zone assignment belongs to the DM.
    """
    import math
    ox, oy = origin[0], origin[1]
    px, py = proposed[0], proposed[1]
    dx, dy = px - ox, py - oy
    dist = math.hypot(dx, dy)
    if dist <= max_feet or dist == 0:
        return proposed
    scale = max_feet / dist
    return (round(ox + dx * scale, 1), round(oy + dy * scale, 1), proposed[2])


def _segment_polygon_entry(
    ox: float, oy: float, tx: float, ty: float,
    vertices: list[tuple[float, ...]],
) -> Optional[tuple[float, float]]:
    """Return (x, y) where segment origin→target first enters the polygon.

    Returns None if the segment does not cross any edge.
    Caller should verify origin is outside and target inside.
    """
    dx, dy = tx - ox, ty - oy
    best_t = float("inf")
    best_pt: Optional[tuple[float, float]] = None
    n = len(vertices)
    for i in range(n):
        ax, ay = vertices[i][0], vertices[i][1]
        bx, by = vertices[(i + 1) % n][0], vertices[(i + 1) % n][1]
        ex, ey = bx - ax, by - ay
        denom = dx * ey - dy * ex
        if abs(denom) < 1e-9:
            continue  # parallel
        t = ((ax - ox) * ey - (ay - oy) * ex) / denom
        u = ((ax - ox) * dy - (ay - oy) * dx) / denom
        if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0 and t < best_t:
            best_t = t
            best_pt = (ox + t * dx, oy + t * dy)
    return best_pt


def _check_impassable(
    character_id: str,
    origin: tuple[float, float, str],
    new_pos: tuple[float, float, str],
    impassable: list,
    zones: Optional[dict] = None,
) -> tuple[bool, list[str], Optional[tuple[float, float]]]:
    """Check whether origin→new_pos enters impassable space.

    Two rules combine:

    1. **Outside all zones** — if ``zones`` is provided and the destination
       is not inside any walkable zone, the move is blocked. This naturally
       handles "background rock" (the negative space between chambers in a
       cavern) without requiring it to be enumerated as an impassable
       polygon.
    2. **Inside an impassable polygon** — for finer-grained obstacles (a
       pool inside a chamber, a pillar in a room) declared in the
       ``## Impassable`` table. Polygons that already contain the origin are
       skipped so a character standing in a pool can step out of it; this is
       also why rule 1 (not rule 2) handles whole-scene "Solid Rock" entries.

    Returns (move_allowed, log_lines, stop_at). ``stop_at`` is set to a
    point just outside the offending edge so the character visibly slides
    up to the wall instead of refusing to leave its origin.
    """
    log_lines: list[str] = []
    if not impassable and not zones:
        return True, log_lines, None

    ox, oy = origin[0], origin[1]
    tx, ty = new_pos[0], new_pos[1]

    # Skip if origin and target are the same point.
    if abs(tx - ox) < 1e-6 and abs(ty - oy) < 1e-6:
        return True, log_lines, None

    origin_pos = Position(ox, oy)
    target_pos = Position(tx, ty)

    best_t = float("inf")
    best_stop: Optional[tuple[float, float]] = None
    best_name = ""

    # Rule 1: destination outside all walkable zones.
    if zones:
        in_any_zone = any(z.contains(target_pos) for z in zones.values())
        if not in_any_zone:
            origin_in_any_zone = any(z.contains(origin_pos) for z in zones.values())
            if origin_in_any_zone:
                # Find first zone exit along origin→target.
                for zname, zpoly in zones.items():
                    if not zpoly.contains(origin_pos):
                        continue
                    exit_pt = _segment_polygon_entry(
                        ox, oy, tx, ty, zpoly.vertices,
                    )
                    if exit_pt is None:
                        continue
                    seg_dx, seg_dy = tx - ox, ty - oy
                    seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
                    if seg_len_sq < 1e-9:
                        continue
                    t = ((exit_pt[0] - ox) * seg_dx + (exit_pt[1] - oy) * seg_dy) / seg_len_sq
                    if t < best_t:
                        best_t = t
                        best_stop = exit_pt
                        best_name = f"edge of {zname}"
            else:
                # Origin already outside zones — rare; let them try to move.
                pass

    # Rule 2: inside a foreground impassable polygon.
    for poly in (impassable or []):
        if poly.contains(origin_pos):
            continue  # already inside (e.g. pool) — let them try to leave
        crosses_in = poly.contains(target_pos)
        entry = _segment_polygon_entry(ox, oy, tx, ty, poly.vertices)
        if not crosses_in and entry is None:
            continue
        if entry is None:
            continue
        ex, ey = entry
        seg_dx, seg_dy = tx - ox, ty - oy
        seg_len_sq = seg_dx * seg_dx + seg_dy * seg_dy
        if seg_len_sq < 1e-9:
            continue
        t = ((ex - ox) * seg_dx + (ey - oy) * seg_dy) / seg_len_sq
        if t < best_t:
            best_t = t
            best_stop = (ex, ey)
            best_name = getattr(poly, "name", None) or "impassable"

    if best_stop is None:
        return True, log_lines, None

    # Back off ~0.5 ft from the edge so the character is clearly outside.
    ex, ey = best_stop
    seg_dx, seg_dy = tx - ox, ty - oy
    seg_len = (seg_dx * seg_dx + seg_dy * seg_dy) ** 0.5
    if seg_len > 1e-6:
        backoff = min(0.5, seg_len * 0.05)
        nx, ny = seg_dx / seg_len, seg_dy / seg_len
        stop_at = (ex - nx * backoff, ey - ny * backoff)
    else:
        stop_at = (ex, ey)

    log_lines.append(
        f"[IMPASSABLE] {character_id} blocked by {best_name}: "
        f"stops at x={stop_at[0]:.1f}, y={stop_at[1]:.1f}"
    )
    return False, log_lines, stop_at


def _check_boundary_crossing(
    character_id: str,
    origin: tuple[float, float, str],
    new_pos: tuple[float, float, str],
    character,
    boundaries: list,
    game_time,
) -> tuple[bool, int, list[str], Optional[tuple[float, float]]]:
    """Check if movement crosses a magical boundary inward.

    Returns (move_allowed, radiant_damage, log_lines, stop_at).
    ``stop_at`` is set when the save fails: a point just outside the barrier
    along the origin→target line, so the character visibly approaches the
    barrier and is repelled (rather than refusing to move at all).
    If the current period has no DC entry in the boundary table the barrier is
    quiescent and crossing is freely permitted (e.g. daylight — the beast avoids
    daylight by its own nature, not barrier force).
    """
    log_lines: list[str] = []

    ox, oy = origin[0], origin[1]
    tx, ty = new_pos[0], new_pos[1]
    origin_pos = Position(ox, oy)
    target_pos = Position(tx, ty)

    race = getattr(character, "race", "").lower().replace(" ", "_")
    char_type = getattr(character, "character_type", "").lower()
    # Strip trailing _N suffix so "shadowbeast_1" matches block entry "shadowbeast"
    base_id = re.sub(r"_\d+$", "", character_id).lower()

    for boundary in (boundaries or []):
        already_inside = boundary.perimeter.contains(origin_pos)
        would_enter = boundary.perimeter.contains(target_pos)

        if already_inside or not would_enter:
            continue  # not crossing inward

        if not (
            boundary.is_blocked(race)
            or boundary.is_blocked(char_type)
            or boundary.is_blocked(character_id)
            or boundary.is_blocked(base_id)
        ):
            continue  # this character is not affected by the boundary

        period = game_time.period if game_time else "night"
        dc = boundary.crossing_dc.get(period)

        if dc is None:
            # No DC for this period — barrier is quiescent, crossing allowed
            log_lines.append(
                f"[BOUNDARY] {character_id} crosses {boundary.name} freely "
                f"(period={period}, barrier quiescent)"
            )
            return True, 0, log_lines, None

        # Wisdom saving throw
        wisdom = getattr(character, "wisdom", 10)
        wis_mod = (wisdom - 10) // 2
        d20 = rng().randint(1, 20)
        total = d20 + wis_mod

        if total >= dc:
            damage_expr = boundary.crossing_damage_success.get(period, "")
            dmg = _roll_damage_expr(damage_expr) if damage_expr else 0
            # Double for radiant vulnerability if the character has it
            vulnerabilities = getattr(character, "damage_vulnerabilities", [])
            if any("radiant" in v.lower() for v in vulnerabilities):
                dmg *= 2
                log_lines.append(
                    f"[BOUNDARY] {character_id} crosses {boundary.name}: "
                    f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → SUCCESS, "
                    f"{dmg} radiant damage (doubled — radiant vulnerability)"
                )
            else:
                log_lines.append(
                    f"[BOUNDARY] {character_id} crosses {boundary.name}: "
                    f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → SUCCESS, "
                    f"{dmg} radiant damage"
                )
            return True, dmg, log_lines, None
        else:
            # Compute the point where the path enters the barrier and back
            # off ~0.5 ft so the character visibly approaches and stops at
            # the shimmer instead of refusing to leave its origin.
            stop_at: Optional[tuple[float, float]] = None
            entry = _segment_polygon_entry(
                ox, oy, tx, ty, boundary.perimeter.vertices,
            )
            if entry is not None:
                ex, ey = entry
                seg_dx, seg_dy = tx - ox, ty - oy
                seg_len = (seg_dx * seg_dx + seg_dy * seg_dy) ** 0.5
                if seg_len > 1e-6:
                    backoff = min(0.5, seg_len * 0.05)
                    nx, ny = seg_dx / seg_len, seg_dy / seg_len
                    stop_at = (ex - nx * backoff, ey - ny * backoff)
                else:
                    stop_at = (ex, ey)
            log_lines.append(
                f"[BOUNDARY] {character_id} repelled by {boundary.name}: "
                f"WIS save d20={d20}+{wis_mod}={total} vs DC {dc} → FAILED"
                + (f" — stops at x={stop_at[0]:.1f}, y={stop_at[1]:.1f}"
                   if stop_at else "")
            )
            return False, 0, log_lines, stop_at

    return True, 0, log_lines, None  # no blocking boundary found
