from pathlib import Path

import pytest

from character_generation import (
    CharacterDraft, fallback_draft, identity_markdown, parse_model_draft,
    save_draft, soul_markdown, validate_draft,
)


def test_fallback_turns_free_form_answers_into_character():
    draft = fallback_draft({
        "player": "Sam", "name": "Mara Vell", "concept": "A rain-soaked former guard",
        "desire": "protect the lost", "fear": "being recognized",
        "play_style": "protect people and heal them", "keepsake": "A cracked bell",
    })
    assert draft.name == "Mara Vell"
    assert draft.player == "Sam"
    assert draft.character_class == "Cleric"
    assert "protect the lost" in draft.values_and_drives
    assert draft.signature_detail == "A cracked bell"


def test_fallback_respects_identity_and_deduces_rules_nomenclature():
    draft = fallback_draft({
        "name": "Orin", "pronouns": "he/him", "gender": "Man",
        "race": "Dwarf", "play_style": "sneak and deceive, improvise with tools",
        "past": "He served as a guard during the border war.",
        "level": "3", "loyalty": "His younger sister",
        "contradiction": "He craves recognition but hides every success.",
    })
    assert (draft.pronouns, draft.gender, draft.race) == ("he/him", "Man", "Dwarf")
    assert (draft.character_class, draft.background, draft.level) == ("Rogue", "Soldier", 3)
    assert draft.loyalties == ["His younger sister"]
    assert draft.internal_contradiction.startswith("He craves recognition")


def test_model_json_accepts_fenced_response_and_ignores_extra_keys():
    draft = parse_model_draft('```json\n{"name":"Ash", "hp":12, "unknown":true}\n```')
    assert draft.name == "Ash"
    assert draft.hp == 12


def test_validation_catches_invalid_mechanics_and_missing_soul():
    draft = CharacterDraft(hp=0, strength=25, values_and_drives=[], voice_and_manner=[])
    errors = validate_draft(draft)
    assert any("HP" in error for error in errors)
    assert any("Strength" in error for error in errors)
    assert any("value" in error for error in errors)


def test_markdown_uses_canonical_sections():
    draft = CharacterDraft(name="Mara Vell", values_and_drives=["Protect pilgrims"],
                           voice_and_manner=["Speaks softly"])
    identity = identity_markdown(draft)
    soul = soul_markdown(draft)
    assert "# IDENTITY.md — Mara Vell" in identity
    assert "- **Current HP:** 10" in identity
    assert "# SOUL.md — Mara Vell" in soul
    assert "## Internal Contradiction" in soul


def test_save_reloads_through_production_loader(tmp_path: Path):
    draft = CharacterDraft(name="Mara Vell", values_and_drives=["Protect pilgrims"],
                           voice_and_manner=["Speaks softly"])
    directory = save_draft(draft, tmp_path)
    assert directory.name == "mara_vell"
    assert (directory / "IDENTITY.md").exists()
    assert (directory / "SOUL.md").exists()
    with pytest.raises(FileExistsError):
        save_draft(draft, tmp_path)
