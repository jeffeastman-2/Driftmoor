"""Tests for LLM prompt building, response parsing, and call_llm integration.

Each role has:
  - build_system_prompt / build_user_prompt  → prompt content tests
  - parse_response                           → parsing tests
  - generate_* with mock call_llm            → integration tests
  - generate_* with call_llm=None            → stub behaviour tests
"""

import asyncio
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
    def test_requests_sections_not_json(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "INTENT" in prompt
        assert "MOVEMENT" in prompt
        assert "TARGET" in prompt
        assert "JSON" not in prompt

    def test_mentions_intent(self, ctx):
        prompt = PlayerLeft().build_system_prompt(ctx)
        assert "INTENT" in prompt

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
    def test_parse_full_sections(self, ctx):
        raw = (
            "**INTENT** — Advance cautiously toward the glade.\n"
            "**MOVEMENT** — 50.0, 50.0, 0.2\n"
            "**TARGET** — none"
        )
        result = PlayerLeft().parse_response(raw, ctx)
        assert isinstance(result, ActionIntent)
        assert "Advance cautiously" in result.intent
        assert result.movement_target == (50.0, 50.0, 0.2)

    def test_parse_minimal_intent_only(self, ctx):
        raw = "**INTENT** — Hold position.\n**MOVEMENT** — none\n**TARGET** — none"
        result = PlayerLeft().parse_response(raw, ctx)
        assert "Hold position" in result.intent
        assert result.movement_target is None
        assert result.interaction_target is None

    def test_parse_with_preamble(self, ctx):
        raw = (
            "Here is my analysis:\n\n"
            "**INTENT** — Wait and watch.\n"
            "**MOVEMENT** — none\n"
            "**TARGET** — none"
        )
        result = PlayerLeft().parse_response(raw, ctx)
        assert "Wait and watch" in result.intent

    def test_parse_movement_2d(self, ctx):
        raw = "**INTENT** — Move.\n**MOVEMENT** — 45, 48\n**TARGET** — none"
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.movement_target == (45.0, 48.0, 0.0)

    def test_parse_interaction_target(self, ctx):
        raw = "**INTENT** — Talk.\n**MOVEMENT** — none\n**TARGET** — fennel"
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.interaction_target == "fennel"

    def test_fallback_no_sections(self, ctx):
        raw = "I will observe my surroundings carefully."
        result = PlayerLeft().parse_response(raw, ctx)
        assert "observe" in result.intent.lower()

    def test_sets_character_and_turn(self, ctx):
        raw = "**INTENT** — Wait.\n**MOVEMENT** — none\n**TARGET** — none"
        result = PlayerLeft().parse_response(raw, ctx)
        assert result.character_id == "aeliana"
        assert result.turn == 1


class TestPlayerLeftLLM:
    def test_calls_llm_when_configured(self, ctx):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return "**INTENT** — Mock action.\n**MOVEMENT** — none\n**TARGET** — none"

        result = asyncio.run(PlayerLeft(call_llm=mock_llm).generate_intent(ctx))
        assert len(calls) == 1
        assert "Mock action" in result.intent

    def test_system_prompt_passed_to_llm(self, ctx):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return "**INTENT** — X.\n**MOVEMENT** — none\n**TARGET** — none"

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

    def test_social_opener_repairs_silent_spoken(self):
        ctx = RoleContext(
            character_id="kaelin",
            turn=1,
            condition_text="dopamine: 0.70, cortisol: 0.35",
            scene_context="Evening in the tavern.",
            soul="You are Kaelin.",
            identity="Bard",
            perception="- Tess (ally, MAIN_ROOM, ~10 ft away)",
            in_combat=False,
        )
        intent = ActionIntent(character_id="kaelin", turn=1, intent="Search the room")
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            if len(calls) == 1:
                return (
                    "**INTERNAL**\nWatching the room.\n\n"
                    "**BODY LANGUAGE**\nStill.\n\n"
                    "**SPOKEN**\n\n\n"
                    "**ACTION**\nSearch the room."
                )
            return "Evening. Anything I should know tonight?"

        result = asyncio.run(PlayerRight(call_llm=mock_llm).generate_action(intent, ctx))
        assert len(calls) == 2
        assert "Evening" in result.spoken

    def test_hostile_perception_does_not_force_social_opener(self):
        ctx = RoleContext(
            character_id="aeliana",
            turn=1,
            condition_text="dopamine: 0.80, cortisol: 0.30",
            scene_context="Threat in view.",
            soul="You are Aeliana.",
            identity="Ranger",
            perception="- shadowbeast (HOSTILE, CLEARING, ~20 ft away)",
            in_combat=False,
        )
        intent = ActionIntent(character_id="aeliana", turn=1, intent="Attack the shadowbeast")
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return (
                "**INTERNAL**\nDanger.\n\n"
                "**BODY LANGUAGE**\nBow raised.\n\n"
                "**SPOKEN**\n\n\n"
                "**ACTION**\nAttack the shadowbeast."
            )

        result = asyncio.run(PlayerRight(call_llm=mock_llm).generate_action(intent, ctx))
        assert len(calls) == 1
        assert result.spoken == ""


# =========================================================================
# DMLeft
# =========================================================================

class TestDMLeftSystemPrompt:
    def test_mentions_adjudicate(self):
        prompt = DMLeft().build_system_prompt()
        assert "adjudicat" in prompt.lower()

    def test_requests_sections_not_json(self):
        prompt = DMLeft().build_system_prompt()
        assert "APPROVED" in prompt
        assert "NEW POSITION" in prompt
        assert "CONDITION" in prompt
        assert "JSON" not in prompt

    def test_mentions_approved(self):
        prompt = DMLeft().build_system_prompt()
        assert "APPROVED" in prompt


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
    def test_parse_approved_with_deltas(self):
        raw = (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**NEW POSITION** — x=3.0, y=2.0, zone=GLADE\n"
            "**CONDITION** — dopamine +0.10\n"
            "**EVENTS** — enters_fey_glade\n"
            "**NOTES** — Valid movement."
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert isinstance(result, Adjudication)
        assert result.approved is True
        assert result.condition_deltas["dopamine"] == 0.10
        assert "enters_fey_glade" in result.spatial_events

    def test_parse_rejected(self):
        raw = (
            "**APPROVED** — No\n"
            "**MODIFIED ACTION** — Cannot cross the barrier.\n"
            "**NEW POSITION** — none\n"
            "**CONDITION** — none\n"
            "**EVENTS** — none\n"
            "**NOTES** — Magical barrier blocks passage."
        )
        result = DMLeft().parse_response(raw, "fennel", 1)
        assert result.approved is False
        assert "barrier" in result.modified_action

    def test_parse_new_position(self):
        raw = (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**MOVEMENT TARGET** — x=5.0, y=3.0\n"
            "**CONDITION** — none\n"
            "**EVENTS** — none\n"
            "**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.movement_target == (5.0, 3.0)

    def test_parse_multiple_condition_deltas(self):
        raw = (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**NEW POSITION** — none\n"
            "**CONDITION** — dopamine +0.1, cortisol -0.05\n"
            "**EVENTS** — none\n"
            "**NOTES** — Calm but alert."
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.condition_deltas["dopamine"] == 0.1
        assert result.condition_deltas["cortisol"] == -0.05

    def test_parse_minimal(self):
        raw = "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n**NEW POSITION** — none\n**CONDITION** — none\n**EVENTS** — none\n**NOTES** — OK"
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.approved is True
        assert result.condition_deltas == {}
        assert result.spatial_events == []

    def test_parse_multiple_events(self):
        raw = (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n"
            "**CONDITION** — none\n"
            "**EVENTS** — enters_fey_glade, crosses_boundary\n"
            "**NOTES** — Two events."
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert "enters_fey_glade" in result.spatial_events
        assert "crosses_boundary" in result.spatial_events

    def test_sets_character_and_turn(self):
        raw = "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n**POSITION DELTA** — none\n**CONDITION** — none\n**EVENTS** — none\n**NOTES** — OK"
        result = DMLeft().parse_response(raw, "fennel", 3)
        assert result.character_id == "fennel"
        assert result.turn == 3

    # ---- Condition delta edge cases (per Sonnet) ----

    def test_condition_unsigned_value(self):
        """LLM writes 'dopamine 0.08' without sign."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n"
            "**CONDITION** — dopamine 0.08\n"
            "**EVENTS** — none\n**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.condition_deltas["dopamine"] == 0.08

    def test_condition_increase_by(self):
        """LLM writes 'increase dopamine by 0.1'."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n"
            "**CONDITION** — increase dopamine by 0.1\n"
            "**EVENTS** — none\n**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.condition_deltas["dopamine"] == 0.1

    def test_condition_decrease_by(self):
        """LLM writes 'decrease cortisol by 0.05'."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n"
            "**CONDITION** — decrease cortisol by 0.05\n"
            "**EVENTS** — none\n**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.condition_deltas["cortisol"] == -0.05

    def test_condition_colon_format(self):
        """LLM writes 'dopamine: +0.1'."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n"
            "**CONDITION** — dopamine: +0.1, cortisol: -0.05\n"
            "**EVENTS** — none\n**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert result.condition_deltas["dopamine"] == 0.1
        assert result.condition_deltas["cortisol"] == -0.05

    # ---- Spatial events edge cases (per Sonnet) ----

    def test_events_bullet_list(self):
        """LLM writes events as bullet points."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n**CONDITION** — none\n"
            "**EVENTS** —\n"
            "- shadowbeast_proximity_detected\n"
            "- pool_cycle_approaching\n"
            "**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert "shadowbeast_proximity_detected" in result.spatial_events
        assert "pool_cycle_approaching" in result.spatial_events

    def test_events_newline_separated(self):
        """LLM writes events on separate lines without bullets."""
        raw = (
            "**APPROVED** — Yes\n**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — none\n**CONDITION** — none\n"
            "**EVENTS** —\n"
            "shadowbeast_proximity_detected\n"
            "pool_cycle_approaching\n"
            "**NOTES** — OK"
        )
        result = DMLeft().parse_response(raw, "aeliana", 1)
        assert "shadowbeast_proximity_detected" in result.spatial_events
        assert "pool_cycle_approaching" in result.spatial_events


class TestDMLeftLLM:
    def test_calls_llm_when_configured(self):
        calls = []

        async def mock_llm(system, user):
            calls.append((system, user))
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — none\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — OK"
            )

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

    def test_assigns_dialogue_exclusively_to_structured_spoken_field(self):
        prompt = DMRight().build_system_prompt().lower()
        assert "do not include dialogue" in prompt
        assert "do not invent another character's spoken response" in prompt


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

    def test_removes_decorative_opening_when_dialogue_repeats_in_prose(self):
        speech = (
            "An adventurer's journey often leaves one with a certain... hunger "
            "for the peculiar. Tell me, does your path require something "
            "functional, perhaps a relic with a bit of spark?"
        )
        raw = (
            f'*“"{speech}"”* Kelem leans against the shop counter. '
            '"An adventurer\'s journey often leaves one with a certain... hunger '
            'for the peculiar," Kelem says. "Tell me, does your path require '
            'something functional, perhaps a relic with a bit of spark?"'
        )
        result = DMRight().parse_response(raw, "kelem", 4)
        assert not result.prose.startswith("*“")
        assert result.prose.count("An adventurer's journey") == 1
        assert result.prose.count("Tell me, does your path") == 1

    def test_configured_pronouns_correct_misgendered_tavern_prose(self):
        raw = (
            "Tess stops polishing an ale tankard and leans his weight onto "
            "the bar. He keeps his gaze fixed on the door."
        )
        result = DMRight().parse_response(
            raw, "tess", 1, character_pronouns={"tess": "she/her"})
        assert "leans her weight" in result.prose
        assert "She keeps her gaze" in result.prose


class TestDMRightLLM:
    def test_removes_near_duplicate_of_structured_spoken_dialogue(self):
        spoken = (
            "Well now, if it isn't the most elegant visitor in Driftmoor! "
            "Come in, come in—don't just stand there letting the breeze in. "
            "Looking for a trim, or just some much-needed conversation?"
        )

        async def mock_llm(_system, _user):
            return (
                "Arlan sweeps the dark curls toward the dustpan and straightens "
                "his apron before facing Gil. *\"Well now, if it isn't the most "
                "elegant visitor in Driftmoor! Come in, come in—don't just stand "
                "there letting the breeze in. Looking for a trim, or just "
                "much-needed conversation?\"*"
            )

        adj = Adjudication(character_id="arlan", turn=2, approved=True)
        output = CharacterOutput(
            character_id="arlan", turn=2, action="sweeps the floor", spoken=spoken
        )
        result = asyncio.run(DMRight(call_llm=mock_llm).narrate(adj, output, ""))
        assert "elegant visitor" not in result.prose
        assert "sweeps the dark curls" in result.prose

    def test_preserves_unrelated_quoted_dialogue(self):
        spoken = "Good morning."

        async def mock_llm(_system, _user):
            return 'Arlan turns to Marta. "Your boots are ready," he says.'

        adj = Adjudication(character_id="arlan", turn=2, approved=True)
        output = CharacterOutput(
            character_id="arlan", turn=2, action="turns", spoken=spoken
        )
        result = asyncio.run(DMRight(call_llm=mock_llm).narrate(adj, output, ""))
        assert "Your boots are ready" in result.prose

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

    def test_stub_surfaces_authoritative_item_interaction(self):
        adj = Adjudication(character_id="gilthaness", turn=6, approved=True)
        output = CharacterOutput(
            character_id="gilthaness", turn=6, action="I unseal the letter")
        result = asyncio.run(DMRight().narrate(
            adj, output, "",
            resolution_log=[
                "[ITEM-INTERACTION] gilthaness open Sealed letter: "
                "Breaking the wax reveals the note."
            ],
        ))
        assert result.prose == "Breaking the wax reveals the note."

    def test_stub_surfaces_authoritative_consumption(self):
        adj = Adjudication(character_id="gilthaness", turn=3, approved=True)
        output = CharacterOutput(
            character_id="gilthaness", turn=3, action="I drink the ale")
        result = asyncio.run(DMRight().narrate(
            adj, output, "",
            resolution_log=[
                "[ITEM] gilthaness drinks Driftmoor Ale: "
                "Gilthaness uses it up. Narrate it."
            ],
        ))
        assert result.prose == "Gilthaness drinks Driftmoor Ale."

    def test_stub_surfaces_authoritative_purchase(self):
        adj = Adjudication(character_id="gilthaness", turn=2, approved=True)
        output = CharacterOutput(
            character_id="gilthaness", turn=2, action="I buy some ale")
        result = asyncio.run(DMRight().narrate(
            adj, output, "",
            resolution_log=[
                "[COMMERCE] SETTLED by the engine — do not alter: gilthaness "
                "bought Driftmoor Ale from tess for exactly 4 cp; it is now in "
                "their possession."
            ],
        ))
        assert result.prose == "Gilthaness buys Driftmoor Ale for 4 cp."
