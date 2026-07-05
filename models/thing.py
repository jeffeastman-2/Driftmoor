"""Thing — the one possessable model for the Driftmoor engine.

A Thing is anything a character can possess or the world can contain: scene
props, weapons, armor, consumables, tools, and shop goods alike. It carries an
*identity* (id / label / description / size / appearance / interactions) plus
mutable runtime state (holder, discovered_by). Later phases add *affordances*,
*effects*, and *carry-state* so that "weapon" and "armor" become affordance +
effect rather than separate classes.

A **shop good is just a Thing with a price**: the optional *market facet*
(``price`` / ``vendor_id`` / ``location_id`` / ``attunement`` / ``category``) is
empty for a rapier on a cave floor and populated for a potion on a vendor's
shelf. There is no separate shop type.

Built by two loaders onto this one type: ``models.contents_loader`` /
``engine.md_loader`` (scene things from CONTENTS/zone.md) and
``models.thing_loader`` (shop rows). Historically this was two classes — scene
``Item`` and shop ``Thing`` — now merged; ``models.item`` re-exports ``Thing``
as ``Item`` during the transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Apparent-size perception model
#
# Identifiability falls off with distance like perspective in 3-D graphics:
# the apparent size of an object is roughly ``physical_size / distance``. That
# ratio is bucketed into named bands. A small object (a dropped torch) shrinks
# below recognizability far sooner than a large one (a head-high obelisk), so
# the *same* bands map to very different absolute distances per item. Below the
# smallest band the object is too small to make out at all.
# ---------------------------------------------------------------------------

# D&D-style size keywords → a representative largest dimension in feet.
SIZE_KEYWORDS_FT: dict[str, float] = {
    "tiny": 1.0,
    "small": 2.5,
    "medium": 5.0,
    "large": 10.0,
    "huge": 15.0,
    "gargantuan": 25.0,
}

# Default largest dimension (ft) for an item that declares no size: medium.
DEFAULT_ITEM_SIZE_FT = 5.0

# (minimum apparent-size ratio, band name), tested in descending order.
_APPARENT_SIZE_BANDS: tuple[tuple[float, str], ...] = (
    (0.50, "near"),
    (0.15, "intermediate"),
    (0.07, "far"),
    (0.035, "distant"),
)

APPEARANCE_BAND_NAMES: tuple[str, ...] = tuple(name for _, name in _APPARENT_SIZE_BANDS)


def apparent_size_band(size_ft: float, dist: float) -> Optional[str]:
    """Return the perception band for an object of ``size_ft`` viewed at ``dist``.

    Computes ``apparent = size_ft / dist`` and buckets it into one of
    ``near`` / ``intermediate`` / ``far`` / ``distant``. Returns ``None`` when
    the apparent size is below the smallest band (too small/far to make out at
    all). ``size_ft <= 0`` is treated as a default medium object.
    """
    if dist <= 0:
        return "near"
    size = size_ft if size_ft and size_ft > 0 else DEFAULT_ITEM_SIZE_FT
    ratio = size / dist
    for min_ratio, name in _APPARENT_SIZE_BANDS:
        if ratio >= min_ratio:
            return name
    return None


@dataclass
class Interaction:
    """A single ``<verb> [(condition)] → <response>`` adjudication entry.

    Attributes:
        verb: Canonical verb (the first phrasing listed in the source).
        aliases: Other verbs that resolve to this interaction.
        condition: Free-text precondition (parenthetical in the source);
            empty string when no condition was given.
        response: DM-authoritative result text.
    """

    verb: str
    aliases: list[str] = field(default_factory=list)
    condition: str = ""
    response: str = ""

    def matches(self, candidate: str) -> bool:
        """True if ``candidate`` (case-insensitive) matches verb or any alias."""
        c = candidate.strip().lower()
        if c == self.verb.lower():
            return True
        return any(c == a.lower() for a in self.aliases)


@dataclass
class Thing:
    """A possessable thing — scene prop, weapon, armor, consumable, or shop good.

    Position/zone are populated from the corresponding GEOMETRY.md entry when
    the loader is given access to a ``SceneGeometry``; otherwise they remain
    ``None``. The *market facet* fields at the bottom are populated only for
    shop goods (``models.thing_loader``) and left empty for scene things.
    """

    id: str
    description: str = ""

    # Properties (parsed from the italicized parenthetical line)
    pickable: bool = False
    flavor_only: bool = False
    pressable: bool = False
    quest_item_for: Optional[str] = None
    extra_facts: list[str] = field(default_factory=list)

    # Largest physical dimension in feet, used by the apparent-size perception
    # model (``apparent_size_band``) to decide how identifiable the item is at
    # a given range. ``0.0`` means unspecified — treated as a medium object.
    size_ft: float = 0.0

    # Optional author-supplied descriptions keyed by perception band name
    # (``near`` / ``intermediate`` / ``far`` / ``distant``). When a band has no
    # entry the engine falls back to the item's label (near/intermediate) or a
    # generic "indistinct shape" (far/distant). See ``apparent_size_band``.
    appearance_bands: dict[str, str] = field(default_factory=dict)

    # Cross-reference: when set, interactions were inherited from this item id.
    interactions_ref: Optional[str] = None

    # List of interactions in source order. The same verb may appear more
    # than once with different conditions (e.g. ``press (when crack is
    # closed)`` vs ``press (when crack is open)``); look-up logic should
    # iterate and match on verb + (optionally) condition.
    interactions: list["Interaction"] = field(default_factory=list)

    # Spatial (populated from GEOMETRY.md by the loader if available)
    position: Optional[object] = None  # models.space_time.Position
    zone: Optional[str] = None
    label: str = ""

    # Weapon: a pickable item that can be wielded. ``weapon_spec`` is the raw
    # ``<library_id>+<enhancement>`` from CONTENTS (e.g. "mace+1"); ``weapon`` is
    # the resolved base Weapon, attached by md_loader once the weapon library is
    # available (Optional[object] to avoid importing models.weapon here).
    weapon_spec: Optional[str] = None
    weapon: Optional[object] = None

    # Mutable runtime state — not parsed; engine maintains these.
    holder: Optional[str] = None
    state: dict[str, str] = field(default_factory=dict)
    discovered_by: set[str] = field(default_factory=set)

    # --- Market facet -------------------------------------------------------
    # Populated only for shop goods (models.thing_loader). A shop good is a
    # Thing with a price; these stay empty for scene props / floor loot.
    # ``category``/``properties``/``dm_properties`` are read by the town economy
    # today and get *derived into* affordances/effects in Phase 2 (not removed).
    name: str = ""                  # shop display name (scene things use `label`)
    category: str = ""              # "mundane", "magical", "obelisk_shard", "shadowbeast_part"
    price: str = ""                 # kept as string: "5 gp", "2-5 gp", "Varies"
    vendor_id: str = ""             # character ID of seller
    location_id: str = ""           # place ID where item currently is
    properties: str = ""            # advertised / player-visible properties
    dm_properties: str = ""         # true / hidden properties (DM only)
    attunement: str = ""            # e.g. "Required (1 hour in dim light)"
    raw: str = ""                   # original markdown source

    def find_interaction(self, verb: str) -> Optional["Interaction"]:
        """Return the first interaction matching ``verb`` (or alias)."""
        for interaction in self.interactions:
            if interaction.matches(verb):
                return interaction
        return None

    def find_interactions(self, verb: str) -> list["Interaction"]:
        """Return ALL interactions matching ``verb`` (or alias).

        Useful when the same verb is listed multiple times with distinct
        conditions; callers can then pick by condition match.
        """
        return [i for i in self.interactions if i.matches(verb)]
