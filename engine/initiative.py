"""Initiative rolling and ordering — 1d20 + DEX modifier per character."""

from __future__ import annotations

import random
from dataclasses import dataclass

from models.character import Character, Creature, NPC, PlayerCharacter


def dex_modifier(character: Character) -> int:
    """Return the DEX modifier for any character type.

    PlayerCharacter, NPC, and Creature all have a ``dexterity`` field.
    Base Characters without one default to +0.
    """
    dex = getattr(character, "dexterity", 10)
    return (dex - 10) // 2


@dataclass
class InitiativeEntry:
    """One character's initiative result for a turn."""

    character_id: str
    roll: int           # raw d20 result (1-20)
    modifier: int       # DEX modifier
    total: int          # roll + modifier

    def __repr__(self) -> str:
        sign = "+" if self.modifier >= 0 else ""
        return f"{self.character_id}: {self.total} (d20={self.roll} {sign}{self.modifier})"


def roll_initiative(
    characters: list[Character],
    *,
    rng: random.Random | None = None,
) -> list[InitiativeEntry]:
    """Roll initiative for a list of characters and return sorted results.

    Rolls 1d20 + DEX modifier for each character, returns entries sorted
    highest-first.  Ties are broken by DEX modifier (higher goes first),
    then by random coin flip.

    Pass an ``rng`` instance for deterministic testing.
    """
    rng = rng or random.Random()

    entries: list[InitiativeEntry] = []
    for char in characters:
        mod = dex_modifier(char)
        roll = rng.randint(1, 20)
        entries.append(InitiativeEntry(
            character_id=char.id,
            roll=roll,
            modifier=mod,
            total=roll + mod,
        ))

    # Sort: highest total first, tie-break by modifier (higher first),
    # then random (stable sort + pre-shuffle handles this)
    rng.shuffle(entries)  # randomise before stable sort for tie-breaking
    entries.sort(key=lambda e: (e.total, e.modifier), reverse=True)

    return entries
