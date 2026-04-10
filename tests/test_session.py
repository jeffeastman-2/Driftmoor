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
    iter_session,
    _build_context,
    _save_turn,
    _checkpoint_filename,
    COMBAT_EVENT,
    EXIT_EVENT,
    MELEE_DURATION,
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
from models.space_time import GameTime


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
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — 0, 0, 0\n"
                "**CONDITION** — dopamine +0.1, cortisol -0.05\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

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
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — 0, 0, 0\n"
                "**CONDITION** — cortisol +0.1\n"
                "**EVENTS** — none\n"
                "**NOTES** — stress"
            )

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
            return "**INTENT** — " + f"action_{call_count}" + "\n**MOVEMENT** — none\n**TARGET** — none"

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

    def test_game_time_checkpoint_naming(self, aeliana_session, tmp_path):
        """With game_time, checkpoints use day/time naming."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=2,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        files = sorted(tmp_path.glob("day*.json"))
        assert len(files) == 2
        assert files[0].name == "day1_14h30m.json"
        assert files[1].name == "day1_14h40m.json"

    def test_game_time_melee_naming(self, aeliana_session, tmp_path):
        """Melee turns use 1-minute intervals."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=1, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=3,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        files = sorted(tmp_path.glob("day*.json"))
        assert len(files) == 3
        assert files[0].name == "day1_14h30m.json"
        assert files[1].name == "day1_14h31m.json"
        assert files[2].name == "day1_14h32m.json"

    def test_game_time_in_checkpoint_data(self, aeliana_session, tmp_path):
        """Checkpoint JSON should contain game_time metadata."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        data = json.loads((tmp_path / "day1_14h30m.json").read_text())
        assert data["game_time"]["hour"] == 14
        assert data["game_time"]["minute"] == 30
        assert data["game_time"]["day"] == 1
        assert data["game_time"]["period"] == "afternoon"

    def test_no_game_time_uses_turn_naming(self, aeliana_session, tmp_path):
        """Without game_time, falls back to turn_NNNN naming."""
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))
        files = sorted(tmp_path.glob("turn_*.json"))
        assert len(files) == 1
        assert files[0].name == "turn_0001.json"


class TestCheckpointFilename:
    def test_without_game_time(self):
        assert _checkpoint_filename(1) == "turn_0001.json"
        assert _checkpoint_filename(42) == "turn_0042.json"

    def test_with_game_time(self):
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        assert _checkpoint_filename(1, gt) == "day1_14h30m.json"

    def test_midnight_wrap(self):
        gt = GameTime(hour=0, minute=5, day=2, season="winter",
                      turn_duration=10, absolute_turn=0)
        assert _checkpoint_filename(1, gt) == "day2_00h05m.json"


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


# ---------------------------------------------------------------------------
# DMLeft receives game_state and geometry context
# ---------------------------------------------------------------------------

class TestDMLeftContext:
    def test_geometry_passed_to_dmleft(self, aeliana_session):
        """DMLeft should receive the geometry_summary in its prompt."""
        captured_prompts = []

        async def capturing_dm_llm(sys, usr):
            captured_prompts.append(usr)
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — 0, 0, 0\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=capturing_dm_llm)),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            geometry_summary="## Boundaries\nRepulsion boundary blocks shadowbeast",
        ))

        assert len(captured_prompts) >= 1
        assert "Repulsion boundary blocks shadowbeast" in captured_prompts[0]

    def test_game_state_passed_to_dmleft(self, aeliana_session):
        """DMLeft should receive creature stats in its prompt."""
        captured_prompts = []

        async def capturing_dm_llm(sys, usr):
            captured_prompts.append(usr)
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — 0, 0, 0\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=capturing_dm_llm)),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            game_state_summary="Shadowbeast: resistant to nonmagical B/P/S",
        ))

        assert len(captured_prompts) >= 1
        assert "resistant to nonmagical B/P/S" in captured_prompts[0]

    def test_both_contexts_empty_by_default(self, aeliana_session):
        """Without context, DMLeft still works (stub mode)."""
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))
        assert len(result.turns) == 1


# ---------------------------------------------------------------------------
# Combat time-switching
# ---------------------------------------------------------------------------

def _make_creature_session(char_id="shadowbeast_1", faction="hostile"):
    """Build a minimal hostile creature session for testing."""
    creature = Creature(
        id=char_id, name="Shadowbeast", race="Monstrosity",
        character_type="creature", dexterity=14,
        faction=faction,
    )
    condition = CharacterCondition(
        character_id=char_id,
        character_name="Shadowbeast",
        state=NeurochemicalState(dopamine=0.80, cortisol=0.10),
    )
    return CharacterSession(
        character=creature,
        condition=condition,
        soul="You are a predator of shadow.",
        identity="Shadowbeast. CR ½.",
        initial_scene="You lurk in the darkness.",
    )


def _combat_dm_llm(event=COMBAT_EVENT):
    """Return a DMLeft LLM stub that emits the given event."""
    async def _llm(sys, usr):
        return (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — 0, 0, 0\n"
            "**CONDITION** — none\n"
            f"**EVENTS** — {event}\n"
            "**NOTES** — combat test"
        )
    return _llm


def _no_event_dm_llm():
    """Return a DMLeft LLM stub that emits no events."""
    async def _llm(sys, usr):
        return (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**POSITION DELTA** — 0, 0, 0\n"
            "**CONDITION** — none\n"
            "**EVENTS** — none\n"
            "**NOTES** — peaceful"
        )
    return _llm


class TestCombatTimeSwitching:
    """Tests for automatic exploration→melee→exploration time switching."""

    def test_combat_initiated_switches_to_melee(self, aeliana_session):
        """combat_initiated event should switch turn_duration to 1."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Creature's DMLeft emits combat_initiated
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            game_time=gt, rng=random.Random(42),
        ))
        # After combat_initiated, turn_duration should be melee (1)
        assert gt.turn_duration == MELEE_DURATION

    def test_combat_end_restores_exploration(self, aeliana_session):
        """When hostile exits scene, combat ends and duration reverts."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }

        call_count = {"n": 0}

        async def turn1_combat_turn2_exit(sys, usr):
            call_count["n"] += 1
            if call_count["n"] <= 2:
                # Turn 1: both characters, beast attacks
                if "shadowbeast" in usr.lower() or "Shadowbeast" in usr:
                    return (
                        "**APPROVED** — Yes\n"
                        "**MODIFIED ACTION** — none\n"
                        "**POSITION DELTA** — 0, 0, 0\n"
                        "**CONDITION** — none\n"
                        f"**EVENTS** — {COMBAT_EVENT}\n"
                        "**NOTES** — beast attacks"
                    )
            if call_count["n"] <= 4:
                # Turn 2: beast exits
                if "shadowbeast" in usr.lower() or "Shadowbeast" in usr:
                    return (
                        "**APPROVED** — Yes\n"
                        "**MODIFIED ACTION** — none\n"
                        "**POSITION DELTA** — 0, 0, 0\n"
                        "**CONDITION** — none\n"
                        f"**EVENTS** — {EXIT_EVENT}\n"
                        "**NOTES** — beast flees"
                    )
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**POSITION DELTA** — 0, 0, 0\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — peaceful"
            )

        roles = {
            "aeliana": RoleSet(
                dm_left=DMLeft(call_llm=turn1_combat_turn2_exit),
            ),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=turn1_combat_turn2_exit),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=3,
            game_time=gt, rng=random.Random(42),
        ))
        # After beast exits, combat should end and duration should revert
        assert gt.turn_duration == 10

    def test_exits_scene_removes_from_initiative(self, aeliana_session):
        """A character that exits_scene should not act in later turns."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=1, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Beast exits on turn 1
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=2,
            game_time=gt, rng=random.Random(42),
        ))
        # Turn 2 should only have aeliana
        turn2_ids = [cr.character_id for cr in result.turns[1].character_results]
        assert "aeliana" in turn2_ids
        assert "shadowbeast_1" not in turn2_ids

    def test_no_combat_without_game_time(self, aeliana_session):
        """Without game_time, combat_initiated event is ignored for timing."""
        beast = _make_creature_session()

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        # Should not crash — combat events without game_time are no-ops
        result = asyncio.run(run_session(
            characters, roles, num_turns=1,
            rng=random.Random(42),
        ))
        assert len(result.turns) == 1

    def test_combat_checkpoints_use_melee_intervals(self, aeliana_session, tmp_path):
        """After combat starts, checkpoints should be 1 minute apart."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Beast attacks turn 1, combat continues
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=3,
            game_time=gt, checkpoint_dir=tmp_path,
            rng=random.Random(42),
        ))
        files = sorted(tmp_path.glob("day*.json"))
        names = [f.name for f in files]
        # Turn 1 at exploration pace (15:00), then combat switches.
        # Turn 2 at melee (15:01), turn 3 at melee (15:02)
        # But the switch happens mid-turn-1 so turn 1 checkpoint is still
        # at the pre-advance time. The advance after turn 1 uses the NEW
        # duration (1 min). So: turn1=15:00, turn2=15:01, turn3=15:02
        assert names[0] == "day1_15h00m.json"
        assert names[1] == "day1_15h01m.json"
        assert names[2] == "day1_15h02m.json"

    def test_faction_defaults(self):
        """Characters default to appropriate factions."""
        pc = PlayerCharacter(
            id="test", name="Test", race="Human",
            character_type="player",
        )
        assert pc.faction == "neutral"  # base default

        creature = Creature(
            id="beast", name="Beast", race="Monster",
            character_type="creature", faction="hostile",
        )
        assert creature.faction == "hostile"

    def test_empty_scene_breaks_early(self):
        """If all characters exit, session ends early."""
        beast = _make_creature_session()
        pc = PlayerCharacter(
            id="test_pc", name="Test", race="Human",
            character_type="player", dexterity=12, faction="party",
        )
        pc_session = CharacterSession(
            character=pc,
            condition=CharacterCondition(
                character_id="test_pc", character_name="Test",
                state=NeurochemicalState(),
            ),
            soul="", identity="", initial_scene="A field.",
        )
        gt = GameTime(hour=12, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {"test_pc": pc_session, "shadowbeast_1": beast}
        # Both exit on turn 1
        roles = {
            "test_pc": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=5,
            game_time=gt, rng=random.Random(42),
        ))
        # Should stop after turn 1 since no characters remain
        assert len(result.turns) == 1


class TestDMLeftCombatPrompt:
    """Verify DMLeft system prompt includes combat event guidance."""

    def test_prompt_mentions_combat_initiated(self):
        dm = DMLeft()
        prompt = dm.build_system_prompt()
        assert "combat_initiated" in prompt

    def test_prompt_mentions_exits_scene(self):
        dm = DMLeft()
        prompt = dm.build_system_prompt()
        assert "exits_scene" in prompt
