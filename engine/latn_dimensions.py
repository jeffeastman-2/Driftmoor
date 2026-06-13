"""Driftmoor's RPG vector dimensions for the LATN parser.

Engraf's LATN core ships a domain-neutral, by-design vector space. Driftmoor
extends it at startup via ``engraf...register_dimensions`` WITHOUT editing
Engraf — the dimension *names* live here.

Two parts:

* **Static** — closed sets known in code: verb-intent dims (the D&D 5e
  action vocabulary — see ``VERB_DIMS``) and faction dims
  (``Character.faction`` values).
* **Derived** — ``race`` / ``character_class`` / ``role`` are FREE-TEXT
  fields populated from world/markdown data, not enums, so their dims are
  scanned from the loaded characters at startup.

Property-value dims are **namespaced by field** (``race_`` / ``class_`` /
``role_`` / ``faction_``) so values from different fields can never collide,
and stay disjoint from Engraf's CAD block and from the bare verb-intent dims.
**One-hot:** one dim per value — nominal categories have no inter-value
ordering, so a single enum-valued dim would invent false similarity. The
matching word ("cleric") stays the surface form; the namespacing is an
internal dim-naming convention the lexicon builder and the scene adapter
both derive from the same normalized value, so they always agree.

Deferred (add when backed/needed): item ``state`` values (free-form dict,
ambiguous without real data), ``Thing.category`` (the grounded scene
``Item`` has no category field), and boolean item flags
(``pickable``/``pressable`` — low query value for now). Minting a dim
without populating it on entities is worse than string matching.

Usage (once Engraf is importable — e.g. ``pip install -e ../Engraf`` or a
shared ``latn`` package after phase 3):

    from engine.latn_dimensions import register_driftmoor_dimensions
    register_driftmoor_dimensions(characters=all_characters)  # once, at startup
"""

from __future__ import annotations

import re
from typing import Iterable


# The D&D 5e action vocabulary, as verb-intent dims. Bare (un-namespaced),
# like Engraf's own intent dims (create / move / ...). The 5e *action* is the
# dimension; the sprawl of surface verbs a player types ("shoot"/"loose an
# arrow"/"slash" -> attack) converges onto it via lexicon entries.
#
# Granularity follows what the ENGINE dispatches on, not 5e's labels: all
# weapon verbs collapse to one ``attack``, but 5e's single "Use an Object" is
# split into the fine object-interaction verbs (take/drop/give/press/examine/
# read) the engine already routes differently. Organized by the resolver that
# owns each — most are declared now for a complete, stable schema even though
# phase 2a only WIRES the object-interaction row (a registered-but-unwired
# verb dim is a harmless dormant axis).
VERB_DIMS: tuple[str, ...] = (
    # Combat -> combat resolver (engine/session.py). Spell name rides an NP.
    "attack", "cast",
    # Movement -> movement resolver. "move" coincides with Engraf's existing
    # locomotion dim (same concept, not a near-miss); register_dimensions
    # dedupes it. Declared here anyway so Driftmoor's required vocabulary is
    # self-contained regardless of the base schema it layers onto.
    "move", "dash", "disengage",
    # Defensive / support / perception -> DM-Left adjudication & combat state.
    "dodge", "help", "ready", "hide", "search",
    # Object interaction -> engine/verb_resolver (phase 2a). The fine split of
    # 5e's "Use an Object" (+ the examine-class verbs already resolved today).
    "examine", "read", "press", "take", "drop", "give",
)

# Character.faction is a closed set (see models/character.py:24).
FACTION_VALUES: tuple[str, ...] = ("party", "hostile", "neutral")


def _norm(value: str) -> str:
    """Normalize a free-text property value to a dim-name token.

    Lower-case, collapse non-alphanumeric runs to single underscores, strip
    leading/trailing underscores. ``"High Elf"`` -> ``"high_elf"``.
    """
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def property_dim(field: str, value: str) -> str:
    """The namespaced one-hot dim name for a property value, or "" if blank.

    ``property_dim("race", "High Elf") -> "race_high_elf"``. The single source
    of truth for this mapping — the lexicon builder and the scene adapter both
    call it so a query word and the entity it should match land on the SAME
    dim.
    """
    token = _norm(value)
    return f"{field}_{token}" if token else ""


def _namespaced(field: str, values: Iterable[str]) -> list[str]:
    """``field`` + normalized value for each, skipping blanks."""
    out = []
    for v in values:
        dim = property_dim(field, v)
        if dim:
            out.append(dim)
    return out


def derive_character_property_dims(characters: Iterable) -> list[str]:
    """Distinct namespaced race/class/role dims across ``characters``.

    Characters are duck-typed: any object exposing ``race`` and optionally
    ``character_class`` / ``role``. Returns a sorted, de-duplicated list like
    ``["class_cleric", "race_dwarf", "role_smith"]``.
    """
    races: set[str] = set()
    classes: set[str] = set()
    roles: set[str] = set()
    for c in characters:
        race = getattr(c, "race", "") or ""
        char_class = getattr(c, "character_class", "") or ""
        role = getattr(c, "role", "") or ""
        if race:
            races.add(race)
        if char_class:
            classes.add(char_class)
        if role:
            roles.add(role)
    dims = (
        _namespaced("race", races)
        + _namespaced("class", classes)
        + _namespaced("role", roles)
    )
    return sorted(set(dims))


def driftmoor_rpg_dimensions(characters: Iterable = ()) -> list[str]:
    """The full RPG dimension list — pure, no Engraf dependency.

    Static verb + faction dims, then character-derived race/class/role dims.
    De-duplicated, static-first. Registration is order-insensitive (Engraf
    appends by name), so order is purely cosmetic.
    """
    static = list(VERB_DIMS) + _namespaced("faction", FACTION_VALUES)
    derived = derive_character_property_dims(characters)
    seen: set[str] = set()
    out: list[str] = []
    for dim in static + derived:
        if dim not in seen:
            seen.add(dim)
            out.append(dim)
    return out


def register_driftmoor_dimensions(characters: Iterable = ()) -> int:
    """Register Driftmoor's RPG dims into the LATN vector space.

    Call once at startup, **before** constructing any ``VectorSpace`` or
    parsing. Requires Engraf on the import path. Idempotent (Engraf's
    ``register_dimensions`` skips names already present), so a second call
    after more characters load only adds the new values. Returns the new
    total dimension count.
    """
    from engine.latn import register_dimensions

    return register_dimensions(driftmoor_rpg_dimensions(characters), semantic=True)
