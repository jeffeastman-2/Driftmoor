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
            landmarks[name] = Position(float(row[1]), float(row[2]))
    result["landmarks"] = landmarks

    # --- Zones ---
    zones_section = _extract_section(text, "Zones")
    zone_rows = _parse_table_rows(zones_section)
    zones: dict[str, Polygon] = {}
    for row in zone_rows:
        if len(row) >= 2:
            name = row[0].strip()
            if name == "name":
                continue
            # Vertices are in the last column (supports 2-col or 3-col tables)
            verts = _parse_vertices(row[-1])
            zones[name] = Polygon(verts)
    result["zones"] = zones

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

    # --- Starting Positions ---
    starting_section = _extract_section(text, "Starting Positions")
    start_rows = _parse_table_rows(starting_section)
    starting: dict[str, Position] = {}
    for row in start_rows:
        if len(row) >= 3:
            name = row[0].strip()
            if name == "character":
                continue
            starting[name] = Position(float(row[1]), float(row[2]))
    result["starting_positions"] = starting

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

        if verts:
            boundaries.append(MagicalBoundary(
                name=heading.strip(),
                perimeter=Polygon(verts),
                blocks=blocks,
                effect=meta.get("effect", ""),
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
        impassable=data["impassable"],
        connections=data["connections"],
    )


def load_geometry_full(path: Path) -> tuple[
    SceneGeometry, list[MagicalBoundary], dict[str, Position]
]:
    """Load GEOMETRY.md returning geometry, boundaries, and starting positions."""
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
        impassable=data["impassable"],
        connections=data["connections"],
    )
    return geometry, data["boundaries"], data["starting_positions"]
