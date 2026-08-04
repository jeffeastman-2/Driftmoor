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
    character_type: str  # "player", "npc", "family"
    physical_description: str = ""
    location: str | None = None
    identity_raw: str = ""
    soul_raw: str = ""
    mood: str = ""
    disposition: str = ""
    faction: str = "neutral"  # "party", "hostile", "neutral"
    # Only explicitly attached companions follow another character's temporary
    # exploration focus. Resident NPCs must never trail a visitor around merely
    # because their faction is friendly.
    follows_party: bool = False
    # Optional authored leash around the scene's initial position. Residents
    # such as stalled horses can move naturally without wandering through the
    # whole scene. None means unrestricted movement.
    movement_radius: float | None = None
    # Item ids currently carried by this character. Kept in sync with each
    # held ``Item.holder`` (see engine.session transfer helpers).
    inventory: list[str] = field(default_factory=list)
    # Hand slots for wielding (humanoid default 2). Per-weapon hand cost plus
    # this budget is what makes "shield + two-handed sword" impossible without
    # a special case (see engine.loadout). Creatures may override.
    hands: int = 2
    # Weapons this character is trained with, for the runtime attack-bonus
    # computation. A flat set that may hold proficiency tiers (``simple`` /
    # ``martial``), weapon groups (``sword``), or specific ids (``dagger``); a
    # weapon is proficient if its id or any of its tags is in this set.
    weapon_proficiencies: set[str] = field(default_factory=set)
    # The individual's NATURAL AC (unarmored / intrinsic) — 10 + DEX for a
    # humanoid, a fixed value for a creature with natural armor (a spider's 14).
    # ``ac`` is then the EFFECTIVE AC = natural adjusted by equipment/effects
    # (worn armor sets the base; a shield/ring/potion adds).
    natural_ac: int = 0
    # Coin purse, in copper pieces (see models.currency). Money is always integer
    # copper; denominations are display-only. Every character can hold coin —
    # players spend it, shopkeepers keep a till, monsters carry loot.
    purse_cp: int = 0

    def can_afford(self, cp: int) -> bool:
        return self.purse_cp >= cp

    def debit(self, cp: int) -> bool:
        """Spend ``cp`` copper if affordable; no-op and return False otherwise
        (including a negative amount)."""
        if cp < 0 or self.purse_cp < cp:
            return False
        self.purse_cp -= cp
        return True

    def credit(self, cp: int) -> None:
        """Receive ``cp`` copper (negative amounts ignored)."""
        if cp > 0:
            self.purse_cp += cp


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
