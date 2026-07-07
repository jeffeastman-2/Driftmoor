"""Consumables: catalog loading, effect-spec parsing, and eating a provision.

Covers engine.consumable_loader (parse_effect / make_consumable /
load_consumables) and the end-to-end path a provision takes — materialized into
cs.things, found by name, classified, and consumed with its effects landing on
the character and the item leaving the pack.
"""
import copy
from pathlib import Path
from types import SimpleNamespace as NS

from engine import loadout, manipulation
from engine.consumable_loader import (
    load_consumables, load_gear, make_consumable, make_thing, parse_effect,
)
from models.condition import CharacterCondition
from models.thing import CONSUMED, DRINKABLE, EDIBLE, TOOL, WEARABLE, Effect

CATALOG = Path("scenario/things/CONSUMABLES.md")
GEAR = Path("scenario/things/GEAR.md")


# --- effect-spec parsing --------------------------------------------------

def test_parse_effect_forms():
    assert parse_effect("heal 3") == Effect(kind="heal", payload={"amount": 3})
    assert parse_effect("hunger -0.4") == Effect(kind="stat", payload={"name": "hunger", "delta": -0.4})
    assert parse_effect("dopamine +0.05") == Effect(kind="neuro", payload={"dim": "dopamine", "delta": 0.05})
    assert parse_effect("status poisoned") == Effect(kind="status", payload={"name": "poisoned"})
    assert parse_effect("") is None


def test_make_consumable_edible_vs_drinkable():
    bread = make_consumable("bread", "Bread", "eat", ["hunger -0.3"])
    ale = make_consumable("ale", "Ale", "drink", ["thirst -0.4"])
    assert EDIBLE in bread.affordances and DRINKABLE not in bread.affordances
    assert DRINKABLE in ale.affordances and EDIBLE not in ale.affordances


# --- catalog ----------------------------------------------------------------

def test_catalog_loads_expected_items():
    lib = load_consumables(CATALOG)
    assert {"pemmican", "hard_tack", "water", "mead"} <= set(lib)
    assert EDIBLE in lib["pemmican"].affordances
    assert DRINKABLE in lib["mead"].affordances
    # mead carries three effects: thirst, intoxication, a dopamine nudge.
    kinds = sorted(e.kind for e in lib["mead"].effects)
    assert kinds == ["neuro", "stat", "stat"]


# --- end to end -------------------------------------------------------------

def _cs_with_provisions(*ids):
    lib = load_consumables(CATALOG)
    cs = NS(
        scene_handle="Gil",
        character=NS(id="gil", name="Gil", hp=20, current_hp=15, conditions=[]),
        condition=CharacterCondition(character_id="gil", character_name="Gil"),
        weapons=[], wielded=[], held_items=[], armor=None, things=[],
        pack=[copy.deepcopy(lib[i]) for i in ids],
    )
    cs.condition.extensions["hunger"] = 0.5
    cs.condition.extensions["thirst"] = 0.5
    loadout.materialize_things(cs)
    return cs


def test_provisions_are_reachable_as_things():
    cs = _cs_with_provisions("pemmican", "water")
    assert manipulation.find_possessed_thing(cs, "eat the pemmican").id == "pemmican"
    assert manipulation.find_possessed_thing(cs, "drink the water").id == "water"


def test_eat_pemmican_reduces_hunger_heals_and_leaves_pack():
    cs = _cs_with_provisions("pemmican")
    pemmican = manipulation.find_possessed_thing(cs, "eat the pemmican")
    assert manipulation.classify_verb("eat the pemmican", pemmican) == "eat"
    res = manipulation.apply_manipulation(
        cs, "eat", pemmican, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)
    assert res.applied
    assert cs.condition.extensions["hunger"] == 0.1    # 0.5 - 0.4
    assert cs.character.current_hp == 17               # +2 heal
    assert cs.pack == []                                # used up, out of the pack


def test_drink_mead_reduces_thirst_and_intoxicates():
    cs = _cs_with_provisions("mead")
    mead = manipulation.find_possessed_thing(cs, "drink the mead")
    assert manipulation.classify_verb("drink the mead", mead) == "drink"
    manipulation.apply_manipulation(
        cs, "drink", mead, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)
    assert cs.condition.extensions["thirst"] == 0.2    # 0.5 - 0.3
    assert cs.condition.extensions["intoxication"] == 0.3
    assert cs.condition.state.dopamine > 0.5


def test_cannot_drink_the_pemmican_or_eat_the_mead():
    cs = _cs_with_provisions("pemmican", "mead")
    assert manipulation.classify_verb("drink the pemmican",
                                      manipulation.find_possessed_thing(cs, "the pemmican")) is None
    assert manipulation.classify_verb("eat the mead",
                                      manipulation.find_possessed_thing(cs, "the mead")) is None


# --- gear catalog (tools / wearables) + id:name instantiation --------------

def test_make_thing_tool_and_wearable_affordances():
    assert TOOL in make_thing("t", "T", "tool", []).affordances
    assert WEARABLE in make_thing("w", "W", "wearable", []).affordances


def test_gear_catalog_loads_with_kinds():
    lib = load_gear(GEAR)
    assert WEARABLE in lib["bracelet"].affordances
    assert TOOL in lib["thieves_tools"].affordances


def test_parse_effect_ac():
    assert parse_effect("ac +2") == Effect(kind="ac", payload={"bonus": 2})


def test_shield_is_holdable_with_an_ac_effect_not_worn():
    from models.thing import HOLDABLE, WEARABLE
    sh = make_thing("shield", "Shield", "shield", ["ac +2"])
    assert HOLDABLE in sh.affordances and WEARABLE not in sh.affordances
    assert any(e.kind == "ac" and e.payload["bonus"] == 2 for e in sh.effects)


def test_make_thing_multi_kind():
    from models.thing import CONTAINER, WEARABLE
    t = make_thing("explorers_pack", "Explorer's Pack", "wearable, container", [])
    assert {WEARABLE, CONTAINER} <= t.affordances


def test_parse_contents():
    from engine.consumable_loader import parse_contents
    assert parse_contents("torch x10, rope, rations×5") == [
        ("torch", 10), ("rope", 1), ("rations", 5)]
    assert parse_contents("") == []


def test_containers_catalog_has_capacity_and_contents():
    from engine.consumable_loader import load_containers
    from models.thing import CONTAINER
    lib = load_containers(Path("scenario/things/CONTAINERS.md"))
    pack = lib["explorers_pack"]
    assert CONTAINER in pack.affordances
    assert pack.capacity == "30 lb"
    assert ("torch", 10) in pack.contents
