"""Unified, affordance-gated manipulation of a character's kit possessions.

One dispatch for draw/wield, sheathe/stow, drop, and wear/remove over a
character's KIT Things (weapons, armor) — replacing the per-verb kit stopgaps
that special-cased weapons because they weren't scene ``Item``s. The kit is
surfaced as Things by ``loadout.materialize_things``; each verb declares the
affordance it requires and the carry-state transition it performs, reuses the
loadout hand-budget primitives, and returns a :class:`ManipulationResult` of
narration side-effects for the caller to apply (so this module stays free of the
turn loop's narration helpers and is easy to unit-test).

Scene-item transfers (a torch on the floor, handing a relic to an ally) keep
flowing through ``session._handle_item_transfer``; this covers exactly the
possessions that used to be invisible to it — kit Weapons and Armor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from models.thing import DRINKABLE, EDIBLE, HOLDABLE, WEAPON, WEARABLE


# Verb → canonical manipulation. Drop/stow/take come from the shared transfer
# lexicon; draw/sheathe/wear/remove have their own phrasings here (the combat
# path keeps its own copies in session._apply_loadout_intent).
_DRAW_RE = re.compile(
    r"\b(draw|draws|ready|readies|wield|wields|unsheath\w*|brandish\w*"
    r"|get|gets|hold|holds|pull out|pulls out|produce|produces)\b", re.IGNORECASE)
_SHEATHE_RE = re.compile(
    r"\b(sheath\w*|holster\w*|put away|puts away|put down)\b", re.IGNORECASE)
_WEAR_RE = re.compile(r"\b(wear|wears|don|dons|put on|puts on|equip\w*)\b", re.IGNORECASE)
_REMOVE_RE = re.compile(
    r"\b(remove|removes|take off|takes off|doff|doffs|unequip\w*)\b", re.IGNORECASE)
# Consumption verbs split by state: solids are eaten, liquids drunk; a few are
# generic (consume/swallow/ingest) and resolve to whichever the thing affords.
_EAT_RE = re.compile(r"\b(eat|eats|devour\w*|bite|bites|chew\w*|munch\w*)\b", re.IGNORECASE)
_DRINK_RE = re.compile(r"\b(drink|drinks|quaff\w*|sip|sips|gulp\w*|swig\w*)\b", re.IGNORECASE)
_CONSUME_RE = re.compile(r"\b(consume|consumes|swallow\w*|ingest\w*)\b", re.IGNORECASE)


@dataclass
class ManipulationResult:
    """Side-effects of a manipulation, for the caller to fold into the turn."""

    applied: bool = False
    log: list = field(default_factory=list)        # -> attack_log lines
    events: list = field(default_factory=list)     # -> recent_events (turn, text)
    memory: list = field(default_factory=list)     # -> _append_memory_note lines


def _name_tokens(thing) -> list[str]:
    """Lower-case identifying tokens for a kit Thing (name/label + id), so a
    provision named "Waterskin" with id "water" matches "drink the water"."""
    from engine.combat_resolver import _weapon_name_tokens
    w = getattr(thing, "weapon", None)
    if w is not None:
        return list(_weapon_name_tokens(w))
    text = " ".join(filter(None, [getattr(thing, "label", ""), getattr(thing, "id", "")]))
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1]


def find_possessed_thing(cs, intent_text: str):
    """The kit Thing (in ``cs.things``) named in ``intent_text``, or None.

    Call ``loadout.materialize_things(cs)`` first so ``cs.things`` reflects the
    current kit. Lets a possession verb act on a kit weapon/armor by name."""
    text = (intent_text or "").lower()
    for thing in (getattr(cs, "things", None) or []):
        if any(re.search(rf"\b{re.escape(tok)}\b", text) for tok in _name_tokens(thing)):
            return thing
    return None


def classify_verb(intent_text: str, thing) -> Optional[str]:
    """Map free-text intent + the target's affordances to a canonical verb:
    ``drop`` / ``sheathe`` / ``draw`` / ``wear`` / ``remove`` / ``eat`` (or None).

    Each verb is gated on the affordance it requires — this is where "wield the
    potion" is refused (a potion has no ``weapon`` affordance, so no verb
    classifies) while "drink the potion" resolves to ``eat``."""
    from engine.verb_resolver import detect_transfer_verb
    aff = getattr(thing, "affordances", set()) or set()
    tv = detect_transfer_verb(intent_text)
    if tv == "drop":
        return "drop"
    # Consumption is state-gated: you can't drink bread or eat water.
    if EDIBLE in aff and _EAT_RE.search(intent_text):
        return "eat"
    if DRINKABLE in aff and _DRINK_RE.search(intent_text):
        return "drink"
    if _CONSUME_RE.search(intent_text):        # generic verb -> whatever it affords
        if EDIBLE in aff:
            return "eat"
        if DRINKABLE in aff:
            return "drink"
    if WEARABLE in aff and WEAPON not in aff:
        if _REMOVE_RE.search(intent_text):
            return "remove"
        if _WEAR_RE.search(intent_text):
            return "wear"
    if WEAPON in aff:  # draw/sheathe are weapon verbs (a potion won't wield)
        if tv == "stow" or _SHEATHE_RE.search(intent_text):
            return "sheathe"
        if tv == "take" or _DRAW_RE.search(intent_text):
            return "draw"
    return None


def apply_manipulation(cs, verb: str, thing, *, items, actor_pos, actor_zone: str,
                       character_id: str, game_time, turn_num: int) -> ManipulationResult:
    """Apply a canonical manipulation verb to a kit ``thing``, mutating the
    loadout/scene and returning the narration side-effects. Re-materializes
    ``cs.things`` afterwards so its carry-state view stays fresh."""
    from engine import loadout
    res = ManipulationResult()
    handle = getattr(cs, "scene_handle", "") or getattr(
        getattr(cs, "character", None), "name", "") or character_id
    name = getattr(thing, "label", None) or getattr(thing, "id", "")
    weapon = getattr(thing, "weapon", None)
    ts = f"{game_time.hour}:{game_time.minute:02d}" if game_time else f"t{turn_num}"

    if verb == "draw" and weapon is not None:
        log: list = []
        loadout.draw(cs, weapon, log)
        if log:
            res.log.append(f"[LOADOUT] {character_id}: " + ", ".join(log))
        res.applied = True
    elif verb == "sheathe" and weapon is not None:
        log = []
        loadout.sheathe(cs, weapon, log)
        if log:
            res.log.append(f"[LOADOUT] {character_id}: " + ", ".join(log))
        res.applied = True
    elif verb == "drop" and weapon is not None:
        _drop_weapon_to_ground(cs, weapon, items, actor_pos, actor_zone, character_id)
        res.log.append(
            f"[ITEM-TRANSFER] {character_id} drops {weapon.name} on the ground in "
            f"{(actor_zone or 'this zone').upper()}: {handle} sets it down. Narrate the drop.")
        res.events.append((turn_num, f"{ts} | {handle} drops the {weapon.name}."))
        res.memory.append(f"Turn {turn_num}: you dropped your {weapon.name}.")
        res.applied = True
    elif verb in ("eat", "drink"):
        # Consume a holdable consumable: it leaves play and its effects transfer
        # onto the character (heal / neurochemical nudge / satiety / status),
        # source-agnostic — a potion and a loaf run the same pipe.
        from engine import effects
        from models.thing import CONSUMED
        notes = effects.apply_thing_effects(cs, thing)
        thing.carry.location = CONSUMED
        # Used up — drop it from the pack.
        pack = getattr(cs, "pack", None)
        if pack is not None:
            cs.pack = [p for p in pack if p is not thing]
        detail = (" (" + ", ".join(notes) + ")") if notes else ""
        pres, past = ("drinks", "drank") if verb == "drink" else ("eats", "ate")
        res.log.append(
            f"[ITEM] {character_id} {pres} {name}{detail}: {handle} uses it up. "
            f"Narrate it and any effect.")
        res.events.append((turn_num, f"{ts} | {handle} {pres} the {name}."))
        res.memory.append(f"Turn {turn_num}: you {past} the {name}{detail}.")
        res.applied = True
    # wear/remove for kit armor is a carry-state change only in the bridge
    # (cs.armor is unchanged); left minimal until equipment wearables are Things.

    loadout.materialize_things(cs)
    return res


def _drop_weapon_to_ground(cs, weapon, items, actor_pos, actor_zone: str,
                           character_id: str) -> None:
    """Take a kit weapon out of hand, remove it from the kit, and materialize a
    loose, pickable Thing where the character stands so it can be picked back up."""
    from engine import loadout
    from models.thing import Thing, derive_affordances
    from models.space_time import Position
    loadout.sheathe(cs, weapon)
    cs.weapons = [w for w in (getattr(cs, "weapons", None) or []) if w.id != weapon.id]
    ax, ay = float(actor_pos[0]), float(actor_pos[1])
    it = (items or {}).get(weapon.id) if items is not None else None
    if it is None:
        it = Thing(id=weapon.id, label=weapon.name,
                   description=f"A {weapon.name.lower()} lies where it was dropped.",
                   pickable=True, weapon=weapon,
                   position=Position(ax, ay), zone=actor_zone, holder=None)
        if items is not None:
            items[weapon.id] = it
    else:
        it.holder = None
        it.position = Position(ax, ay)
        it.zone = actor_zone
        it.weapon = weapon
        it.pickable = True
    derive_affordances(it)
    it.discovered_by.add(character_id)
