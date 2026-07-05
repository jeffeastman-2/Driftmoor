"""Parse scene-level CONTENTS.md or zone files into Item objects.

See ``specs/CONTENTS.md`` for the file-format specification.
The exemplar / reference file is
``scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md``.

Public API:

    parse_contents_md(text)      -> dict (raw parse: items, sections, ...)
    load_contents(path)          -> dict[item_id, Item]
    load_contents_with_geometry(contents_path, geometry)
                                 -> dict[item_id, Item] with positions/zones
    load_zone_contents_with_geometry(zones_dir, geometry)
                                 -> dict[item_id, Item] with positions/zones
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from models.item import SIZE_KEYWORDS_FT, Interaction, Item
from models.puzzle import PuzzleEffect, PuzzleSpec


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

# Optional ``*Size:* <keyword|N ft>`` line declaring the item's largest
# physical dimension. Drives the apparent-size perception model.
_SIZE_LINE_RE = re.compile(
    r"^\s*\*Size:\*\s*(.+?)\s*$",
    re.MULTILINE,
)

# Optional ``*Weapon:* <library_id>+<enhancement>`` line marking a pickable
# item as a usable weapon (e.g. ``*Weapon:* mace+1``). md_loader resolves it
# against the weapon library on load.
_WEAPON_LINE_RE = re.compile(
    r"^\s*\*Weapon:\*\s*([A-Za-z0-9_]+(?:[+-]\d+)?)\s*$",
    re.MULTILINE,
)

# Opener of the optional apparent-size appearance block.
_APPEARANCE_OPENER_RE = re.compile(
    r"^\s*\*Appearance by distance:\*\s*$",
    re.MULTILINE,
)


def _extract_weapon_spec(body: str) -> tuple[str, Optional[str]]:
    """Pull an optional ``*Weapon:* <spec>`` line out of an item body.

    Returns ``(body_without_line, spec)``; ``spec`` is None when absent.
    """
    m = _WEAPON_LINE_RE.search(body)
    if not m:
        return body, None
    spec = m.group(1).strip()
    new_body = body[: m.start()] + body[m.end():]
    return new_body, spec

# An appearance bullet: ``- **<band>** → <description>`` where band is one of
# near / intermediate / far / distant. The arrow may be ``→`` or ``->``.
_APPEARANCE_BULLET_RE = re.compile(
    r"^\s*-\s*\*\*\s*(near|intermediate|far|distant)\s*\*\*\s*(?:→|->)\s*(.+?)\s*$",
    re.MULTILINE | re.IGNORECASE,
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


def _extract_size(body: str) -> tuple[str, float]:
    """Pull an optional ``*Size:* <keyword|N ft>`` line out of an item body.

    Returns ``(body_without_line, size_ft)``. ``size_ft`` is ``0.0`` when no
    size line is present (the engine then treats the item as a default medium
    object). Accepts D&D size keywords (tiny/small/medium/large/huge/
    gargantuan) or an explicit measurement like ``6 ft``.
    """
    m = _SIZE_LINE_RE.search(body)
    if not m:
        return body, 0.0
    raw = m.group(1).strip().lower()
    size_ft = 0.0
    num = re.match(r"(\d+(?:\.\d+)?)\s*(?:ft|feet|')?", raw)
    if num:
        size_ft = float(num.group(1))
    else:
        for keyword, value in SIZE_KEYWORDS_FT.items():
            if keyword in raw:
                size_ft = value
                break
    new_body = body[: m.start()] + body[m.end():]
    return new_body, size_ft


def _extract_appearance_bands(body: str) -> tuple[str, dict[str, str]]:
    """Pull the optional ``*Appearance by distance:*`` block out of an item body.

    Returns ``(body_without_block, bands)`` where ``bands`` maps each named
    band (``near`` / ``intermediate`` / ``far`` / ``distant``) to its authored
    description. The block — opener plus its bullets — is removed from the
    returned body. Empty dict when no block is present.
    """
    m = _APPEARANCE_OPENER_RE.search(body)
    if not m:
        return body, {}
    # The block ends at the Interactions opener if present, else end of body.
    inter = _INTERACTIONS_OPENER_RE.search(body, m.end())
    block_end = inter.start() if inter else len(body)
    block = body[m.end():block_end]
    bands: dict[str, str] = {}
    for bm in _APPEARANCE_BULLET_RE.finditer(block):
        bands[bm.group(1).strip().lower()] = bm.group(2).strip()
    # Remove only the opener + its bullets, preserving any later content.
    new_body = body[: m.start()] + body[block_end:]
    return new_body, bands


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
# Puzzle parsing
# ---------------------------------------------------------------------------


# Matches the ``*Type: <kind>*`` line in a puzzle block.
_PUZZLE_TYPE_RE = re.compile(r"\*Type:\s*([A-Za-z_]+)\s*\*", re.IGNORECASE)


def _spec_from_interactions(
    puzzle_id: str,
    kind: str,
    interactions: list[Interaction],
) -> PuzzleSpec:
    """Map parsed bullet interactions into a :class:`PuzzleSpec`.

    Recognised bullet verbs (case-insensitive):
      - ``solution``  → comma/space separated ordered item ids
      - ``step``      → response for one correct, non-final press (repeatable)
      - ``solve``     → final-press response; ``(condition)`` names the effect
      - ``reset``     → out-of-order press response
      - ``reverse``   → press-while-solved response; ``(condition)`` is effect
      - ``broadcast`` → world-event text; ``(condition)`` names the effect it
                        attaches to (matched against solve/reverse effects)
      - ``prompt``    → focused-exchange follow-up question
    """
    spec = PuzzleSpec(id=puzzle_id, kind=kind or "sequence")
    broadcasts: list[tuple[str, str]] = []  # (effect_type, text)

    for inter in interactions:
        verb = inter.verb.strip().lower()
        cond = (inter.condition or "").strip()
        resp = (inter.response or "").strip()

        if verb == "solution":
            spec.solution = [
                tok for tok in re.split(r"[,\s]+", resp) if tok
            ]
        elif verb == "step":
            spec.step_responses.append(resp)
        elif verb == "solve":
            spec.solve_response = resp
            if cond:
                spec.solve_effects.append(PuzzleEffect(type=cond))
        elif verb == "reset":
            spec.reset_response = resp
        elif verb == "reverse":
            spec.reverse_response = resp
            if cond:
                spec.reverse_effects.append(PuzzleEffect(type=cond))
        elif verb == "broadcast":
            if cond:
                broadcasts.append((cond, resp))
        elif verb == "prompt":
            if resp:
                spec.prompt = resp

    # Attach broadcast text to the matching effect by type.
    for effect_type, text in broadcasts:
        for effect in (*spec.solve_effects, *spec.reverse_effects):
            if effect.type == effect_type:
                effect.broadcast = text
                break

    return spec


def parse_puzzles(text: str) -> dict[str, PuzzleSpec]:
    """Parse the optional ``## Puzzles`` section into ``{id: PuzzleSpec}``.

    Returns an empty dict when the section is absent. Each ``### <puzzle_id>``
    block declares a ``*Type: <kind>*`` line and a set of bullets parsed by
    the same machinery as item interactions.
    """
    section = _extract_section(text, "Puzzles")
    if not section:
        return {}

    specs: dict[str, PuzzleSpec] = {}
    for puzzle_id, body in _split_item_blocks(section):
        kind = "sequence"
        m = _PUZZLE_TYPE_RE.search(body)
        if m:
            kind = m.group(1).lower()
        interactions = _parse_interactions(body)
        specs[puzzle_id] = _spec_from_interactions(puzzle_id, kind, interactions)
    return specs


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
        body, size_ft = _extract_size(body)
        body, weapon_spec = _extract_weapon_spec(body)
        body, appearance_bands = _extract_appearance_bands(body)
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
            size_ft=size_ft,
            weapon_spec=weapon_spec,
            appearance_bands=appearance_bands,
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
        "puzzles": parse_puzzles(text),
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


def load_puzzles(path: Path) -> dict[str, PuzzleSpec]:
    """Load the ``## Puzzles`` section of a CONTENTS.md, if any.

    Returns ``{puzzle_id: PuzzleSpec}`` (empty when the file has no puzzles).
    """
    text = Path(path).read_text(encoding="utf-8")
    return parse_puzzles(text)


def _parse_geometry_items_table(geometry_text: str) -> dict[str, dict]:
    """Parse the ``## Items`` table out of a GEOMETRY.md.

    Returns ``{item_id: {"x": float, "y": float, "z": float, "label": str}}``.
    Header-driven so columns are read by NAME (id/x/y/z/label) — the optional
    ``z`` column (height above the zone floor, blank = 0.0) can be present or
    absent and in any order. Empty cells are preserved positionally so a blank
    z doesn't shift the label. Defined here (rather than in geometry_loader) so
    the contents loader can validate against geometry without touching
    SceneGeometry's schema.
    """
    pattern = re.compile(
        r"^##\s+Items[^\n]*\n(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(geometry_text)
    if not match:
        return {}
    header: Optional[dict] = None
    rows: dict[str, dict] = {}
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        # Keep INTERNAL blank cells (drop only the outer empties from the
        # leading/trailing pipe) so a blank z column stays positional.
        cells = [c.strip() for c in line.split("|")][1:-1]
        if not cells:
            continue
        # Separator row (---). Ignore blanks when checking.
        if all(re.match(r"^-+$", c) for c in cells if c):
            continue
        low = [c.lower() for c in cells]
        if "id" in low and "x" in low and "y" in low:  # header row
            header = {name: i for i, name in enumerate(low)}
            continue
        if header is None:
            continue

        def _cell(name: str, default: str = "") -> str:
            i = header.get(name)
            return cells[i] if i is not None and i < len(cells) else default

        try:
            x = float(_cell("x"))
            y = float(_cell("y"))
        except ValueError:
            continue
        z_raw = _cell("z")
        try:
            z = float(z_raw) if z_raw else 0.0
        except ValueError:
            z = 0.0
        item_id = _cell("id")
        if item_id:
            rows[item_id] = {"x": x, "y": y, "z": z, "label": _cell("label")}
    return rows


def _parse_bool(value: str, *, default: bool = False) -> bool:
    """Parse common boolean strings used in markdown fields."""
    v = (value or "").strip().lower()
    if v in {"true", "yes", "y", "1"}:
        return True
    if v in {"false", "no", "n", "0", "", "n/a", "na", "-"}:
        return False
    return default


def _size_to_feet(size_value: str) -> float:
    """Convert zone-schema ``size`` field to feet.

    Accepts D&D keywords (tiny/small/medium/...) or explicit numeric forms
    like ``2 ft``. Returns 0.0 when unspecified.
    """
    raw = (size_value or "").strip().lower()
    if not raw or raw in {"n/a", "na", "-"}:
        return 0.0
    m = re.match(r"(\d+(?:\.\d+)?)\s*(?:ft|feet|')?", raw)
    if m:
        return float(m.group(1))
    return SIZE_KEYWORDS_FT.get(raw, 0.0)


def _parse_zone_item_body(body: str) -> Item:
    """Parse one zone-file item body (schema bullets) into an :class:`Item`."""
    fields: dict[str, str] = {}
    appearance: dict[str, str] = {}
    interactions: list[Interaction] = []

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\n")
        top = re.match(r"^\s*-\s*([^:]+):\s*(.*)$", line)
        if not top:
            i += 1
            continue

        key = top.group(1).strip().lower()
        value = top.group(2).strip()

        if key == "appearance by distance":
            i += 1
            while i < len(lines):
                sub = re.match(r"^\s{2,}-\s*([^:]+):\s*(.*)$", lines[i])
                if not sub:
                    break
                band = sub.group(1).strip().lower()
                desc = sub.group(2).strip()
                if band in {"near", "intermediate", "far", "distant"} and desc:
                    appearance[band] = desc
                i += 1
            continue

        if key == "interactions":
            i += 1
            while i < len(lines):
                sub = re.match(r"^\s{2,}-\s*([^:]+):\s*(.*)$", lines[i])
                if not sub:
                    break
                verb = sub.group(1).strip()
                resp = sub.group(2).strip()
                if verb and resp:
                    interactions.append(
                        Interaction(verb=verb, aliases=[], condition="", response=resp)
                    )
                i += 1
            continue

        fields[key] = value
        i += 1

    # Preserve non-core affordances as free facts for future grounding policy.
    extra_facts: list[str] = []
    for name in ("weight", "wearable"):
        val = fields.get(name, "").strip()
        if val and val.lower() not in {"n/a", "na", "-", "false", "none"}:
            extra_facts.append(f"{name}: {val}")

    return Item(
        id="",
        description=fields.get("description", "").strip(),
        pickable=_parse_bool(fields.get("pickable", "false")),
        flavor_only=_parse_bool(fields.get("flavor_only", "false")),
        # Pressable is a first-class affordance used by resolver pathways.
        pressable=any((inter.verb or "").strip().lower() == "press" for inter in interactions),
        extra_facts=extra_facts,
        size_ft=_size_to_feet(fields.get("size", "")),
        appearance_bands=appearance,
        interactions=interactions,
    )


def parse_zone_md(text: str) -> dict[str, Item]:
    """Parse one zone markdown file and return ``{item_id: Item}``.

    Zone files may legitimately have no item blocks in their ``## Items``
    section; this returns an empty dict in that case.
    """
    items_section = _extract_section(text, "Items")
    if not items_section:
        return {}

    out: dict[str, Item] = {}
    for item_id, body in _split_item_blocks(items_section):
        item = _parse_zone_item_body(body)
        item.id = item_id
        out[item_id] = item
    return out


def load_zone_contents_with_geometry(
    zones_dir: Path,
    geometry_path: Path,
    *,
    scene_geometry=None,
) -> dict[str, Item]:
    """Load all ``zones/*.md`` item blocks and merge geometry metadata.

    Validates id parity with GEOMETRY.md's ``## Items`` table exactly like the
    legacy CONTENTS loader path.
    """
    from models.space_time import Position  # local import to avoid cycle

    zones_path = Path(zones_dir)
    zone_files = sorted(p for p in zones_path.glob("*.md") if p.is_file())
    if not zone_files:
        raise ValueError(f"No zone markdown files found under: {zones_path}")

    items: dict[str, Item] = {}
    for zone_file in zone_files:
        parsed = parse_zone_md(zone_file.read_text(encoding="utf-8"))
        for item_id, item in parsed.items():
            if item_id in items:
                raise ValueError(
                    f"Duplicate item id {item_id!r} across zone files "
                    f"(latest: {zone_file.name})"
                )
            items[item_id] = item

    geometry_text = Path(geometry_path).read_text(encoding="utf-8")
    geom_items = _parse_geometry_items_table(geometry_text)

    zones_only = set(items) - set(geom_items)
    geometry_only = set(geom_items) - set(items)
    if zones_only:
        raise ValueError(
            f"Items in zones/*.md but not in GEOMETRY.md: {sorted(zones_only)}"
        )
    if geometry_only:
        raise ValueError(
            f"Items in GEOMETRY.md but not in zones/*.md: {sorted(geometry_only)}"
        )

    zone_at = getattr(scene_geometry, "zone_at", None) if scene_geometry else None
    for item_id, item in items.items():
        row = geom_items[item_id]
        position = Position(row["x"], row["y"], row.get("z", 0.0))
        item.position = position
        item.label = row["label"]
        if callable(zone_at):
            item.zone = zone_at(position)

    return items


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
        # z = height above the zone floor (default 0.0 on the floor).
        position = Position(row["x"], row["y"], row.get("z", 0.0))
        item.position = position
        item.label = row["label"]
        if callable(zone_at):
            item.zone = zone_at(position)

    return items
