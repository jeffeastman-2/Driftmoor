"""Load scene geometry from GEOMETRY.md files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.space_time import (
    Position, Polygon, SceneGeometry, MagicalBoundary,
)


# ---------------------------------------------------------------------------
# Auto-walls: zone boundaries are impassable by default
# ---------------------------------------------------------------------------

# EXTERIOR is excluded from auto-walling: it's a huge background zone whose
# polygon commonly extends far past a building's real footprint (so a scene
# can place a character "just outside the door"), which means it rarely
# shares a *true* wall edge with an interior zone the way two interior zones
# do. The tavern's own back wall sits inset a couple of feet from KITCHEN's
# nominal zone edge for exactly this reason. Exterior-facing walls stay a
# manual ## Impassable concern, same as they always were.
_AUTO_WALL_EXCLUDED_ZONES = frozenset({"EXTERIOR"})


def _axis_aligned_overlap(
    a1: tuple[float, float], a2: tuple[float, float],
    b1: tuple[float, float], b2: tuple[float, float],
) -> Optional[tuple[str, float, float, float]]:
    """Overlapping run of two collinear axis-aligned segments, or None.

    Returns (orientation, coord, lo, hi): orientation is 'h' (shared y) or
    'v' (shared x); coord is that shared line; lo/hi is the overlap range
    along the other axis. Segments that aren't both horizontal, both
    vertical, or on the same line, or that don't actually overlap, return
    None. Diagonal edges are never produced by this game's rectangular
    zones, so they're simply not matched rather than guessed at.
    """
    ax1, ay1 = a1
    ax2, ay2 = a2
    bx1, by1 = b1
    bx2, by2 = b2
    if ay1 == ay2 and by1 == by2 and ay1 == by1:
        a_lo, a_hi = sorted((ax1, ax2))
        b_lo, b_hi = sorted((bx1, bx2))
        lo, hi = max(a_lo, b_lo), min(a_hi, b_hi)
        if hi - lo > 1e-6:
            return ("h", ay1, lo, hi)
        return None
    if ax1 == ax2 and bx1 == bx2 and ax1 == bx1:
        a_lo, a_hi = sorted((ay1, ay2))
        b_lo, b_hi = sorted((by1, by2))
        lo, hi = max(a_lo, b_lo), min(a_hi, b_hi)
        if hi - lo > 1e-6:
            return ("v", ax1, lo, hi)
        return None
    return None


def _bbox(verts: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    return min(xs), min(ys), max(xs), max(ys)


def _bbox_contains(
    outer: tuple[float, float, float, float],
    inner: tuple[float, float, float, float],
) -> bool:
    ox0, oy0, ox1, oy1 = outer
    ix0, iy0, ix1, iy1 = inner
    return ox0 <= ix0 and oy0 <= iy0 and ox1 >= ix1 and oy1 >= iy1


def compute_auto_walls(
    zones: dict[str, list[tuple[float, float]]],
    landmarks: dict[str, tuple[float, float]],
    *,
    door_gap_ft: float = 3.0,
    wall_thickness_ft: float = 1.0,
    excluded_zones: frozenset[str] = frozenset(),
) -> list[list[tuple[float, float]]]:
    """Wall every zone-boundary segment solid, except where a door or
    archway landmark opens it — including the boundary against EXTERIOR
    (or against nothing at all), not just shared edges between two named
    interior zones.

    A landmark whose name contains "door" (case-insensitive) sits on the
    edge and carves a ``door_gap_ft``-wide gap centered on itself —
    multiple doors on the same long wall each get their own gap. A
    landmark whose name contains "archway" instead leaves that entire
    edge open with no wall at all, for boundaries that were never meant
    to have a real door (a stairway landing, walking up to a bar
    counter). A whole scene opts out with "## Walls\n- **auto_wall:**
    false"; a single zone within an otherwise auto-walled scene opts out
    via its own Zones-table "auto_wall" column (e.g. TOWN_COMMON's soft
    "beyond this line is wilderness" edge, which a hard wall would
    contradict) — ``excluded_zones`` carries that per-zone set in from
    the caller.

    A walled zone enforces its whole perimeter regardless of what's on
    the other side of any given edge, so a zone named in
    ``excluded_zones`` only waives its *own* boundary — a neighbor that
    isn't excluded still walls its side of a shared edge (needing a
    door/archway to cross, same as any other wall). An edge is left
    fully open only when *both* zones sharing it are excluded. Driftmoor
    town is the motivating case: TOWN_COMMON opts out for its open
    "beyond this line is wilderness" edge, but GREYWATER_RIVER doesn't —
    so the river still can't be walked into directly, only crossed where
    the model already treats it as a non-boundary (BRIDGE nested over
    it, the same exemption a stairway landing gets from its hall).

    EXTERIOR itself is excluded from the zone list: its polygon commonly
    extends past a building's real footprint (so a scene can place a
    character "just outside the door"), so its own edges essentially
    never land exactly on an interior zone's edge the way two interior
    zones' edges do. Rather than require that alignment, every edge of
    every remaining zone is walled by default; an edge actually shared
    with a neighboring zone (found by the usual exact-coincidence
    matching) is walled once as that shared segment, and whatever's left
    over — the part of the zone's perimeter no neighbor claimed — is
    walled too, standing in for the boundary against EXTERIOR or open
    space that was never given its own aligned zone.

    A zone whose bounding box is fully contained within another's is
    exempted from this leftover pass entirely: it isn't a real room with
    its own exterior-facing walls, just a named sub-region carved out of
    the larger zone by table order (a stairway landing labeled out of
    its hall, matching the "zone order matters, first match wins"
    convention used for zone_at()) — trying to wall its "leftover"
    perimeter would seal it off from the very zone it's part of.

    Only axis-aligned edges are considered, matching every zone authored
    in this game so far. Returns raw rectangle vertex lists — callers
    wrap them as Polygon (the engine) or (description, verts) tuples
    (the map renderer) to match their own Impassable representation.
    """
    excluded_upper = {n.upper() for n in excluded_zones}
    names = [n for n in zones if n.upper() not in _AUTO_WALL_EXCLUDED_ZONES]
    boxes = {n: _bbox(zones[n]) for n in names}
    half_thickness = wall_thickness_ft / 2.0
    half_gap = door_gap_ft / 2.0
    walls: list[list[tuple[float, float]]] = []

    def wall_segment(orient: str, coord: float, lo: float, hi: float) -> None:
        door_positions: list[float] = []
        archway_found = False
        for lname, (lx, ly) in landmarks.items():
            lname_low = lname.lower()
            is_door = "door" in lname_low or "gate" in lname_low
            is_archway = "archway" in lname_low
            if not is_door and not is_archway:
                continue
            along, perp = (lx, ly) if orient == "h" else (ly, lx)
            if abs(perp - coord) > 0.05 or not (lo - 0.01 <= along <= hi + 0.01):
                continue
            if is_archway:
                archway_found = True
            else:
                door_positions.append(along)
        if archway_found:
            return  # intentionally open — no wall on this segment at all

        cursor = lo
        spans: list[tuple[float, float]] = []
        for d in sorted(door_positions):
            gap_lo, gap_hi = d - half_gap, d + half_gap
            if gap_lo > cursor:
                spans.append((cursor, gap_lo))
            cursor = max(cursor, gap_hi)
        if cursor < hi:
            spans.append((cursor, hi))

        for s0, s1 in spans:
            if s1 - s0 <= 1e-6:
                continue
            if orient == "h":
                walls.append([
                    (s0, coord - half_thickness),
                    (s1, coord - half_thickness),
                    (s1, coord + half_thickness),
                    (s0, coord + half_thickness),
                ])
            else:
                walls.append([
                    (coord - half_thickness, s0),
                    (coord + half_thickness, s0),
                    (coord + half_thickness, s1),
                    (coord - half_thickness, s1),
                ])

    # Pass 1: shared edges between two real (non-nested) zones. Also
    # records, per zone, which sub-ranges of its own edges got claimed by
    # a neighbor, so pass 2 knows what's left over.
    claimed: dict[str, list[tuple[str, float, float, float]]] = {n: [] for n in names}
    for i in range(len(names)):
        verts_a = zones[names[i]]
        edges_a = list(zip(verts_a, verts_a[1:] + verts_a[:1]))
        for j in range(i + 1, len(names)):
            if (
                _bbox_contains(boxes[names[i]], boxes[names[j]])
                or _bbox_contains(boxes[names[j]], boxes[names[i]])
            ):
                continue
            verts_b = zones[names[j]]
            edges_b = list(zip(verts_b, verts_b[1:] + verts_b[:1]))
            for a1, a2 in edges_a:
                for b1, b2 in edges_b:
                    seg = _axis_aligned_overlap(a1, a2, b1, b2)
                    if seg is None:
                        continue
                    orient, coord, lo, hi = seg
                    # A walled zone enforces its whole perimeter — doors
                    # and archways aside — regardless of whether the
                    # zone on the other side of a given edge opted out.
                    # auto_wall:false only exempts a zone from enforcing
                    # its *own* boundary; it can't waive a neighbor's.
                    # This edge is open only if both sides opted out.
                    if (
                        names[i].upper() not in excluded_upper
                        or names[j].upper() not in excluded_upper
                    ):
                        wall_segment(orient, coord, lo, hi)
                    claimed[names[i]].append((orient, coord, lo, hi))
                    claimed[names[j]].append((orient, coord, lo, hi))

    # Pass 2: each zone's own perimeter, minus whatever pass 1 already
    # claimed — the leftover stands in for the boundary against EXTERIOR
    # (or against nothing at all). A zone with auto_wall:false is skipped
    # entirely here too, so its true unclaimed perimeter stays open.
    for name in names:
        if name.upper() in excluded_upper:
            continue
        if any(
            other != name and _bbox_contains(boxes[other], boxes[name])
            for other in names
        ):
            continue  # nested sub-region — not exposed to the outside
        verts = zones[name]
        edges = list(zip(verts, verts[1:] + verts[:1]))
        for (ax1, ay1), (ax2, ay2) in edges:
            if ay1 == ay2:
                orient, coord = "h", ay1
            elif ax1 == ax2:
                orient, coord = "v", ax1
            else:
                continue  # diagonal, not produced by this game's zones
            lo, hi = sorted((ax1, ax2) if orient == "h" else (ay1, ay2))
            overlaps = sorted(
                (clo, chi) for (co, cc, clo, chi) in claimed[name]
                if co == orient and abs(cc - coord) < 1e-6
            )
            cursor = lo
            for clo, chi in overlaps:
                if clo > cursor:
                    wall_segment(orient, coord, cursor, clo)
                cursor = max(cursor, chi)
            if cursor < hi:
                wall_segment(orient, coord, cursor, hi)
    return walls


def _shares_an_edge(
    verts_a: list[tuple[float, float]], verts_b: list[tuple[float, float]],
) -> bool:
    edges_a = list(zip(verts_a, verts_a[1:] + verts_a[:1]))
    edges_b = list(zip(verts_b, verts_b[1:] + verts_b[:1]))
    return any(
        _axis_aligned_overlap(a1, a2, b1, b2) is not None
        for a1, a2 in edges_a for b1, b2 in edges_b
    )


def _point_in_polygon(x: float, y: float, verts: list[tuple[float, float]]) -> bool:
    inside = False
    n = len(verts)
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def compute_venue_walls(
    zones: dict[str, list[tuple[float, float]]],
    connections: dict[str, tuple[float, float]],
    *,
    wall_thickness_ft: float = 1.0,
) -> list[list[tuple[float, float]]]:
    """Fully wall the perimeter of every zone that's a sealed "venue" — an
    isolated building or structure with its own place, identified by a
    Connections entry whose point lands inside it.

    A town-square building (TAVERN, ELYSSA_COTTAGE, ...) is a small zone
    nested entirely inside a much bigger one (TOWN_COMMON): it shares no
    boundary *edge* with anything, so ``compute_auto_walls`` (which only
    walls shared edges) never touches it, and a character could walk
    straight through its footprint. Venue entry crosses scenes via the
    "enter <place>" action (see the venue-entry-via-LATN design), not by
    walking through geometry, so unlike a room-to-room doorway a venue
    zone gets no door/archway carve-out — the wall is solid all the way
    around.

    Open terrain that merely nests on the map (a garden, a bridge, a well,
    the docks) has no Connections point inside it and is left untouched. A
    zone that shares a real boundary edge with any other zone is never
    treated as a venue even if a connection point happens to fall inside
    it — that's an ordinary room (a building's own STUDY or MAIN_ROOM,
    whose front-door connection back out to its parent place naturally
    sits inside it) or a background region (TOWN_COMMON, NORTH_BANK,
    AZURE_SEA border each other along real coastline/riverbank edges);
    either way ``compute_auto_walls``'s door-gap mechanism is what
    applies to it, not a full seal.
    """
    names = [n for n in zones if n.upper() not in _AUTO_WALL_EXCLUDED_ZONES]
    conn_points = list(connections.values())
    half = wall_thickness_ft / 2.0
    walls: list[list[tuple[float, float]]] = []

    for name in names:
        verts = zones[name]
        if any(
            other != name and _shares_an_edge(verts, zones[other])
            for other in names
        ):
            continue  # edge-adjacent to something — an ordinary room/region
        if not any(_point_in_polygon(cx, cy, verts) for cx, cy in conn_points):
            continue  # open terrain, no place of its own
        edges = list(zip(verts, verts[1:] + verts[:1]))
        for (x1, y1), (x2, y2) in edges:
            if y1 == y2:
                lo, hi = sorted((x1, x2))
                walls.append([
                    (lo, y1 - half), (hi, y1 - half),
                    (hi, y1 + half), (lo, y1 + half),
                ])
            elif x1 == x2:
                lo, hi = sorted((y1, y2))
                walls.append([
                    (x1 - half, lo), (x1 + half, lo),
                    (x1 + half, hi), (x1 - half, hi),
                ])
    return walls


def door_landmarks_between(
    zones: dict[str, "Polygon"],
    landmarks: dict[str, "Position"],
    zone_a: str,
    zone_b: str,
) -> list[tuple[str, float, float, str]]:
    """Door/archway landmarks sitting on the shared boundary of two zones.

    Returns (name, x, y, orientation) — orientation is 'h' for a landmark
    on a horizontal (shared-y) boundary, 'v' for vertical (shared-x), so a
    caller building a safe approach route knows which axis is "along the
    wall" versus "through it".

    Movement routing (``_waypoint_for_zone`` in engine/session.py) uses this
    to aim at the actual authored doorway between two zones instead of a
    generic "nearest boundary point toward the centroid" guess — the latter
    has no idea where walls are and, now that zone boundaries are
    impassable by default (see ``compute_auto_walls``), routinely aims
    straight into one. Same edge-matching and name convention as
    ``compute_auto_walls``; kept as a separate query since callers want the
    landmark position itself, not a generated wall.
    """
    za, zb = zone_a.upper(), zone_b.upper()
    poly_a = next((p for n, p in zones.items() if n.upper() == za), None)
    poly_b = next((p for n, p in zones.items() if n.upper() == zb), None)
    if poly_a is None or poly_b is None:
        return []
    verts_a = [(v[0], v[1]) for v in poly_a.vertices]
    verts_b = [(v[0], v[1]) for v in poly_b.vertices]
    edges_a = list(zip(verts_a, verts_a[1:] + verts_a[:1]))
    edges_b = list(zip(verts_b, verts_b[1:] + verts_b[:1]))

    found: list[tuple[str, float, float, str]] = []
    for a1, a2 in edges_a:
        for b1, b2 in edges_b:
            seg = _axis_aligned_overlap(a1, a2, b1, b2)
            if seg is None:
                continue
            orient, coord, lo, hi = seg
            for lname, pos in landmarks.items():
                lname_low = lname.lower()
                if (
                    "door" not in lname_low
                    and "gate" not in lname_low
                    and "archway" not in lname_low
                ):
                    continue
                lx, ly = pos.x, pos.y
                along, perp = (lx, ly) if orient == "h" else (ly, lx)
                if abs(perp - coord) <= 0.05 and lo - 0.01 <= along <= hi + 0.01:
                    found.append((lname, lx, ly, orient))
    return found


# ---------------------------------------------------------------------------
# Low-level parsing helpers
# ---------------------------------------------------------------------------


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a ``## heading`` up to the next ``##`` or EOF."""
    pattern = rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_subsection(text: str, heading: str) -> str:
    """Extract content under a ``### heading`` up to the next ``###``, ``##``, or EOF."""
    pattern = rf"^###\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^###?\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_table_rows(section_text: str) -> list[list[str]]:
    """Parse markdown table rows, skipping header and separator lines."""
    rows: list[list[str]] = []
    lines = section_text.strip().splitlines()
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # Remove empty first/last from leading/trailing |
        cells = [c for c in cells if c]
        # Skip separator lines (----)
        if cells and all(re.match(r"^-+$", c) for c in cells):
            continue
        # Skip header row (detected by being the first row)
        if cells:
            rows.append(cells)
    return rows


def _parse_position(x_str: str, y_str: str, z_str: str = "0.0") -> Position:
    """Parse x, y, z strings into a Position."""
    return Position(float(x_str), float(y_str), float(z_str))


def _parse_vertices(text: str) -> list[tuple[float, ...]]:
    """Parse vertex tuples like '(x,y)' or '(x,y,z)' into a list."""
    pairs = re.findall(r"\(\s*([-\d.]+)\s*,\s*([-\d.]+)(?:\s*,\s*([-\d.]+))?\s*\)", text)
    result: list[tuple[float, ...]] = []
    for match in pairs:
        x, y, z = match
        if z:
            result.append((float(x), float(y), float(z)))
        else:
            result.append((float(x), float(y)))
    return result


def _parse_metadata(section_text: str) -> dict[str, str]:
    """Parse ``- **key:** value`` lines into a dict."""
    result: dict[str, str] = {}
    for line in section_text.splitlines():
        m = re.match(r"-\s*\*\*(.+?):\*\*\s*(.+)", line.strip())
        if m:
            result[m.group(1).strip()] = m.group(2).strip()
    return result


# ---------------------------------------------------------------------------
# High-level parse
# ---------------------------------------------------------------------------


def parse_geometry_md(text: str) -> dict:
    """Parse a GEOMETRY.md file into a dict of geometry data."""
    result: dict = {}

    # --- Scene metadata ---
    scene_section = _extract_section(text, "Scene")
    scene_meta = _parse_metadata(scene_section)
    result["name"] = scene_meta.get("name", "")
    result["place_path"] = scene_meta.get("place_path", "")
    result["z_level"] = float(scene_meta.get("z_level", "0.0"))
    result["width"] = float(scene_meta.get("width", "0.0"))
    result["height"] = float(scene_meta.get("height", "0.0"))

    origin_str = scene_meta.get("origin", "0, 0, 0")
    origin_parts = [float(p.strip()) for p in origin_str.split(",")]
    result["origin"] = Position(*origin_parts)

    # --- Landmarks ---
    landmarks_section = _extract_section(text, "Landmarks")
    table_rows = _parse_table_rows(landmarks_section)
    landmarks: dict[str, Position] = {}
    for row in table_rows:
        if len(row) >= 3:
            name = row[0].strip()
            if name == "name":  # skip header
                continue
            z = float(row[3]) if len(row) >= 4 else 0.0
            landmarks[name] = Position(float(row[1]), float(row[2]), z)
    result["landmarks"] = landmarks

    # --- Zones ---
    zones_section = _extract_section(text, "Zones")
    zone_rows = _parse_table_rows(zones_section)
    zones: dict[str, Polygon] = {}
    zone_floor_z: dict[str, float] = {}
    zone_ceiling_z: dict[str, float] = {}
    zone_z_explicit: set[str] = set()
    zone_auto_wall_off: set[str] = set()
    zone_headers = {
        cell.strip().lower(): i
        for i, cell in enumerate(zone_rows[0])
    } if zone_rows else {}
    for row in zone_rows[1:] if zone_rows else []:
        if len(row) >= 2:
            name = row[0].strip()
            # Vertices are in the last column (supports 2-col or 3-col tables)
            verts = _parse_vertices(row[-1])
            zones[name] = Polygon(verts)
            auto_wall_idx = zone_headers.get("auto_wall")
            if auto_wall_idx is not None and auto_wall_idx < len(row):
                if row[auto_wall_idx].strip().lower() in {"false", "no", "0"}:
                    zone_auto_wall_off.add(name)
            floor_idx = zone_headers.get("floor_z")
            ceiling_idx = zone_headers.get("ceiling_z")
            if floor_idx is not None or ceiling_idx is not None:
                zone_z_explicit.add(name)
            try:
                floor = float(row[floor_idx]) if floor_idx is not None else 0.0
            except (ValueError, IndexError):
                floor = 0.0
            try:
                ceiling = (
                    float(row[ceiling_idx]) if ceiling_idx is not None else 8.0
                )
            except (ValueError, IndexError):
                ceiling = 8.0
            if ceiling <= floor:
                raise ValueError(
                    f"Zone {name!r} ceiling_z ({ceiling}) must exceed "
                    f"floor_z ({floor})"
                )
            zone_floor_z[name] = floor
            zone_ceiling_z[name] = ceiling
    result["zones"] = zones
    result["zone_floor_z"] = zone_floor_z
    result["zone_ceiling_z"] = zone_ceiling_z
    result["zone_z_explicit"] = zone_z_explicit

    # --- Connections --- (parsed ahead of Impassable: compute_venue_walls
    # needs connection points to identify sealed-venue zones)
    connections_section = _extract_section(text, "Connections")
    conn_rows = _parse_table_rows(connections_section)
    connections: dict[str, Position] = {}
    for row in conn_rows:
        if len(row) >= 3:
            name = row[0].strip()
            if name == "name":
                continue
            connections[name] = Position(float(row[1]), float(row[2]))
    result["connections"] = connections

    # --- Impassable ---
    impassable_section = _extract_section(text, "Impassable")
    impassable_rows = _parse_table_rows(impassable_section)
    impassable: list[Polygon] = []
    for row in impassable_rows:
        if len(row) >= 2:
            desc = row[0].strip()
            if desc == "description":
                continue
            verts = _parse_vertices(row[1])
            if verts:
                impassable.append(Polygon(verts))
    # Zone boundaries are impassable by default; door/archway landmarks
    # open them (see compute_auto_walls). On by default for every scene;
    # opt out with "## Walls\n- **auto_wall:** false" for the rare scene
    # whose zones don't map cleanly onto this convention (e.g. fey_glade's
    # diagonal TRAIL zone and non-"*_door"/"*_archway" landmark names).
    # A single zone within an otherwise auto-walled scene can opt out via
    # its own Zones-table "auto_wall" column instead (zone_auto_wall_off).
    walls_meta = _parse_metadata(_extract_section(text, "Walls"))
    if walls_meta.get("auto_wall", "true").strip().lower() not in {
        "false", "no", "0",
    }:
        _zone_verts = {
            name: [(v[0], v[1]) for v in poly.vertices]
            for name, poly in zones.items()
        }
        _landmark_xy = {name: (pos.x, pos.y) for name, pos in landmarks.items()}
        _connection_xy = {name: (pos.x, pos.y) for name, pos in connections.items()}
        impassable.extend(
            Polygon(verts)
            for verts in compute_auto_walls(
                _zone_verts, _landmark_xy,
                excluded_zones=frozenset(zone_auto_wall_off),
            )
        )
        impassable.extend(
            Polygon(verts)
            for verts in compute_venue_walls(_zone_verts, _connection_xy)
        )
    result["impassable"] = impassable

    # --- Boundaries ---
    boundaries_section = _extract_section(text, "Boundaries")
    result["boundaries"] = _parse_boundaries(boundaries_section)

    # Character placement is a scene concern (authored in scenes/<scene>.md), not
    # geometry: GEOMETRY.md is a pure stage. There is no "Starting Positions"
    # table to parse here.

    # --- Visibility ---
    visibility_section = _extract_section(text, "Visibility")
    vis_rows = _parse_table_rows(visibility_section)
    visibility: dict[tuple[str, str], float] = {}
    for row in vis_rows:
        if len(row) >= 3:
            from_zone = row[0].strip().upper()
            to_zone = row[1].strip().upper()
            if from_zone in ("FROM_ZONE", "FROM"):
                continue
            try:
                max_range = float(row[2].strip())
            except ValueError:
                continue
            visibility[(from_zone, to_zone)] = max_range
    result["visibility"] = visibility

    # --- Ambient Visibility (light-limited sight range) ---
    ambient_section = _extract_section(text, "Ambient Visibility")
    ambient_default: Optional[float] = None
    zone_visibility: dict[str, float] = {}
    if ambient_section:
        meta = _parse_metadata(ambient_section)
        default_raw = meta.get("default", "")
        if default_raw:
            try:
                ambient_default = float(default_raw)
            except ValueError:
                ambient_default = None
        for row in _parse_table_rows(ambient_section):
            if len(row) >= 2:
                zone = row[0].strip().upper()
                if zone in ("ZONE", "NAME"):
                    continue
                try:
                    zone_visibility[zone] = float(row[1].strip())
                except ValueError:
                    continue
    result["ambient_visibility_ft"] = ambient_default
    result["zone_visibility_ft"] = zone_visibility

    return result


def _parse_period_dict(value: str) -> dict[str, str]:
    """Parse 'dusk:8, evening:14' or 'dusk:2d6, evening:1d6' into a dict."""
    result: dict[str, str] = {}
    for part in value.split(","):
        part = part.strip()
        if ":" in part:
            period, val = part.split(":", 1)
            result[period.strip().lower()] = val.strip()
    return result


def _parse_boundaries(text: str) -> list[MagicalBoundary]:
    """Parse boundary subsections from the Boundaries section."""
    boundaries: list[MagicalBoundary] = []
    # Find all ### headings
    headings = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)
    for heading in headings:
        sub = _extract_subsection(text, heading)
        meta = _parse_metadata(sub)

        blocks_str = meta.get("blocks", "")
        blocks = [
            b.strip() for b in blocks_str.split(",")
            if b.strip() and b.strip().lower() not in {"none", "nothing", "no"}
        ]

        verts_str = meta.get("vertices", "")
        verts = _parse_vertices(verts_str)

        # Crossing rules
        dc_raw = _parse_period_dict(meta.get("crossing_dc", ""))
        crossing_dc = {k: int(v) for k, v in dc_raw.items() if v.isdigit()}
        crossing_damage_success = _parse_period_dict(meta.get("crossing_damage_success", ""))

        if verts:
            boundaries.append(MagicalBoundary(
                name=heading.strip(),
                perimeter=Polygon(verts),
                blocks=blocks,
                effect=meta.get("effect", ""),
                save=meta.get("save", "wisdom"),
                crossing_dc=crossing_dc,
                crossing_damage_success=crossing_damage_success,
            ))
    return boundaries


# ---------------------------------------------------------------------------
# Load from file → SceneGeometry
# ---------------------------------------------------------------------------


def load_geometry(path: Path) -> SceneGeometry:
    """Load a GEOMETRY.md file and return a SceneGeometry instance."""
    text = path.read_text(encoding="utf-8")
    data = parse_geometry_md(text)
    return SceneGeometry(
        name=data["name"],
        place_path=data["place_path"],
        z_level=data["z_level"],
        width=data["width"],
        height=data["height"],
        origin=data["origin"],
        landmarks=data["landmarks"],
        zones=data["zones"],
        zone_floor_z=data.get("zone_floor_z", {}),
        zone_ceiling_z=data.get("zone_ceiling_z", {}),
        zone_z_explicit=data.get("zone_z_explicit", set()),
        impassable=data["impassable"],
        connections=data["connections"],
        visibility_rules=data.get("visibility", {}),
        boundaries=data.get("boundaries", []),
        ambient_visibility_ft=data.get("ambient_visibility_ft"),
        zone_visibility_ft=data.get("zone_visibility_ft", {}),
    )

def load_geometry_full(path: Path) -> tuple[SceneGeometry, list[MagicalBoundary]]:
    """Load GEOMETRY.md returning geometry and its boundaries.

    (Character placement is a scene concern now — see ``scenes/<scene>.md`` and
    ``md_loader`` — so it is not returned here.)
    """
    text = path.read_text(encoding="utf-8")
    data = parse_geometry_md(text)
    geometry = SceneGeometry(
        name=data["name"],
        place_path=data["place_path"],
        z_level=data["z_level"],
        width=data["width"],
        height=data["height"],
        origin=data["origin"],
        landmarks=data["landmarks"],
        zones=data["zones"],
        zone_floor_z=data.get("zone_floor_z", {}),
        zone_ceiling_z=data.get("zone_ceiling_z", {}),
        zone_z_explicit=data.get("zone_z_explicit", set()),
        impassable=data["impassable"],
        connections=data["connections"],
    )
    return geometry, data["boundaries"]
