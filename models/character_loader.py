"""Load and parse character data from scenario markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from models.character import Character, PlayerCharacter, NPC


# ---------------------------------------------------------------------------
# Low-level parsing helpers
# ---------------------------------------------------------------------------


def _extract_field(text: str, field_name: str) -> str | None:
    """Extract value from a '- **Field Name:** Value' line."""
    pattern = rf"-\s*\*\*{re.escape(field_name)}:\*\*\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a ``## heading`` up to the next ``##`` or EOF.

    Uses prefix matching so ``"Spells"`` matches ``"## Spells and Abilities"``.
    """
    pattern = rf"^##\s+{re.escape(heading)}[^\n]*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_section_flexible(text: str, *headings: str) -> str:
    """Try multiple heading variants; return the first match."""
    for heading in headings:
        result = _extract_section(text, heading)
        if result:
            return result
    return ""


def _parse_list_items(section_text: str) -> list[str]:
    """Parse ``- item`` and numbered-list lines from a section."""
    items: list[str] = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = line[2:].strip()
            # skip metadata lines like "*(Updated …)*"
            if item and not item.startswith("*("):
                items.append(item)
        elif re.match(r"^\d+\.\s", line):
            items.append(re.sub(r"^\d+\.\s*", "", line).strip())
    return items


def _parse_ability_scores(text: str) -> dict[str, int]:
    """Parse ability scores from stat lines."""
    scores: dict[str, int] = {}
    for ability in ("STR", "DEX", "CON", "INT", "WIS", "CHA"):
        match = re.search(rf"\*\*{ability}:\*\*\s*(\d+)", text)
        if match:
            scores[ability.lower()] = int(match.group(1))
    return scores


def _parse_relationships(section_text: str) -> dict[str, str]:
    """Parse ``- **Name:** Description`` pairs into a dict."""
    relationships: dict[str, str] = {}
    for line in section_text.splitlines():
        line = line.strip()
        m = re.match(r"-\s*\*\*(.+?):\*\*\s*(.+)", line)
        if m:
            relationships[m.group(1).strip()] = m.group(2).strip()
    return relationships


def _parse_int(value: str | None) -> int:
    """Extract leading integer from a string like ``'14 (leather armor)'``."""
    if not value:
        return 0
    match = re.match(r"(\d+)", value)
    return int(match.group(1)) if match else 0


def _parse_class_level(value: str | None) -> tuple[str, int]:
    """Parse ``'Rogue, Level 1'`` → ``('Rogue', 1)``."""
    if not value:
        return ("", 1)
    m = re.match(r"(.+?),\s*Level\s+(\d+)", value, re.IGNORECASE)
    if m:
        return (m.group(1).strip(), int(m.group(2)))
    return (value.strip(), 1)


# ---------------------------------------------------------------------------
# High-level parse functions (markdown text → dict)
# ---------------------------------------------------------------------------


def parse_player_identity(text: str) -> dict:
    """Parse structured fields from a player character's IDENTITY.md."""
    result: dict = {}

    # Static profile
    result["name"] = _extract_field(text, "Full Name") or ""
    result["player"] = _extract_field(text, "Player") or ""
    result["race"] = _extract_field(text, "Race") or ""
    result["background"] = _extract_field(text, "Background") or ""
    result["alignment"] = _extract_field(text, "Alignment") or ""

    cls = _extract_field(text, "Class")
    result["character_class"], result["level"] = _parse_class_level(cls)

    # Physical description
    result["physical_description"] = _extract_section(text, "Physical Description")

    # Combat stats
    result["hp"] = _parse_int(_extract_field(text, "HP"))
    result["ac"] = _parse_int(_extract_field(text, "AC"))

    scores = _parse_ability_scores(text)
    for attr in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
        result[attr] = scores.get(attr[:3], 0)

    # Abilities
    abilities_text = _extract_section_flexible(text, "Abilities and Proficiencies")
    result["abilities"] = _parse_list_items(abilities_text) if abilities_text else []

    # Spells (separate section, or combined "Spells and Abilities")
    spells_text = _extract_section_flexible(text, "Spells", "Spells and Abilities")
    raw_spells = _parse_list_items(spells_text) if spells_text else []
    result["spells"] = [s for s in raw_spells if s.lower() not in ("none", "*none*")]

    # Equipment
    equip_text = _extract_section(text, "Equipment")
    result["equipment"] = _parse_list_items(equip_text)

    # Dynamic state
    result["current_hp"] = _parse_int(_extract_field(text, "Current HP"))
    result["mood"] = _extract_field(text, "Mood") or ""
    result["disposition"] = _extract_field(text, "Disposition toward party") or ""

    threads_str = _extract_field(text, "Open threads")
    if threads_str and threads_str.lower() not in ("none", "none yet"):
        result["open_threads"] = [t.strip() for t in threads_str.split(";") if t.strip()]
    else:
        result["open_threads"] = []

    return result


def parse_npc_identity(text: str) -> dict:
    """Parse structured fields from an NPC's IDENTITY.md."""
    result: dict = {}

    # Name: prefer "Full Name" field, fall back to title line
    result["name"] = _extract_field(text, "Full Name") or ""
    if not result["name"]:
        m = re.search(r"^#\s+IDENTITY\.md\s*[—–\-]\s*(.+)", text, re.MULTILINE)
        result["name"] = m.group(1).strip() if m else ""

    result["role"] = _extract_field(text, "Role") or ""
    result["race"] = _extract_field(text, "Race") or ""
    result["location"] = _extract_field(text, "Location") or None
    result["physical_description"] = _extract_section(text, "Physical Description")

    # Key relationships
    rel_text = _extract_section(text, "Key Relationships")
    result["relationships"] = _parse_relationships(rel_text) if rel_text else {}

    # Knowledge (various heading variants)
    knowledge_text = _extract_section_flexible(
        text,
        "What He Knows",
        "What She Knows",
        "What They Know",
    )
    result["knowledge"] = _parse_list_items(knowledge_text) if knowledge_text else []

    # Adventure hooks + wants/needs from the party
    hooks_text = _extract_section_flexible(
        text,
        "Adventure Hooks He Can Offer",
        "Adventure Hooks She Can Offer",
        "Adventure Hooks",
    )
    wants_text = _extract_section_flexible(
        text,
        "What He Wants From the Party",
        "What She Needs From the Party",
        "What He Needs From the Party",
        "What She Wants From the Party",
        "What They Need From the Party",
    )
    result["hooks"] = (
        (_parse_list_items(hooks_text) if hooks_text else [])
        + (_parse_list_items(wants_text) if wants_text else [])
    )

    # Dynamic state
    result["mood"] = _extract_field(text, "Current mood") or _extract_field(text, "Mood") or ""
    result["disposition"] = _extract_field(text, "Disposition toward party") or ""

    concerns_str = (
        _extract_field(text, "Active concerns")
        or _extract_field(text, "Active schemes")
        or ""
    )
    if concerns_str and concerns_str.lower() not in ("none", "none established"):
        result["active_concerns"] = [c.strip() for c in re.split(r"[,;]", concerns_str) if c.strip()]
    else:
        result["active_concerns"] = []

    return result


def parse_family_md(text: str) -> dict:
    """Parse a single-file family member markdown (e.g. haversteads/davin.md)."""
    result: dict = {}

    # Name from title: "# Davin Haverstead — Son, age 18"
    m = re.search(r"^#\s+(.+?)\s*[—–]\s*(.+)$", text, re.MULTILINE)
    if m:
        result["name"] = m.group(1).strip()
        result["role"] = m.group(2).strip()
    else:
        m2 = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        result["name"] = m2.group(1).strip() if m2 else ""
        result["role"] = ""

    # Role section overrides the title-derived role if present
    role_text = _extract_section(text, "Role")
    if role_text:
        result["role"] = role_text.splitlines()[0].strip()

    result["physical_description"] = _extract_section(text, "Physical Description")
    result["race"] = ""  # not specified in family .md files

    # Knowledge
    knowledge_text = _extract_section_flexible(
        text, "What He Knows", "What She Knows", "What They Know",
    )
    result["knowledge"] = _parse_list_items(knowledge_text) if knowledge_text else []

    # Hooks
    hooks_text = _extract_section(text, "Adventure Hooks")
    result["hooks"] = _parse_list_items(hooks_text) if hooks_text else []

    return result


# ---------------------------------------------------------------------------
# Loading functions (directory / file → model objects)
# ---------------------------------------------------------------------------


def load_player_character(directory: Path) -> PlayerCharacter:
    """Load a PlayerCharacter from a directory with IDENTITY.md + SOUL.md."""
    identity_raw = (directory / "IDENTITY.md").read_text(encoding="utf-8")
    soul_path = directory / "SOUL.md"
    soul_raw = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""

    p = parse_player_identity(identity_raw)

    return PlayerCharacter(
        id=directory.name,
        name=p["name"],
        race=p["race"],
        character_type="player",
        physical_description=p["physical_description"],
        identity_raw=identity_raw,
        soul_raw=soul_raw,
        mood=p["mood"],
        disposition=p["disposition"],
        player=p["player"],
        character_class=p["character_class"],
        level=p["level"],
        background=p["background"],
        alignment=p["alignment"],
        hp=p["hp"],
        ac=p["ac"],
        strength=p["strength"],
        dexterity=p["dexterity"],
        constitution=p["constitution"],
        intelligence=p["intelligence"],
        wisdom=p["wisdom"],
        charisma=p["charisma"],
        abilities=p["abilities"],
        spells=p["spells"],
        equipment=p["equipment"],
        current_hp=p["current_hp"],
        open_threads=p["open_threads"],
    )


def load_npc(directory: Path, character_type: str = "npc") -> NPC:
    """Load an NPC from a directory with IDENTITY.md + SOUL.md."""
    identity_raw = (directory / "IDENTITY.md").read_text(encoding="utf-8")
    soul_path = directory / "SOUL.md"
    soul_raw = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""

    p = parse_npc_identity(identity_raw)

    return NPC(
        id=directory.name,
        name=p["name"],
        race=p["race"],
        character_type=character_type,
        physical_description=p["physical_description"],
        home_location=p["location"] or "",
        identity_raw=identity_raw,
        soul_raw=soul_raw,
        mood=p["mood"],
        disposition=p["disposition"],
        role=p["role"],
        relationships=p["relationships"],
        knowledge=p["knowledge"],
        hooks=p["hooks"],
        active_concerns=p["active_concerns"],
    )


def load_family_npc(filepath: Path) -> NPC:
    """Load an NPC from a single markdown file (e.g. haversteads/davin.md)."""
    text = filepath.read_text(encoding="utf-8")
    p = parse_family_md(text)

    return NPC(
        id=filepath.stem,
        name=p["name"],
        race=p["race"],
        character_type="family",
        physical_description=p["physical_description"],
        identity_raw=text,
        soul_raw="",
        role=p["role"],
        knowledge=p["knowledge"],
        hooks=p["hooks"],
    )


def load_all_characters(people_dir: Path) -> list[Character]:
    """Load all characters from the scenario/people directory tree."""
    characters: list[Character] = []

    # Players
    players_dir = people_dir / "players"
    if players_dir.exists():
        for d in sorted(players_dir.iterdir()):
            if d.is_dir() and (d / "IDENTITY.md").exists():
                characters.append(load_player_character(d))

    # NPCs
    npcs_dir = people_dir / "npcs"
    if npcs_dir.exists():
        for entry in sorted(npcs_dir.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue

            if entry.name == "background":
                for bg_dir in sorted(entry.iterdir()):
                    if bg_dir.is_dir() and (bg_dir / "IDENTITY.md").exists():
                        characters.append(load_npc(bg_dir, character_type="background"))

            elif entry.name == "haversteads":
                for md_file in sorted(entry.glob("*.md")):
                    characters.append(load_family_npc(md_file))

            elif (entry / "IDENTITY.md").exists():
                characters.append(load_npc(entry, character_type="npc"))

    return characters
