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


# ---------------------------------------------------------------------------
# Affordances, effects, carry-state
#
# A Thing is manipulated through its *affordances* (capability tags that gate
# verbs) and *effects* (what it does), while its *carry-state* says where it is
# relative to a possessor. "weapon" and "armor" are just affordance + effect,
# not separate classes. These are additive scaffolding in this phase — the
# unified verb dispatch and derived legacy views (cs.weapons/wielded/...) wire
# them up in the switchover phase.
# ---------------------------------------------------------------------------

# Affordance tags (a Thing may carry several).
HOLDABLE = "holdable"      # can occupy a hand (take/draw/stow/drop)
WEARABLE = "wearable"      # can occupy a body slot (wear/remove)
WEAPON = "weapon"          # holdable whose in-hand-use effect is an attack
ARMOR = "armor"            # wearable whose worn effect is an AC bonus
CONSUMABLE = "consumable"  # umbrella: destroyed on use (edible OR drinkable)
EDIBLE = "edible"          # a solid consumable — "eat"
DRINKABLE = "drinkable"    # a liquid consumable — "drink"
TOOL = "tool"              # grants a `use` action / check bonus / produces a Thing
READABLE = "readable"      # has a `read` interaction
CONTAINER = "container"    # can hold other Things
LIGHT = "light"            # light source (stateful lit/unlit)
PRESSABLE = "pressable"    # has a `press` interaction

# Carry-state locations (where a Thing is relative to its holder).
IN_WORLD = "in_world"      # loose in the world (holder is None), at `position`
CARRIED = "carried"        # possessed, in the pack (not in hand or worn)
IN_HAND = "in_hand"        # occupying hand slot(s)
WORN = "worn"              # occupying a body slot
CONSUMED = "consumed"      # used up / destroyed


@dataclass
class Effect:
    """Something a Thing does. ``kind`` is the effect family (``damage``/``ac``/
    ``heal``/``check_bonus``/``light``/``produce``/…); ``payload`` carries its
    data; ``source`` distinguishes intrinsic effects from added enchantments;
    ``state`` holds mutable per-effect runtime (e.g. wand charges)."""

    kind: str
    payload: dict = field(default_factory=dict)
    source: str = "intrinsic"     # "intrinsic" | "enchantment"
    state: dict = field(default_factory=dict)


@dataclass
class CarryState:
    """Where a Thing is relative to its holder, and what slots it occupies."""

    location: str = IN_WORLD      # one of the IN_WORLD/CARRIED/IN_HAND/WORN/CONSUMED constants
    hands: int = 0                # hand slots used while IN_HAND
    slot: str = ""                # body slot filled while WORN (e.g. "torso", "head")


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

    # Weight in pounds — the encumbrance lever (coins weigh too: 50/lb). 0.0
    # means unspecified. Volume/3-D packing is deliberately not modelled.
    weight_lb: float = 0.0

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
    # Ownership (property), distinct from `holder` (possession/who's carrying it)
    # and from position/zone (where it sits). A pack left in the rooming house is
    # holder=None, zone=rooming_house, owner=<player>. None = unowned. Set at load
    # for shop goods (from vendor_id) and moved by the transfer primitive.
    owner: Optional[str] = None
    state: dict[str, str] = field(default_factory=dict)
    discovered_by: set[str] = field(default_factory=set)

    # Resolved Armor for a wearable-armor Thing (mirrors ``weapon`` above;
    # Optional[object] to avoid importing models.weapon here).
    armor: Optional[object] = None

    # --- Affordances / effects / carry-state --------------------------------
    # Capability tags gating verbs, what the thing does, and where it is on the
    # body. Populated by ``derive_affordances`` (and, for the kit, at load).
    affordances: set[str] = field(default_factory=set)
    effects: list["Effect"] = field(default_factory=list)
    carry: "CarryState" = field(default_factory=CarryState)

    # How many of this identical thing (10 torches, 10 days of rations). A stack.
    quantity: int = 1
    # --- Container facet (a pack/bag/chest; empty for everything else) -------
    # Its contents as (catalog_id, quantity) pairs, expanded into the holder's
    # possessions at load; and a free-text capacity (e.g. "30 lb"). Containers
    # get their own catalog (CONTAINERS.md) since their attributes diverge.
    contents: list = field(default_factory=list)
    capacity: str = ""

    # --- Market facet -------------------------------------------------------
    # Populated only for shop goods (models.thing_loader). A shop good is a
    # Thing with a price; these stay empty for scene props / floor loot.
    # ``category``/``properties``/``dm_properties`` are read by the town economy
    # today and get *derived into* affordances/effects in Phase 2 (not removed).
    name: str = ""                  # shop display name (scene things use `label`)
    category: str = ""              # "mundane", "magical", "obelisk_shard", "shadowbeast_part"
    price: str = ""                 # kept as string: "5 gp", "2-5 gp", "Varies"
    value_cp: Optional[int] = None  # base/market worth in copper (parsed from `price`); None = unknown
    listed_price_cp: Optional[int] = None  # the ask in copper; None = NOT for sale
    vendor_id: str = ""             # character ID of seller
    location_id: str = ""           # place ID where item currently is
    properties: str = ""            # advertised / player-visible properties
    dm_properties: str = ""         # true / hidden properties (DM only)
    attunement: str = ""            # e.g. "Required (1 hour in dim light)"
    raw: str = ""                   # original markdown source

    def __post_init__(self) -> None:
        # Derive the structured money fields from the authored `price`/`vendor_id`
        # — one source of truth for every construction path (loaders and the
        # Phase-4 materialize-kit alike). Explicitly-passed values win.
        from models.currency import parse_coins
        if self.value_cp is None and self.price:
            self.value_cp = parse_coins(self.price)
        # A shop good (it has a vendor) is for sale at its value by default;
        # scene props (no vendor) stay not-for-sale (listed_price_cp None), and
        # a shop good's owner defaults to its vendor.
        if self.listed_price_cp is None and self.vendor_id and self.value_cp is not None:
            self.listed_price_cp = self.value_cp
        if self.owner is None and self.vendor_id:
            self.owner = self.vendor_id

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


def derive_affordances(thing: "Thing") -> "Thing":
    """Fill in a scene Thing's ``affordances``/``effects`` from its already-parsed
    fields (pickable / weapon / armor / interactions). Idempotent — uses set
    semantics — so it is safe to call more than once (e.g. before and after the
    weapon library is resolved). Returns the same Thing for chaining.

    Kit-supplied Things (weapons, armor, tools, consumables materialized from a
    character's equipment) declare their affordances directly at build time;
    this covers scene props parsed from CONTENTS/zone.md.
    """
    aff = thing.affordances

    # A flavor-only prop can't be manipulated: no carry affordances.
    if not thing.flavor_only and thing.pickable:
        aff.add(HOLDABLE)

    if thing.weapon is not None:
        aff.add(WEAPON)
        aff.add(HOLDABLE)  # a weapon occupies a hand
        if not any(e.kind == "damage" for e in thing.effects):
            w = thing.weapon
            thing.effects.append(Effect(kind="damage", payload={
                "weapon_id": getattr(w, "id", thing.id),
                "damage_dice": getattr(w, "damage_dice", ""),
                "damage_type": getattr(w, "damage_type", ""),
            }))

    if thing.armor is not None:
        aff.add(WEARABLE)
        aff.add(ARMOR)
        if not any(e.kind == "ac" for e in thing.effects):
            a = thing.armor
            thing.effects.append(Effect(kind="ac", payload={
                "armor_id": getattr(a, "id", thing.id),
                "ac_base": getattr(a, "ac_base", None),
            }))

    # Interaction-derived affordances (so "read/press/drink the X" can ground).
    if thing.pressable or thing.find_interaction("press") is not None:
        aff.add(PRESSABLE)
    if thing.find_interaction("read") is not None:
        aff.add(READABLE)
    edible = thing.find_interaction("eat") is not None
    drinkable = thing.find_interaction("drink") is not None
    if edible:
        aff.add(EDIBLE)
    if drinkable:
        aff.add(DRINKABLE)
    if edible or drinkable:
        aff.add(CONSUMABLE)  # umbrella: consumable == edible or drinkable
        aff.add(HOLDABLE)    # you hold it to consume it

    return thing
