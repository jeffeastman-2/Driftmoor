"""Economy pt7a: the standard item libraries stamp canonical 5e ``value_cp``.

Weapons, armor, gear, consumables, and containers each carry a market worth so a
player can sell them (the sell path bids ``value_cp * BUY_RATE``). Bespoke or
fictional ids stay unpriced (``None``).
"""
from pathlib import Path

from engine.weapon_loader import load_weapons, load_armors
from engine.consumable_loader import load_consumables, load_gear, load_containers

THINGS = Path("scenario/things")


def test_weapons_priced_from_5e():
    lib = load_weapons(THINGS / "WEAPONS.md")
    assert lib["longbow"].value_cp == 5000
    assert lib["dagger"].value_cp == 200
    assert lib["quarterstaff"].value_cp == 20
    # Improvised weapon has no market worth.
    assert lib["improvised_spear"].value_cp is None


def test_armor_priced_from_5e():
    lib = load_armors(THINGS / "ARMOR.md")
    assert lib["plate_armor"].value_cp == 150000
    assert lib["leather_armor"].value_cp == 1000
    assert lib["clothing"].value_cp == 50


def test_gear_priced_from_5e():
    lib = load_gear(THINGS / "GEAR.md")
    assert lib["shield"].value_cp == 1000
    assert lib["thieves_tools"].value_cp == 2500
    assert lib["torch"].value_cp == 1
    # A plain trinket with no fixed 5e price stays unpriced.
    assert lib["bracelet"].value_cp is None


def test_consumables_priced_from_5e():
    lib = load_consumables(THINGS / "CONSUMABLES.md")
    assert lib["rations"].value_cp == 50
    assert lib["mead"].value_cp == 20
    # Fictional herbs are unpriced.
    assert lib["moonlace"].value_cp is None


def test_containers_priced_from_5e():
    lib = load_containers(THINGS / "CONTAINERS.md")
    assert lib["explorers_pack"].value_cp == 1000
    assert lib["scholars_pack"].value_cp == 4000
    # A named personal pack is bespoke → unpriced.
    assert lib["gils_pack"].value_cp is None
