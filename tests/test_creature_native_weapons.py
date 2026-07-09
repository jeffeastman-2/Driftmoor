from pathlib import Path

from engine.md_loader import configure_from_md


def test_shadowbeast_native_weapon_synthesizes_from_identity():
    config = configure_from_md(Path("scenes/fey_glade.md"))
    # Creatures are loaded from place file and merged into characters
    session = config.characters.get("shadowbeast_1")
    assert session is not None, "shadowbeast_1 should be loaded from place file"
    
    weapons = getattr(session, "weapons", []) or []

    assert any(w.id == "shadowbeast_claw" for w in weapons)
    claw = next(w for w in weapons if w.id == "shadowbeast_claw")
    assert claw.attack_bonus == 4
    assert claw.damage_dice == "1d6"
    assert claw.damage_type == "slashing"
    assert "natural" in claw.properties


def test_giant_spider_native_weapon_synthesizes_from_identity():
    config = configure_from_md(Path("scenes/echoing_caverns.md"))
    # Creatures are loaded from place file and merged into characters
    session = config.characters.get("giant_spider")
    assert session is not None, "giant_spider should be loaded from place file"
    
    weapons = getattr(session, "weapons", []) or []

    assert any(w.id == "spider_bite" for w in weapons)
    bite = next(w for w in weapons if w.id == "spider_bite")
    assert bite.attack_bonus == 5
    assert bite.damage_dice == "1d8+3"
    assert bite.damage_type == "piercing"
    assert "natural" in bite.properties
