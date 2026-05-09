"""Parse scene-level CONTENTS.md files into Item objects.

See ``engine/CONTENTS.md`` for the file-format specification.
The exemplar / reference file is
``scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md``.

Public API:

    parse_contents_md(text)      -> dict (raw parse: items, sections, ...)
    load_contents(path)          -> dict[item_id, Item]
    load_contents_with_geometry(contents_path, geometry)
                                 -> dict[item_id, Item] with positions/zones
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.item import Interaction, Item


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a ``## heading`` up to the next ``##`` or EOF."""
    pattern = rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _split_item_blocks(items_section: str) -> list[tuple[str, str]]:
    """Split the Items section body into ``[(item_id, body_text), ...]``.

    Each block runs from a ``### <item_id>`` line to the next ``###`` (or
    ``##``, but the section extractor has already stripped subsequent ``##``).
    """
    pattern = re.compile(r"^###\s+(\S+)[^\n]*\n", re.MULTILINE)
    matches = list(pattern.finditer(items_section))
    blocks: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        item_id = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(items_section)
        body = items_section[start:end].strip()
        blocks.append((item_id, body))
    return blocks


# ---------------------------------------------------------------------------
# Item-body parsing
# ---------------------------------------------------------------------------


# Literal opener of the Interactions block. The spec mandates this exact
# string (italicized, with the "(DM ground truth):" parenthetical).
_INTERACTIONS_OPENER_RE = re.compile(
    r"^\s*\*Interactions\s*\(DM ground truth\):\*\s*$",
    re.MULTILINE,
)

# Italicized parenthetical "*(...)*" — used to find the properties line.
# Allows either a whole-line form or a trailing-of-paragraph form. Captures
# the inner text of the parenthetical (without the surrounding ``*(`` and ``)*``).
_PROPERTIES_RE = re.compile(r"\*\(\s*(.+?)\s*\)\*", re.DOTALL)

# An interaction bullet line. Captures: verb-phrase, optional condition,
# response head (rest of the line after the arrow).
#
#   - **<verb>** [(<condition>)] → <result>
#
# Both ``→`` (U+2192) and ASCII ``->`` are accepted.
_BULLET_RE = re.compile(
    r"""
    ^\s*-\s+                       # bullet marker
    \*\*(?P<verb>[^*]+?)\*\*       # **verb-phrase**
    \s*
    (?:\((?P<cond>[^)]*)\)\s*)?    # optional (condition)
    (?:→|->)                       # arrow
    \s*
    (?P<head>.*)                   # rest-of-line response
    """,
    re.VERBOSE,
)


def _split_prose_and_interactions(body: str) -> tuple[str, str]:
    """Split an item body at the Interactions opener.

    Returns ``(prose_part, interactions_part)``. ``interactions_part`` is the
    text *after* the opener line; empty string if no opener is present.
    """
    m = _INTERACTIONS_OPENER_RE.search(body)
    if not m:
        return body.strip(), ""
    prose = body[: m.start()].rstrip()
    interactions = body[m.end():].strip()
    return prose, interactions


def _parse_properties(prose: str) -> tuple[str, dict]:
    """Extract the trailing ``*(...)*`` properties parenthetical from prose.

    Returns ``(prose_without_properties, props_dict)`` where ``props_dict``
    has keys: ``pickable`` (bool|None), ``flavor_only`` (bool), ``pressable``
    (bool), ``quest_item_for`` (str|None), ``interactions_ref`` (str|None),
    ``extra_facts`` (list[str]). When no parenthetical is found, all flags
    default to None/False/[].

    Strategy: find the *last* ``*(...)*`` match in the prose. If it sits at
    the very end of the prose (modulo trailing whitespace/punctuation), strip
    it from the displayed description.
    """
    props = {
        "pickable": None,
        "flavor_only": False,
        "pressable": False,
        "quest_item_for": None,
        "interactions_ref": None,
        "extra_facts": [],
    }

    matches = list(_PROPERTIES_RE.finditer(prose))
    if not matches:
        return prose.strip(), props

    last = matches[-1]
    inner = last.group(1)

    # Only treat the parenthetical as a "properties" line if it sits at (or
    # very near) the end of the prose. This avoids mis-classifying an italic
    # aside in the middle of a paragraph.
    tail = prose[last.end():].strip()
    if tail:
        # The parenthetical is mid-prose, not the trailing properties line.
        return prose.strip(), props

    # Strip the parenthetical (and trailing whitespace) from the prose.
    new_prose = prose[: last.start()].rstrip()

    # Split the parenthetical body into facts. Semicolons are the primary
    # separator; periods followed by whitespace are also accepted so writers
    # can use natural sentence punctuation between distinct facts.
    raw_facts = re.split(r";|(?:\.\s+)", inner)
    facts = [f.strip() for f in raw_facts if f.strip()]
    for fact in facts:
        if _try_match_fact(fact, props):
            continue
        # Unrecognized fact — preserve verbatim in extra_facts.
        # Strip a trailing period for tidiness.
        cleaned = fact.rstrip(".")
        if cleaned:
            props["extra_facts"].append(cleaned)

    return new_prose, props


def _try_match_fact(fact: str, props: dict) -> bool:
    """Try to match a single fact against reserved keywords. Returns True
    if recognized; False otherwise.
    """
    f = fact.lower().rstrip(".")

    # Cross-reference: "see <id> for interactions" (id may be backtick-wrapped)
    m = re.match(r"see\s+`?([a-z][a-z0-9_]*)`?\s+for\s+interactions", f)
    if m:
        props["interactions_ref"] = m.group(1)
        return True

    # Quest item: "quest item for <character_id>"
    m = re.match(r"quest\s+item\s+for\s+([a-z][a-z0-9_ ]*?)$", f)
    if m:
        # Take the first whitespace-separated token as the character id.
        # ``Father Elden`` etc. sneak through as "father elden" — we keep the
        # raw matched group so callers can compare flexibly.
        props["quest_item_for"] = m.group(1).strip()
        return True

    # Pickable: prefix may include modifiers ("pickup-able with care").
    if re.match(r"not\s+pick(up-)?able", f):
        props["pickable"] = False
        return True
    if re.match(r"pick(up-)?able", f):
        props["pickable"] = True
        return True

    if f == "flavor":
        props["flavor_only"] = True
        return True

    if f == "pressable":
        props["pressable"] = True
        return True

    return False


def _parse_interactions(text: str) -> list[Interaction]:
    """Parse the body of the Interactions block into a list of Interaction.

    Continuation lines (indented, no leading bullet marker) are appended to
    the most-recent bullet's response.
    """
    if not text.strip():
        return []

    interactions: list[Interaction] = []
    current_lines: list[str] = []
    current: Optional[Interaction] = None

    def _finalize() -> None:
        if current is None:
            return
        body = "\n".join(current_lines).strip()
        # Collapse internal runs of whitespace inside each line, but preserve
        # paragraph-style line breaks. Simple normalization: join broken lines
        # with a single space.
        body = re.sub(r"\s*\n\s*", " ", body).strip()
        current.response = body
        interactions.append(current)

    for raw_line in text.splitlines():
        # New bullet?
        m = _BULLET_RE.match(raw_line)
        if m:
            _finalize()
            verb_phrase = m.group("verb").strip()
            cond = (m.group("cond") or "").strip()
            head = m.group("head").rstrip()

            # Verb phrase may list alternates with " / "
            parts = [p.strip() for p in verb_phrase.split("/") if p.strip()]

            # Conditions may be written INSIDE the bold span — e.g.
            # ``**press (when crack is closed)**``. Extract a trailing
            # parenthetical from each alt and use it as condition (the last
            # such match wins, so authors should be consistent).
            cleaned_parts: list[str] = []
            for part in parts:
                pm = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", part)
                if pm:
                    cleaned_parts.append(pm.group(1).strip())
                    if not cond:
                        cond = pm.group(2).strip()
                else:
                    cleaned_parts.append(part)
            parts = [p for p in cleaned_parts if p]

            canonical = parts[0] if parts else verb_phrase
            aliases = parts[1:]

            current = Interaction(
                verb=canonical,
                aliases=aliases,
                condition=cond,
                response="",
            )
            current_lines = [head] if head else []
            continue

        # Continuation of the current bullet, or text outside any bullet.
        if current is not None:
            stripped = raw_line.strip()
            if stripped:
                current_lines.append(stripped)
            else:
                # Blank line: keep it as a paragraph break in the buffer.
                current_lines.append("")

    _finalize()
    return interactions


# ---------------------------------------------------------------------------
# Top-level parse
# ---------------------------------------------------------------------------


def parse_contents_md(text: str) -> dict:
    """Parse a CONTENTS.md file into a structured dict.

    Returns a dict with keys:

    - ``items``: dict[item_id, Item]
    - ``creatures_section``: raw string under ``## Creatures`` ("" if absent)
    - ``zones_section``: raw string under ``## Zone Descriptions``
    - ``landmarks_section``: raw string under ``## Landmarks``
    - ``dm_notes_section``: raw string under ``## Notes for DM``
    """
    items_section = _extract_section(text, "Items")
    items: dict[str, Item] = {}

    for item_id, body in _split_item_blocks(items_section):
        prose, interactions_text = _split_prose_and_interactions(body)
        prose_clean, props = _parse_properties(prose)

        item = Item(
            id=item_id,
            description=prose_clean.strip(),
            pickable=bool(props["pickable"]) if props["pickable"] is not None else False,
            flavor_only=props["flavor_only"],
            pressable=props["pressable"],
            quest_item_for=props["quest_item_for"],
            extra_facts=list(props["extra_facts"]),
            interactions_ref=props["interactions_ref"],
        )

        for inter in _parse_interactions(interactions_text):
            item.interactions.append(inter)

        items[item_id] = item

    # Resolve cross-references: "see <other> for interactions" copies the
    # other item's interactions into this one. Reference target must exist
    # in the same file. Existing (explicit) interactions on this item are
    # preserved; inherited ones are appended after.
    for item in items.values():
        ref = item.interactions_ref
        if ref:
            target = items.get(ref)
            if target is None:
                raise ValueError(
                    f"Item {item.id!r} references unknown interactions source {ref!r}"
                )
            existing_keys = {(i.verb.lower(), i.condition) for i in item.interactions}
            for inter in target.interactions:
                key = (inter.verb.lower(), inter.condition)
                if key not in existing_keys:
                    item.interactions.append(inter)

    return {
        "items": items,
        "creatures_section": _extract_section(text, "Creatures"),
        "zones_section": _extract_section(text, "Zone Descriptions"),
        "landmarks_section": _extract_section(text, "Landmarks"),
        "dm_notes_section": _extract_section(text, "Notes for DM"),
    }


# ---------------------------------------------------------------------------
# File loaders
# ---------------------------------------------------------------------------


def load_contents(path: Path) -> dict[str, Item]:
    """Load a CONTENTS.md file and return ``{item_id: Item}``.

    The Item objects do NOT have ``position``, ``zone``, or ``label``
    populated — use ``load_contents_with_geometry`` for that.
    """
    text = Path(path).read_text(encoding="utf-8")
    parsed = parse_contents_md(text)
    return parsed["items"]


def _parse_geometry_items_table(geometry_text: str) -> dict[str, dict]:
    """Parse the ``## Items`` table out of a GEOMETRY.md.

    Returns ``{item_id: {"x": float, "y": float, "label": str}}``.
    Defined here (rather than in geometry_loader) so the contents loader
    can validate against geometry without touching SceneGeometry's schema.
    """
    pattern = re.compile(
        r"^##\s+Items[^\n]*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(geometry_text)
    if not match:
        return {}
    rows: dict[str, dict] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|") if c.strip() != ""]
        if not cells:
            continue
        # Skip header and separator rows.
        if cells[0].lower() == "id":
            continue
        if all(re.match(r"^-+$", c) for c in cells):
            continue
        if len(cells) < 3:
            continue
        try:
            x = float(cells[1])
            y = float(cells[2])
        except ValueError:
            continue
        label = cells[3] if len(cells) >= 4 else ""
        rows[cells[0]] = {"x": x, "y": y, "label": label}
    return rows


def load_contents_with_geometry(
    contents_path: Path,
    geometry_path: Path,
    *,
    scene_geometry=None,
) -> dict[str, Item]:
    """Load a CONTENTS.md file and merge in spatial info from a GEOMETRY.md.

    Parses both files, validates that the item id sets match exactly, and
    returns ``{item_id: Item}`` with ``position``, ``label``, and (when
    ``scene_geometry`` is provided) ``zone`` populated.

    Args:
        contents_path: Path to a CONTENTS.md file.
        geometry_path: Path to the sibling GEOMETRY.md file.
        scene_geometry: Optional ``SceneGeometry`` for zone resolution; when
            provided, ``item.zone`` is set via ``scene_geometry.zone_at``.
    """
    from models.space_time import Position  # local import to avoid cycle

    items = load_contents(Path(contents_path))
    geometry_text = Path(geometry_path).read_text(encoding="utf-8")
    geom_items = _parse_geometry_items_table(geometry_text)

    contents_only = set(items) - set(geom_items)
    geometry_only = set(geom_items) - set(items)
    if contents_only:
        raise ValueError(
            f"Items in CONTENTS.md but not in GEOMETRY.md: {sorted(contents_only)}"
        )
    if geometry_only:
        raise ValueError(
            f"Items in GEOMETRY.md but not in CONTENTS.md: {sorted(geometry_only)}"
        )

    zone_at = getattr(scene_geometry, "zone_at", None) if scene_geometry else None

    for item_id, item in items.items():
        row = geom_items[item_id]
        position = Position(row["x"], row["y"])
        item.position = position
        item.label = row["label"]
        if callable(zone_at):
            item.zone = zone_at(position)

    return items
