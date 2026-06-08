"""Spellcasting profile parsing (specs/SPELLCASTING.md Migration Step 1).

Telemetry-only: parses the structured ``## Spells`` (or
``## Spells and Abilities``) section of a character's ``IDENTITY.md`` into a
``SpellcastingProfile``. No slot enforcement, concentration tracking, or
resolver hooks yet — those land in later migration steps. The parser is
forgiving: legacy free-form spell lists (e.g. Aeliana the Ranger) yield
``None`` and are not an error.

Companion validator ``validate_spellcasting`` returns a list of human-readable
warning strings comparing the parsed profile against RAW expectations at the
given class/level. Callers may log these for telemetry; they are advisory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Spell:
    """One parsed spell entry. Free-form ``raw`` text is preserved for the LLM."""

    name: str
    level: int = 0  # 0 = cantrip
    action: str = ""  # "1 action" | "1 bonus action" | "1 reaction"
    concentration: bool = False
    save: str = ""  # e.g. "DEX save DC 13"
    is_domain: bool = False  # subclass always-prepared (Cleric domain etc.)
    ritual: bool = False  # reserved; not yet parsed
    raw: str = ""


@dataclass
class SpellcastingProfile:
    """Parsed spellcasting block. Resource counters start at zero."""

    ability: str = ""  # "WIS" | "INT" | "CHA"
    save_dc: int = 0
    attack_bonus: int = 0
    cantrips: list[Spell] = field(default_factory=list)
    prepared: list[Spell] = field(default_factory=list)
    known: list[Spell] = field(default_factory=list)
    spell_slots_max: dict[int, int] = field(default_factory=dict)
    spell_slots_used: dict[int, int] = field(default_factory=dict)
    ritual_caster: bool = False  # reserved; not yet parsed


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


_HEADER_RE = re.compile(
    r"\*\*Spellcasting ability:\*\*\s*(\w+).*?"
    r"\*\*Spell save DC:\*\*\s*(\d+).*?"
    r"\*\*Spell attack:\*\*\s*\+?(-?\d+)",
    re.IGNORECASE | re.DOTALL,
)
_SLOT_RE = re.compile(
    r"\*\*(\d+)(?:st|nd|rd|th)-level spell slots?:\*\*\s*(\d+)",
    re.IGNORECASE,
)

_CANTRIP_HEADER_RE = re.compile(r"\*\*Cantrips? known[^*]*:\*\*", re.IGNORECASE)
_PREPARED_HEADER_RE = re.compile(r"\*\*Prepared spells?[^*]*:\*\*", re.IGNORECASE)
_KNOWN_HEADER_RE = re.compile(r"\*\*Spells? known[^*]*:\*\*", re.IGNORECASE)

_SAVE_RE = re.compile(
    r"\b(?:STR|DEX|CON|INT|WIS|CHA)\s+save\s+DC\s+\d+", re.IGNORECASE
)
_ACTION_RE = re.compile(
    r"\b1\s+(?:bonus\s+action|reaction|action)\b", re.IGNORECASE
)
_DOMAIN_RE = re.compile(r"\*\([A-Za-z]+\s+domain[^)]*\)\*", re.IGNORECASE)


def parse_spellcasting(section_text: str) -> SpellcastingProfile | None:
    """Parse a ``## Spells`` section into a profile, or ``None`` if absent.

    Returns ``None`` when the section is missing the ``**Spellcasting
    ability:**`` header line (legacy free-form lists fall through unparsed).
    """
    if not section_text:
        return None
    header = _HEADER_RE.search(section_text)
    if not header:
        return None
    profile = SpellcastingProfile(
        ability=header.group(1).upper(),
        save_dc=int(header.group(2)),
        attack_bonus=int(header.group(3)),
    )
    for sm in _SLOT_RE.finditer(section_text):
        level = int(sm.group(1))
        profile.spell_slots_max[level] = int(sm.group(2))
        profile.spell_slots_used[level] = 0

    for group_header, bullets in _split_bullet_groups(section_text):
        if _CANTRIP_HEADER_RE.search(group_header):
            for b in bullets:
                profile.cantrips.append(_parse_spell_bullet(b, level=0))
        elif _PREPARED_HEADER_RE.search(group_header):
            for b in bullets:
                profile.prepared.append(_parse_spell_bullet(b, level=1))
        elif _KNOWN_HEADER_RE.search(group_header):
            for b in bullets:
                profile.known.append(_parse_spell_bullet(b, level=1))
    return profile


def _split_bullet_groups(text: str) -> list[tuple[str, list[str]]]:
    """Group ``**Header:**`` lines with the ``- bullet`` lines that follow.

    A blank line ends a group. Bullets appearing without a preceding header
    are ignored. Only ``- `` bullets are collected (not numbered lists).
    """
    groups: list[tuple[str, list[str]]] = []
    cur_header: str | None = None
    cur_bullets: list[str] = []

    def _flush() -> None:
        nonlocal cur_header, cur_bullets
        if cur_header is not None:
            groups.append((cur_header, cur_bullets))
        cur_header = None
        cur_bullets = []

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("**") and ":" in stripped:
            _flush()
            cur_header = stripped
            cur_bullets = []
        elif stripped.startswith("- ") and cur_header is not None:
            cur_bullets.append(stripped[2:].strip())
        elif not stripped:
            _flush()
    _flush()
    return groups


def _parse_spell_bullet(bullet: str, level: int) -> Spell:
    """Parse one ``- Name: ...`` or ``- Name *(domain)* — ...`` bullet."""
    # Name: text up to the first ":", " — ", " - ", or " *(" (domain tag).
    m = re.match(r"\s*(.+?)(?=\s*\*\(|\s*[—:]|\s+-\s+|$)", bullet)
    if m:
        name = m.group(1).strip()
    else:
        # Fallback: split on the first delimiter we find.
        name = re.split(r"\s+-\s+|[:—]", bullet, maxsplit=1)[0].strip()

    save_m = _SAVE_RE.search(bullet)
    action_m = _ACTION_RE.search(bullet)
    domain_m = _DOMAIN_RE.search(bullet)
    concentration = bool(re.search(r"\bconc(?:\.|entration\b)", bullet, re.IGNORECASE))

    return Spell(
        name=name,
        level=level,
        action=action_m.group(0) if action_m else "",
        concentration=concentration,
        save=save_m.group(0) if save_m else "",
        is_domain=bool(domain_m),
        raw=bullet,
    )


# ---------------------------------------------------------------------------
# Validation (telemetry-only)
# ---------------------------------------------------------------------------


# RAW level-1 cantrip counts by primary class (PHB 2014).
_CANTRIPS_AT_L1: dict[str, int] = {
    "cleric": 3,
    "wizard": 3,
    "bard": 2,
    "sorcerer": 4,
    "druid": 2,
    "warlock": 2,
}

# RAW level-1 spell slot counts (Warlock uses Pact Magic — 1 slot at L1).
_SLOTS_AT_L1: dict[str, int] = {
    "cleric": 2,
    "wizard": 2,
    "bard": 2,
    "sorcerer": 2,
    "druid": 2,
    "warlock": 1,
}

_FULL_CASTERS = set(_CANTRIPS_AT_L1)


def _normalize_class(character_class: str) -> str:
    """``'Cleric (Life Domain)'`` -> ``'cleric'``; empty -> ``''``."""
    if not character_class:
        return ""
    head = re.split(r"[\s(/,]", character_class.strip(), maxsplit=1)[0]
    return head.lower()


def validate_spellcasting(
    profile: SpellcastingProfile | None,
    character_class: str,
    level: int,
) -> list[str]:
    """Return advisory warnings about a profile vs. RAW expectations.

    An empty list means no issues detected. The check is intentionally
    narrow: cantrip count and L1 slot count for full casters at level 1.
    Half-casters and L2+ characters are not checked here yet.
    """
    if profile is None:
        return []
    cls = _normalize_class(character_class)
    if cls not in _FULL_CASTERS or level != 1:
        return []

    warnings: list[str] = []
    expected_cantrips = _CANTRIPS_AT_L1[cls]
    if len(profile.cantrips) != expected_cantrips:
        warnings.append(
            f"{character_class} L1: expected {expected_cantrips} cantrips, "
            f"got {len(profile.cantrips)}"
        )
    expected_slots = _SLOTS_AT_L1[cls]
    got_slots = profile.spell_slots_max.get(1, 0)
    if got_slots != expected_slots:
        warnings.append(
            f"{character_class} L1: expected {expected_slots} first-level "
            f"slots, got {got_slots}"
        )
    if not profile.save_dc:
        warnings.append(f"{character_class}: missing spell save DC")
    return warnings
