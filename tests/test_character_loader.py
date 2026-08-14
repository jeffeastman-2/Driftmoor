"""Tests for loading and parsing characters from scenario markdown files."""

import pytest
from pathlib import Path

from models.character import Character, PlayerCharacter, NPC
from models.character_loader import (
    parse_player_identity,
    parse_npc_identity,
    parse_family_md,
    load_player_character,
    load_npc,
    load_family_npc,
    load_all_characters,
)

SCENARIO_DIR = Path(__file__).parent.parent / "scenario" / "people"


# ---------------------------------------------------------------------------
# Unit tests: parse structured fields from sample markdown text
# ---------------------------------------------------------------------------


class TestParsePlayerIdentity:
    """Parse structured fields from player IDENTITY.md content."""

    SAMPLE = """\
# IDENTITY.md — Seraphina Duskwhisper

## Static Profile
- **Full Name:** Seraphina Duskwhisper
- **Player:** TBD
- **Race:** Half-Elf
- **Class:** Rogue, Level 1
- **Background:** Charlatan
- **Alignment:** Chaotic Neutral

## Physical Description
Lithe, raven-black hair cropped above the shoulders, piercing green eyes.

## Combat Statistics
- **HP:** 9
- **AC:** 11 (leather armor)
- **STR:** 8 (-1) | **DEX:** 16 (+3) | **CON:** 12 (+1)
- **INT:** 14 (+2) | **WIS:** 10 | **CHA:** 15 (+2)

## Abilities and Proficiencies
- Sneak Attack: 1d6 extra damage once per turn when attacking with advantage
- Thieves' Cant
- Deception +2 (CHA)
- Sleight of Hand +2 (DEX)
- Proficient: thieves' tools, disguise kit

## Equipment
- Leather armor
- Two daggers (1d4 piercing), one concealed in boot
- Short bow + 20 arrows (1d4 piercing)
- Thieves' tools
- Disguise kit
- Crescent moon pendant (personal, not for trade)

## Dynamic State
*(Updated by monitor agent each round)*

- **Current HP:** 9
- **Mood:** Guarded, watchful
- **Disposition toward party:** Professionally cooperative, warmer than she admits
- **Notable recent actions:** None yet — session not started
- **Active conditions:** None
- **Resources expended:** None
- **Open threads:** Unexplained arcane ability; guild history unresolved
"""

    def test_parse_name(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["name"] == "Seraphina Duskwhisper"

    def test_parse_player(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["player"] == "TBD"

    def test_parse_race(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["race"] == "Half-Elf"

    def test_parse_class_and_level(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["character_class"] == "Rogue"
        assert result["level"] == 1

    def test_parse_class_with_domain(self):
        """Handle class strings like 'Cleric (Light Domain), Level 1'."""
        text = '- **Class:** Cleric (Light Domain), Level 1\n'
        result = parse_player_identity(text)
        assert result["character_class"] == "Cleric (Light Domain)"
        assert result["level"] == 1

    def test_parse_hp(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["hp"] == 9

    def test_parse_ac(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["ac"] == 11

    def test_parse_ac_with_variants(self):
        """AC like '18 (plate) / 20 (with shield)' → extracts first number."""
        text = '- **AC:** 18 (plate) / 20 (with shield)\n'
        result = parse_player_identity(text)
        assert result["ac"] == 18

    def test_parse_ability_scores(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["strength"] == 8
        assert result["dexterity"] == 16
        assert result["constitution"] == 12
        assert result["intelligence"] == 14
        assert result["wisdom"] == 10
        assert result["charisma"] == 15

    def test_parse_abilities(self):
        result = parse_player_identity(self.SAMPLE)
        assert len(result["abilities"]) == 5
        assert "Thieves' Cant" in result["abilities"]

    def test_parse_equipment(self):
        result = parse_player_identity(self.SAMPLE)
        assert len(result["equipment"]) == 6
        assert "Leather armor" in result["equipment"]

    def test_parse_no_spells(self):
        """Characters without a Spells section get an empty list."""
        result = parse_player_identity(self.SAMPLE)
        assert result["spells"] == []

    def test_parse_spells_section(self):
        text = self.SAMPLE + "\n## Spells\n- Fireball\n- Shield\n"
        result = parse_player_identity(text)
        assert "Fireball" in result["spells"]
        assert "Shield" in result["spells"]

    def test_parse_dynamic_state(self):
        result = parse_player_identity(self.SAMPLE)
        assert result["current_hp"] == 9
        assert "Guarded" in result["mood"]
        assert "Professionally cooperative" in result["disposition"]

    def test_parse_open_threads(self):
        result = parse_player_identity(self.SAMPLE)
        assert len(result["open_threads"]) == 2
        assert "Unexplained arcane ability" in result["open_threads"]

    def test_parse_physical_description(self):
        result = parse_player_identity(self.SAMPLE)
        assert "raven-black hair" in result["physical_description"]


class TestParseNPCIdentity:
    """Parse structured fields from NPC IDENTITY.md content."""

    SAMPLE = """\
# IDENTITY.md — Aldren Thorne

## Static Profile
- **Role:** Mayor of Driftmoor
- **Race:** Human, Male, mid-50s
- **Location:** Mayor's Hall, village square

## Physical Description
Stout, broad-shouldered. Weathered skin, thinning gray hair.

## Key Relationships
- **Elyssa Moonglow:** Wary, dismissive of her methods
- **Jorgen Hallowtide:** Trusted, reliable

## What He Knows
- Supply caravans have gone missing
- Shadowbeast sightings are increasing

## What He Wants From the Party
- Practical help: find missing caravans, investigate threats

## Adventure Hooks He Can Offer
1. Missing supply shipment
2. Land dispute between farmers

## Dynamic State
*(Updated by monitor agent each round)*

- **Current mood:** Guarded, preoccupied
- **Disposition toward party:** Neutral/watchful
- **Recent events:** None yet — session not started
- **Active concerns:** Missing ledger, escalating shadowbeast reports
"""

    def test_parse_name_from_title(self):
        result = parse_npc_identity(self.SAMPLE)
        assert result["name"] == "Aldren Thorne"

    def test_parse_role(self):
        result = parse_npc_identity(self.SAMPLE)
        assert result["role"] == "Mayor of Driftmoor"

    def test_parse_race(self):
        result = parse_npc_identity(self.SAMPLE)
        assert result["race"] == "Human, Male, mid-50s"

    def test_parse_location(self):
        result = parse_npc_identity(self.SAMPLE)
        assert result["location"] == "Mayor's Hall, village square"

    def test_parse_physical_description(self):
        result = parse_npc_identity(self.SAMPLE)
        assert "Stout" in result["physical_description"]

    def test_parse_relationships(self):
        result = parse_npc_identity(self.SAMPLE)
        assert "Elyssa Moonglow" in result["relationships"]
        assert "Wary" in result["relationships"]["Elyssa Moonglow"]
        assert "Jorgen Hallowtide" in result["relationships"]

    def test_parse_knowledge(self):
        result = parse_npc_identity(self.SAMPLE)
        assert len(result["knowledge"]) == 2

    def test_parse_hooks(self):
        result = parse_npc_identity(self.SAMPLE)
        assert len(result["hooks"]) >= 2

    def test_parse_mood(self):
        result = parse_npc_identity(self.SAMPLE)
        assert "Guarded" in result["mood"]

    def test_parse_disposition(self):
        result = parse_npc_identity(self.SAMPLE)
        assert "Neutral" in result["disposition"]

    def test_parse_active_concerns(self):
        result = parse_npc_identity(self.SAMPLE)
        assert len(result["active_concerns"]) == 2
        assert "Missing ledger" in result["active_concerns"]

    def test_name_fallback_to_full_name_field(self):
        """If Full Name field exists, use it over the title."""
        text = "# IDENTITY.md — X\n\n- **Full Name:** Real Name\n"
        result = parse_npc_identity(text)
        assert result["name"] == "Real Name"

    def test_knowledge_with_wont_volunteer(self):
        """Knowledge section with parenthetical heading variant."""
        text = "## What He Knows (and Won't Volunteer)\n- Secret one\n- Secret two\n"
        result = parse_npc_identity(text)
        assert len(result["knowledge"]) == 2


class TestParseFamilyMd:
    """Parse single-file family member markdown."""

    SAMPLE = """\
# Davin Haverstead — Son, age 18

## Role
Mill assistant; aspires to more than he can currently do.

## Physical Description
Lanky, mop of dark hair, friendly open face.

## Personality and Voice
- Eager, inexperienced, wants to be useful and often isn't quite.
- Fascinated by adventurers.

## Drives and Fears
- Wants to be strong enough to help his father properly.
- Fear: being ordinary, being stuck, not mattering.

## What He Knows
- He has been listening to the farmers who come to the mill.
- He knows which farmers have seen things near the obelisk.

## Adventure Hooks
1. Can point to specific farmers with obelisk sightings
"""

    def test_parse_name(self):
        result = parse_family_md(self.SAMPLE)
        assert result["name"] == "Davin Haverstead"

    def test_parse_role(self):
        result = parse_family_md(self.SAMPLE)
        assert "Mill assistant" in result["role"]

    def test_parse_physical_description(self):
        result = parse_family_md(self.SAMPLE)
        assert "Lanky" in result["physical_description"]

    def test_parse_knowledge(self):
        result = parse_family_md(self.SAMPLE)
        assert len(result["knowledge"]) == 2

    def test_parse_hooks(self):
        result = parse_family_md(self.SAMPLE)
        assert len(result["hooks"]) >= 1

    def test_name_without_dash(self):
        """Handle title with no em-dash separator."""
        text = "# Simple Name\n\n## Role\nA role.\n"
        result = parse_family_md(text)
        assert result["name"] == "Simple Name"


# ---------------------------------------------------------------------------
# Integration tests: load actual characters from scenario files on disk
# ---------------------------------------------------------------------------


class TestLoadPlayerCharacter:
    def test_load_seraphina(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "seraphina")
        assert pc.id == "seraphina"
        assert pc.name == "Seraphina Duskwhisper"
        assert pc.race == "Half-Elf"
        assert pc.character_class == "Rogue"
        assert pc.level == 2
        assert pc.player == "Kristin"
        assert pc.hp == 9
        assert pc.ac == 10          # authored natural AC base (effective adds DEX/armor at load)
        assert pc.dexterity == 16
        assert pc.character_type == "player"
        assert isinstance(pc, PlayerCharacter)

    def test_load_thorgrim(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "thorgrim")
        assert pc.name == "Thorgrim Stoneheart"
        assert pc.character_class == "Fighter"
        assert pc.hp == 13
        assert pc.ac == 10          # authored natural AC base (effective adds DEX/armor at load)
        assert pc.strength == 16

    def test_load_aeliana_has_spells(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "aeliana")
        assert pc.name == "Aeliana Moonglade"
        assert pc.character_class == "Ranger"
        assert len(pc.spells) >= 3

    def test_load_kaelin(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "kaelin")
        assert pc.name == "Kaelin Brightspark"
        assert pc.character_class == "Bard"

    def test_load_lilar(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "lilar")
        assert pc.name == "Father Lilar Hearthsong"
        assert "Cleric" in pc.character_class
        assert len(pc.spells) >= 3

    def test_preserves_raw_content(self):
        pc = load_player_character(SCENARIO_DIR / "players" / "seraphina")
        assert "IDENTITY.md" in pc.identity_raw
        assert "SOUL.md" in pc.soul_raw
        assert len(pc.identity_raw) > 100
        assert len(pc.soul_raw) > 100

    def test_all_players_load(self):
        player_dir = SCENARIO_DIR / "players"
        players = [
            load_player_character(d)
            for d in sorted(player_dir.iterdir())
            if d.is_dir() and (d / "IDENTITY.md").exists()
        ]
        expected_count = len([d for d in player_dir.iterdir() if d.is_dir() and (d / "IDENTITY.md").exists()])
        assert len(players) == expected_count
        names = {p.name for p in players}
        assert "Seraphina Duskwhisper" in names
        assert "Thorgrim Stoneheart" in names
        assert "Varrak Ironflame" in names
        assert "Sister Amara Solbright" in names


class TestLoadNPC:
    def test_load_aldren(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "aldren")
        assert npc.id == "aldren"
        assert npc.name == "Aldren Thorne"
        assert npc.role == "Mayor of Driftmoor"
        assert npc.character_type == "npc"
        assert isinstance(npc, NPC)

    def test_load_elyssa(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "elyssa")
        assert npc.name == "Elyssa Moonglow"
        assert "Scholar" in npc.role

    def test_load_kelem(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "kelem")
        assert npc.name == "Kelem Dustcloak"
        assert "merchant" in npc.role.lower() or "fence" in npc.role.lower()

    def test_npc_has_soul(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "aldren")
        assert len(npc.soul_raw) > 0
        assert "Values" in npc.soul_raw

    def test_npc_has_relationships(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "aldren")
        assert len(npc.relationships) > 0

    def test_npc_has_knowledge(self):
        npc = load_npc(SCENARIO_DIR / "npcs" / "aldren")
        assert len(npc.knowledge) > 0

    def test_load_promoted_npc(self):
        # The former "background" tier was promoted to full NPCs at the top level.
        npc = load_npc(SCENARIO_DIR / "npcs" / "alina", character_type="npc")
        assert npc.id == "alina"
        assert npc.character_type == "npc"
        assert isinstance(npc, NPC)


class TestLoadFamilyNPC:
    def test_load_davin(self):
        npc = load_family_npc(SCENARIO_DIR / "npcs" / "haversteads" / "davin.md")
        assert npc.id == "davin"
        assert "Davin" in npc.name
        assert npc.character_type == "family"
        assert isinstance(npc, NPC)

    def test_load_gregan(self):
        npc = load_family_npc(SCENARIO_DIR / "npcs" / "haversteads" / "gregan.md")
        assert "Gregan" in npc.name

    def test_family_has_knowledge(self):
        npc = load_family_npc(SCENARIO_DIR / "npcs" / "haversteads" / "davin.md")
        assert len(npc.knowledge) > 0

    def test_family_has_hooks(self):
        npc = load_family_npc(SCENARIO_DIR / "npcs" / "haversteads" / "gregan.md")
        assert len(npc.hooks) > 0


class TestLoadAllCharacters:
    def test_load_all(self):
        characters = load_all_characters(SCENARIO_DIR)
        players = [c for c in characters if isinstance(c, PlayerCharacter)]
        npcs = [c for c in characters if isinstance(c, NPC)]
        player_dir = SCENARIO_DIR / "players"
        expected_players = len([d for d in player_dir.iterdir() if d.is_dir() and (d / "IDENTITY.md").exists()])
        assert len(players) == expected_players
        assert len(npcs) >= 25  # named NPCs (incl. former background tier) + family

    def test_no_duplicate_ids(self):
        characters = load_all_characters(SCENARIO_DIR)
        ids = [c.id for c in characters]
        assert len(ids) == len(set(ids))

    def test_character_types_present(self):
        characters = load_all_characters(SCENARIO_DIR)
        types = {c.character_type for c in characters}
        assert "player" in types
        assert "npc" in types
        assert "family" in types

    def test_every_character_has_name(self):
        characters = load_all_characters(SCENARIO_DIR)
        for c in characters:
            assert c.name, f"Character {c.id} has no name"
