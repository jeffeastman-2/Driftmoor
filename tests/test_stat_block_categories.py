from pathlib import Path

import pytest

from engine.md_loader import configure_from_md, configure_from_place_path
from models.character_loader import load_all_characters, load_all_creatures


ROOT = Path(__file__).parent.parent


def test_categorized_creature_library_loads_recursively():
    templates = load_all_creatures(ROOT / "scenario" / "creatures")
    ids = {template.id for template in templates}
    assert {"horse", "shadowbeast", "cultist", "bandit_captain"} <= ids
    assert len(ids) == len(templates)


def test_duplicate_template_ids_are_rejected(tmp_path):
    for category in ("one", "two"):
        directory = tmp_path / category / "duplicate"
        directory.mkdir(parents=True)
        (directory / "CREATURE.md").write_text(
            "Duplicate\nArmor Class: 10\nHit Points: 1\n", encoding="utf-8"
        )
    with pytest.raises(ValueError, match="Duplicate creature template id"):
        load_all_creatures(tmp_path)


def test_jareth_is_named_npc_with_cultist_statistics_globally():
    characters = load_all_characters(ROOT / "scenario" / "people")
    jareth = next(character for character in characters if character.id == "jareth")
    assert jareth.character_type == "npc"
    assert jareth.hp == 9
    assert jareth.ac == 12
    assert "ritual that used Isla" in jareth.soul_raw


def test_jareth_composes_personality_and_archetype_in_scene():
    config = configure_from_md(ROOT / "scenes" / "broken_lantern.md")
    jareth = config.characters["jareth"]
    assert jareth.character.character_type == "npc"
    assert jareth.character.hp == 9
    assert any(weapon.id == "scimitar" for weapon in jareth.weapons)
    assert "Brother Jareth" in jareth.soul


def test_named_horses_keep_individual_souls_and_generic_hooves():
    config = configure_from_place_path("places/driftmoor/stables")
    bramble = config.characters["bramble"]
    thistle = config.characters["thistle"]
    assert "BRAMBLE" in bramble.soul
    assert "THISTLE" in thistle.soul
    assert any(weapon.id == "horse_hooves" for weapon in bramble.weapons)
    assert any(weapon.id == "horse_hooves" for weapon in thistle.weapons)
