"""Tests for the Thing affordance/effect/carry-state scaffolding (Phase 2).

These cover the additive model surface — `derive_affordances` mapping a scene
Thing's parsed fields onto capability tags + effects, and the defaults of
`CarryState`/`Effect`. The unified verb dispatch that consumes them lands in a
later phase.
"""
from models.thing import (
    ARMOR,
    CARRIED,
    HOLDABLE,
    IN_WORLD,
    PRESSABLE,
    READABLE,
    WEAPON,
    WEARABLE,
    CarryState,
    Effect,
    Interaction,
    Thing,
    derive_affordances,
)
from models.weapon import Armor, Weapon


def test_thing_defaults_are_empty_and_in_world():
    t = Thing(id="rock")
    assert t.affordances == set()
    assert t.effects == []
    assert t.carry.location == IN_WORLD
    assert t.carry.hands == 0 and t.carry.slot == ""


def test_pickable_prop_is_holdable():
    t = derive_affordances(Thing(id="torch", pickable=True))
    assert HOLDABLE in t.affordances


def test_flavor_only_is_not_holdable_even_if_pickable():
    # A flavor prop can't be manipulated, so it gets no carry affordance.
    t = derive_affordances(Thing(id="mural", pickable=True, flavor_only=True))
    assert HOLDABLE not in t.affordances


def test_weapon_thing_is_holdable_weapon_with_damage_effect():
    w = Weapon(id="rapier", name="Rapier", damage_dice="1d8", damage_type="piercing")
    t = derive_affordances(Thing(id="rapier", weapon=w))
    assert {HOLDABLE, WEAPON} <= t.affordances
    dmg = [e for e in t.effects if e.kind == "damage"]
    assert len(dmg) == 1 and dmg[0].payload["damage_dice"] == "1d8"


def test_armor_thing_is_wearable_armor_with_ac_effect():
    a = Armor(id="chain_mail", name="Chain Mail", ac_base=16)
    t = derive_affordances(Thing(id="chain_mail", armor=a))
    assert {WEARABLE, ARMOR} <= t.affordances
    assert any(e.kind == "ac" and e.payload["ac_base"] == 16 for e in t.effects)


def test_interaction_derived_affordances():
    t = Thing(id="lever", interactions=[Interaction(verb="press")])
    t2 = Thing(id="tome", interactions=[Interaction(verb="read")])
    assert PRESSABLE in derive_affordances(t).affordances
    assert READABLE in derive_affordances(t2).affordances


def test_derive_is_idempotent():
    w = Weapon(id="dagger", name="Dagger", damage_dice="1d4", damage_type="piercing")
    t = Thing(id="dagger", weapon=w)
    derive_affordances(t)
    derive_affordances(t)  # second pass must not duplicate the damage effect
    assert len([e for e in t.effects if e.kind == "damage"]) == 1


def test_effect_and_carrystate_shape():
    e = Effect(kind="heal", payload={"amount": "2d4+2"})
    assert e.source == "intrinsic" and e.state == {}
    c = CarryState(location=CARRIED, hands=1, slot="")
    assert c.location == CARRIED and c.hands == 1
