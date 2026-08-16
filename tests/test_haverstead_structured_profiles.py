from pathlib import Path

from models.character_loader import load_all_characters, load_npc


PEOPLE_DIR = Path(__file__).parent.parent / "scenario" / "people"
HAVERSTEADS_DIR = PEOPLE_DIR / "npcs" / "haversteads"


def test_structured_haverstead_profiles_load_identity_and_soul():
    for npc_id in ("gregan", "mara", "davin", "tessa", "isla"):
        npc = load_npc(HAVERSTEADS_DIR / npc_id, character_type="family")
        assert npc.id == npc_id
        assert npc.identity_raw
        assert npc.soul_raw
        assert npc.hp > 0
        assert npc.ac > 0


def test_all_character_loader_prefers_structured_haversteads_without_duplicates():
    characters = load_all_characters(PEOPLE_DIR)
    haverstead_ids = [
        character.id
        for character in characters
        if character.id in {"gregan", "mara", "davin", "tessa", "isla"}
    ]
    assert sorted(haverstead_ids) == ["davin", "gregan", "isla", "mara", "tessa"]
    for character in characters:
        if character.id in haverstead_ids:
            assert character.soul_raw
