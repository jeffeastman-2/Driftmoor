"""Tests for LLM prompt building, response parsing, and call_llm integration.

Each role has:
  - build_system_prompt / build_user_prompt  → prompt content tests
  - parse_response                           → parsing tests
  - generate_* with mock call_llm            → integration tests
  - generate_* with call_llm=None            → stub behaviour tests
"""

import asyncio
import json
import pytest

from engine.player_router import (
    PlayerLeft, PlayerRight, ActionIntent, CharacterOutput, RoleContext,
)
from engine.dm_agent import DMLeft, DMRight, Adjudication, Narration


# ---- Shared fixtures ----

@pytest.fixture
def ctx():
    return RoleContext(
        character_id="aeliana",
        turn=1,
        condition_text="dopamine: 0.85, cortisol: 0.25",
        scene_context="You are on the trail. The glade shimmers ahead.",
        soul="You are AELIANA MOONGLADE, Wood Elf Ranger.",
        identity="Race: Wood Elf\nClass: Ranger (Level 3)",
    )


# =========================================================================
# PlayerLeft
# =========================================================================

class TestPlayerLeftSystemPrompt:
    def test_mentions_json(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "JSON" in prompt or "json" in prompt

    def test_mentions_intent(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "intent" in prompt

    def test_includes_character_soul(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "AELIANA" in prompt

    def test_includes_character_id(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "aeliana" in prompt


class TestPlayerLeftUserPrompt:
    def test_has_condition(self, ctx):
        prompt = PlayerLeft().build_user_prompt(ctx)
        assert "dopamine" in prompt

    def test_has_scene(self, ctx):
        prompt = PlayerLeft().build_user_prompt(ctx)
        assert "trail" in prompt

    def test_has_turn(self, ctx):
        prompt = PlayerLeft().build_user_prompt(ctx)
        assert "Turn 1" in prompt


class TestPlayerLeftParsing:
    def test_parse_full_json(self, ctx):
        raw = json.dumps({
            "intent": "advance cautiously toward the glade",
            "movement_target": [50.0, 50.0, 0.2],
            "interaction_target": None,
        })
        result = PlayerLeft().parse_response(raw, ctx)
        assert isinstance(result, ActionIntent)
        assert result.intent == "advance cautiously toward the glade"
        assert result.movement_target == (50.0, 50.0, 0.2)

    def test_parse_minimal_json(self, ctx):
        raw = json.dumps({"intent": "hold position"})
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.intent == "hold position"
        assert result.movement_target is None
        assert result.interaction_target is None

    def test_parse_json_in_markdown_block(self, ctx):
        raw = '```json\n{"intent": "observe"}\n```'
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.intent == "observe"

    def test_parse_json_with_preamble(self, ctx):
        raw = 'Here is my analysis:\n{"intent": "wait and watch"}'
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.intent == "wait and watch"

    def test_sets_character_and_turn(self, ctx):
        raw = json.dumps({"intent": "wait"})
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.character_id == "aeliana"
        assert result.turn == 1


class TestPlayerLeftLLM:
    def test_calls_llm_when_configured(self, ctx):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return json.dumps({"intent": "mock action"})

        result = asyncio.run(PlayerLeft(call_llm=mock_llm).generate_intent(ctx))
        assert len(calls) == 1
        assert result.intent == "mock action"

    def test_system_prompt_passed_to_llm(self, ctx):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return json.dumps({"intent": "x"})

        asyncio.run(PlayerLeft(call_llm=mock_llm).generate_intent(ctx))
        assert "strategic mind" in calls[0][0]

    def test_stub_when_no_llm(self, ctx):
        result = asyncio.run(PlayerLeft().generate_intent(ctx))
        assert result.intent == "observe surroundings and hold position"


# =========================================================================
# PlayerRight
# =========================================================================

class TestPlayerRightSystemPrompt:
    def test_has_soul(self, ctx):
        prompt = PlayerRight().build_system_prompt(ctx)
        assert "AELIANA" in prompt

    def test_has_identity(self, ctx):
        prompt = PlayerRight().build_system_prompt(ctx)
        assert "Ranger" in prompt

    def test_mentions_four_sections(self, ctx):
        prompt = PlayerRight().build_system_prompt(ctx)
        assert "INTERNAL" in prompt
        assert "BODY LANGUAGE" in prompt
        assert "SPOKEN" in prompt
        assert "ACTION" in prompt


class TestPlayerRightUserPrompt:
    def test_has_intent(self, ctx):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance toward glade")
        prompt = PlayerRight().build_user_prompt(intent, ctx)
        assert "advance toward glade" in prompt

    def test_has_condition(self, ctx):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        prompt = PlayerRight().build_user_prompt(intent, ctx)
        assert "dopamine" in prompt

    def test_has_scene(self, ctx):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        prompt = PlayerRight().build_user_prompt(intent, ctx)
        assert "trail" in prompt


class TestPlayerRightParsing:
    def test_parse_four_sections(self, ctx):
        raw = (
            "**INTERNAL**\n"
            "The trail ends here. Something shimmers.\n\n"
            "**BODY LANGUAGE**\n"
            "Crouched low, alert.\n\n"
            "**SPOKEN**\n"
            "(silent)\n\n"
            "**ACTION**\n"
            "Advance carefully toward the glade."
        )
        result = PlayerRight().parse_response(raw, ctx)
        assert isinstance(result, CharacterOutput)
        assert "shimmers" in result.internal
        assert "Crouched" in result.body_language
        assert "Advance" in result.action

    def test_parse_with_em_dash(self, ctx):
        raw = (
            "**INTERNAL** — Thinking carefully.\n\n"
            "**BODY LANGUAGE** — Still, quiet.\n\n"
            "**SPOKEN** —\n\n"
            "**ACTION** — Wait and observe."
        )
        result = PlayerRight().parse_response(raw, ctx)
        assert "Thinking" in result.internal
        assert "Wait" in result.action

    def test_parse_missing_section(self, ctx):
        raw = "**INTERNAL**\nJust thinking.\n\n**ACTION**\nWait."
        result = PlayerRight().parse_response(raw, ctx)
        assert "thinking" in result.internal.lower()
        assert result.body_language == ""

    def test_sets_character_and_turn(self, ctx):
        raw = "**INTERNAL**\nX.\n\n**BODY LANGUAGE**\nY.\n\n**SPOKEN**\n\n\n**ACTION**\nZ."
        result = PlayerRight().parse_response(raw, ctx)
        assert result.character_id == "aeliana"
        assert result.turn == 1


class TestPlayerRightLLM:
    def test_calls_llm_when_configured(self, ctx):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return (
                "**INTERNAL**\nMock thought.\n\n"
                "**BODY LANGUAGE**\nStill.\n\n"
                "**SPOKEN**\n\n\n"
                "**ACTION**\nMock action."
            )

        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        result = asyncio.run(PlayerRight(call_llm=mock_llm).generate_action(intent, ctx))
        assert len(calls) == 1
        assert "Mock thought" in result.internal

    def test_stub_when_no_llm(self, ctx):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        result = asyncio.run(PlayerRight().generate_action(intent, ctx))
        assert "advance" in result.action


# =========================================================================
# DMLeft
# =========================================================================

class TestDMLeftSystemPrompt:
    def test_mentions_adjudicate(self):
        prompt = DMLeft().build_system_prompt()
        assert "adjudicat" in prompt.lower()

    def test_mentions_json(self):
        prompt = DMLeft().build_system_prompt()
        assert "JSON" in prompt or "json" in prompt

    def test_mentions_approved(self):
        prompt = DMLeft().build_system_prompt()
        assert "approved" in prompt


class TestDMLeftUserPrompt:
    def test_has_action(self):
        output = CharacterOutput(
            character_id="aeliana", turn=1,
            action="advance toward the glade",
        )
        prompt = DMLeft().build_user_prompt(output, "game state", "geometry")
        assert "advance toward the glade" in prompt

    def test_has_game_state(self):
        output = CharacterOutput(character_id="aeliana", turn=1, action="wait")
        prompt = DMLeft().build_user_prompt(output, "Turn 1, Fey Glade", "")
        assert "Turn 1" in prompt

    def test_has_character_id(self):
        output = CharacterOutput(character_id="fennel", turn=2, action="gather")
        prompt = DMLeft().build_user_prompt(output, "", "")
        assert "fennel" in prompt


class TestDMLeftParsing:
    def test_parse_approved(self):
        raw = json.dumps({
            "approved": True,
            "condition_deltas": {"dopamine": 0.10},
            "spatial_events": ["enters_fey_glade"],
            "notes": "Valid movement.",
        })
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert isinstance(result, Adjudication)
        assert result.approved is True
        assert result.condition_deltas["dopamine"] == 0.10
        assert "enters_fey_glade" in result.spatial_events

    def test_parse_rejected(self):
        raw = json.dumps({
            "approved": False,
            "modified_action": "Cannot cross the barrier.",
        })
        result = DMLeft().parse_response(raw, "fennel", 1)
        assert result.approved is False
        assert "barrier" in result.modified_action

    def test_parse_position_delta(self):
        raw = json.dumps({
            "approved": True,
            "position_delta": [5.0, 3.0, 0.0],
        })
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.position_delta == (5.0, 3.0, 0.0)

    def test_parse_json_in_markdown_block(self):
        raw = '```json\n{"approved": true, "notes": "OK"}\n```'
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.approved is True
        assert result.notes == "OK"

    def test_parse_minimal(self):
        raw = json.dumps({"approved": True})
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.approved is True
        assert result.condition_deltas == {}
        assert result.spatial_events == []

    def test_sets_character_and_turn(self):
        raw = json.dumps({"approved": True})
        result = DMLeft().parse_response(raw, "fennel", 3)
        assert result.character_id == "fennel"
        assert result.turn == 3


class TestDMLeftLLM:
    def test_calls_llm_when_configured(self):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return json.dumps({"approved": True, "notes": "OK"})

        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        result = asyncio.run(DMLeft(call_llm=mock_llm).adjudicate(output, "", ""))
        assert len(calls) == 1
        assert result.approved is True

    def test_stub_when_no_llm(self):
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        result = asyncio.run(DMLeft().adjudicate(output, "", ""))
        assert result.approved is True


# =========================================================================
# DMRight
# =========================================================================

class TestDMRightSystemPrompt:
    def test_mentions_narrative(self):
        prompt = DMRight().build_system_prompt()
        assert "narrat" in prompt.lower()

    def test_mentions_prose(self):
        prompt = DMRight().build_system_prompt()
        assert "prose" in prompt

    def test_mentions_third_person(self):
        prompt = DMRight().build_system_prompt()
        assert "third-person" in prompt


class TestDMRightUserPrompt:
    def test_has_action(self):
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(
            character_id="aeliana", turn=1, action="advance toward the glade",
        )
        prompt = DMRight().build_user_prompt(adj, output, "")
        assert "advance toward the glade" in prompt

    def test_has_approved_status(self):
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(character_id="aeliana", turn=1, action="wait")
        prompt = DMRight().build_user_prompt(adj, output, "")
        assert "APPROVED" in prompt

    def test_has_modified_status(self):
        adj = Adjudication(
            character_id="fennel", turn=1, approved=False,
            modified_action="Blocked by barrier.",
        )
        output = CharacterOutput(character_id="fennel", turn=1, action="cross")
        prompt = DMRight().build_user_prompt(adj, output, "")
        assert "MODIFIED" in prompt
        assert "Blocked by barrier" in prompt

    def test_has_scene_history(self):
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(character_id="aeliana", turn=1, action="wait")
        prompt = DMRight().build_user_prompt(adj, output, "Fennel entered the glade.")
        assert "Fennel" in prompt

    def test_has_notes(self):
        adj = Adjudication(
            character_id="aeliana", turn=1, approved=True,
            notes="Movement costs 5m.",
        )
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        prompt = DMRight().build_user_prompt(adj, output, "")
        assert "Movement costs 5m" in prompt


class TestDMRightParsing:
    def test_parse_prose(self):
        raw = "Aeliana moves cautiously through the shimmer."
        result = DMRight().parse_response(raw, "aeliana", 1)
        assert isinstance(result, Narration)
        assert "Aeliana" in result.prose

    def test_strips_whitespace(self):
        raw = "\n  The shadowbeast stirs.\n"
        result = DMRight().parse_response(raw, "shadowbeast", 1)
        assert result.prose == "The shadowbeast stirs."

    def test_sets_character_and_turn(self):
        raw = "Things happen."
        result = DMRight().parse_response(raw, "fennel", 2)
        assert result.character_id == "fennel"
        assert result.turn == 2


class TestDMRightLLM:
    def test_calls_llm_when_configured(self):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return "The ranger advances cautiously."

        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        result = asyncio.run(DMRight(call_llm=mock_llm).narrate(adj, output, ""))
        assert len(calls) == 1
        assert "ranger" in result.prose

    def test_stub_when_no_llm(self):
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        result = asyncio.run(DMRight().narrate(adj, output, ""))
        assert "aeliana" in result.prose
