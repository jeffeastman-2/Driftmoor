"""Loader for Thing objects from scenario/things markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from models.thing import Thing


# ---------------------------------------------------------------------------
# Vendor mapping — section heading text → (vendor character_id, place_id)
# ---------------------------------------------------------------------------

_VENDOR_MAP: dict[str, tuple[str, str]] = {
    "salt & iron mercantile": ("jorgen", "salt_and_iron"),
    "the bitter remedy": ("lytha", "bitter_remedy"),
    "ironhoof forge": ("darrin", "ironhoof_forge"),
    "the gilded trinket": ("tavian", "gilded_trinket"),
    "dustcloak's curios": ("kelem", "dustcloaks_curios"),
    "the broken lantern": ("tess", "broken_lantern"),
    "the weary traveler": ("martha", "weary_traveler"),
    "the beacon church": ("elden", "beacon_church"),
    "the rusty razor": ("arlan", "rusty_razor"),
    # Simple businesses — mapped from sub-headings
    "the tannery": ("boren", "tannery"),
    "carpenter's workshop": ("hilda", "carpenters_workshop"),
    "the fishmonger's shack": ("kessla", "fishmongers_shack"),
    "the weaver's cottage": ("eadric", "weavers_cottage"),
    "the bakery": ("maribel", "bakery"),
    "the tailor's shop": ("vindra", "tailors_shop"),
    "the general store": ("jedrin", "general_store"),
    "the cooper's shed": ("tomas", "coopers_shed"),
    "the cobbler's shop": ("marta", "cobblers_shop"),
    "the midwife's home": ("gran_lorie", "midwifes_home"),
}


def _slugify(text: str) -> str:
    """Turn a display name into a snake_case id."""
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _lookup_vendor(heading: str) -> tuple[str, str]:
    """Match a section heading to (vendor_id, place_id)."""
    h = heading.lower().strip()
    # Strip parentheticals for matching: "The Gilded Trinket (Pawnshop)" → "the gilded trinket"
    h_base = re.sub(r"\s*\(.*?\)\s*", "", h).strip()
    for key, val in _VENDOR_MAP.items():
        if key in h_base or h_base in key:
            return val
    return ("", "")


# ---------------------------------------------------------------------------
# Parse markdown tables
# ---------------------------------------------------------------------------

def _parse_table(lines: list[str]) -> list[dict[str, str]]:
    """Parse a markdown table into list of dicts keyed by header columns."""
    if len(lines) < 3:
        return []
    # Header row
    headers = [h.strip() for h in lines[0].strip().strip("|").split("|")]
    # Skip separator row (lines[1])
    rows = []
    for line in lines[2:]:
        line = line.strip()
        if not line or not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip("|").split("|")]
        row = {}
        for i, h in enumerate(headers):
            row[h] = cells[i] if i < len(cells) else ""
        rows.append(row)
    return rows


def _find_tables(text: str) -> list[tuple[int, list[str]]]:
    """Find all markdown tables in text. Returns (start_line_idx, table_lines) pairs."""
    lines = text.split("\n")
    tables: list[tuple[int, list[str]]] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # A table starts with a | row, followed by a |---|---| separator
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|", lines[i + 1].strip()):
            table_lines = []
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                table_lines.append(lines[j])
                j += 1
            tables.append((i, table_lines))
            i = j
        else:
            i += 1
    return tables


# ---------------------------------------------------------------------------
# Mundane item parsing
# ---------------------------------------------------------------------------

def parse_mundane_items(path: Path) -> list[Thing]:
    """Parse mundane_items.md into Thing objects."""
    text = path.read_text()
    lines = text.split("\n")
    things: list[Thing] = []
    seen_ids: set[str] = set()

    current_vendor_id = ""
    current_location_id = ""

    for table_start, table_lines in _find_tables(text):
        # Walk backwards from table to find the nearest ## or ### heading
        vendor_id, location_id = _find_vendor_for_table(lines, table_start)
        if vendor_id:
            current_vendor_id = vendor_id
            current_location_id = location_id

        rows = _parse_table(table_lines)
        for row in rows:
            # Find the name column — could be "Item", "Service", "Item / Service", etc.
            name = ""
            for key in row:
                kl = key.lower()
                if kl in ("item", "service", "item / service", "service / item",
                          "deal", "option"):
                    name = row[key]
                    break
            if not name:
                continue

            # Clean name: strip markdown emphasis and links
            name = re.sub(r"\*+([^*]+)\*+", r"\1", name)
            name = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", name)
            name = name.strip()
            if not name:
                continue

            # Find price column
            price = ""
            for key in row:
                kl = key.lower()
                if kl in ("price", "cost", "price paid", "suggested donation"):
                    price = row[key]
                    break
            price = price.strip()

            # Find description column
            desc = ""
            for key in row:
                kl = key.lower()
                if kl in ("description", "effect", "notes", "effect / use",
                           "condition required", "terms", "time"):
                    desc = row[key]
                    break
            desc = desc.strip()

            # Build unique ID
            base_id = _slugify(name)
            thing_id = base_id
            if thing_id in seen_ids:
                thing_id = f"{base_id}_{_slugify(current_location_id)}" if current_location_id else f"{base_id}_2"
            if thing_id in seen_ids:
                # Last resort — append counter
                n = 2
                while f"{base_id}_{n}" in seen_ids:
                    n += 1
                thing_id = f"{base_id}_{n}"
            seen_ids.add(thing_id)

            things.append(Thing(
                id=thing_id,
                name=name,
                category="mundane",
                price=price,
                description=desc,
                vendor_id=current_vendor_id,
                location_id=current_location_id,
            ))

    return things


def _find_vendor_for_table(lines: list[str], table_start: int) -> tuple[str, str]:
    """Walk backwards from a table to find the vendor from the nearest heading."""
    for i in range(table_start - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith("## ") or line.startswith("### "):
            heading = re.sub(r"^#{2,3}\s+", "", line).strip()
            vendor_id, location_id = _lookup_vendor(heading)
            if vendor_id:
                return vendor_id, location_id
            # For "Simple Businesses" sub-headings like "### The Tannery (Boren Thatch)"
            # Strip the parenthetical name
            h_clean = re.sub(r"\s*\(.*?\)\s*", "", heading).strip()
            vendor_id, location_id = _lookup_vendor(h_clean)
            if vendor_id:
                return vendor_id, location_id
    return ("", "")


# ---------------------------------------------------------------------------
# Magical item parsing
# ---------------------------------------------------------------------------

_MAGICAL_VENDOR_MAP: dict[str, tuple[str, str]] = {
    "kelem dustcloak": ("kelem", "dustcloaks_curios"),
    "the gilded trinket": ("tavian", "gilded_trinket"),
    "elyssa moonglow": ("elyssa", "elyssa_cottage"),
}


def parse_magical_items(path: Path) -> list[Thing]:
    """Parse magical_items.md into Thing objects."""
    text = path.read_text()
    lines = text.split("\n")
    things: list[Thing] = []
    seen_ids: set[str] = set()

    current_vendor_id = ""
    current_location_id = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Track ## vendor sections
        if line.startswith("## ") and not line.startswith("## Overview") and not line.startswith("## Items to Be") and not line.startswith("## DM "):
            heading = line[3:].strip()
            for key, (vid, pid) in _MAGICAL_VENDOR_MAP.items():
                if key in heading.lower():
                    current_vendor_id = vid
                    current_location_id = pid
                    break
            i += 1
            continue

        # ### item heading — start parsing an item block
        if line.startswith("### "):
            item_name = line[4:].strip()
            # Collect the entire item block until next ### or ##
            block_lines = [lines[i]]
            j = i + 1
            while j < len(lines):
                jline = lines[j].strip()
                if jline.startswith("## ") or jline.startswith("### "):
                    break
                block_lines.append(lines[j])
                j += 1
            block_text = "\n".join(block_lines)

            thing = _parse_magical_block(
                item_name, block_text,
                current_vendor_id, current_location_id,
                seen_ids,
            )
            if thing:
                things.append(thing)
                seen_ids.add(thing.id)

            i = j
            continue

        i += 1

    return things


def _parse_magical_block(
    name: str,
    block: str,
    vendor_id: str,
    location_id: str,
    seen_ids: set[str],
) -> Thing | None:
    """Parse a single magical item block."""
    # Extract fields from **Key:** value patterns
    price = _extract_field(block, "asking price") or _extract_field(block, "listed price") or ""
    attunement = _extract_field(block, "attunement") or ""

    # Override location from block if specified
    loc_field = _extract_field(block, "session-start location") or ""
    if loc_field:
        # Try to extract a place_id from backtick references or known names
        if "elyssa" in loc_field.lower():
            location_id = "elyssa_cottage"
        elif "gilded trinket" in loc_field.lower():
            location_id = "gilded_trinket"
        elif "dustcloak" in loc_field.lower():
            location_id = "dustcloaks_curios"

    # Advertised properties
    properties = _extract_section(block, "advertised properties") or _extract_section(block, "advertised")
    # True properties (DM only)
    dm_properties = _extract_section(block, "true properties")

    base_id = _slugify(name)
    thing_id = base_id
    if thing_id in seen_ids:
        thing_id = f"{base_id}_{_slugify(location_id)}"
    if thing_id in seen_ids:
        n = 2
        while f"{base_id}_{n}" in seen_ids:
            n += 1
        thing_id = f"{base_id}_{n}"

    # Determine description from advertised or first non-field line
    desc = _extract_field(block, "advertised") or ""

    return Thing(
        id=thing_id,
        name=name,
        category="magical",
        price=price,
        description=desc,
        vendor_id=vendor_id,
        location_id=location_id,
        properties=properties,
        dm_properties=dm_properties,
        attunement=attunement,
        raw=block.strip(),
    )


def _extract_field(block: str, field_name: str) -> str:
    """Extract a **Field:** value from a block."""
    pattern = rf"\*\*{re.escape(field_name)}:\*\*\s*(.+)"
    m = re.search(pattern, block, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_section(block: str, section_name: str) -> str:
    """Extract content after a **Section (...):** line until next **bold** or end."""
    pattern = rf"\*\*{re.escape(section_name)}[^*]*\*\*:?"
    m = re.search(pattern, block, re.IGNORECASE)
    if not m:
        return ""
    start = m.end()
    # Find next **bold:** or end of block
    rest = block[start:]
    end_match = re.search(r"\n\*\*[A-Z]", rest)
    section = rest[:end_match.start()] if end_match else rest
    # Clean up: join lines, strip bullets
    lines = [line.strip().lstrip("- ") for line in section.strip().split("\n") if line.strip()]
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Obelisk shards parsing
# ---------------------------------------------------------------------------

def parse_obelisk_shards(path: Path) -> list[Thing]:
    """Parse obelisk_shards.md — extract the 'Known Shard Locations' table."""
    text = path.read_text()
    things: list[Thing] = []
    seen_ids: set[str] = set()

    # Find the locations table
    tables = _find_tables(text)
    for _, table_lines in tables:
        rows = _parse_table(table_lines)
        if not rows:
            continue
        # Check if this is the locations table (has "Location" and "Description" columns)
        headers = {k.lower() for k in rows[0].keys()}
        if "location" not in headers:
            continue

        for row in rows:
            location_ref = row.get("Location", "")
            description = row.get("Description", "")
            status = row.get("Status", "")

            # Extract place_id from backtick path like `places/driftmoor/elyssa_cottage/laboratory`
            place_match = re.search(r"`places/([^`]+)`", location_ref)
            if place_match:
                # Take the deepest non-generic directory as place_id
                parts = place_match.group(1).strip("/").split("/")
                place_id = parts[-1] if parts else ""
            else:
                place_id = _slugify(location_ref)

            # Simplify place_id to match our place model IDs
            # e.g. "laboratory" → parent is "elyssa_cottage"
            # Map known nested locations to their parent place
            place_id_map = {
                "laboratory": "elyssa_cottage",
                "shopfront": "dustcloaks_curios",
                "backroom": "dustcloaks_curios",
            }
            place_id = place_id_map.get(place_id, place_id)

            base_id = f"shard_{_slugify(place_id)}"
            thing_id = base_id
            if thing_id in seen_ids:
                n = 2
                while f"{base_id}_{n}" in seen_ids:
                    n += 1
                thing_id = f"{base_id}_{n}"
            seen_ids.add(thing_id)

            things.append(Thing(
                id=thing_id,
                name=f"Obelisk Shard ({description})" if description else "Obelisk Shard",
                category="obelisk_shard",
                location_id=place_id,
                description=description,
                properties=status,
            ))

    return things


# ---------------------------------------------------------------------------
# Shadowbeast parts parsing
# ---------------------------------------------------------------------------

def parse_shadowbeast_parts(path: Path) -> list[Thing]:
    """Parse shadowbeast_parts.md — extract the 4 harvestable part types."""
    text = path.read_text()
    lines = text.split("\n")
    things: list[Thing] = []
    seen_ids: set[str] = set()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # ### Shadowbeast Pelt, ### Shadowbeast Claws, etc.
        if line.startswith("### Shadowbeast "):
            part_name = line[4:].strip()
            # Collect block
            block_lines = [lines[i]]
            j = i + 1
            while j < len(lines):
                jline = lines[j].strip()
                if jline.startswith("### ") or jline.startswith("## "):
                    break
                block_lines.append(lines[j])
                j += 1
            block_text = "\n".join(block_lines)

            # Extract fields
            harvest_dc = _extract_field(block_text, "Harvest DC") or ""
            yield_info = _extract_field(block_text, "Yield") or ""
            condition = _extract_field(block_text, "Condition") or ""
            properties = f"Harvest DC {harvest_dc}. Yield: {yield_info}." if harvest_dc else ""

            # Build description from the Properties sub-section
            desc_section = _extract_section(block_text, "Properties")

            thing_id = _slugify(part_name)
            thing_id = f"part_{thing_id}"  # prefix to avoid cross-file dupes
            if thing_id in seen_ids:
                thing_id = f"{thing_id}_2"
            seen_ids.add(thing_id)

            things.append(Thing(
                id=thing_id,
                name=part_name,
                category="shadowbeast_part",
                description=desc_section or condition,
                properties=properties,
                raw=block_text.strip(),
            ))

            i = j
            continue
        i += 1

    return things


# ---------------------------------------------------------------------------
# Top-level loader
# ---------------------------------------------------------------------------

def load_all_things(things_dir: Path) -> list[Thing]:
    """Load all things from the scenario/things directory.

    When an item appears in both mundane and magical files (e.g. Gilded
    Trinket curios), the magical version wins since it has richer data.
    """
    magical = parse_magical_items(things_dir / "magical_items.md")
    mundane = parse_mundane_items(things_dir / "mundane_items.md")
    shards = parse_obelisk_shards(things_dir / "obelisk_shards.md")
    parts = parse_shadowbeast_parts(things_dir / "shadowbeast_parts.md")

    # Magical items take priority — remove mundane dupes by slug match
    magical_slugs = {_slugify(t.name) for t in magical}
    mundane_deduped = [t for t in mundane if _slugify(t.name) not in magical_slugs]

    all_things: list[Thing] = []
    all_things.extend(mundane_deduped)
    all_things.extend(magical)
    all_things.extend(shards)
    all_things.extend(parts)
    return all_things
