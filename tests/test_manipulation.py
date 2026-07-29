"""Tests for the unified affordance-gated kit-manipulation dispatch (Phase 3).

These exercise engine.manipulation over a character's materialized kit Things —
resolving a named weapon/armor, classifying the verb from its affordances, and
applying draw / sheathe / drop. This replaces the old kit-weapon stopgaps
(_find_carried_weapon / _drop_carried_weapon).
"""
from types import SimpleNamespace as NS

from engine import loadout, manipulation
from models.thing import CARRIED, HOLDABLE, IN_HAND, Thing, WEAPON, WEARABLE, WORN
from models.weapon import Armor, Weapon


def _cs(wielded=("rapier",)):
    rapier = Weapon(id="rapier", name="Rapier", damage_dice="1d8", damage_type="piercing")
    dagger = Weapon(id="dagger", name="Dagger", damage_dice="1d4", damage_type="piercing")
    armor = Armor(id="studded_leather", name="Studded Leather", ac_base=12)
    cs = NS(scene_handle="Gil", episodic_memory=[],
            character=NS(id="gil", name="Gil", inventory=[], hands=2),
            weapons=[rapier, dagger], wielded=list(wielded), held_items=[],
            armor=armor, things=[], pack=[])
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


def test_find_structured_armor_by_generic_armor_name():
    cs = _cs()
    thing = manipulation.find_possessed_thing(cs, "remove my armor")
    assert thing is not None
    assert thing.id == "studded_leather"


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


def test_wear_sets_pack_thing_to_worn_and_frees_hand():
    from models.thing import Thing, CarryState, derive_affordances

    cs = _cs(wielded=[])
    bracelet = Thing(id="bracelet", label="Wooden bracelet", pickable=True)
    bracelet.affordances.add(WEARABLE)
    bracelet.carry = CarryState(location=CARRIED)
    derive_affordances(bracelet)
    cs.pack = [bracelet]
    cs.held_items = ["bracelet"]
    loadout.materialize_things(cs)

    thing = manipulation.find_possessed_thing(cs, "wear the bracelet")
    assert thing is not None
    assert manipulation.classify_verb("wear the bracelet", thing) == "wear"
    res = manipulation.apply_manipulation(
        cs, "wear", thing, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)

    assert res.applied
    assert bracelet.carry.location == WORN
    assert "bracelet" not in cs.held_items


def test_remove_sets_pack_thing_back_to_carried():
    from models.thing import Thing, CarryState, derive_affordances

    cs = _cs(wielded=[])
    bracelet = Thing(id="bracelet", label="Wooden bracelet", pickable=True)
    bracelet.affordances.add(WEARABLE)
    bracelet.carry = CarryState(location=WORN)
    derive_affordances(bracelet)
    cs.pack = [bracelet]
    loadout.materialize_things(cs)

    thing = manipulation.find_possessed_thing(cs, "remove the bracelet")
    assert thing is not None
    assert manipulation.classify_verb("remove the bracelet", thing) == "remove"
    res = manipulation.apply_manipulation(
        cs, "remove", thing, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)

    assert res.applied
    assert bracelet.carry.location == CARRIED


def test_remove_structured_armor_moves_it_to_pack_and_drops_ac():
    cs = _cs(wielded=[])
    cs.character.dexterity = 14
    cs.character.natural_ac = 10
    cs.character.ac = loadout.armor_class(cs.character, cs.armor, cs.pack)

    armor = manipulation.find_possessed_thing(cs, "remove my leather")
    assert armor is not None
    res = manipulation.apply_manipulation(
        cs, "remove", armor, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)

    assert res.applied
    assert cs.armor is None
    assert any(getattr(t, "id", "") == "studded_leather" for t in cs.pack)
    assert cs.character.ac == 12


def test_wear_removed_structured_armor_restores_it_and_ac():
    cs = _cs(wielded=[])
    cs.character.dexterity = 14
    cs.character.natural_ac = 10
    cs.character.ac = loadout.armor_class(cs.character, cs.armor, cs.pack)

    armor = manipulation.find_possessed_thing(cs, "remove my armor")
    manipulation.apply_manipulation(
        cs, "remove", armor, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)
    loadout.materialize_things(cs)

    packed_armor = manipulation.find_possessed_thing(cs, "wear my armor")
    assert packed_armor is not None
    res = manipulation.apply_manipulation(
        cs, "wear", packed_armor, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=2)

    assert res.applied
    assert cs.armor is not None
    assert all(getattr(t, "id", "") != "studded_leather" for t in cs.pack)
    assert cs.character.ac == 14


def test_hold_pack_item_puts_it_in_hand():
    cs = _cs(wielded=[])
    pack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    pack.affordances.update({HOLDABLE, WEARABLE})
    cs.pack = [pack]
    loadout.materialize_things(cs)

    thing = manipulation.find_possessed_thing(cs, "get my backpack")
    assert thing is not None
    assert manipulation.classify_verb("get my backpack", thing) == "hold"
    res = manipulation.apply_manipulation(
        cs, "hold", thing, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)

    assert res.applied
    assert "gils_pack" in cs.held_items


def test_drop_pack_item_moves_it_to_scene_items():
    cs = _cs(wielded=[])
    pack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    pack.affordances.update({HOLDABLE, WEARABLE})
    cs.pack = [pack]
    cs.held_items = ["gils_pack"]
    loadout.materialize_things(cs)
    items: dict = {}

    thing = manipulation.find_possessed_thing(cs, "drop my backpack")
    assert thing is not None
    assert manipulation.classify_verb("drop my backpack", thing) == "drop"
    res = manipulation.apply_manipulation(
        cs, "drop", thing, items=items, actor_pos=(10.0, 20.0, "ENTRY CHAMBER"),
        actor_zone="ENTRY CHAMBER", character_id="gil", game_time=None, turn_num=1)

    assert res.applied
    assert "gils_pack" not in cs.held_items
    assert pack not in cs.pack
    it = items["gils_pack"]
    assert it.holder is None
    assert (it.position.x, it.position.y) == (10.0, 20.0)
    assert it.zone == "ENTRY CHAMBER"


def test_container_child_does_not_ground_when_parent_not_held():
    cs = _cs(wielded=[])
    pack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    pack.affordances.update({HOLDABLE, WEARABLE})
    waterskin = Thing(id="water", label="Water", pickable=True)
    waterskin.parent_container_id = "gils_pack"
    cs.pack = [pack, waterskin]
    loadout.materialize_things(cs)

    assert manipulation.find_possessed_thing(cs, "drink the water") is None


def test_container_child_grounds_when_parent_held():
    cs = _cs(wielded=[])
    pack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    pack.affordances.update({HOLDABLE, WEARABLE})
    waterskin = Thing(id="water", label="Water", pickable=True)
    waterskin.parent_container_id = "gils_pack"
    cs.pack = [pack, waterskin]
    cs.held_items = ["gils_pack"]
    loadout.materialize_things(cs)

    thing = manipulation.find_possessed_thing(cs, "drink the water")
    assert thing is not None and thing.id == "water"


def test_apply_manipulation_refuses_inaccessible_container_child():
    from models.thing import CarryState, DRINKABLE

    cs = _cs(wielded=[])
    pack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    pack.affordances.update({HOLDABLE, WEARABLE})
    waterskin = Thing(id="water", label="Water", pickable=True)
    waterskin.parent_container_id = "gils_pack"
    waterskin.affordances.add(DRINKABLE)
    waterskin.carry = CarryState(location=CARRIED)
    cs.pack = [pack, waterskin]
    loadout.materialize_things(cs)

    res = manipulation.apply_manipulation(
        cs, "drink", waterskin, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)

    assert not res.applied
    assert waterskin in cs.pack


def test_find_possessed_scene_thing_finds_held_scene_item():
    cs = _cs(wielded=[])
    cs.character.inventory = ["discarded_pack"]
    cs.held_items = ["discarded_pack"]
    scene_pack = Thing(id="discarded_pack", label="Discarded pack", pickable=True)
    scene_pack.holder = "gil"
    items = {"discarded_pack": scene_pack}

    thing = manipulation.find_possessed_scene_thing(
        cs, "wear the backpack", items, "discarded pack"
    )
    assert thing is not None
    assert thing.id == "discarded_pack"


def test_find_consumed_scene_thing_explains_repeat_use():
    from models.thing import CarryState, CONSUMED

    cs = _cs(wielded=[])
    ale = Thing(id="ale_i1", name="Driftmoor Ale", holder="gil")
    ale.carry = CarryState(location=CONSUMED)
    found = manipulation.find_consumed_scene_thing(
        cs, "I drink the ale", {"ale_i1": ale})
    assert found is ale


def test_backpack_does_not_match_old_pouch_container():
    from models.thing import CarryState, derive_affordances

    cs = _cs(wielded=[])
    pouch = Thing(id="gils_pouch", label="Old leather pouch", pickable=True)
    pouch.carry = CarryState(location=CARRIED)
    derive_affordances(pouch)
    backpack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    backpack.carry = CarryState(location=CARRIED)
    backpack.affordances.update({HOLDABLE, WEARABLE})
    cs.pack = [pouch, backpack]
    loadout.materialize_things(cs)

    thing = manipulation.find_possessed_thing(cs, "wear the backpack")
    assert thing is not None
    assert thing.id == "gils_pack"


def test_carry_backpack_classifies_as_hold():
    from models.thing import CarryState, derive_affordances

    backpack = Thing(id="gils_pack", label="Gil's Pack", pickable=True)
    backpack.carry = CarryState(location=CARRIED)
    backpack.affordances.update({HOLDABLE, WEARABLE})
    derive_affordances(backpack)

    assert manipulation.classify_verb("I carry the backpack", backpack) == "hold"


def test_classify_wear_for_pack_like_scene_item_without_wearable_tag():
    from models.thing import CarryState, derive_affordances

    pack = Thing(id="discarded_pack", label="Discarded pack", pickable=True)
    pack.carry = CarryState(location=IN_HAND)
    derive_affordances(pack)  # holdable only

    assert manipulation.classify_verb("wear the backpack", pack) == "wear"
