"""Load and parse character data from scenario markdown files."""

from __future__ import annotations

import re
from pathlib import Path

from models.character import Character, Creature, PlayerCharacter, NPC
from models.currency import parse_coins
from models.spellcasting import parse_spellcasting


# ---------------------------------------------------------------------------
# Low-level parsing helpers
# ---------------------------------------------------------------------------


def _extract_field(text: str, field_name: str) -> str | None:
    """Extract value from a '- **Field Name:** Value' line."""
    pattern = rf"-\s*\*\*{re.escape(field_name)}:\*\*\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _parse_purse(text: str) -> int:
    """Starting coin in copper from an optional ``- **Purse:** 15 gp`` line
    (typically under a ``## Wealth`` section). Absent/unparseable → 0."""
    return parse_coins(_extract_field(text, "Purse")) or 0


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


def _name_from_identity_title(text: str) -> str:
    """Extract character name from '# IDENTITY.md — Name' heading when present."""
    m = re.search(r"^#\s+IDENTITY\.md\s*[—–\-]\s*(.+)", text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _normalize_name(value: str | None) -> str:
    """Normalize long-form name fields that may include extra narrative text."""
    if not value:
        return ""
    # Newer sheets sometimes append descriptive prose after the first sentence.
    primary = value.split(".", 1)[0].strip()
    return primary or value.strip()


# ---------------------------------------------------------------------------
# High-level parse functions (markdown text → dict)
# ---------------------------------------------------------------------------


def parse_player_identity(text: str) -> dict:
    """Parse structured fields from a player character's IDENTITY.md."""
    result: dict = {}

    # Static profile
    result["name"] = (
        _normalize_name(_extract_field(text, "Full Name"))
        or _normalize_name(_extract_field(text, "Name"))
        or _name_from_identity_title(text)
    )
    result["player"] = _extract_field(text, "Player") or ""
    result["race"] = _extract_field(text, "Race") or ""
    result["background"] = _extract_field(text, "Background") or ""
    result["alignment"] = _extract_field(text, "Alignment") or ""

    cls = _extract_field(text, "Class")
    result["character_class"], parsed_level = _parse_class_level(cls)
    explicit_level = _parse_int(_extract_field(text, "Level"))
    result["level"] = explicit_level or parsed_level

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
    # Structured spellcasting profile (None for legacy free-form sections).
    result["spellcasting"] = parse_spellcasting(spells_text)

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

    # Optional combat stats (present on some NPCs like Fennel)
    result["hp"] = _parse_int(_extract_field(text, "HP"))
    result["ac"] = _parse_int(_extract_field(text, "AC"))
    scores = _parse_ability_scores(text)
    for attr in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
        result[attr] = scores.get(attr[:3], 10)

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
        natural_ac=p["ac"],
        strength=p["strength"],
        dexterity=p["dexterity"],
        constitution=p["constitution"],
        intelligence=p["intelligence"],
        wisdom=p["wisdom"],
        charisma=p["charisma"],
        abilities=p["abilities"],
        spells=p["spells"],
        spellcasting=p["spellcasting"],
        equipment=p["equipment"],
        current_hp=p["current_hp"],
        open_threads=p["open_threads"],
        purse_cp=_parse_purse(identity_raw),
    )


def load_npc(directory: Path, character_type: str = "npc") -> NPC:
    """Load an NPC from a directory with IDENTITY.md + SOUL.md."""
    identity_raw = (directory / "IDENTITY.md").read_text(encoding="utf-8")
    soul_path = directory / "SOUL.md"
    soul_raw = soul_path.read_text(encoding="utf-8") if soul_path.exists() else ""

    p = parse_npc_identity(identity_raw)
    dex_mod = (int(p["dexterity"]) - 10) // 2

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
        hp=p["hp"],
        ac=p["ac"],
        natural_ac=max(10, int(p["ac"]) - dex_mod) if p["ac"] else 10,
        strength=p["strength"],
        dexterity=p["dexterity"],
        constitution=p["constitution"],
        intelligence=p["intelligence"],
        wisdom=p["wisdom"],
        charisma=p["charisma"],
        purse_cp=_parse_purse(identity_raw),
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
        purse_cp=_parse_purse(text),
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

            if entry.name == "haversteads":
                # Prefer fully structured NPC directories when present.  Keep
                # loading the legacy single-file profiles for family members
                # that have not yet been migrated.
                migrated_ids: set[str] = set()
                for family_dir in sorted(entry.iterdir()):
                    if family_dir.is_dir() and (family_dir / "IDENTITY.md").exists():
                        characters.append(load_npc(family_dir, character_type="family"))
                        migrated_ids.add(family_dir.name)
                for md_file in sorted(entry.glob("*.md")):
                    if md_file.stem not in migrated_ids:
                        characters.append(load_family_npc(md_file))

            elif (entry / "IDENTITY.md").exists():
                characters.append(load_npc(entry, character_type="npc"))

    return characters


# ---------------------------------------------------------------------------
# Creature loading (scenario/creatures/<id>/CREATURE.md)
# ---------------------------------------------------------------------------

def _parse_creature_stat(text: str, label: str) -> int:
    """Extract an ability score like ``Strength: 6 (-2)``."""
    m = re.search(rf"{re.escape(label)}:\s*(\d+)", text)
    return int(m.group(1)) if m else 0


def _parse_bullet_items(text: str, header: str) -> list[str]:
    """Extract bullet items under a line starting with *header*.

    Handles both ``•`` and ``-`` bullets.  Collects until the next blank
    line, non-bullet line, or end-of-string.
    """
    pattern = rf"^{re.escape(header)}.*\n((?:[\t •\-].*\n?)*)"
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        return []
    items: list[str] = []
    for line in m.group(1).splitlines():
        line = re.sub(r"^[\t •\-]+", "", line).strip()
        if line:
            items.append(line)
    return items


def _extract_plain_section(text: str, header: str) -> str:
    """Extract text from a line starting with *header* to the next header-like line."""
    pattern = rf"^{re.escape(header)}[^\n]*\n(.*?)(?=^[A-Z][a-z]+.*:\s*$|^[A-Z][a-z]+ |^$\n^[A-Z]|\Z)"
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_creature_md(text: str) -> dict:
    """Parse a creature stat block from a single markdown file."""
    result: dict = {}

    # Name — first non-empty line
    for line in text.splitlines():
        line = line.strip()
        if line:
            result["name"] = line
            break

    # Description — paragraph(s) between name and first stat line
    m = re.search(
        r"^.+\n(.*?)(?=^Race:|^Alignment:|^Armor Class:)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    result["physical_description"] = m.group(1).strip() if m else ""

    # Top-level key-value fields
    result["race"] = ""
    m = re.search(r"^Race:\s*(.+)", text, re.MULTILINE)
    if m:
        result["race"] = m.group(1).strip()

    result["alignment"] = ""
    m = re.search(r"^Alignment:\s*(.+)", text, re.MULTILINE)
    if m:
        result["alignment"] = m.group(1).strip()

    result["ac"] = 0
    m = re.search(r"^Armor Class:\s*(\d+)", text, re.MULTILINE)
    if m:
        result["ac"] = int(m.group(1))

    result["hp"] = 0
    m = re.search(r"^Hit Points:\s*(\d+)", text, re.MULTILINE)
    if m:
        result["hp"] = int(m.group(1))

    result["speed"] = ""
    m = re.search(r"^Speed:\s*(.+)", text, re.MULTILINE)
    if m:
        result["speed"] = m.group(1).strip()

    result["challenge"] = ""
    m = re.search(r"^Challenge:\s*(.+)", text, re.MULTILINE)
    if m:
        result["challenge"] = m.group(1).strip()

    # Ability scores
    for ability in ("Strength", "Dexterity", "Constitution",
                    "Intelligence", "Wisdom", "Charisma"):
        result[ability.lower()] = _parse_creature_stat(text, ability)

    # Bullet-list sections
    result["skills"] = _parse_bullet_items(text, "Skills:")
    result["damage_resistances"] = _parse_bullet_items(text, "Damage Resistances:")
    result["damage_vulnerabilities"] = _parse_bullet_items(text, "Damage Vulnerabilities:")
    result["condition_immunities"] = _parse_bullet_items(text, "Condition Immunities:")
    result["senses"] = _parse_bullet_items(text, "Senses:")

    # Features — collect lines between "Features" header and "Actions" header
    features_m = re.search(
        r"^Features?\s*\n(.*?)(?=^Actions?\s*$|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if features_m:
        result["features"] = [
            line.strip()
            for line in re.sub(r"^[•\-\t ]+", "", features_m.group(1), flags=re.MULTILINE).splitlines()
            if line.strip()
        ]
    else:
        result["features"] = []

    # Actions — collect lines between "Actions" header and "Tactics:" header
    actions_m = re.search(
        r"^Actions?\s*\n(.*?)(?=^Tactics:|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if actions_m:
        result["actions"] = [
            line.strip()
            for line in re.sub(r"^[•\-\t ]+", "", actions_m.group(1), flags=re.MULTILINE).splitlines()
            if line.strip()
        ]
    else:
        result["actions"] = []

    # Tactics
    tactics_m = re.search(r"^Tactics:\s*\n(.*)", text, re.MULTILINE | re.DOTALL)
    result["tactics"] = tactics_m.group(1).strip() if tactics_m else ""

    return result


def load_creature(filepath: Path) -> Creature:
    """Load a creature template from a single markdown stat-block file."""
    text = filepath.read_text(encoding="utf-8")
    p = parse_creature_md(text)
    creature_id = filepath.parent.name if filepath.name.upper() == "CREATURE.MD" else filepath.stem

    return Creature(
        id=creature_id,
        name=p.get("name", creature_id),
        race=p.get("race", ""),
        character_type="creature",
        physical_description=p.get("physical_description", ""),
        identity_raw=text,
        alignment=p.get("alignment", ""),
        hp=p.get("hp", 0),
        ac=p.get("ac", 0),
        natural_ac=p.get("ac", 0),
        speed=p.get("speed", ""),
        challenge=p.get("challenge", ""),
        strength=p.get("strength", 0),
        dexterity=p.get("dexterity", 0),
        constitution=p.get("constitution", 0),
        intelligence=p.get("intelligence", 0),
        wisdom=p.get("wisdom", 0),
        charisma=p.get("charisma", 0),
        skills=p.get("skills", []),
        damage_resistances=p.get("damage_resistances", []),
        damage_vulnerabilities=p.get("damage_vulnerabilities", []),
        condition_immunities=p.get("condition_immunities", []),
        senses=p.get("senses", []),
        features=p.get("features", []),
        actions=p.get("actions", []),
        tactics=p.get("tactics", ""),
    )


def load_all_creatures(creatures_dir: Path) -> list[Creature]:
    """Load all creature templates from scenario/creatures/<id>/CREATURE.md."""
    creatures: list[Creature] = []
    if creatures_dir.exists():
        for creature_dir in sorted(creatures_dir.iterdir()):
            if not creature_dir.is_dir():
                continue
            creature_file = creature_dir / "CREATURE.md"
            if creature_file.exists():
                creatures.append(load_creature(creature_file))
    return creatures
