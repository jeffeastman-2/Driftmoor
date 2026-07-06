"""Tests for the unified affordance-gated kit-manipulation dispatch (Phase 3).

These exercise engine.manipulation over a character's materialized kit Things —
resolving a named weapon/armor, classifying the verb from its affordances, and
applying draw / sheathe / drop. This replaces the old kit-weapon stopgaps
(_find_carried_weapon / _drop_carried_weapon).
"""
from types import SimpleNamespace as NS

from engine import loadout, manipulation
from models.thing import HOLDABLE, IN_HAND, WEAPON, WEARABLE
from models.weapon import Armor, Weapon


def _cs(wielded=("rapier",)):
    rapier = Weapon(id="rapier", name="Rapier", damage_dice="1d8", damage_type="piercing")
    dagger = Weapon(id="dagger", name="Dagger", damage_dice="1d4", damage_type="piercing")
    armor = Armor(id="studded_leather", name="Studded Leather", ac_base=12)
    cs = NS(scene_handle="Gil", episodic_memory=[],
            character=NS(id="gil", name="Gil", inventory=[], hands=2),
            weapons=[rapier, dagger], wielded=list(wielded), held_items=[],
            armor=armor, things=[])
    loadout.materialize_things(cs)
    return cs


def test_materialize_things_tags_kit_with_affordances_and_carry():
    cs = _cs(wielded=["rapier"])
    by_id = {t.id: t for t in cs.things}
    assert {HOLDABLE, WEAPON} <= by_id["rapier"].affordances
    assert by_id["rapier"].carry.location == IN_HAND      # wielded -> in hand
    assert by_id["dagger"].carry.location != IN_HAND      # sheathed -> carried
    assert WEARABLE in by_id["studded_leather"].affordances


def test_materialize_honors_restored_wielded_state():
    # Resume restores cs.wielded before run_session's setup loop calls
    # materialize_things, so a non-default wielded set (dagger, when rapier is
    # the default_wield pick) is reflected in the Thing carry-state — carry-state
    # survives a checkpoint via the existing wielded persistence.
    cs = _cs(wielded=["dagger"])          # as if restored from a checkpoint
    by_id = {t.id: t for t in cs.things}
    assert by_id["dagger"].carry.location == IN_HAND
    assert by_id["rapier"].carry.location != IN_HAND


def test_find_possessed_thing_by_name():
    cs = _cs()
    assert manipulation.find_possessed_thing(cs, "I drop my rapier").id == "rapier"
    assert manipulation.find_possessed_thing(cs, "I move north") is None


def test_find_possessed_thing_by_category_tag():
    # "draw my sword" grounds to the rapier via its `sword` tag; nouns attend to
    # category tags. An axe request must NOT match a sword.
    from types import SimpleNamespace as NS
    from models.weapon import Weapon
    rapier = Weapon(id="rapier", name="Rapier", damage_dice="1d8",
                    damage_type="piercing", tags=["martial", "sword", "blade"])
    cs = NS(scene_handle="Gil", character=NS(id="gil", name="Gil", hands=2),
            weapons=[rapier], wielded=[], held_items=[], armor=None, things=[], pack=[])
    loadout.materialize_things(cs)
    assert manipulation.find_possessed_thing(cs, "draw my sword").id == "rapier"
    assert manipulation.find_possessed_thing(cs, "wield my blade").id == "rapier"
    assert manipulation.find_possessed_thing(cs, "draw my axe") is None


def test_classify_verb_from_affordances():
    cs = _cs()
    rapier = manipulation.find_possessed_thing(cs, "the rapier")
    armor = manipulation.find_possessed_thing(cs, "the studded leather")
    assert manipulation.classify_verb("drop my rapier", rapier) == "drop"
    assert manipulation.classify_verb("sheathe the rapier", rapier) == "sheathe"
    assert manipulation.classify_verb("unsheathe the rapier", rapier) == "draw"
    assert manipulation.classify_verb("get my rapier", rapier) == "draw"
    assert manipulation.classify_verb("remove the studded leather", armor) == "remove"


def test_draw_a_sheathed_weapon_wields_it():
    cs = _cs(wielded=["rapier"])          # dagger starts sheathed
    dagger = manipulation.find_possessed_thing(cs, "the dagger")
    res = manipulation.apply_manipulation(
        cs, "draw", dagger, items={}, actor_pos=(0.0, 0.0, "Z"),
        actor_zone="Z", character_id="gil", game_time=None, turn_num=1)
    assert res.applied and "dagger" in cs.wielded


def test_sheathe_a_wielded_weapon_unhands_it():
    cs = _cs(wielded=["rapier"])
    rapier = manipulation.find_possessed_thing(cs, "the rapier")
    res = manipulation.apply_manipulation(
        cs, "sheathe", rapier, items={}, actor_pos=(0.0, 0.0, "Z"),
        actor_zone="Z", character_id="gil", game_time=None, turn_num=1)
    assert res.applied and "rapier" not in cs.wielded


def test_drop_unhands_removes_from_kit_and_materializes_loose_thing():
    cs = _cs(wielded=["rapier"])
    rapier = manipulation.find_possessed_thing(cs, "the rapier")
    items: dict = {}
    res = manipulation.apply_manipulation(
        cs, "drop", rapier, items=items, actor_pos=(10.0, 20.0, "ENTRY CHAMBER"),
        actor_zone="ENTRY CHAMBER", character_id="gil", game_time=None, turn_num=1)
    assert res.applied
    assert "rapier" not in cs.wielded                       # out of hand
    assert all(w.id != "rapier" for w in cs.weapons)        # out of the kit
    it = items["rapier"]                                    # loose, re-pickable
    assert it.holder is None and it.pickable
    assert (it.position.x, it.position.y) == (10.0, 20.0) and it.zone == "ENTRY CHAMBER"
    assert HOLDABLE in it.affordances                       # grounding-ready
    assert res.memory and res.events                        # narration side-effects
