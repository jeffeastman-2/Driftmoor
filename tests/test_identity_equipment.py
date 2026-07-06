"""IDENTITY equipment parsing + resolution.

`## Equipment` is a FLAT list of catalog id references (`id[+N][: Name]`, any
order); the loader routes each id by which catalog holds it, and keeps anything
unrecognized as free-text. A legacy `## Combat Equipment` block still supplies
structured weapons/armor for un-migrated characters.
"""
from pathlib import Path
from types import SimpleNamespace as NS

from engine.consumable_loader import load_consumables, load_gear
from engine.md_loader import _apply_equipment, _parse_equip_entry, parse_identity_stats
from engine.weapon_loader import load_armors, load_weapons
from models.condition import CharacterCondition
from models.thing import TOOL, WEARABLE

FLAT = """\
## Equipment
- rapier+5
- studded_leather
- pemmican
- water
- bracelet: Wooden vine-carved bracelet
- thieves_tools
- A lucky coin
"""

LEGACY = """\
## Combat Equipment
- **weapons:** mace+3
- **armor:** chain_mail

## Equipment
- Mace (1d6 bludgeoning)
- Holy symbol
"""


def test_flat_equipment_is_a_raw_entry_list():
    s = parse_identity_stats(FLAT)
    assert s["equipment_entries"] == [
        "rapier+5", "studded_leather", "pemmican", "water",
        "bracelet: Wooden vine-carved bracelet", "thieves_tools", "A lucky coin"]


def test_legacy_combat_equipment_still_structured():
    s = parse_identity_stats(LEGACY)
    assert s.get("weapons") == "mace+3"
    assert s.get("armor") == "chain_mail"
    assert s.get("equipment_entries") == ["Mace (1d6 bludgeoning)", "Holy symbol"]


def test_parse_equip_entry_forms():
    assert _parse_equip_entry("rapier+5") == ("rapier", "+5", "")
    assert _parse_equip_entry("studded_leather") == ("studded_leather", "", "")
    assert _parse_equip_entry("bracelet: Wooden vine-carved bracelet") == (
        "bracelet", "", "Wooden vine-carved bracelet")
    assert _parse_equip_entry("Holy symbol") is None            # prose -> free-text
    assert _parse_equip_entry("Mace (1d6 bludgeoning)") is None


def _libs():
    return (load_weapons(Path("scenario/things/WEAPONS.md")),
            load_armors(Path("scenario/things/ARMOR.md")),
            load_consumables(Path("scenario/things/CONSUMABLES.md")),
            load_gear(Path("scenario/things/GEAR.md")))


def _session():
    return NS(character=NS(id="gil", name="Gil", equipment=[]),
              condition=CharacterCondition(character_id="gil", character_name="Gil"),
              weapons=[], armor=None, pack=[])


def test_apply_equipment_routes_flat_entries_by_catalog():
    wl, al, cl, gl = _libs()
    s = _session()
    id_stats = {"equipment_entries": [
        "rapier+5", "studded_leather", "pemmican", "water",
        "bracelet: Wooden vine-carved bracelet", "thieves_tools", "A lucky coin"]}
    _apply_equipment(s, id_stats, {}, wl, al, cl, gl)

    assert [w.id for w in s.weapons] == ["rapier"]     # weapon -> cs.weapons
    assert s.weapons[0].attack_bonus == 5              # +N override honored
    assert s.armor.id == "studded_leather"             # armor -> cs.armor (structured)

    pack = {t.id: t for t in s.pack}                   # consumables + gear -> pack
    assert {"pemmican", "water", "bracelet", "thieves_tools"} <= set(pack)
    assert pack["bracelet"].label == "Wooden vine-carved bracelet"   # name override
    assert WEARABLE in pack["bracelet"].affordances
    assert TOOL in pack["thieves_tools"].affordances

    assert s.character.equipment == ["A lucky coin"]   # unrecognized -> free-text
    assert s.condition.extensions["hunger"] == 0.5     # carries food/drink -> seeded
    assert s.condition.extensions["thirst"] == 0.5


def test_weapon_honors_name_and_bonus_override():
    wl, al, cl, gl = _libs()
    s = _session()
    _apply_equipment(s, {"equipment_entries": ["rapier+5: Silver handled rapier"]},
                     {}, wl, al, cl, gl)
    w = s.weapons[0]
    assert w.id == "rapier"                 # catalog template
    assert w.name == "Silver handled rapier"  # : Name override applied
    assert w.attack_bonus == 5                # +N override applied
    assert w.damage_dice == "1d8"             # base stats still from the catalog
