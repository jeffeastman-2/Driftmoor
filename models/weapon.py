"""Weapon and Armor data models.

Weapons are objectified combat items with explicit stats that the Python
combat resolver uses instead of parsing prose from identity files.
Attack bonuses are per-character (set when loading from CONFIG.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Weapon:
    """A weapon with fully resolved per-character combat stats.

    ``attack_bonus`` is set at character-load time (from CONFIG.md notation
    like ``longbow+5``), NOT stored in the weapon library.  All other fields
    come from the WEAPONS.md library.
    """
    id: str               # e.g. "longbow", "shadowbeast_claw"
    name: str             # e.g. "Longbow"
    damage_dice: str      # e.g. "1d8", "1d6", "1d4+2"
    damage_type: str      # e.g. "piercing", "slashing", "bludgeoning"
    attack_bonus: int = 0 # resolved: ability_mod + prof (if proficient)
    reach: int = 5        # melee reach in feet; also used as min range for ranged weapons
    range_normal: int = 0 # ranged normal distance in feet; 0 = melee only
    range_max: int = 0    # ranged maximum distance in feet; 0 = melee only
    properties: list[str] = field(default_factory=list)  # finesse, light, thrown, two_handed, natural, ammunition
    ammunition_id: str = ""  # item id for ammo (e.g. "arrow"); "" = no ammo needed

    @property
    def is_ranged(self) -> bool:
        return self.range_normal > 0

    @property
    def max_effective_range(self) -> float:
        """Longest distance from which this weapon can be used."""
        if self.is_ranged:
            return float(self.range_normal)
        return float(self.reach)


@dataclass
class Armor:
    """Armor with AC calculation data."""
    id: str
    name: str
    ac_base: int
    ac_dex_cap: int | None = None   # None = DEX modifier uncapped (light armor)
    stealth_disadvantage: bool = False
