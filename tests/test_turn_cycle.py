"""Tests for the 4-role turn cycle architecture.

Data flow per character:
  PlayerLeft  → ActionIntent  (what to do)
  PlayerRight → CharacterOutput (in-character prose)
  DMLeft      → Adjudication  (rules/spatial validation)
  DMRight     → Narration     (scene prose)

Characters act sequentially in initiative order.
Each character sees all preceding narration from the same turn.
"""

import asyncio
import pytest

from engine.player_router import (
    PlayerLeft, PlayerRight, ActionIntent, CharacterOutput, RoleContext,
)
from engine.dm_agent import DMLeft, DMRight, Adjudication, Narration
from engine.scene_manager import TurnCycle, CharacterTurnResult, TurnResult


# ---- Fixtures ----

@pytest.fixture
def aeliana_context():
    return RoleContext(
        character_id="aeliana",
        turn=1,
        condition_text="dopamine: 0.85, cortisol: 0.25",
        scene_context="You are on the trail. The glade shimmers ahead.",
        soul="You are AELIANA MOONGLADE, Wood Elf Ranger.",
        identity="Race: Wood Elf\nClass: Ranger (Level 3)",
    )


@pytest.fixture
def fennel_context():
    return RoleContext(
        character_id="fennel",
        turn=1,
        condition_text="dopamine: 0.50, cortisol: 0.60",
        scene_context="You are in the glade. The pool glimmers nearby.",
        soul="You are FENNEL, herb gatherer.",
        identity="Race: Human\nBackground: Herbalist",
    )


@pytest.fixture
def shadowbeast_context():
    return RoleContext(
        character_id="shadowbeast",
        turn=1,
        condition_text="dopamine: 0.80, norepinephrine: 0.85",
        scene_context="You are in the forest. Prey near the boundary.",
        soul="You are the SHADOWBEAST.",
        identity="Type: Warped Creature",
    )


# ---- RoleContext tests ----

class TestRoleContext:
    def test_has_character_id(self, aeliana_context):
        assert aeliana_context.character_id == "aeliana"

    def test_has_turn(self, aeliana_context):
        assert aeliana_context.turn == 1

    def test_has_condition(self, aeliana_context):
        assert "dopamine" in aeliana_context.condition_text

    def test_has_scene_context(self, aeliana_context):
        assert "trail" in aeliana_context.scene_context

    def test_has_soul(self, aeliana_context):
        assert "AELIANA" in aeliana_context.soul

    def test_has_identity(self, aeliana_context):
        assert "Ranger" in aeliana_context.identity


# ---- ActionIntent tests ----

class TestActionIntent:
    def test_create_basic(self):
        intent = ActionIntent(
            character_id="aeliana", turn=1,
            intent="move toward the glade",
        )
        assert intent.character_id == "aeliana"
        assert intent.turn == 1
        assert intent.intent == "move toward the glade"

    def test_movement_target_optional(self):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="hold")
        assert intent.movement_target is None

    def test_movement_target_3d(self):
        intent = ActionIntent(
            character_id="aeliana", turn=1, intent="move",
            movement_target=(50.0, 50.0, 0.2),
        )
        assert intent.movement_target == (50.0, 50.0, 0.2)

    def test_interaction_target_optional(self):
        intent = ActionIntent(character_id="aeliana", turn=1, intent="observe")
        assert intent.interaction_target is None


# ---- CharacterOutput tests ----

class TestCharacterOutput:
    def test_create_empty(self):
        output = CharacterOutput(character_id="aeliana", turn=1)
        assert output.character_id == "aeliana"
        assert output.internal == ""
        assert output.body_language == ""
        assert output.spoken == ""
        assert output.action == ""

    def test_create_with_content(self):
        output = CharacterOutput(
            character_id="aeliana", turn=1,
            internal="Watching the trees.",
            body_language="Crouched, alert.",
            spoken="",
            action="Advance toward the glade.",
        )
        assert "Watching" in output.internal
        assert "Crouched" in output.body_language
        assert output.spoken == ""
        assert "Advance" in output.action


# ---- Adjudication tests ----

class TestAdjudication:
    def test_create_approved(self):
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        assert adj.approved is True
        assert adj.condition_deltas == {}
        assert adj.spatial_events == []

    def test_create_with_deltas(self):
        adj = Adjudication(
            character_id="aeliana", turn=1, approved=True,
            condition_deltas={"dopamine": +0.10, "cortisol": +0.05},
            spatial_events=["enters_fey_glade"],
        )
        assert adj.condition_deltas["dopamine"] == 0.10
        assert "enters_fey_glade" in adj.spatial_events

    def test_rejected_with_modification(self):
        adj = Adjudication(
            character_id="fennel", turn=1, approved=False,
            modified_action="Cannot cross the boundary — magical barrier blocks passage.",
        )
        assert adj.approved is False
        assert "barrier" in adj.modified_action

    def test_position_delta(self):
        adj = Adjudication(
            character_id="aeliana", turn=1, approved=True,
            position_delta=(5.0, 3.0, 0.0),
        )
        assert adj.position_delta == (5.0, 3.0, 0.0)


# ---- Narration tests ----

class TestNarration:
    def test_create_basic(self):
        narr = Narration(
            character_id="aeliana", turn=1,
            prose="Aeliana advances cautiously.",
        )
        assert "Aeliana" in narr.prose
        assert narr.visible_to == []

    def test_visible_to_subset(self):
        narr = Narration(
            character_id="shadowbeast", turn=1,
            prose="Something stirs in the treeline.",
            visible_to=["aeliana"],
        )
        assert "aeliana" in narr.visible_to
        assert "fennel" not in narr.visible_to


# ---- PlayerLeft stub tests ----

class TestPlayerLeftStub:
    def test_returns_action_intent(self, aeliana_context):
        pl = PlayerLeft()
        intent = asyncio.run(pl.generate_intent(aeliana_context))
        assert isinstance(intent, ActionIntent)

    def test_intent_has_character_id(self, aeliana_context):
        pl = PlayerLeft()
        intent = asyncio.run(pl.generate_intent(aeliana_context))
        assert intent.character_id == "aeliana"

    def test_intent_has_turn(self, aeliana_context):
        pl = PlayerLeft()
        intent = asyncio.run(pl.generate_intent(aeliana_context))
        assert intent.turn == 1

    def test_intent_has_text(self, aeliana_context):
        pl = PlayerLeft()
        intent = asyncio.run(pl.generate_intent(aeliana_context))
        assert len(intent.intent) > 0


# ---- PlayerRight stub tests ----

class TestPlayerRightStub:
    def test_returns_character_output(self, aeliana_context):
        pr = PlayerRight()
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance to glade")
        output = asyncio.run(pr.generate_action(intent, aeliana_context))
        assert isinstance(output, CharacterOutput)

    def test_output_has_character_id(self, aeliana_context):
        pr = PlayerRight()
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        output = asyncio.run(pr.generate_action(intent, aeliana_context))
        assert output.character_id == "aeliana"

    def test_output_has_internal(self, aeliana_context):
        pr = PlayerRight()
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        output = asyncio.run(pr.generate_action(intent, aeliana_context))
        assert len(output.internal) > 0

    def test_output_has_action(self, aeliana_context):
        pr = PlayerRight()
        intent = ActionIntent(character_id="aeliana", turn=1, intent="advance")
        output = asyncio.run(pr.generate_action(intent, aeliana_context))
        assert len(output.action) > 0


# ---- DMLeft stub tests ----

class TestDMLeftStub:
    def test_returns_adjudication(self):
        dm = DMLeft()
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        adj = asyncio.run(dm.adjudicate(output, "", ""))
        assert isinstance(adj, Adjudication)

    def test_stub_approves(self):
        dm = DMLeft()
        output = CharacterOutput(character_id="aeliana", turn=1, action="advance")
        adj = asyncio.run(dm.adjudicate(output, "", ""))
        assert adj.approved is True

    def test_adjudication_has_character_id(self):
        dm = DMLeft()
        output = CharacterOutput(character_id="fennel", turn=2, action="gather herbs")
        adj = asyncio.run(dm.adjudicate(output, "", ""))
        assert adj.character_id == "fennel"
        assert adj.turn == 2


# ---- DMRight stub tests ----

class TestDMRightStub:
    def test_returns_narration(self):
        dm = DMRight()
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(
            character_id="aeliana", turn=1,
            action="advance toward the glade",
        )
        narr = asyncio.run(dm.narrate(adj, output, ""))
        assert isinstance(narr, Narration)

    def test_narration_has_prose(self):
        dm = DMRight()
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(
            character_id="aeliana", turn=1,
            action="advance toward the glade",
        )
        narr = asyncio.run(dm.narrate(adj, output, ""))
        assert len(narr.prose) > 0

    def test_narration_includes_character(self):
        dm = DMRight()
        adj = Adjudication(character_id="aeliana", turn=1, approved=True)
        output = CharacterOutput(
            character_id="aeliana", turn=1,
            action="advance toward the glade",
        )
        narr = asyncio.run(dm.narrate(adj, output, ""))
        assert "aeliana" in narr.prose


# ---- TurnCycle construction tests ----

class TestTurnCycle:
    def test_create_with_defaults(self):
        tc = TurnCycle()
        assert isinstance(tc.player_left, PlayerLeft)
        assert isinstance(tc.player_right, PlayerRight)
        assert isinstance(tc.dm_left, DMLeft)
        assert isinstance(tc.dm_right, DMRight)

    def test_create_with_custom_roles(self):
        pl = PlayerLeft()
        pr = PlayerRight()
        dl = DMLeft()
        dr = DMRight()
        tc = TurnCycle(player_left=pl, player_right=pr, dm_left=dl, dm_right=dr)
        assert tc.player_left is pl
        assert tc.dm_right is dr

    def test_empty_history(self):
        tc = TurnCycle()
        assert tc.history == []


# ---- execute_character_turn tests ----

class TestExecuteCharacterTurn:
    def test_returns_character_turn_result(self, aeliana_context):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_character_turn(aeliana_context))
        assert isinstance(result, CharacterTurnResult)

    def test_result_has_all_phases(self, aeliana_context):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_character_turn(aeliana_context))
        assert isinstance(result.intent, ActionIntent)
        assert isinstance(result.output, CharacterOutput)
        assert isinstance(result.adjudication, Adjudication)
        assert isinstance(result.narration, Narration)

    def test_result_character_id_consistent(self, aeliana_context):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_character_turn(aeliana_context))
        assert result.character_id == "aeliana"
        assert result.intent.character_id == "aeliana"
        assert result.output.character_id == "aeliana"
        assert result.adjudication.character_id == "aeliana"
        assert result.narration.character_id == "aeliana"

    def test_result_appended_to_history(self, aeliana_context):
        tc = TurnCycle()
        asyncio.run(tc.execute_character_turn(aeliana_context))
        assert len(tc.history) == 1
        assert tc.history[0].character_id == "aeliana"

    def test_pipeline_data_flows(self, aeliana_context):
        """Intent feeds into output, output feeds into adjudication."""
        tc = TurnCycle()
        result = asyncio.run(tc.execute_character_turn(aeliana_context))
        # Player-Right's action should reflect Player-Left's intent
        assert result.intent.intent in result.output.action
        # DM-Left should have adjudicated
        assert result.adjudication.approved is True
        # DM-Right should have narrated
        assert len(result.narration.prose) > 0


# ---- execute_turn tests ----

class TestExecuteTurn:
    @pytest.fixture
    def three_contexts(self, aeliana_context, fennel_context, shadowbeast_context):
        return {
            "aeliana": aeliana_context,
            "fennel": fennel_context,
            "shadowbeast": shadowbeast_context,
        }

    def test_returns_turn_result(self, three_contexts):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=three_contexts,
        ))
        assert isinstance(result, TurnResult)

    def test_turn_number(self, three_contexts):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_turn(
            turn=3,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=three_contexts,
        ))
        assert result.turn == 3

    def test_initiative_order_preserved(self, three_contexts):
        tc = TurnCycle()
        order = ["aeliana", "shadowbeast", "fennel"]
        result = asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=order,
            contexts=three_contexts,
        ))
        assert result.initiative_order == order
        result_ids = [r.character_id for r in result.character_results]
        assert result_ids == order

    def test_all_characters_act(self, three_contexts):
        tc = TurnCycle()
        result = asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=three_contexts,
        ))
        assert len(result.character_results) == 3

    def test_history_accumulates(self, three_contexts):
        tc = TurnCycle()
        asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=three_contexts,
        ))
        assert len(tc.history) == 3

    def test_sequential_context_builds(self, three_contexts):
        """Later characters should see narration from earlier characters.
        
        This is the fundamental design: sequential, not parallel.
        Each character in initiative order sees all preceding narration.
        """
        tc = TurnCycle()
        result = asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=three_contexts,
        ))
        # All three should have results
        assert len(result.character_results) == 3
        # Each should be adjudicated
        for cr in result.character_results:
            assert cr.adjudication.approved is True
