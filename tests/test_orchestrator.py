"""Tests for the multi-scene Orchestrator.

The Orchestrator uses GameClock to decide which scene advances next.
Each scene wraps the existing TurnCycle with its own characters,
roles, and state. Combat scenes advance in 6s ticks, exploration
in 60s ticks — the min-cursor rule naturally pauses exploration
scenes during combat.
"""

import asyncio
import random
import pytest

from engine.game_clock import GameClock, SceneClock, TimeScale
from engine.multi_scene import SceneSession, Orchestrator
from engine.scene_manager import TurnCycle, RoleSet
from engine.player_router import PlayerLeft
from engine.session import CharacterSession
from models.character import Character
from models.condition import CharacterCondition, NeurochemicalState


# ---- Fixtures ----

def _make_character(char_id: str) -> Character:
    return Character(
        id=char_id,
        name=char_id.capitalize(),
        race="Human",
        character_type="player",
        identity_raw="",
        soul_raw="",
    )


def _make_session(char_id: str, scene: str = "") -> CharacterSession:
    return CharacterSession(
        character=_make_character(char_id),
        condition=CharacterCondition(
            character_id=char_id,
            character_name=char_id.capitalize(),
            state=NeurochemicalState(),
        ),
        soul=f"You are {char_id}.",
        identity=f"Character: {char_id}",
        initial_scene=scene or "A quiet place.",
    )


@pytest.fixture
def glade_session():
    return SceneSession(
        scene_id="fey_glade",
        characters={
            "aeliana": _make_session("aeliana", "The fey glade shimmers."),
            "fennel": _make_session("fennel", "The fey glade shimmers."),
        },
        roles={
            "aeliana": RoleSet(),
            "fennel": RoleSet(),
        },
    )


@pytest.fixture
def market_session():
    return SceneSession(
        scene_id="market",
        characters={
            "mira": _make_session("mira", "The market bustles."),
        },
        roles={
            "mira": RoleSet(),
        },
    )


# =========================================================================
# SceneSession
# =========================================================================

class TestSceneSession:
    def test_create(self, glade_session):
        assert glade_session.scene_id == "fey_glade"
        assert "aeliana" in glade_session.characters
        assert "fennel" in glade_session.characters

    def test_character_ids(self, glade_session):
        ids = glade_session.character_ids
        assert "aeliana" in ids
        assert "fennel" in ids

    def test_turn_counter_starts_at_zero(self, glade_session):
        assert glade_session.turn == 0

    def test_scene_history_starts_empty(self, glade_session):
        assert glade_session.scene_history == ""

    def test_run_turn_increments_counter(self, glade_session):
        asyncio.run(glade_session.run_turn())
        assert glade_session.turn == 1

    def test_run_turn_returns_turn_result(self, glade_session):
        result = asyncio.run(glade_session.run_turn())
        assert result.turn == 1
        assert len(result.character_results) == 2

    def test_run_turn_accumulates_history(self, glade_session):
        asyncio.run(glade_session.run_turn())
        assert len(glade_session.scene_history) > 0

    def test_run_two_turns(self, glade_session):
        asyncio.run(glade_session.run_turn())
        asyncio.run(glade_session.run_turn())
        assert glade_session.turn == 2


# =========================================================================
# Orchestrator
# =========================================================================

class TestOrchestrator:
    def test_create(self, glade_session):
        orch = Orchestrator()
        orch.add_scene(glade_session)
        assert "fey_glade" in orch.scenes

    def test_run_one_tick(self, glade_session):
        orch = Orchestrator()
        orch.add_scene(glade_session)
        scene_id, result = asyncio.run(orch.run_one())
        assert scene_id == "fey_glade"
        assert result.turn == 1
        assert orch.clock.scenes["fey_glade"].time_cursor == 600.0

    def test_two_scenes_alternation(self, glade_session, market_session):
        """Two exploration scenes at same heartbeat should alternate."""
        orch = Orchestrator()
        orch.add_scene(glade_session)
        orch.add_scene(market_session)

        # First tick: both at 0, one gets picked
        s1, _ = asyncio.run(orch.run_one())
        # That scene is now at 60, the other is at 0
        s2, _ = asyncio.run(orch.run_one())
        # They should have picked different scenes
        assert {s1, s2} == {"fey_glade", "market"}

    def test_combat_scene_runs_many_before_exploration(
        self, glade_session, market_session,
    ):
        """After one exploration tick, combat scene needs 100 ticks to catch up."""
        orch = Orchestrator()
        orch.add_scene(glade_session)
        orch.add_scene(market_session)

        # Market does one exploration turn
        asyncio.run(orch.run_one())  # one scene at 600, other at 0
        asyncio.run(orch.run_one())  # both at 600

        # Now glade enters combat
        orch.enter_combat("fey_glade")

        # Market does one more exploration turn → 1200
        # Glade is at 600. For next ~100 ticks, glade should go.
        scene_ids = []
        for _ in range(101):
            sid, _ = asyncio.run(orch.run_one())
            scene_ids.append(sid)

        # First should be market (both at 600, but market goes to 1200)
        # Then glade should run ~100 times to catch up from 600 to 1200
        glade_count = scene_ids.count("fey_glade")
        assert glade_count >= 99  # at least 99 of 101 should be glade

    def test_enter_exit_combat(self, glade_session):
        orch = Orchestrator()
        orch.add_scene(glade_session)
        orch.enter_combat("fey_glade")
        assert orch.clock.scenes["fey_glade"].in_combat is True
        orch.exit_combat("fey_glade")
        assert orch.clock.scenes["fey_glade"].in_combat is False

    def test_global_time_property(self, glade_session, market_session):
        orch = Orchestrator()
        orch.add_scene(glade_session)
        orch.add_scene(market_session)
        assert orch.global_time == 0.0
        asyncio.run(orch.run_one())
        # One scene advanced, the other hasn't
        assert orch.global_time == 0.0
        asyncio.run(orch.run_one())
        # Both advanced once
        assert orch.global_time == 600.0

    def test_run_n_ticks(self, glade_session):
        orch = Orchestrator()
        orch.add_scene(glade_session)
        results = asyncio.run(orch.run(3))
        assert len(results) == 3
        assert glade_session.turn == 3
        assert orch.clock.scenes["fey_glade"].time_cursor == 1800.0
