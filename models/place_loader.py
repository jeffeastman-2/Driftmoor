"""Load and parse place data from scenario markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from models.place import Place


# ---------------------------------------------------------------------------
# Low-level parsing helpers
# ---------------------------------------------------------------------------


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a ``## heading`` up to the next ``##`` or EOF."""
    pattern = rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_list_items(section_text: str) -> list[str]:
    """Parse ``- item`` lines from a section, skipping metadata."""
    items: list[str] = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = line[2:].strip()
            if item and not item.startswith("*("):
                items.append(item)
    return items


def _parse_sub_places(section_text: str) -> list[str]:
    """Extract folder names from sub-place lines like ``- `folder_name/` — desc``."""
    children: list[str] = []
    for line in section_text.splitlines():
        m = re.match(r"-\s*`([^`]+?)/?`", line.strip())
        if m:
            children.append(m.group(1).strip("/"))
    return children


def _parse_dynamic_state(section_text: str) -> dict[str, str]:
    """Parse ``- **Key:** Value`` pairs from a Dynamic State section."""
    state: dict[str, str] = {}
    for line in section_text.splitlines():
        m = re.match(r"-\s*\*\*(.+?):\*\*\s*(.+)", line.strip())
        if m:
            state[m.group(1).strip()] = m.group(2).strip()
    return state


# ---------------------------------------------------------------------------
# High-level parse function (markdown text → dict)
# ---------------------------------------------------------------------------


def parse_place_md(text: str) -> dict:
    """Parse structured fields from a PLACE.md file."""
    result: dict = {}

    # Name from title line
    m = re.search(r"^#\s+PLACE\.md\s*[—–\-]\s*(.+)", text, re.MULTILINE)
    result["name"] = m.group(1).strip() if m else ""

    identity = _extract_section(text, "Place Identity")
    identity_fields = _parse_dynamic_state(identity) if identity else {}
    result["id"] = identity_fields.get("id", "").strip()

    # Description
    result["description"] = _extract_section(text, "Description and Atmosphere")

    # Sub-places (children)
    sub_text = _extract_section(text, "Sub-Places")
    result["children"] = _parse_sub_places(sub_text) if sub_text else []

    # Who is here
    who_text = _extract_section(text, "Who Is Normally Here")
    result["who_is_here"] = _parse_list_items(who_text) if who_text else []

    # Connections
    conn_text = _extract_section(text, "Connections")
    result["connections"] = _parse_list_items(conn_text) if conn_text else []

    # Dynamic state
    dyn_text = _extract_section(text, "Dynamic State")
    result["dynamic_state"] = _parse_dynamic_state(dyn_text) if dyn_text else {}

    return result


# ---------------------------------------------------------------------------
# Loading functions (directory → model objects)
# ---------------------------------------------------------------------------


def load_place(
    directory: Path,
    place_id: str | None = None,
    parent_id: str | None = None,
) -> Place:
    """Load a Place and its colocated narrative content.

    Per-zone markdown is the current source of truth.  ``CONTENTS.md`` remains
    a compatibility fallback for places that have not yet been migrated.
    Keeping the merged zone text in ``Place.contents_raw`` preserves the legacy
    model field without making a migrated place depend on an obsolete file.
    """
    place_path = directory / "PLACE.md"
    place_raw = place_path.read_text(encoding="utf-8")
    zones_dir = directory / "zones"
    zone_paths = sorted(p for p in zones_dir.glob("*.md") if p.is_file())
    contents_path = directory / "CONTENTS.md"
    if zone_paths:
        contents_raw = "\n\n---\n\n".join(
            path.read_text(encoding="utf-8") for path in zone_paths
        )
    else:
        contents_raw = (
            contents_path.read_text(encoding="utf-8")
            if contents_path.exists()
            else ""
        )

    p = parse_place_md(place_raw)

    # An explicit identity decouples the globally unique game-state id from the
    # directory basename. This matters for naturally recurring nested names
    # such as ``upstairs`` under more than one building.
    resolved_id = p["id"] or place_id or directory.name

    return Place(
        id=resolved_id,
        name=p["name"],
        description=p["description"],
        parent_id=parent_id,
        children=p["children"],
        connections=p["connections"],
        who_is_here=p["who_is_here"],
        place_raw=place_raw,
        contents_raw=contents_raw,
        dynamic_state=p["dynamic_state"],
    )


def load_all_places(places_dir: Path) -> list[Place]:
    """Recursively load all places from the scenario/places directory tree."""
    places: list[Place] = []
    _load_recursive(places_dir, parent_id=None, place_id="region", places=places)
    return places


def _load_recursive(
    directory: Path,
    parent_id: str | None,
    place_id: str,
    places: list[Place],
) -> None:
    """Walk the directory tree, loading each PLACE.md found."""
    place_path = directory / "PLACE.md"
    if not place_path.exists():
        return

    place = load_place(directory, place_id=place_id, parent_id=parent_id)
    places.append(place)

    # Recurse into child directories that have their own PLACE.md
    for child_dir in sorted(directory.iterdir()):
        if child_dir.is_dir() and (child_dir / "PLACE.md").exists():
            _load_recursive(
                child_dir,
                parent_id=place.id,
                place_id=child_dir.name,
                places=places,
            )
