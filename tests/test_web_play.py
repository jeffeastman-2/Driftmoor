"""Tests for web_play helpers — the browser play app's inventory readout.

These cover the pure helpers (icon mapping, possession split from the live
character); the interactive LLM play itself is validated by running the app.
"""
from types import SimpleNamespace as NS

import web_play


def _weapon(wid, name):
    return NS(id=wid, name=name)


def _cs(weapons=(), wielded=(), held_items=(), inventory=(), equipment=()):
    return NS(weapons=list(weapons), wielded=list(wielded),
              held_items=list(held_items),
              character=NS(inventory=list(inventory), equipment=list(equipment)))


def test_item_icon_keyword_and_fallback():
    assert web_play._item_icon("Snapped torch") == "🔥"
    assert web_play._item_icon("Rapier") == "🗡️"
    assert web_play._item_icon("Light crossbow") == "🏹"
    assert web_play._item_icon("Glowing orb") == "📦"  # no keyword -> fallback


def test_inventory_none_character_is_empty():
    assert web_play._player_inventory(None, {}) == {"hand": [], "pack": []}


def test_inventory_weapons_split_by_wielded():
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger"),
                      _weapon("light_crossbow", "Light Crossbow")],
             wielded=["rapier"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]
    assert {c["label"] for c in inv["pack"]} == {"Dagger", "Light Crossbow"}


def test_inventory_unwielded_weapons_all_in_pack():
    # Turn 0: nothing wielded yet -> the whole kit shows in the pack.
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger")])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == []
    assert {c["label"] for c in inv["pack"]} == {"Rapier", "Dagger"}


def test_inventory_held_torch_in_hand_then_stowed():
    items = {"snapped_torch": NS(label="Snapped torch")}
    # Held: torch in hand alongside the wielded rapier.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             held_items=["snapped_torch"], inventory=["snapped_torch"])
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier", "Snapped torch"}
    assert inv["pack"] == []
    # Stowed: torch moves to the pack (still carried, not in hand).
    cs.held_items = []
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier"}
    assert {c["label"] for c in inv["pack"]} == {"Snapped torch"}


def test_inventory_picked_up_weapon_not_double_listed():
    # A picked-up weapon lands in BOTH cs.weapons and character.inventory; it
    # must appear once (as a weapon), not twice.
    cs = _cs(weapons=[_weapon("mace", "Mace")], inventory=["mace"])
    inv = web_play._player_inventory(cs, {"mace": NS(label="Mace")})
    labels = [c["label"] for c in inv["hand"] + inv["pack"]]
    assert labels.count("Mace") == 1


def test_inventory_includes_non_weapon_equipment():
    # Character-sheet equipment (armor, tools, trinkets) shows in the pack;
    # equipment entries that just restate a weapon are de-duped, and stat
    # parentheticals are stripped.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             equipment=["Rapier (1d8 piercing)", "Studded leather armor",
                        "Thieves' tools", "Wooden vine-carved bracelet"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]  # wielded weapon
    pack = {c["label"] for c in inv["pack"]}
    assert pack == {"Studded leather armor", "Thieves' tools",
                    "Wooden vine-carved bracelet"}  # Rapier de-duped, no "(...)"
