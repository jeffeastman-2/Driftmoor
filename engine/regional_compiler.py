"""Compile regional authoring layers into runtime GEOMETRY.md.

Usage: ``python -m engine.regional_compiler scenario/places``.
"""
from __future__ import annotations

import re
from pathlib import Path


def _rows(path: Path, section: str) -> list[list[str]]:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"##\s+{re.escape(section)}\b(.*?)(?=\n##\s+|\Z)", text, re.DOTALL)
    out = []
    for line in (match.group(1).splitlines() if match else []):
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if cells and cells[0].lower() not in {"id", "name"} and not set(cells[0]) <= {"-", ":"}:
            out.append(cells)
    return out


def _replace_section(text: str, heading: str, body: str) -> str:
    match = re.search(rf"##\s+{re.escape(heading)}\b.*?(?=\n##\s+|\Z)", text, re.DOTALL)
    replacement = f"## {heading}\n\n{body.rstrip()}\n"
    if match:
        return text[:match.start()] + replacement + text[match.end():]
    return text.rstrip() + "\n\n" + replacement


def compile_regional_geometry(place_dir: Path) -> Path:
    place_dir = Path(place_dir)
    geometry_path = place_dir / "GEOMETRY.md"
    text = geometry_path.read_text(encoding="utf-8")

    points = {row[0]: (float(row[1]), float(row[2])) for row in _rows(place_dir / "REGIONS.md", "Points")}
    regions = _rows(place_dir / "REGIONS.md", "Regions")
    subzones = _rows(place_dir / "SUBZONES.md", "Subzones")
    zone_rows = ["| name | render_z | auto_wall | vertices |", "|---|---|---|---|"]
    styles = ["| target | fill |", "|---|---|"]
    aliases = {"DRIFTMOOR": "DRIFTMOOR_TOWN"}
    compiled_regions = []
    for name, fill, ids in regions:
        vertices = " ".join(f"({points[pid][0]:g},{points[pid][1]:g})" for pid in ids.split())
        target = aliases.get(name, name)
        compiled_regions.append((target, vertices))
        styles.append(f"| {target} | {fill} |")
    for name, fill, vertices in subzones:
        target = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
        zone_rows.append(f"| {target} | 20 | false | {vertices} |")
        styles.append(f"| {target} | {fill} |")
    # Smaller/specific faces must precede broad faces for zone_at().
    for target, vertices in sorted(compiled_regions, key=lambda item: item[0] != "DRIFTMOOR_TOWN"):
        zone_rows.append(f"| {target} | 10 | false | {vertices} |")
    # A catch-all must remain last for zone_at().
    zone_rows.append("| EXTERIOR | 0 | false | (0,0) (126750,0) (126750,169000) (0,169000) |")
    text = _replace_section(text, "Zones", "\n".join(zone_rows))
    text = _replace_section(
        text, "Walls",
        "- **auto_wall:** false\n\nRegional face edges are map boundaries, not movement-blocking walls.",
    )

    # The root map's visible cartography is owned exclusively by the editor
    # layers. Legacy landmarks and obstacle/boundary polygons duplicated child
    # places (Fey Glade, Old Mill, etc.) and made them look like root sub-zones.
    # Connections remain untouched below: they are traversal metadata and are
    # not drawn as regional features.
    landmark_rows = [
        "| name | x | y | z | label | destination |",
        "|---|---|---|---|---|---|",
    ]
    for row in _rows(place_dir / "LANDMARKS.md", "Landmarks"):
        if len(row) >= 6 and row[5].lower() in {"true", "yes", "1"}:
            landmark_rows.append(
                f"| {row[0]} | {row[2]} | {row[3]} | 0 | {row[1]} | {row[4]} |"
            )
    text = _replace_section(text, "Landmarks", "\n".join(landmark_rows))
    text = _replace_section(
        text, "Impassable",
        "| description | vertices |\n|---|---|",
    )
    text = _replace_section(
        text, "Boundaries",
        "No regional boundaries are authored outside the editable region and sub-zone layers.",
    )
    connections = [
        "| name | x | y | destination |",
        "|---|---|---|---|",
        "| to_driftmoor | 30631 | 28518 | places/driftmoor |",
        "| to_azure_sea | 9506 | 46475 | places/azure_sea |",
        "| to_greywater_valley | 57037 | 45418 | places/greywater_river |",
        "| to_mistwood_hills | 68656 | 97175 | places/mistwood_hills |",
        "| to_obelisk_reach | 36968 | 135200 | places/obelisk_reach |",
        "| to_plains | 105625 | 21125 | places/plains_of_stonehearth |",
    ]
    text = _replace_section(text, "Connections", "\n".join(connections))

    routes = ["| name | kind | color | width | vertices |", "|---|---|---|---|---|"]
    river_names = {"Greywater": "Greywater River", "Gold": "Gold Run", "Blackwater": "Blackwater River"}
    for row in _rows(place_dir / "RIVERS.md", "Rivers"):
        routes.append(
            f"| {river_names.get(row[0], row[0])} | river | {row[1]} | {row[2]} | {row[3]} |"
        )
    for row in _rows(place_dir / "ROADS.md", "Roads"):
        routes.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |")
    text = _replace_section(text, "Routes", "\n".join(routes))
    text = _replace_section(text, "Map Styles", "\n".join(styles))
    geometry_path.write_text(text, encoding="utf-8")
    return geometry_path


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("place", nargs="?", default="scenario/places")
    args = parser.parse_args()
    print(compile_regional_geometry(Path(args.place).resolve()))


if __name__ == "__main__":
    main()
