from engine.md_loader import parse_identity_stats, _merge_identity_defaults


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