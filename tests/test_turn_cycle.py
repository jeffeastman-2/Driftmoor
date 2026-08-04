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
from engine.scene_manager import TurnCycle, CharacterTurnResult, TurnResult, RoleSet


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
            new_position=(5.0, 3.0, "GLADE"),
        )
        assert adj.new_position == (5.0, 3.0, "GLADE")


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


class TestPlayerLeftTargetInference:
    def test_infers_target_from_intent_and_perception_items(self):
        pl = PlayerLeft()
        ctx = RoleContext(
            character_id="amara",
            turn=3,
            condition_text="",
            scene_context="",
            soul="",
            identity="",
            perception=(
                "Items in this zone:\n"
                "- Snapped torch (~10 ft away)\n"
                "- Drag marks (~15 ft away) (already examined)"
            ),
        )
        raw = (
            "**INTENT** Search the area around the snapped torch for clues.\n"
            "**MOVEMENT** 138, 265\n"
            "**TARGET** none"
        )
        result = pl.parse_response(raw, ctx)
        assert result.interaction_target == "Snapped torch"

    def test_keeps_explicit_target_when_present(self):
        pl = PlayerLeft()
        ctx = RoleContext(
            character_id="thorgrim",
            turn=4,
            condition_text="",
            scene_context="",
            soul="",
            identity="",
            perception=(
                "Items in this zone:\n"
                "- Snapped torch (~10 ft away)\n"
                "- Drag marks (~15 ft away)"
            ),
        )
        raw = (
            "**INTENT** Examine the stain and compare it to the drag marks.\n"
            "**MOVEMENT** none\n"
            "**TARGET** Drag marks"
        )
        result = pl.parse_response(raw, ctx)
        assert result.interaction_target == "Drag marks"

    def test_no_inference_without_items_block(self):
        pl = PlayerLeft()
        ctx = RoleContext(
            character_id="seraphina",
            turn=2,
            condition_text="",
            scene_context="",
            soul="",
            identity="",
            perception="No other creatures are visible from your current position.",
        )
        raw = (
            "**INTENT** Search the area for clues.\n"
            "**MOVEMENT** none\n"
            "**TARGET** none"
        )
        result = pl.parse_response(raw, ctx)
        assert result.interaction_target is None


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


# ---- Ground truth parser edge cases ----

AELIANA_GROUND_TRUTH = """
**INTERNAL**
The trail ends here. Warmth in the air\u2014wrong warmth, not sun-fed. The shimmer ahead calls. No predator scent, no decay. Only power, unguarded or waiting. The shadowbeasts would not linger here. This is older, or broken. The obelisk. Its echo may have spilled here. Step soft. Do not startle the memory.

**BODY LANGUAGE**
Crouched low, one hand on bowstring, other hovering near quiver. Weight balanced on the balls of her feet. Her eyes scan the clearing with slow, deliberate sweeps. Breathing shallow and silent.

**SPOKEN**
(silent)

**ACTION**
Move in a slow, wide arc along the edge of the clearing toward the rising light, keeping low and observing for disturbances before approaching directly.
"""

FENNEL_GROUND_TRUTH = """
**INTERNAL**
Pull\u2014toward her. Anchor. Not alone. Cold edge at back. Watching. Waiting. Stillness holds. Sound breaks. Teeth in silence. Do not break. Do not call. Stay. Stay. Stay.

**BODY LANGUAGE**
Fennel freezes, breath shallow and controlled. His raised hand stops mid-motion. His eyes lock on Aeliana's back, then flick once toward the shifting shadow before fixing forward again. Stance tightens, knees slightly bent, ready but unmoving.

**SPOKEN**
(silent)

**ACTION**
Slowly wave arms from glade edge toward her, hold up open-hand stop gesture, then point directly toward the shadowbeast's position.
"""

SHADOWBEAST_GROUND_TRUTH = """
**INTERNAL**
warmth-pulse close... alert-shape breathing-slow at boundary... shimmer-wrong pushes-back... pull stronger... shadow-body coils... hunger-thrum... still... wait... dusk-pull builds...

**BODY LANGUAGE**
Shadows along the treeline thicken unnaturally. Tendrils of black mist curl slowly outward, then retract. The air grows colder near the boundary. A faint vibration hums through the ground.

**SPOKEN**
(silence)

**ACTION**
Slides sideways along the boundary, keeping equal distance from the watching prey. Settles into stillness opposite the one near the pool. Holds.
"""


class TestGroundTruthParsing:
    """Verify the PlayerRight parser handles real LLM ground truth output."""

    @pytest.fixture
    def parser(self):
        return PlayerRight()

    @pytest.fixture
    def ctx(self):
        return RoleContext(
            character_id="test", turn=1,
            condition_text="", scene_context="", soul="", identity="",
        )

    def test_aeliana_em_dash_in_internal(self, parser, ctx):
        result = parser.parse_response(AELIANA_GROUND_TRUTH, ctx)
        assert "wrong warmth" in result.internal
        assert result.internal.startswith("The trail ends here")

    def test_aeliana_body_language(self, parser, ctx):
        result = parser.parse_response(AELIANA_GROUND_TRUTH, ctx)
        assert "bowstring" in result.body_language
        assert "Crouched" in result.body_language

    def test_aeliana_spoken_is_silent(self, parser, ctx):
        result = parser.parse_response(AELIANA_GROUND_TRUTH, ctx)
        assert "silent" in result.spoken.lower()

    def test_aeliana_action(self, parser, ctx):
        result = parser.parse_response(AELIANA_GROUND_TRUTH, ctx)
        assert "slow, wide arc" in result.action

    def test_fennel_em_dash_starts_internal(self, parser, ctx):
        """Fennel's internal starts with 'Pull\u2014toward her' \u2014 em-dash right after a word."""
        result = parser.parse_response(FENNEL_GROUND_TRUTH, ctx)
        assert "Pull" in result.internal
        assert "toward her" in result.internal

    def test_fennel_fragmented_prose(self, parser, ctx):
        """Fennel's internal is fragmented: short sentences, no verbs sometimes."""
        result = parser.parse_response(FENNEL_GROUND_TRUTH, ctx)
        assert "Teeth in silence" in result.internal
        assert "Stay. Stay. Stay." in result.internal

    def test_fennel_body_language(self, parser, ctx):
        result = parser.parse_response(FENNEL_GROUND_TRUTH, ctx)
        assert "freezes" in result.body_language

    def test_fennel_action(self, parser, ctx):
        result = parser.parse_response(FENNEL_GROUND_TRUTH, ctx)
        assert "wave arms" in result.action
        assert "shadowbeast" in result.action

    def test_shadowbeast_sensation_language(self, parser, ctx):
        """Shadowbeast uses non-human sensation language with ellipsis."""
        result = parser.parse_response(SHADOWBEAST_GROUND_TRUTH, ctx)
        assert "warmth-pulse" in result.internal
        assert "hunger-thrum" in result.internal

    def test_shadowbeast_silence_variant(self, parser, ctx):
        """Shadowbeast uses '(silence)' not '(silent)'."""
        result = parser.parse_response(SHADOWBEAST_GROUND_TRUTH, ctx)
        assert "silence" in result.spoken.lower()

    def test_shadowbeast_body_language(self, parser, ctx):
        result = parser.parse_response(SHADOWBEAST_GROUND_TRUTH, ctx)
        assert "Tendrils" in result.body_language

    def test_shadowbeast_action(self, parser, ctx):
        result = parser.parse_response(SHADOWBEAST_GROUND_TRUTH, ctx)
        assert "boundary" in result.action
        assert "Holds" in result.action

    def test_no_spoken_section_at_all(self, parser, ctx):
        """Edge case: SPOKEN section completely absent."""
        raw = (
            "**INTERNAL**\nHunger.\n\n"
            "**BODY LANGUAGE**\nCoiled.\n\n"
            "**ACTION**\nStrike."
        )
        result = parser.parse_response(raw, ctx)
        assert result.internal == "Hunger."
        assert result.body_language == "Coiled."
        assert result.spoken == ""
        assert result.action == "Strike."

    def test_spoken_section_strips_models_own_quote_marks(self, parser, ctx):
        """A model routinely wraps SPOKEN in its own quotes even though the
        field is dialogue-only by convention. Left in place, the web log's
        display quoting doubles up around them (e.g. ""like this""), which is
        exactly what showed up live for Elyssa's own (non-reply) turns."""
        raw = (
            "**INTERNAL**\nCurious.\n\n"
            '**SPOKEN**\n"Observe the intersection point here."\n\n'
            "**ACTION**\nPoints at the map."
        )
        result = parser.parse_response(raw, ctx)
        assert result.spoken == "Observe the intersection point here."


# ---- Per-character provider routing ----

class TestPerCharacterRouting:
    """Verify that character_roles routes each character to its own LLM."""

    def test_different_llm_per_character(self, aeliana_context, fennel_context):
        """Aeliana uses one mock LLM, Fennel uses a different one."""

        async def grok_llm(system, user):
            return "**INTENT** — grok intent\n**MOVEMENT** — none\n**TARGET** — none"

        async def chatgpt_llm(system, user):
            return "**INTENT** — chatgpt intent\n**MOVEMENT** — none\n**TARGET** — none"

        tc = TurnCycle(
            character_roles={
                "aeliana": RoleSet(
                    player_left=PlayerLeft(call_llm=grok_llm),
                ),
                "fennel": RoleSet(
                    player_left=PlayerLeft(call_llm=chatgpt_llm),
                ),
            },
        )

        r1 = asyncio.run(tc.execute_character_turn(aeliana_context))
        assert r1.intent.intent == "grok intent"

        r2 = asyncio.run(tc.execute_character_turn(fennel_context))
        assert r2.intent.intent == "chatgpt intent"

    def test_unrouted_character_uses_defaults(self, shadowbeast_context):
        """Characters not in character_roles get stub defaults."""
        tc = TurnCycle(
            character_roles={"aeliana": RoleSet()},  # only aeliana routed
        )
        result = asyncio.run(tc.execute_character_turn(shadowbeast_context))
        # Shadowbeast falls back to the default stub
        assert result.intent.intent == "observe surroundings and hold position"

    def test_roleset_partial_override(self, aeliana_context):
        """RoleSet can override just one role; others get defaults."""

        async def custom_llm(system, user):
            return "**INTENT** — custom only for player-left\n**MOVEMENT** — none\n**TARGET** — none"

        tc = TurnCycle(
            character_roles={
                "aeliana": RoleSet(
                    player_left=PlayerLeft(call_llm=custom_llm),
                    # player_right, dm_left, dm_right are default stubs
                ),
            },
        )
        result = asyncio.run(tc.execute_character_turn(aeliana_context))
        assert result.intent.intent == "custom only for player-left"
        # The rest should be stub defaults
        assert result.adjudication.approved is True

    def test_three_providers_in_one_turn(
        self, aeliana_context, fennel_context, shadowbeast_context,
    ):
        """Full turn with three different mock providers."""

        async def grok(s, u):
            return "**INTENT** — grok\n**MOVEMENT** — none\n**TARGET** — none"

        async def chatgpt(s, u):
            return "**INTENT** — chatgpt\n**MOVEMENT** — none\n**TARGET** — none"

        async def gemini(s, u):
            return "**INTENT** — gemini\n**MOVEMENT** — none\n**TARGET** — none"

        tc = TurnCycle(
            character_roles={
                "aeliana": RoleSet(player_left=PlayerLeft(call_llm=grok)),
                "fennel": RoleSet(player_left=PlayerLeft(call_llm=chatgpt)),
                "shadowbeast": RoleSet(player_left=PlayerLeft(call_llm=gemini)),
            },
        )

        contexts = {
            "aeliana": aeliana_context,
            "fennel": fennel_context,
            "shadowbeast": shadowbeast_context,
        }
        result = asyncio.run(tc.execute_turn(
            turn=1,
            initiative_order=["aeliana", "shadowbeast", "fennel"],
            contexts=contexts,
        ))

        intents = {r.character_id: r.intent.intent for r in result.character_results}
        assert intents["aeliana"] == "grok"
        assert intents["shadowbeast"] == "gemini"
        assert intents["fennel"] == "chatgpt"


# ---- RoleSet datatype ----

class TestRoleSet:
    def test_default_construction(self):
        rs = RoleSet()
        assert isinstance(rs.player_left, PlayerLeft)
        assert isinstance(rs.player_right, PlayerRight)
        assert isinstance(rs.dm_left, DMLeft)
        assert isinstance(rs.dm_right, DMRight)

    def test_partial_construction(self):
        pl = PlayerLeft()
        rs = RoleSet(player_left=pl)
        assert rs.player_left is pl
        assert isinstance(rs.dm_right, DMRight)
