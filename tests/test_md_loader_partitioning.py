from types import SimpleNamespace

from engine.md_loader import (
    configure_from_place_path,
    _build_player_or_npc,
    parse_identity_stats,
    _merge_identity_defaults,
    _warn_unarmed_combatants,
    _char_llm_config,
)


class TestCharLLMConfig:
    """A character inherits the scene's DM provider/model unless its own scene
    block overrides them; identities never contribute."""

    def test_inherits_dm_when_unspecified(self):
        assert _char_llm_config({}, "ollama", "gemma4:26b") == ("ollama", "gemma4:26b")

    def test_block_overrides_both(self):
        cfg = {"provider": "openai", "model": "gpt-4o"}
        assert _char_llm_config(cfg, "ollama", "gemma4:26b") == ("openai", "gpt-4o")

    def test_block_overrides_model_only(self):
        cfg = {"model": "gemma4:9b"}
        assert _char_llm_config(cfg, "ollama", "gemma4:26b") == ("ollama", "gemma4:9b")

    def test_empty_string_falls_back_to_dm(self):
        cfg = {"provider": "", "model": ""}
        assert _char_llm_config(cfg, "ollama", "gemma4:26b") == ("ollama", "gemma4:26b")

    def test_identity_provider_not_merged(self):
        # _merge_identity_defaults must NOT pull provider/model off the identity.
        cfg = {}
        _merge_identity_defaults(cfg, {"provider": "openai", "model": "gpt-4o"})
        assert "provider" not in cfg and "model" not in cfg


def _sess(faction, weapons):
    return SimpleNamespace(
        character=SimpleNamespace(faction=faction),
        weapons=weapons,
    )


class TestUnarmedCombatantWarning:
    def test_flags_weaponless_party_when_hostile_present(self, capsys):
        chars = {
            "gilthaness": _sess("party", []),          # weaponless party member
            "aeliana": _sess("party", ["rapier"]),     # armed
            "giant_spider": _sess("hostile", []),      # weaponless hostile
        }
        flagged = _warn_unarmed_combatants(chars, "echoing_caverns")
        # Both weaponless combatants flagged; the armed one is not.
        assert flagged == ["giant_spider", "gilthaness"]
        err = capsys.readouterr().err
        assert "gilthaness" in err and "giant_spider" in err
        assert "aeliana" not in err

    def test_silent_without_hostiles(self, capsys):
        chars = {
            "gilthaness": _sess("party", []),
            "fennel": _sess("party", []),
        }
        flagged = _warn_unarmed_combatants(chars, "fey_glade")
        assert flagged == []
        assert capsys.readouterr().err == ""

    def test_silent_when_all_combatants_armed(self, capsys):
        chars = {
            "aeliana": _sess("party", ["longbow"]),
            "giant_spider": _sess("hostile", ["spider_bite"]),
        }
        flagged = _warn_unarmed_combatants(chars, "echoing_caverns")
        assert flagged == []
        assert capsys.readouterr().err == ""


def test_parse_identity_equipment_list():
    text = """
# IDENTITY.md - Example Character

## Combat Equipment
- **weapons:** rapier+5, dagger+10

## Equipment
- Rapier (1d8 piercing)
- Studded leather armor
- Thieves' tools
- Wooden vine-carved bracelet
""".strip()
    stats = parse_identity_stats(text)
    # Combat Equipment still parses the structured weapons line...
    assert stats["weapons"] == "rapier+5, dagger+10"
    # ...and the flat ## Equipment list is captured verbatim as raw entries, in
    # order (resolved to ids/free-text later, at load).
    assert stats["equipment_entries"] == [
        "Rapier (1d8 piercing)", "Studded leather armor",
        "Thieves' tools", "Wooden vine-carved bracelet",
    ]


def test_parse_identity_runtime_defaults_block():
    text = """
# IDENTITY.md - Example Character

## Runtime Defaults
- **player_transport:** telegram
- **channel:** telegram
- **host:** ultra
- **inbox:** ~/messages/from-example
- **outbox:** ~/messages/to-example
- **scene_handle:** The field mage
- **activation:** visible_hostiles_only
""".strip()

    stats = parse_identity_stats(text)

    assert stats["player_transport"] == "telegram"
    assert stats["channel"] == "telegram"
    assert stats["host"] == "ultra"
    assert stats["inbox"] == "~/messages/from-example"
    assert stats["outbox"] == "~/messages/to-example"
    assert stats["scene_handle"] == "The field mage"
    assert stats["activation"] == "visible_hostiles_only"


def test_merge_identity_defaults_fills_missing_and_preserves_scene_override():
    cfg = {
        "player": "",
        "channel": "telegram",  # explicit scene override
        "host": "",
        "scene_handle": "",  # should be filled from identity
    }
    id_stats = {
        "player_transport": "telegram",
        "channel": "whatsapp",
        "host": "ultra",
        "scene_handle": "The scholar",
        "activation": "always",
    }

    _merge_identity_defaults(cfg, id_stats)

    # Filled from identity when missing.
    assert cfg["player"] == "telegram"
    assert cfg["host"] == "ultra"
    assert cfg["scene_handle"] == "The scholar"
    assert cfg["activation"] == "always"

    # Scene value remains authoritative.
    assert cfg["channel"] == "telegram"


def test_configure_from_place_path_loads_resident_npc_without_intro_block():
    cfg = configure_from_place_path("places/driftmoor/bitter_remedy")

    assert "lytha" in cfg.characters
    lytha = cfg.characters["lytha"]
    assert lytha.character.character_type == "npc"


def test_build_npc_allows_missing_scene_introduction():
    cs = _build_player_or_npc(
        "lytha",
        {
            "type": "npc",
            "identity_file": "scenario/people/npcs/lytha/IDENTITY.md",
            "soul_file": "scenario/people/npcs/lytha/SOUL.md",
        },
        introductions={},
    )

    assert cs.character.character_type == "npc"
    assert "currently present in this location" in cs.initial_scene