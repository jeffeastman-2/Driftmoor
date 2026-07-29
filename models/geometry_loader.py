"""Load scene geometry from GEOMETRY.md files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.space_time import (
    Position, Polygon, SceneGeometry, MagicalBoundary,
)


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
    result["impassable"] = impassable

    # --- Connections ---
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
        blocks = [b.strip() for b in blocks_str.split(",") if b.strip()]

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
