"""Phase 4: affordance-aware grounding.

Two levels, both reading a Thing's affordances (the tabular truth projected as
the dimensions a verb attends to):

* the manipulation dispatch *gates* verbs on the affordance they require —
  "wield the potion" is refused, "drink the potion" resolves to eat;
* the LATN resolver *soft-ranks* grounded candidates toward the verb's
  affordance, breaking ties without ever losing a sole grounding.
"""
from types import SimpleNamespace as NS

from engine import manipulation
from engine.latn_resolver import _prefer_affordance
from models.thing import (
    CONSUMABLE, CONSUMED, DRINKABLE, EDIBLE, PRESSABLE, READABLE,
    Interaction, Thing, derive_affordances,
)
from models.weapon import Weapon


# --- manipulation gate: wield vs drink, eat vs drink ----------------------

def _potion():
    return derive_affordances(Thing(
        id="healing_potion", label="Healing potion", pickable=True,
        interactions=[Interaction(verb="drink", response="You drink it.")]))


def _bread():
    return derive_affordances(Thing(
        id="bread", label="Loaf of bread", pickable=True,
        interactions=[Interaction(verb="eat", response="You eat it.")]))


def test_potion_is_drinkable_bread_is_edible():
    assert {CONSUMABLE, DRINKABLE} <= _potion().affordances
    assert EDIBLE not in _potion().affordances
    assert {CONSUMABLE, EDIBLE} <= _bread().affordances
    assert DRINKABLE not in _bread().affordances
    assert "weapon" not in _potion().affordances


def test_wield_the_potion_is_refused():
    # No weapon affordance -> no manipulation verb classifies -> refused.
    assert manipulation.classify_verb("wield the potion", _potion()) is None
    assert manipulation.classify_verb("draw the potion", _potion()) is None


def test_drink_the_potion_resolves_to_drink():
    assert manipulation.classify_verb("drink the potion", _potion()) == "drink"
    assert manipulation.classify_verb("quaff the healing potion", _potion()) == "drink"


def test_eat_the_bread_resolves_to_eat():
    assert manipulation.classify_verb("eat the bread", _bread()) == "eat"


def test_state_strictness_no_drinking_solids_or_eating_liquids():
    assert manipulation.classify_verb("drink the bread", _bread()) is None   # can't drink a solid
    assert manipulation.classify_verb("eat the potion", _potion()) is None   # can't eat a liquid


def test_generic_consume_resolves_to_whichever_it_affords():
    assert manipulation.classify_verb("consume the potion", _potion()) == "drink"
    assert manipulation.classify_verb("swallow the bread", _bread()) == "eat"


def test_eat_consumes_the_thing():
    cs = NS(scene_handle="Gil", character=NS(id="gil", name="Gil"),
            weapons=[], wielded=[], held_items=[], armor=None, things=[])
    p = _potion()
    res = manipulation.apply_manipulation(
        cs, "eat", p, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)
    assert res.applied and p.carry.location == CONSUMED
    assert res.memory and res.events


def test_a_weapon_still_wields():
    w = Weapon(id="rapier", name="Rapier", damage_dice="1d8", damage_type="piercing")
    rapier = derive_affordances(Thing(id="rapier", label="Rapier", weapon=w))
    assert manipulation.classify_verb("wield the rapier", rapier) == "draw"


# --- LATN soft re-rank: verbs attend affordances --------------------------

def _cand(thing_id, affordances):
    t = Thing(id=thing_id)
    t.affordances = set(affordances)
    return NS(item=t)


def test_prefer_affordance_breaks_tie_toward_readable():
    lever = _cand("lever", {PRESSABLE})
    tome = _cand("tome", {READABLE})
    ranked = [(1.0, lever), (1.0, tome)]           # a tie
    kept = _prefer_affordance(ranked, "read")
    assert [e.item.id for _, e in kept] == ["tome"]  # readable wins


def test_prefer_affordance_never_empties_a_sole_candidate():
    rock = _cand("rock", set())                    # not readable
    kept = _prefer_affordance([(1.0, rock)], "read")
    assert [e.item.id for _, e in kept] == ["rock"]  # sole grounding untouched


def test_prefer_affordance_noop_when_verb_has_no_affordance():
    a, b = _cand("a", set()), _cand("b", set())
    assert _prefer_affordance([(1.0, a), (0.9, b)], "examine") == [(1.0, a), (0.9, b)]
