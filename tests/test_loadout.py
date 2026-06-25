"""Phase 2: wielded-weapon / hand-slot model."""

from __future__ import annotations

from types import SimpleNamespace as NS

from models.weapon import Weapon
from engine.loadout import (
    weapon_hands,
    hands_used,
    hands_free,
    wielded_weapons,
    is_wielding,
    can_wield,
    default_wield,
)


def _w(wid, name, dice="1d6", props=None, **kw):
    return Weapon(id=wid, name=name, damage_dice=dice, damage_type="piercing",
                  properties=props or [], **kw)


RAPIER = _w("rapier", "Rapier", "1d8")
DAGGER = _w("dagger", "Dagger", "1d4")
GREATSWORD = _w("greatsword", "Greatsword", "2d6", props=["two_handed"])
BITE = _w("bite", "Bite", "1d8", props=["natural"])


def _cs(weapons, wielded=None, hands=2, held_items=None):
    return NS(character=NS(hands=hands), weapons=list(weapons),
              wielded=list(wielded or []), held_items=list(held_items or []))


class TestWeaponHands:
    def test_one_handed(self):
        assert weapon_hands(RAPIER) == 1

    def test_two_handed(self):
        assert weapon_hands(GREATSWORD) == 2

    def test_natural_is_free(self):
        assert weapon_hands(BITE) == 0


class TestHandBudget:
    def test_hands_used_and_free(self):
        cs = _cs([RAPIER, DAGGER], wielded=["rapier"])
        assert hands_used(cs.wielded, cs.weapons) == 1
        assert hands_free(cs) == 1

    def test_two_hander_consumes_both(self):
        cs = _cs([GREATSWORD], wielded=["greatsword"])
        assert hands_free(cs) == 0

    def test_can_wield_respects_budget(self):
        # One hand left -> can add a one-hander but not a two-hander.
        cs = _cs([RAPIER, DAGGER, GREATSWORD], wielded=["rapier"])
        assert can_wield(cs, DAGGER) is True
        assert can_wield(cs, GREATSWORD) is False

    def test_shield_two_hander_exclusion_is_implicit(self):
        # A two-hander already in both hands leaves no room for anything else —
        # the rule "can't also hold a shield" falls out of the budget.
        cs = _cs([GREATSWORD, DAGGER], wielded=["greatsword"])
        assert can_wield(cs, DAGGER) is False

    def test_natural_always_wieldable(self):
        cs = _cs([GREATSWORD, BITE], wielded=["greatsword"])  # no free hands
        assert can_wield(cs, BITE) is True


class TestWieldedWeapons:
    def test_only_wielded_plus_naturals(self):
        cs = _cs([RAPIER, DAGGER, BITE], wielded=["rapier"])
        names = {w.name for w in wielded_weapons(cs)}
        assert names == {"Rapier", "Bite"}        # dagger sheathed; bite always
        assert is_wielding(cs, RAPIER) and not is_wielding(cs, DAGGER)
        assert is_wielding(cs, BITE)              # natural


class TestDefaultWield:
    def test_picks_highest_damage_one_hander(self):
        cs = _cs([DAGGER, RAPIER])  # nothing wielded
        default_wield(cs)
        assert cs.wielded == ["rapier"]           # 1d8 > 1d4

    def test_noop_when_already_wielding(self):
        cs = _cs([DAGGER, RAPIER], wielded=["dagger"])
        default_wield(cs)
        assert cs.wielded == ["dagger"]

    def test_noop_with_only_natural_weapons(self):
        cs = _cs([BITE])
        default_wield(cs)
        assert cs.wielded == []                   # naturals need no hand

    def test_two_hander_fits_two_hand_budget(self):
        cs = _cs([GREATSWORD], hands=2)
        default_wield(cs)
        assert cs.wielded == ["greatsword"]


def _mace_item(holder=None):
    # build_item_weapon stores the enhancement in attack_bonus and folds it into
    # the dice; register_held_weapon adds the wielder's prof + ability mod.
    base = _w("mace_plus_one", "Mace +1", dice="1d6+1")
    base = base.__class__(**{**base.__dict__, "attack_bonus": 1})
    return NS(id="mace_plus_one", weapon=base, holder=holder)


def _char(strength=10, dexterity=10, level=1, cid="gil"):
    return NS(character=NS(id=cid, strength=strength, dexterity=dexterity,
                           level=level, hands=2),
              weapons=[], wielded=[])


class TestHeldWeapons:
    def test_register_computes_prof_plus_mod_plus_enhancement(self):
        from engine.loadout import register_held_weapon
        cs = _char(strength=10, level=1)          # prof 2, STR mod 0
        w = register_held_weapon(cs, _mace_item())
        assert w.attack_bonus == 3                 # 2 + 0 + 1(enh)
        assert w.damage_dice == "1d6+1"
        assert w in cs.weapons

    def test_register_scales_with_level_and_strength(self):
        from engine.loadout import register_held_weapon
        cs = _char(strength=16, level=5)           # prof 3, STR mod +3
        w = register_held_weapon(cs, _mace_item())
        assert w.attack_bonus == 7                 # 3 + 3 + 1

    def test_register_is_idempotent(self):
        from engine.loadout import register_held_weapon
        cs = _char()
        register_held_weapon(cs, _mace_item())
        register_held_weapon(cs, _mace_item())
        assert sum(1 for x in cs.weapons if x.id == "mace_plus_one") == 1

    def test_register_noop_without_weapon_spec(self):
        from engine.loadout import register_held_weapon
        cs = _char()
        assert register_held_weapon(cs, NS(id="rock", weapon=None)) is None
        assert cs.weapons == []

    def test_sync_registers_only_held_items(self):
        from engine.loadout import sync_held_weapons
        cs = _char(cid="gil")
        items = {
            "mine": _mace_item(holder="gil"),
            "theirs": _mace_item(holder="thorgrim"),
        }
        items["theirs"].id = "other_mace"
        items["theirs"].weapon = items["theirs"].weapon.__class__(
            **{**items["theirs"].weapon.__dict__, "id": "other_mace"})
        sync_held_weapons(cs, items)
        ids = {w.id for w in cs.weapons}
        assert "mace_plus_one" in ids and "other_mace" not in ids


class TestHeldItems:
    """Non-weapon items held in-hand (e.g. a torch): they occupy a hand like a
    weapon, can be stowed to the pack (freeing the hand), and round-trip."""

    def test_hold_item_takes_a_hand(self):
        from engine.loadout import hold_item, held_items, hands_free
        cs = _cs([RAPIER], wielded=["rapier"])  # 1 hand free
        assert hold_item(cs, "snapped_torch") is True
        assert held_items(cs) == ["snapped_torch"]
        assert hands_free(cs) == 0

    def test_hold_item_is_idempotent(self):
        from engine.loadout import hold_item, held_items
        cs = _cs([], held_items=["torch"])
        assert hold_item(cs, "torch") is True
        assert held_items(cs) == ["torch"]

    def test_hold_item_auto_sheathes_a_weapon_when_full(self):
        from engine.loadout import hold_item, held_items
        cs = _cs([RAPIER, DAGGER], wielded=["rapier", "dagger"])  # 0 free
        log: list[str] = []
        assert hold_item(cs, "torch", log) is True
        # The lower-value weapon (dagger) is sheathed to free a hand.
        assert "dagger" not in cs.wielded and "rapier" in cs.wielded
        assert any("sheathes" in line for line in log)
        assert held_items(cs) == ["torch"]

    def test_hold_item_sheathes_two_hander_to_free_a_hand(self):
        from engine.loadout import hold_item, held_items
        cs = _cs([GREATSWORD], wielded=["greatsword"])  # 0 free
        # The greatsword is the only weapon; sheathing it frees both hands, so
        # the torch can be taken in one hand.
        assert hold_item(cs, "torch") is True
        assert held_items(cs) == ["torch"]
        assert cs.wielded == []

    def test_stow_item_frees_the_hand_but_keeps_it(self):
        from engine.loadout import stow_item, held_items, hands_free
        cs = _cs([RAPIER], wielded=["rapier"], held_items=["torch"])
        assert hands_free(cs) == 0
        assert stow_item(cs, "torch") is True
        assert held_items(cs) == []
        assert hands_free(cs) == 1

    def test_stow_item_noop_when_not_held(self):
        from engine.loadout import stow_item
        cs = _cs([RAPIER], wielded=["rapier"])
        assert stow_item(cs, "torch") is False

    def test_held_item_counts_against_hands_free(self):
        from engine.loadout import hands_free
        cs = _cs([RAPIER], wielded=["rapier"], held_items=["torch"])
        assert hands_free(cs) == 0
