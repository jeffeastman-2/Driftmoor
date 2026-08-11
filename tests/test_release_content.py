"""Release-readiness audits for authored Driftmoor town content."""

from pathlib import Path

from models.character_loader import load_npc
from models.game_init import INITIAL_LOCATIONS


ROOT = Path(__file__).parent.parent
NPCS = ROOT / "scenario" / "people" / "npcs"
TOWN_PLACES = ROOT / "scenario" / "places" / "driftmoor"


def _town_npc_dirs():
    for directory in sorted(NPCS.iterdir()):
        location = INITIAL_LOCATIONS.get(directory.name, "")
        if (directory / "IDENTITY.md").is_file() and (
            TOWN_PLACES / location / "PLACE.md"
        ).is_file():
            yield directory


def test_every_driftmoor_npc_has_required_runtime_identity_fields():
    required = ("name", "role", "race", "physical_description")
    for directory in _town_npc_dirs():
        npc = load_npc(directory)
        for field in required:
            assert getattr(npc, field), f"{directory.name} is missing {field}"


def test_every_driftmoor_npc_has_stable_soul_material():
    for directory in _town_npc_dirs():
        soul = (directory / "SOUL.md").read_text(encoding="utf-8")
        assert "## Core Identity" in soul, directory.name
        assert "## Values and Drives" in soul, directory.name
        assert any(
            heading in soul
            for heading in ("## Voice and Manner", "## Personality and Voice")
        ), f"{directory.name} has no stable voice section"


def test_npc_runtime_context_has_no_explicit_dm_only_markers():
    forbidden = ("dm only", "dm-only", "dm's eyes only", "for the dm")
    for directory in _town_npc_dirs():
        for filename in ("IDENTITY.md", "SOUL.md"):
            text = (directory / filename).read_text(encoding="utf-8").lower()
            for marker in forbidden:
                assert marker not in text, (
                    f"{directory.name}/{filename} exposes {marker!r} to the NPC"
                )
