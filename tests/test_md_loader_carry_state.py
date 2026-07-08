from types import SimpleNamespace as NS

from engine.md_loader import _apply_scene_carry_overrides
from models.thing import CarryState, CARRIED, WORN
from models.weapon import Weapon


def _weapon(wid: str, name: str, dmg: str = "1d4"):
    return Weapon(id=wid, name=name, damage_dice=dmg, damage_type="piercing")


def _thing(tid: str, label: str):
    return NS(id=tid, label=label, carry=CarryState(location=CARRIED))


def _session():
    return NS(
        character=NS(hands=2),
        weapons=[_weapon("longsword", "Longsword", "1d8"), _weapon("dagger", "Dagger")],
        wielded=[],
        held_items=[],
        pack=[_thing("snapped_torch", "Snapped torch"), _thing("mead", "Mug of ale")],
    )


def test_in_hand_draws_weapon_and_holds_pack_item():
    cs = _session()
    _apply_scene_carry_overrides(cs, {"in_hand": "dagger, snapped_torch"})
    assert "dagger" in cs.wielded
    assert "snapped_torch" in cs.held_items


def test_alias_keys_and_label_match_work():
    cs = _session()
    _apply_scene_carry_overrides(cs, {"held_items": "mug of ale"})
    assert "mead" in cs.held_items


def test_worn_marks_pack_item_and_removes_from_hand():
    cs = _session()
    _apply_scene_carry_overrides(cs, {"in_hand": "snapped_torch", "worn": "snapped_torch"})
    torch = next(t for t in cs.pack if t.id == "snapped_torch")
    assert torch.carry.location == WORN
    assert "snapped_torch" not in cs.held_items
