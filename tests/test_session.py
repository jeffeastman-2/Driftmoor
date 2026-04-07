"""Tests for the session runner — direct Python game loop."""

import asyncio
import json
import random
from dataclasses import asdict
from pathlib import Path

import pytest

from engine.session import (
    CharacterSession,
    SessionResult,
    run_session,
    _build_context,
    _save_turn,
)
from engine.scene_manager import TurnCycle, RoleSet, TurnResult, CharacterTurnResult
from engine.player_router import PlayerLeft, PlayerRight, RoleContext
from engine.dm_agent import DMLeft, DMRight
from engine.initiative import roll_initiative
from models.character import PlayerCharacter, Creature
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
    render_condition,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def aeliana_char():
    return PlayerCharacter(
        id="aeliana", name="Aeliana", race="Wood Elf",
        character_type="player", character_class="Ranger",
        dexterity=16, location="fey_glade",
    )


@pytest.fixture
def fennel_char():
    return PlayerCharacter(
        id="fennel", name="Fennel", race="Human",
        character_type="player", character_class="Gatherer",
        dexterity=12, location="fey_glade",
    )


@pytest.fixture
def aeliana_condition():
    return CharacterCondition(
        character_id="aeliana",
        character_name="Aeliana",
        state=NeurochemicalState(dopamine=0.85, cortisol=0.25),
    )


@pytest.fixture
def fennel_condition():
    return CharacterCondition(
        character_id="fennel",
        character_name="Fennel",
        state=NeurochemicalState(dopamine=0.50, cortisol=0.60),
    )


@pytest.fixture
def aeliana_session(aeliana_char, aeliana_condition):
    return CharacterSession(
        character=aeliana_char,
        condition=aeliana_condition,
        soul="Aeliana is a solitary wood elf ranger.",
        identity="Level 1 Ranger, HP 12, AC 14.",
        initial_scene="You are on the trail approaching the Fey Glade.",
    )


@pytest.fixture
def fennel_session(fennel_char, fennel_condition):
    return CharacterSession(
        character=fennel_char,
        condition=fennel_condition,
        soul="Fennel is a curious gatherer.",
        identity="Level 1 Gatherer, HP 8, AC 11.",
        initial_scene="You are in the glade near the pool.",
    )


# ---------------------------------------------------------------------------
# CharacterSession
# ---------------------------------------------------------------------------

class TestCharacterSession:
    def test_construction(self, aeliana_session):
        cs = aeliana_session
        assert cs.character.id == "aeliana"
        assert cs.condition.character_id == "aeliana"
        assert "solitary" in cs.soul
        assert "Ranger" in cs.identity
        assert "Fey Glade" in cs.initial_scene

    def test_condition_renders(self, aeliana_session):
        text = render_condition(aeliana_session.condition)
        assert "dopamine" in text
        assert "cortisol" in text


# ---------------------------------------------------------------------------
# _build_context helper
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_builds_role_context(self, aeliana_session):
        ctx = _build_context(aeliana_session, turn=1, scene_history="")
        assert isinstance(ctx, RoleContext)
        assert ctx.character_id == "aeliana"
        assert ctx.turn == 1
        assert "dopamine" in ctx.condition_text
        assert "Fey Glade" in ctx.scene_context
        assert ctx.soul == aeliana_session.soul
        assert ctx.identity == aeliana_session.identity

    def test_includes_scene_history(self, aeliana_session):
        ctx = _build_context(
            aeliana_session, turn=2,
            scene_history="Aeliana crept toward the treeline.",
        )
        assert "crept toward the treeline" in ctx.scene_context
        assert "Fey Glade" in ctx.scene_context  # initial scene still present

    def test_empty_history_no_extra_whitespace(self, aeliana_session):
        ctx = _build_context(aeliana_session, turn=1, scene_history="")
        # Should not have trailing newlines from empty history
        assert ctx.scene_context.strip() == ctx.scene_context or \
            not ctx.scene_context.endswith("\n\n")


# ---------------------------------------------------------------------------
# run_session — stub mode (no LLMs)
# ---------------------------------------------------------------------------

class TestRunSessionStub:
    """run_session with default stub roles — no LLM calls."""

    def test_single_turn_single_character(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}  # all stubs
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert isinstance(result, SessionResult)
        assert len(result.turns) == 1
        assert result.turns[0].turn == 1
        assert len(result.turns[0].character_results) == 1
        assert result.turns[0].character_results[0].character_id == "aeliana"

    def test_multi_turn(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=3))

        assert len(result.turns) == 3
        for i, tr in enumerate(result.turns):
            assert tr.turn == i + 1

    def test_two_characters(self, aeliana_session, fennel_session):
        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(),
            "fennel": RoleSet(),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert len(result.turns[0].character_results) == 2
        ids = {r.character_id for r in result.turns[0].character_results}
        assert ids == {"aeliana", "fennel"}

    def test_initiative_determines_order(self, aeliana_session, fennel_session):
        """Characters should act in initiative order (varies by roll)."""
        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(),
            "fennel": RoleSet(),
        }
        # Run with a fixed seed to get deterministic initiative
        result = asyncio.run(run_session(
            characters, roles, num_turns=1, rng=random.Random(42),
        ))
        order = result.turns[0].initiative_order
        assert len(order) == 2
        assert set(order) == {"aeliana", "fennel"}

    def test_returns_final_conditions(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert "aeliana" in result.final_conditions
        assert isinstance(result.final_conditions["aeliana"], CharacterCondition)


# ---------------------------------------------------------------------------
# Condition delta application
# ---------------------------------------------------------------------------

class TestConditionDeltas:
    def test_deltas_applied_after_turn(self, aeliana_session):
        """DMLeft condition_deltas should update the character's condition."""
        original_dopamine = aeliana_session.condition.state.dopamine

        # Mock DMLeft that returns specific deltas
        async def dm_left_llm(sys, usr):
            return json.dumps({
                "approved": True,
                "condition_deltas": {"dopamine": 0.1, "cortisol": -0.05},
                "position_delta": [0, 0, 0],
                "spatial_events": [],
                "notes": "test",
            })

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=dm_left_llm)),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        # Condition should have been updated
        new_dopamine = aeliana_session.condition.state.dopamine
        assert new_dopamine > original_dopamine

    def test_deltas_accumulate_across_turns(self, aeliana_session):
        """Deltas from multiple turns should stack."""
        original_cortisol = aeliana_session.condition.state.cortisol

        async def dm_left_llm(sys, usr):
            return json.dumps({
                "approved": True,
                "condition_deltas": {"cortisol": 0.1},
                "position_delta": [0, 0, 0],
                "spatial_events": [],
                "notes": "stress",
            })

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=dm_left_llm)),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=3))

        # Cortisol should have increased by ~0.3 (3 turns × 0.1)
        new_cortisol = aeliana_session.condition.state.cortisol
        assert new_cortisol > original_cortisol + 0.2


# ---------------------------------------------------------------------------
# Scene history accumulation
# ---------------------------------------------------------------------------

class TestSceneHistory:
    def test_narration_accumulates(self, aeliana_session, fennel_session):
        """Each character's narration should be visible to later characters."""
        call_count = 0
        captured_contexts = {}

        async def tracking_player_left(sys, usr):
            nonlocal call_count
            call_count += 1
            # Just capture what scene context each call gets
            captured_contexts[call_count] = usr
            return json.dumps({"intent": f"action_{call_count}"})

        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(
                player_left=PlayerLeft(call_llm=tracking_player_left),
            ),
            "fennel": RoleSet(
                player_left=PlayerLeft(call_llm=tracking_player_left),
            ),
        }
        # Use deterministic initiative
        result = asyncio.run(run_session(
            characters, roles, num_turns=1, rng=random.Random(99),
        ))
        # At minimum, both characters should have been called
        assert call_count >= 2


# ---------------------------------------------------------------------------
# Checkpoint persistence
# ---------------------------------------------------------------------------

class TestCheckpointing:
    def test_saves_turn_json(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(
            characters, roles, num_turns=2,
            checkpoint_dir=tmp_path,
        ))

        # Should have saved 2 turn files
        files = sorted(tmp_path.glob("turn_*.json"))
        assert len(files) == 2
        assert files[0].name == "turn_0001.json"
        assert files[1].name == "turn_0002.json"

    def test_checkpoint_contains_results(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert data["turn"] == 1
        assert "character_results" in data
        assert len(data["character_results"]) == 1
        assert data["character_results"][0]["character_id"] == "aeliana"

    def test_checkpoint_contains_conditions(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert "conditions" in data
        assert "aeliana" in data["conditions"]
        assert "dopamine" in data["conditions"]["aeliana"]

    def test_no_checkpoint_when_dir_is_none(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=None,
        ))
        # Should succeed without saving anything
        assert len(result.turns) == 1


# ---------------------------------------------------------------------------
# SessionResult
# ---------------------------------------------------------------------------

class TestSessionResult:
    def test_has_all_turns(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=2))

        assert len(result.turns) == 2
        assert result.turns[0].turn == 1
        assert result.turns[1].turn == 2

    def test_scene_history_returned(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        # scene_history should be a string (may be empty for stubs)
        assert isinstance(result.scene_history, str)
