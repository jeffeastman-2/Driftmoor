"""Sense-range resolution for creatures (players and NPCs alike).

Every creature has senses. Sight is limited by ambient light (resolved by the
scene geometry); special senses extend detection:

* **Darkvision** extends *sight* in darkness (but not through mist/occlusion).
* **Blindsight / Tremorsense** give non-visual detection out to a fixed range,
  independent of light.
* **Keen Hearing/Smell** (a feature, not a listed sense) grants a modest
  non-visual detection range.

Ranges are parsed from a creature's ``Senses:`` block (e.g. "Darkvision 60
ft.") and ``features`` list; players without an explicit block fall back to a
racial darkvision default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

# Canonical 5e racial darkvision (ft). Humans, halflings, dragonborn, and
# fairies have none. Drow/Duergar have superior (120 ft) darkvision.
_RACE_DARKVISION_FT: dict[str, float] = {
    "dwarf": 60.0,
    "elf": 60.0,
    "half-elf": 60.0,
    "halfelf": 60.0,
    "gnome": 60.0,
    "half-orc": 60.0,
    "halforc": 60.0,
    "orc": 60.0,
    "tiefling": 60.0,
    "goblin": 60.0,
    "hobgoblin": 60.0,
    "kobold": 60.0,
    "drow": 120.0,
    "duergar": 120.0,
}

# Detection range granted by keen hearing/smell when no explicit sense range
# is present.
_KEEN_SENSES_FT = 30.0


@dataclass(frozen=True)
class SenseProfile:
    """Resolved detection ranges for a creature."""

    darkvision_ft: float = 0.0
    blindsight_ft: float = 0.0
    tremorsense_ft: float = 0.0
    keen_senses: bool = False

    @property
    def nonvisual_range_ft(self) -> float:
        """Detection range that does not depend on sight (sound/scent/vibration)."""
        rng = max(self.blindsight_ft, self.tremorsense_ft)
        if self.keen_senses:
            rng = max(rng, _KEEN_SENSES_FT)
        return rng


def _range_for(entries: Iterable[str], keyword: str) -> float:
    """Return the largest ``<keyword> N ft`` range found in ``entries``."""
    best = 0.0
    pat = re.compile(rf"{keyword}\s+(\d+)\s*(?:ft|feet|')", re.IGNORECASE)
    for entry in entries:
        for m in pat.finditer(entry or ""):
            best = max(best, float(m.group(1)))
    return best


def _racial_darkvision(race: str) -> float:
    race_l = (race or "").lower()
    for key, rng in _RACE_DARKVISION_FT.items():
        if key in race_l:
            return rng
    return 0.0


def resolve_senses(
    race: str = "",
    senses: Optional[Iterable[str]] = None,
    features: Optional[Iterable[str]] = None,
) -> SenseProfile:
    """Resolve a creature's sense ranges from race, senses, and features.

    Explicit ``Senses:`` entries win; otherwise darkvision falls back to a
    racial default so every creature has the senses its kind would.
    """
    senses = list(senses or [])
    features = list(features or [])

    darkvision = _range_for(senses, "darkvision")
    if darkvision == 0.0:
        darkvision = _racial_darkvision(race)

    blindsight = _range_for(senses, "blindsight")
    tremorsense = _range_for(senses, "tremorsense")

    blob = " ".join(senses + features).lower()
    keen = ("keen hearing" in blob) or ("keen smell" in blob) or (
        "keen senses" in blob
    )

    return SenseProfile(
        darkvision_ft=darkvision,
        blindsight_ft=blindsight,
        tremorsense_ft=tremorsense,
        keen_senses=keen,
    )
