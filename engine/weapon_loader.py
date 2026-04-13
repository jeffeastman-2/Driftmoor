"""Load weapon and armor tables from WEAPONS.md and ARMOR.md.

Parses the markdown tables into dict[id, Weapon] and dict[id, Armor].
The weapon library is keyed by weapon id (e.g. "longbow").
Attack bonuses are NOT stored here; they come from CONFIG.md per-character.
"""

from __future__ import annotations

import re
from pathlib import Path

from models.weapon import Weapon, Armor


def _parse_md_table(text: str) -> list[dict[str, str]]:
    """Parse a simple markdown table into a list of row dicts.

    Handles the header row, separator row, and data rows.
    Keys are lowercased header names with spaces replaced by underscores.
    """
    rows: list[dict[str, str]] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return rows

    # Extract headers
    headers = [h.strip().lower().replace(" ", "_") for h in lines[0].strip("|").split("|")]

    # Skip separator line (line 1)
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def load_weapons(weapons_md: Path) -> dict[str, Weapon]:
    """Parse WEAPONS.md and return {weapon_id: Weapon}."""
    text = weapons_md.read_text(encoding="utf-8") if weapons_md.exists() else ""
    result: dict[str, Weapon] = {}
    for row in _parse_md_table(text):
        wid = row.get("id", "").strip()
        if not wid:
            continue

        # Parse reach / ranges
        reach = int(row.get("reach", "5") or "5")
        range_normal = int(row.get("range_normal", "0") or "0")
        range_max = int(row.get("range_max", "0") or "0")

        # Parse properties: "finesse,light,ammunition:arrow"
        props_raw = row.get("properties", "")
        properties: list[str] = []
        ammunition_id = ""
        for p in props_raw.split(","):
            p = p.strip()
            if not p:
                continue
            if p.startswith("ammunition:"):
                ammunition_id = p.split(":", 1)[1].strip()
                properties.append("ammunition")
            else:
                properties.append(p)

        result[wid] = Weapon(
            id=wid,
            name=row.get("name", wid).strip(),
            damage_dice=row.get("damage", "1d4").strip(),
            damage_type=row.get("damage_type", "").strip(),
            reach=reach,
            range_normal=range_normal,
            range_max=range_max,
            properties=properties,
            ammunition_id=ammunition_id,
        )
    return result


def load_armors(armor_md: Path) -> dict[str, Armor]:
    """Parse ARMOR.md and return {armor_id: Armor}."""
    text = armor_md.read_text(encoding="utf-8") if armor_md.exists() else ""
    result: dict[str, Armor] = {}
    for row in _parse_md_table(text):
        aid = row.get("id", "").strip()
        if not aid:
            continue

        ac_base = int(row.get("ac_base", "10") or "10")
        cap_raw = row.get("ac_dex_cap", "none").strip().lower()
        ac_dex_cap: int | None = None if cap_raw in ("none", "", "null") else int(cap_raw)
        stealth_raw = row.get("stealth_disadvantage", "false").strip().lower()
        stealth_disadvantage = stealth_raw in ("true", "yes", "1")

        result[aid] = Armor(
            id=aid,
            name=row.get("name", aid).strip(),
            ac_base=ac_base,
            ac_dex_cap=ac_dex_cap,
            stealth_disadvantage=stealth_disadvantage,
        )
    return result


def parse_character_weapons(
    weapons_cfg: str,
    weapon_library: dict[str, Weapon],
) -> list[Weapon]:
    """Parse a character's ``weapons:`` CONFIG.md field into Weapon instances.

    Format: comma-separated entries, each optionally with an attack bonus suffix:
        weapons: longbow+5, shortsword+5, dagger+5

    The bonus is stripped from the library weapon and assigned per-character.
    Unknown weapon ids are silently skipped.
    """
    weapons: list[Weapon] = []
    for entry in weapons_cfg.split(","):
        entry = entry.strip()
        if not entry:
            continue
        m = re.match(r'^(\w+)([+-]\d+)?$', entry)
        if not m:
            continue
        wid = m.group(1)
        bonus = int(m.group(2)) if m.group(2) else 0
        base = weapon_library.get(wid)
        if base is None:
            continue
        # Make a copy with the per-character attack_bonus
        import dataclasses
        w = dataclasses.replace(base, attack_bonus=bonus)
        weapons.append(w)
    return weapons
