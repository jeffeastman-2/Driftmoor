"""Wielded-weapon / hand-slot model (Phase 2).

A character owns a kit (``CharacterSession.weapons`` + armor + inventory). At any
moment a subset is *wielded* — actually in hand. Hand capacity
(``Character.hands``, humanoid default 2) plus a per-weapon hand cost constrains
what can be held at once, which is what makes "a shield and a two-handed sword
at the same time" impossible without a special case. Natural weapons (claw,
bite) cost no hands and are always available, so creatures aren't limited.

This module is pure (no engine imports beyond models + the dice helper) so it is
cheap to unit-test and reuse from the resolver, the turn loop, and the parser.
"""

from __future__ import annotations

from models.weapon import Weapon


def weapon_hands(w: Weapon) -> int:
    """Hand slots a weapon occupies: 0 natural, 2 two-handed, else 1."""
    props = [p.lower() for p in (getattr(w, "properties", None) or [])]
    if "natural" in props:
        return 0
    if "two_handed" in props:
        return 2
    return 1


def _by_id(weapons) -> dict[str, Weapon]:
    return {w.id: w for w in (weapons or [])}


def hands_used(wielded, weapons) -> int:
    """Total hand slots consumed by the wielded ids."""
    by_id = _by_id(weapons)
    return sum(weapon_hands(by_id[wid]) for wid in (wielded or []) if wid in by_id)


def hands_total(cs) -> int:
    return int(getattr(getattr(cs, "character", None), "hands", 2) or 0)


def hands_free(cs) -> int:
    used = hands_used(getattr(cs, "wielded", None), getattr(cs, "weapons", None))
    used += len(getattr(cs, "held_items", None) or [])  # torch etc. — 1 hand each
    return max(0, hands_total(cs) - used)


def held_items(cs) -> list[str]:
    """Non-weapon item ids currently in-hand (e.g. a torch)."""
    return list(getattr(cs, "held_items", None) or [])


def hold_item(cs, item_id: str, log: list | None = None) -> bool:
    """Take a non-weapon item into a free hand, auto-sheathing the lowest-value
    wielded weapon when no hand is free. Returns True if it ends up in hand.
    Idempotent. Each held item costs one hand."""
    if getattr(cs, "held_items", None) is None:
        cs.held_items = []
    if item_id in cs.held_items:
        return True
    from engine.combat_resolver import _avg_damage
    while hands_free(cs) < 1 and (getattr(cs, "wielded", None) or []):
        by_id = _by_id(getattr(cs, "weapons", None))
        held = [by_id[w] for w in cs.wielded if w in by_id]
        if not held:
            break
        victim = min(held, key=lambda w: _avg_damage(w.damage_dice))
        cs.wielded.remove(victim.id)
        if log is not None:
            log.append(f"sheathes {victim.name}")
    if hands_free(cs) >= 1:
        cs.held_items.append(item_id)
        return True
    return False


def stow_item(cs, item_id: str) -> bool:
    """Move a held item from hand to pack: it stays in inventory but frees the
    hand. Returns True if it was in hand."""
    held = getattr(cs, "held_items", None)
    if held and item_id in held:
        held.remove(item_id)
        return True
    return False


def wielded_weapons(cs) -> list[Weapon]:
    """Weapons the character can attack with this turn: everything in the
    wielded set, plus natural weapons (always available)."""
    by_id = _by_id(getattr(cs, "weapons", None))
    out: list[Weapon] = []
    for wid in (getattr(cs, "wielded", None) or []):
        w = by_id.get(wid)
        if w is not None and w not in out:
            out.append(w)
    for w in (getattr(cs, "weapons", None) or []):
        if weapon_hands(w) == 0 and w not in out:
            out.append(w)
    return out


def is_wielding(cs, weapon: Weapon) -> bool:
    """True if the weapon is in hand (or natural — always in hand)."""
    if weapon_hands(weapon) == 0:
        return True
    return weapon.id in (getattr(cs, "wielded", None) or [])


def can_wield(cs, weapon: Weapon) -> bool:
    """True if the weapon fits in the free hands (naturals always fit)."""
    need = weapon_hands(weapon)
    return True if need == 0 else hands_free(cs) >= need


def proficient_with(character, weapon: Weapon) -> bool:
    """True if ``character`` is trained with ``weapon`` — by its id, any of its
    category/group tags (simple/martial/sword/…), or because it's a natural
    weapon (creatures are always proficient with their own body). Reads
    ``character.weapon_proficiencies`` (a flat set of ids/tiers/groups)."""
    tags = {t.lower() for t in (getattr(weapon, "tags", None) or [])}
    if "natural" in tags or "natural" in {
            p.lower() for p in (getattr(weapon, "properties", None) or [])}:
        return True
    profs = {p.lower() for p in (getattr(character, "weapon_proficiencies", None) or set())}
    return weapon.id.lower() in profs or bool(tags & profs)


def weapon_attack_bonus(character, weapon: Weapon) -> int:
    """The character's attack (to-hit) bonus with ``weapon``, computed at
    runtime: ability modifier (finesse picks the better of STR/DEX; ranged uses
    DEX) + proficiency bonus IF proficient + the weapon's own magic enhancement
    (``weapon.attack_bonus``, set for a +N magic item). Replaces the frozen
    per-character ``+N`` total."""
    enhancement = int(getattr(weapon, "attack_bonus", 0) or 0)
    level = int(getattr(character, "level", 1) or 1)
    prof = 2 + (level - 1) // 4
    props = [p.lower() for p in (getattr(weapon, "properties", None) or [])]
    str_mod = (int(getattr(character, "strength", 10) or 10) - 10) // 2
    dex_mod = (int(getattr(character, "dexterity", 10) or 10) - 10) // 2
    if getattr(weapon, "range_normal", 0) > 0:
        mod = dex_mod
    elif "finesse" in props:
        mod = max(str_mod, dex_mod)
    else:
        mod = str_mod
    return mod + (prof if proficient_with(character, weapon) else 0) + enhancement


def _held_weapon_attack_bonus(character, base: Weapon) -> int:
    """Attack bonus for a picked-up weapon (kept as a thin wrapper). Now
    proficiency-aware via ``weapon_attack_bonus`` — a character no longer gets
    the proficiency bonus for a weapon they aren't trained with."""
    return weapon_attack_bonus(character, base)


def register_held_weapon(cs, item) -> Weapon | None:
    """Ensure a per-character Weapon for a picked-up weapon ``item`` exists in
    ``cs.weapons`` (keyed by the item id) and return it. Idempotent; returns
    None when the item carries no weapon spec."""
    base = getattr(item, "weapon", None)
    if base is None:
        return None
    if getattr(cs, "weapons", None) is None:
        cs.weapons = []
    existing = next((w for w in cs.weapons if w.id == base.id), None)
    if existing is not None:
        return existing
    import dataclasses
    w = dataclasses.replace(
        base, attack_bonus=_held_weapon_attack_bonus(cs.character, base))
    cs.weapons.append(w)
    return w


def sync_held_weapons(cs, items) -> None:
    """Register every weapon item this character is currently holding, so a
    picked-up weapon survives a resume (item.holder is checkpointed; cs.weapons
    is rebuilt from the kit at load and must be re-augmented)."""
    cid = getattr(getattr(cs, "character", None), "id", None)
    if not cid or not items:
        return
    for item in (items.values() if hasattr(items, "values") else items):
        if getattr(item, "holder", None) == cid and getattr(item, "weapon", None) is not None:
            register_held_weapon(cs, item)


def draw(cs, weapon: Weapon, log: list | None = None) -> bool:
    """Ready a weapon, auto-sheathing the lowest-value held weapons as needed to
    free hands. Returns True if it ends up wielded. Naturals are always ready."""
    if is_wielding(cs, weapon):
        return True
    need = weapon_hands(weapon)
    if need == 0:
        return True
    from engine.combat_resolver import _avg_damage
    while hands_free(cs) < need and (getattr(cs, "wielded", None) or []):
        by_id = _by_id(getattr(cs, "weapons", None))
        held = [by_id[w] for w in cs.wielded if w in by_id]
        if not held:
            break
        victim = min(held, key=lambda w: _avg_damage(w.damage_dice))
        cs.wielded.remove(victim.id)
        if log is not None:
            log.append(f"sheathes {victim.name}")
    if hands_free(cs) >= need:
        cs.wielded.append(weapon.id)
        if log is not None:
            log.append(f"draws {weapon.name}")
        return True
    return False


def sheathe(cs, weapon: Weapon, log: list | None = None) -> bool:
    """Stow a wielded weapon. Returns True if it was wielded and is now stowed."""
    wielded = getattr(cs, "wielded", None) or []
    if weapon.id in wielded:
        cs.wielded.remove(weapon.id)
        if log is not None:
            log.append(f"sheathes {weapon.name}")
        return True
    return False


def materialize_things(cs) -> None:
    """(Re)build ``cs.things`` — a derived Thing-view of the character's kit
    (weapons + armor) carrying affordances and carry-state mirrored from the
    live loadout (``cs.weapons``/``wielded``/``armor``, which stay the source of
    truth). This is what makes kit possessions visible to the unified
    manipulation dispatch and affordance-aware grounding as Things. Cheap and
    idempotent — call it after any loadout change (draw/sheathe/pickup/drop)."""
    from models.thing import (
        Thing, CarryState, derive_affordances, IN_HAND, IN_WORLD, CARRIED, WORN,
    )
    holder = getattr(getattr(cs, "character", None), "id", None)
    wielded = set(getattr(cs, "wielded", None) or [])
    things: list = []
    for w in (getattr(cs, "weapons", None) or []):
        in_hand = w.id in wielded
        t = Thing(id=w.id, label=getattr(w, "name", w.id), weapon=w, holder=holder,
                  pickable=True)
        t.carry = CarryState(
            location=IN_HAND if in_hand else CARRIED,
            hands=weapon_hands(w) if in_hand else 0,
        )
        derive_affordances(t)
        things.append(t)
    armor = getattr(cs, "armor", None)
    if armor is not None:
        t = Thing(id=getattr(armor, "id", "armor"),
                  label=getattr(armor, "name", "armor"), armor=armor, holder=holder)
        t.carry = CarryState(location=WORN, slot="torso")
        derive_affordances(t)
        things.append(t)
    # The pack: catalog-instantiated possessions (food, drink, tools,
    # wearables) — already full Things with affordances + effects. Stateful
    # storage, folded in so eat/drink/wear/use can reach them.
    for prov in (getattr(cs, "pack", None) or []):
        if getattr(prov, "holder", None) is None:
            prov.holder = holder
        if prov.carry.location in ("", IN_WORLD):
            prov.carry.location = CARRIED
        things.append(prov)
    cs.things = things


def default_wield(cs) -> None:
    """Put a sensible primary weapon in hand at scene start so a character is
    not empty-handed. Picks the highest-average-damage weapon that fits the
    hand budget (mirrors the resolver's default). No-op if already wielding or
    if the character only has natural weapons (always available)."""
    if getattr(cs, "wielded", None):
        return
    total = hands_total(cs)
    candidates = [
        w for w in (getattr(cs, "weapons", None) or [])
        if 0 < weapon_hands(w) <= total
    ]
    if not candidates:
        return
    from engine.combat_resolver import _avg_damage
    best = max(candidates, key=lambda w: _avg_damage(w.damage_dice))
    cs.wielded = [best.id]
