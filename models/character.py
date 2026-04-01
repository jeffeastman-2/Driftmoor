"""Character models for the Driftmoor RPG engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Character:
    """Base character with fields common to all character types."""

    id: str
    name: str
    race: str
    character_type: str  # "player", "npc", "family", "background"
    physical_description: str = ""
    location: str | None = None
    identity_raw: str = ""
    soul_raw: str = ""
    mood: str = ""
    disposition: str = ""


@dataclass
class PlayerCharacter(Character):
    """A player character with full D&D 5e stat block."""

    player: str = ""
    character_class: str = ""
    level: int = 1
    background: str = ""
    alignment: str = ""
    # Combat stats
    hp: int = 0
    ac: int = 0
    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0
    # Lists
    abilities: list[str] = field(default_factory=list)
    spells: list[str] = field(default_factory=list)
    equipment: list[str] = field(default_factory=list)
    # Dynamic state
    current_hp: int = 0

    def modifier(self, ability: str) -> int:
        """Compute the D&D 5e ability modifier: floor((score - 10) / 2)."""
        return (getattr(self, ability) - 10) // 2
    conditions: list[str] = field(default_factory=list)
    spell_slots_used: list[str] = field(default_factory=list)
    resources_expended: list[str] = field(default_factory=list)
    open_threads: list[str] = field(default_factory=list)


@dataclass
class NPC(Character):
    """A non-player character."""

    role: str = ""
    home_location: str = ""
    relationships: dict[str, str] = field(default_factory=dict)
    knowledge: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    active_concerns: list[str] = field(default_factory=list)
