from types import SimpleNamespace as NS

from engine.md_loader import configure_from_place_path
from engine.posture import (
    apply_posture,
    posture_landmark_target,
    resolve_posture,
    settle_posture,
)
from models.character import PlayerCharacter


def _cs():
    character = PlayerCharacter(
        id="gilthaness", name="Gilthaness", race="Elf",
        character_type="player", conditions=[],
    )
    return NS(character=character, posture="standing")


def test_latn_resolves_common_posture_phrasings():
    expected = {
        "I sit in the chair": "seated",
        "I take a seat": "seated",
        "I stand up": "standing",
        "I rise": "standing",
        "I kneel": "kneeling",
        "I crouch": "kneeling",
        "I lie down": "prone",
        "I go prone": "prone",
    }
    for phrase, posture in expected.items():
        assert resolve_posture(phrase) == posture, phrase


def test_sitting_in_ambiguous_chair_uses_nearest_authored_landmark():
    geometry = configure_from_place_path(
        "places/driftmoor/rusty_razor"
    ).scene_geometry
    target = posture_landmark_target(
        "I sit in the chair", "seated", geometry, (8.0, 6.5, "SHOP")
    )
    assert target is not None
    assert target[:2] == (9.5, 6.5)


def test_furniture_posture_waits_until_character_is_in_reach():
    cs = _cs()
    target = (30.0, 0.0, "SHOP")
    assert not settle_posture(cs, "seated", (0.0, 0.0, "SHOP"), target)
    assert cs.posture == "standing"
    assert settle_posture(cs, "seated", (27.0, 0.0, "SHOP"), target)
    assert cs.posture == "seated"


def test_only_prone_posture_sets_prone_condition():
    cs = _cs()
    apply_posture(cs, "prone")
    assert cs.posture == "prone" and cs.character.conditions == ["prone"]
    apply_posture(cs, "kneeling")
    assert cs.posture == "kneeling" and "prone" not in cs.character.conditions
