"""Phase 6: character-borne effect application.

Eating a consumable destroys the vehicle and lands its Effect(s) on the eater —
a heal on HP, a neurochemical nudge on the condition dims, a satiety bump in the
condition's `extensions` bucket, a status on the conditions list. The headline
property: this is source-agnostic — an arcane potion and a mundane loaf run the
SAME pipe, differing only by Effect.source ("magical" is a flavor tag).
"""
from types import SimpleNamespace as NS

from engine import effects, manipulation
from models.condition import CharacterCondition
from models.thing import CONSUMED, Effect, Interaction, Thing, derive_affordances


def _cs():
    return NS(
        scene_handle="Gil",
        character=NS(id="gil", name="Gil", hp=20, current_hp=10, conditions=[]),
        condition=CharacterCondition(character_id="gil", character_name="Gil"),
        weapons=[], wielded=[], held_items=[], armor=None, things=[],
    )


def _consumable(eid, label, effects_list):
    t = Thing(id=eid, label=label, pickable=True,
              interactions=[Interaction(verb="drink", response="You drink it.")])
    t.effects = list(effects_list)
    return derive_affordances(t)


def test_heal_effect_raises_hp_capped():
    cs = _cs()
    note = effects.apply_effect(cs, Effect(kind="heal", payload={"amount": 5}))
    assert cs.character.current_hp == 15 and note == "heals 5 HP"
    # Cap at max hp.
    effects.apply_effect(cs, Effect(kind="heal", payload={"amount": 100}))
    assert cs.character.current_hp == 20


def test_neuro_effect_nudges_condition_dim():
    cs = _cs()
    before = cs.condition.state.dopamine
    effects.apply_effect(cs, Effect(kind="neuro", payload={"dim": "dopamine", "delta": 0.2}))
    assert cs.condition.state.dopamine > before


def test_stat_effect_lands_in_extensions_bucket():
    cs = _cs()
    effects.apply_effect(cs, Effect(kind="stat", payload={"name": "satiety", "delta": 0.3}))
    assert cs.condition.extensions["satiety"] == 0.3


def test_status_effect_appends_condition():
    cs = _cs()
    effects.apply_effect(cs, Effect(kind="status", payload={"name": "poisoned"}))
    assert "poisoned" in cs.character.conditions


def test_thing_borne_kinds_are_not_applied_here():
    cs = _cs()
    # A weapon's damage applies through combat, not to the eater's character.
    assert effects.apply_effect(cs, Effect(kind="damage", payload={"damage_dice": "1d8"})) is None
    assert cs.character.current_hp == 10


def test_magic_is_source_agnostic_same_pipe():
    # An arcane potion and a mundane loaf, same heal Effect, heal identically.
    arcane = _cs()
    mundane = _cs()
    effects.apply_effect(arcane, Effect(kind="heal", payload={"amount": 6}, source="arcane"))
    effects.apply_effect(mundane, Effect(kind="heal", payload={"amount": 6}, source="mundane"))
    assert arcane.character.current_hp == mundane.character.current_hp == 16


def test_drink_applies_effects_and_consumes():
    cs = _cs()
    potion = _consumable("healing_potion", "Healing potion",
                         [Effect(kind="heal", payload={"amount": 8}, source="arcane")])
    res = manipulation.apply_manipulation(
        cs, "drink", potion, items={}, actor_pos=(0.0, 0.0, "Z"), actor_zone="Z",
        character_id="gil", game_time=None, turn_num=1)
    assert res.applied
    assert cs.character.current_hp == 18          # effect landed
    assert potion.carry.location == CONSUMED       # vehicle destroyed
    assert any("heals 8 HP" in line for line in res.log)


def test_eat_multi_effect_consumable():
    cs = _cs()
    # A stew: heals a little AND raises satiety AND bumps a neurochemical.
    stew = _consumable("hot_stew", "Hot stew", [
        Effect(kind="heal", payload={"amount": 2}),
        Effect(kind="stat", payload={"name": "satiety", "delta": 0.4}),
        Effect(kind="neuro", payload={"dim": "serotonin", "delta": 0.1}),
    ])
    notes = effects.apply_thing_effects(cs, stew)
    assert len(notes) == 3
    assert cs.character.current_hp == 12
    assert cs.condition.extensions["satiety"] == 0.4
    assert cs.condition.state.serotonin > 0.5
