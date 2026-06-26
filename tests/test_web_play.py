"""Tests for web_play helpers — the browser play app's inventory readout.

These cover the pure helpers (icon mapping, possession split from the live
character); the interactive LLM play itself is validated by running the app.
"""
from types import SimpleNamespace as NS

import web_play


def _weapon(wid, name):
    return NS(id=wid, name=name)


def _cs(weapons=(), wielded=(), held_items=(), inventory=(), equipment=(), armor=None):
    return NS(weapons=list(weapons), wielded=list(wielded),
              held_items=list(held_items), armor=armor,
              character=NS(inventory=list(inventory), equipment=list(equipment)))


def test_highlight_names_collects_player_and_monster_names():
    chars = {
        "seraphina": NS(character=NS(name="Seraphina Duskwhisper")),
        "amara": NS(character=NS(name="Sister Amara Solbright")),
        "giant_spider": NS(character=NS(name="Giant Spider")),
    }
    names = web_play._highlight_names(chars)
    assert "seraphina" in names and "amara" in names      # cids
    assert "giant spider" in names and "spider" in names  # monster, full + token
    assert "sister" not in names                          # title dropped
    assert all(n == n.lower() for n in names)             # lower-cased
    assert names == sorted(names, key=len, reverse=True)  # longest-first


def test_item_icon_keyword_and_fallback():
    assert web_play._item_icon("Snapped torch") == "🔥"
    assert web_play._item_icon("Rapier") == "🗡️"
    assert web_play._item_icon("Light crossbow") == "🏹"
    assert web_play._item_icon("Glowing orb") == "📦"  # no keyword -> fallback


def test_inventory_none_character_is_empty():
    assert web_play._player_inventory(None, {}) == {"hand": [], "worn": [], "carried": []}


def test_inventory_weapons_split_by_wielded():
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger"),
                      _weapon("light_crossbow", "Light Crossbow")],
             wielded=["rapier"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]
    assert {c["label"] for c in inv["carried"]} == {"Dagger", "Light Crossbow"}


def test_inventory_unwielded_weapons_all_carried():
    # Turn 0: nothing wielded yet -> the whole weapon kit shows as carried.
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger")])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == []
    assert {c["label"] for c in inv["carried"]} == {"Rapier", "Dagger"}


def test_inventory_held_torch_in_hand_then_carried():
    items = {"snapped_torch": NS(label="Snapped torch")}
    # Held: torch in hand alongside the wielded rapier.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             held_items=["snapped_torch"], inventory=["snapped_torch"])
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier", "Snapped torch"}
    assert inv["carried"] == []
    # Stowed: torch moves to carried (still on the character, not in hand).
    cs.held_items = []
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier"}
    assert {c["label"] for c in inv["carried"]} == {"Snapped torch"}


def test_inventory_picked_up_weapon_not_double_listed():
    # A picked-up weapon lands in BOTH cs.weapons and character.inventory; it
    # must appear once (as a weapon), not twice.
    cs = _cs(weapons=[_weapon("mace", "Mace")], inventory=["mace"])
    inv = web_play._player_inventory(cs, {"mace": NS(label="Mace")})
    labels = [c["label"] for c in inv["hand"] + inv["worn"] + inv["carried"]]
    assert labels.count("Mace") == 1


def test_inventory_worn_vs_carried_split():
    # Character-sheet equipment splits: armor/trinkets -> worn; tools/kits ->
    # carried. Weapon restatements de-duped, stat parentheticals stripped.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             equipment=["Rapier (1d8 piercing)", "Studded leather armor",
                        "Thieves' tools", "Wooden vine-carved bracelet"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]      # wielded
    assert {c["label"] for c in inv["worn"]} == {
        "Studded leather armor", "Wooden vine-carved bracelet"}    # armor + trinket
    assert {c["label"] for c in inv["carried"]} == {"Thieves' tools"}  # Rapier de-duped


def test_inventory_structured_armor_is_worn():
    cs = _cs(weapons=[], armor=NS(name="Chain Mail"))
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["worn"]} == {"Chain Mail"}
