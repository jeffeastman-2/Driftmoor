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
    r"|get|gets|hold|holds|carry|carries|carrying|pull out|pulls out|produce|produces)\b", re.IGNORECASE)
_HOLD_RE = re.compile(
    r"\b(get|gets|hold|holds|carry|carries|carrying|pull out|pulls out|produce|produces)\b",
    re.IGNORECASE,
)
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
    """Lower-case identifying tokens for a kit Thing — its name/label + id, plus
    any CATEGORY tags (a rapier's `sword`/`blade`). So "draw my sword" grounds to
    the rapier and "drink the water" finds a "Waterskin" with id "water". Nouns
    attend to category tags."""
    from engine.combat_resolver import _weapon_name_tokens
    toks: list[str] = []
    w = getattr(thing, "weapon", None)
    if w is not None:
        toks += list(_weapon_name_tokens(w))
        toks += [t.lower() for t in (getattr(w, "tags", None) or [])]
    else:
        text = " ".join(filter(None, [getattr(thing, "label", ""), getattr(thing, "id", "")]))
        toks += [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) > 1]
        if getattr(thing, "armor", None) is not None:
            toks += ["armor"]
        low = text.lower()
        if any(k in low for k in ("pack", "backpack")):
            toks += ["pack", "backpack", "bag", "satchel"]
        elif any(k in low for k in ("bag", "satchel")):
            toks += ["bag", "satchel", "pack"]
        elif "pouch" in low:
            toks += ["pouch"]
    toks += [t.lower() for t in (getattr(thing, "tags", None) or [])]  # Thing-level categories
    return toks


def _is_accessible_possession(cs, thing) -> bool:
    """True when ``thing`` is currently reachable for direct manipulation.

    Container children (pack contents expanded from a parent container) are
    only directly usable while that parent container is in hand. This keeps
    grounding/manipulation aligned with inventory visibility semantics.
    """
    parent_id = str(getattr(thing, "parent_container_id", "") or "").strip()
    if not parent_id:
        return True
    held = set(getattr(cs, "held_items", None) or [])
    return parent_id in held


def _is_pack_like_container(thing) -> bool:
    """Heuristic: pack/bag-like containers are wearable even when authored as
    generic scene props (e.g. a dropped/picked backpack)."""
    text = " ".join(
        filter(None, [str(getattr(thing, "label", "")), str(getattr(thing, "id", ""))])
    ).lower()
    return any(k in text for k in ("pack", "backpack", "bag", "pouch", "satchel"))


def find_possessed_thing(cs, intent_text: str):
    """The kit Thing (in ``cs.things``) named in ``intent_text``, or None.

    Call ``loadout.materialize_things(cs)`` first so ``cs.things`` reflects the
    current kit. Lets a possession verb act on a kit weapon/armor by name."""
    text = (intent_text or "").lower()
    for thing in (getattr(cs, "things", None) or []):
        if not _is_accessible_possession(cs, thing):
            continue
        if any(re.search(rf"\b{re.escape(tok)}\b", text) for tok in _name_tokens(thing)):
            return thing
    return None


def find_possessed_scene_thing(cs, intent_text: str, items: Optional[dict],
                               interaction_target: Optional[str] = None):
    """A held scene item named in intent/target text, or None.

    This is the fallback when an item is carried from the scene registry but is
    not part of ``cs.things`` (kit/materialized possessions).
    """
    if not items:
        return None
    actor_id = getattr(getattr(cs, "character", None), "id", "")
    if not actor_id:
        return None
    text = " ".join(filter(None, [(intent_text or "").lower(), (interaction_target or "").lower()]))
    held = set(getattr(cs, "held_items", None) or [])
    for thing in items.values():
        if getattr(thing, "holder", None) != actor_id:
            continue
        tid = str(getattr(thing, "id", "") or "")
        if tid and tid not in held:
            continue
        if not _is_accessible_possession(cs, thing):
            continue
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
    carry = getattr(thing, "carry", None)
    carry_loc = getattr(carry, "location", "") if carry is not None else ""
    if WEAPON not in aff and _REMOVE_RE.search(intent_text) and (
        WEARABLE in aff or carry_loc == "worn" or _is_pack_like_container(thing)
    ):
        return "remove"
    if WEAPON not in aff and _WEAR_RE.search(intent_text) and (
        WEARABLE in aff or _is_pack_like_container(thing)
    ):
        return "wear"
    if WEARABLE in aff and WEAPON not in aff:
        if _REMOVE_RE.search(intent_text):
            return "remove"
        if _WEAR_RE.search(intent_text):
            return "wear"
    if HOLDABLE in aff and WEAPON not in aff:
        if tv == "drop":
            return "drop"
        if tv == "stow" or _SHEATHE_RE.search(intent_text):
            return "stow"
        # Non-weapons should not answer to weapon verbs like "wield/draw".
        if tv == "take" or _HOLD_RE.search(intent_text):
            return "hold"
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
    thing_id = getattr(thing, "id", "")

    if not _is_accessible_possession(cs, thing):
        loadout.materialize_things(cs)
        return res

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
    elif verb == "hold" and weapon is None and thing_id:
        if loadout.hold_item(cs, thing_id):
            res.log.append(
                f"[ITEM] {character_id} holds {name}: {handle} takes it in hand. Narrate it."
            )
            res.events.append((turn_num, f"{ts} | {handle} takes up {name}."))
            res.memory.append(f"Turn {turn_num}: you took {name} in hand.")
            res.applied = True
    elif verb == "stow" and weapon is None and thing_id:
        if loadout.stow_item(cs, thing_id):
            carry = getattr(thing, "carry", None)
            if carry is not None:
                from models.thing import CARRIED
                carry.location = CARRIED
            res.log.append(
                f"[ITEM] {character_id} stows {name}: {handle} puts it away. Narrate it."
            )
            res.events.append((turn_num, f"{ts} | {handle} stows {name}."))
            res.memory.append(f"Turn {turn_num}: you put away {name}.")
            res.applied = True
    elif verb == "drop" and weapon is None:
        _drop_pack_thing_to_ground(cs, thing, items, actor_pos, actor_zone, character_id)
        res.log.append(
            f"[ITEM-TRANSFER] {character_id} drops {name} on the ground in "
            f"{(actor_zone or 'this zone').upper()}: {handle} sets it down. Narrate the drop."
        )
        res.events.append((turn_num, f"{ts} | {handle} drops the {name}."))
        res.memory.append(f"Turn {turn_num}: you dropped your {name}.")
        res.applied = True
    elif verb in ("eat", "drink"):
        # Consume a holdable consumable: it leaves play and its effects transfer
        # onto the character (heal / neurochemical nudge / satiety / status),
        # source-agnostic — a potion and a loaf run the same pipe.
        from engine import effects
        from models.thing import CONSUMED
        notes = effects.apply_thing_effects(cs, thing)
        qty = int(getattr(thing, "quantity", 1) or 1)
        if qty > 1:
            thing.quantity = qty - 1           # deplete one from the stack; the rest remain
        else:
            thing.carry.location = CONSUMED    # last one — used up, leaves the pack
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
    elif verb == "wear":
        from models.thing import WORN
        if thing_id:
            loadout.stow_item(cs, thing_id)  # if it was in hand, free the hand
        if getattr(thing, "armor", None) is not None:
            cs.armor = thing.armor
            cs.pack = [p for p in (getattr(cs, "pack", None) or []) if p is not thing]
        else:
            carry = getattr(thing, "carry", None)
            if carry is not None:
                carry.location = WORN
        if getattr(getattr(cs, "character", None), "ac", None) is not None:
            cs.character.ac = loadout.armor_class(cs.character, cs.armor, cs.pack)
        res.log.append(
            f"[ITEM] {character_id} wears {name}: {handle} puts it on. Narrate it."
        )
        res.events.append((turn_num, f"{ts} | {handle} wears {name}."))
        res.memory.append(f"Turn {turn_num}: you put on {name}.")
        res.applied = True
    elif verb == "remove":
        from models.thing import CARRIED
        if getattr(thing, "armor", None) is not None:
            cs.armor = None
            carry = getattr(thing, "carry", None)
            if carry is not None:
                carry.location = CARRIED
            if thing not in (getattr(cs, "pack", None) or []):
                if getattr(cs, "pack", None) is None:
                    cs.pack = []
                cs.pack.append(thing)
        else:
            carry = getattr(thing, "carry", None)
            if carry is not None:
                carry.location = CARRIED
        if getattr(getattr(cs, "character", None), "ac", None) is not None:
            cs.character.ac = loadout.armor_class(cs.character, cs.armor, cs.pack)
        res.log.append(
            f"[ITEM] {character_id} removes {name}: {handle} takes it off. Narrate it."
        )
        res.events.append((turn_num, f"{ts} | {handle} removes {name}."))
        res.memory.append(f"Turn {turn_num}: you took off {name}.")
        res.applied = True

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


def _drop_pack_thing_to_ground(cs, thing, items, actor_pos, actor_zone: str,
                               character_id: str) -> None:
    """Remove a non-weapon kit possession from the pack and place it in-world."""
    from engine import loadout
    from models.thing import IN_WORLD, derive_affordances
    from models.space_time import Position

    thing_id = getattr(thing, "id", "")
    if thing_id:
        loadout.stow_item(cs, thing_id)
    cs.pack = [p for p in (getattr(cs, "pack", None) or []) if p is not thing]
    ax, ay = float(actor_pos[0]), float(actor_pos[1])
    thing.holder = None
    thing.position = Position(ax, ay)
    thing.zone = actor_zone
    thing.carry.location = IN_WORLD
    thing.carry.hands = 0
    if items is not None and thing_id:
        items[thing_id] = thing
    derive_affordances(thing)
    thing.discovered_by.add(character_id)
