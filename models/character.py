"""Character models for the Driftmoor RPG engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.spellcasting import SpellcastingProfile


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
    faction: str = "neutral"  # "party", "hostile", "neutral"
    # Item ids currently carried by this character. Kept in sync with each
    # held ``Item.holder`` (see engine.session transfer helpers).
    inventory: list[str] = field(default_factory=list)


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
    speed: str = "30 ft"
    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0
    # Lists
    abilities: list[str] = field(default_factory=list)
    spells: list[str] = field(default_factory=list)
    spellcasting: SpellcastingProfile | None = None
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
    # Optional combat stats — default 10 gives +0 modifier
    hp: int = 0
    current_hp: int = 0
    ac: int = 0
    speed: str = "30 ft"
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def modifier(self, ability: str) -> int:
        """Compute the D&D 5e ability modifier: floor((score - 10) / 2)."""
        return (getattr(self, ability) - 10) // 2


@dataclass
class Creature(Character):
    """A creature / monster with a D&D 5e stat block."""

    alignment: str = ""
    hp: int = 0
    current_hp: int = 0  # tracks damage; initialised to hp at scene start
    ac: int = 0
    speed: str = ""
    challenge: str = ""
    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0

    def modifier(self, ability: str) -> int:
        """Compute the D&D 5e ability modifier: floor((score - 10) / 2)."""
        return (getattr(self, ability) - 10) // 2

    skills: list[str] = field(default_factory=list)
    damage_resistances: list[str] = field(default_factory=list)
    damage_vulnerabilities: list[str] = field(default_factory=list)
    condition_immunities: list[str] = field(default_factory=list)
    senses: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    tactics: str = ""
