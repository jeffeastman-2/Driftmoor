"""Multi-scene orchestrator using GameClock for time synchronisation.

SceneSession wraps a single scene's characters, roles, and turn state.
Orchestrator manages multiple SceneSessions, advancing the scene
furthest behind in global time on each tick.

This replaces run_session() for multi-scene play while reusing
TurnCycle, initiative, and condition mechanics unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from engine.game_clock import GameClock
from engine.initiative import roll_initiative
from engine.player_router import RoleContext
from engine.scene_manager import TurnCycle, TurnResult, RoleSet
from engine.session import CharacterSession
from models.condition import render_condition


# ---------------------------------------------------------------------------
# SceneSession — one scene's state and turn execution
# ---------------------------------------------------------------------------

class SceneSession:
    """Wraps a scene's characters, roles, and accumulated state.

    Each call to run_turn() executes one full turn (all characters
    in initiative order) through the 4-role pipeline and returns
    the TurnResult.
    """

    def __init__(
        self,
        scene_id: str,
        characters: dict[str, CharacterSession],
        roles: dict[str, RoleSet],
        *,
        game_state_summary: str = "",
        geometry_summary: str = "",
        rng: Optional[random.Random] = None,
    ) -> None:
        self.scene_id = scene_id
        self.characters = characters
        self.roles = roles
        self.game_state_summary = game_state_summary
        self.geometry_summary = geometry_summary
        self.rng = rng

        self.turn = 0
        self.scene_history = ""
        self._turn_cycle = TurnCycle(character_roles=roles)

    @property
    def character_ids(self) -> list[str]:
        return list(self.characters.keys())

    async def run_turn(self) -> TurnResult:
        """Execute one turn for all characters in this scene."""
        self.turn += 1

        # Roll initiative
        char_list = [cs.character for cs in self.characters.values()]
        entries = roll_initiative(char_list, rng=self.rng)
        order = [e.character_id for e in entries]

        # Build per-character contexts
        contexts = {}
        for char_id, cs in self.characters.items():
            scene = cs.initial_scene
            if self.scene_history:
                scene = f"{cs.initial_scene}\n\n{self.scene_history}"
            contexts[char_id] = RoleContext(
                character_id=cs.character.id,
                turn=self.turn,
                condition_text=render_condition(cs.condition),
                scene_context=scene,
                soul=cs.soul,
                identity=cs.identity,
            )

        # Execute turn through 4-role pipeline
        result = await self._turn_cycle.execute_turn(
            turn=self.turn,
            initiative_order=order,
            contexts=contexts,
            game_state_summary=self.game_state_summary,
            geometry_summary=self.geometry_summary,
        )

        # Apply condition deltas and accumulate narration
        for cr in result.character_results:
            if cr.adjudication.condition_deltas:
                self.characters[cr.character_id].condition.apply_delta(
                    cr.adjudication.condition_deltas
                )
            if cr.narration.prose:
                self.scene_history += f"\n{cr.narration.prose}"

        return result


# ---------------------------------------------------------------------------
# Orchestrator — multi-scene game loop
# ---------------------------------------------------------------------------

class Orchestrator:
    """Runs multiple scenes, advancing the one furthest behind in time.

    Uses GameClock to track each scene's time cursor. call run_one()
    to execute a single scene tick, or run(n) to execute n ticks
    across all scenes.
    """

    def __init__(self) -> None:
        self.clock = GameClock()
        self.scenes: dict[str, SceneSession] = {}

    def add_scene(
        self,
        session: SceneSession,
        *,
        heartbeat: float | None = None,
    ) -> None:
        """Register a scene with the orchestrator and clock."""
        self.scenes[session.scene_id] = session
        kwargs = {}
        if heartbeat is not None:
            kwargs["heartbeat"] = heartbeat
        self.clock.add_scene(session.scene_id, **kwargs)

    def enter_combat(self, scene_id: str) -> None:
        """Switch a scene to combat time (6s rounds)."""
        self.clock.enter_combat(scene_id)

    def exit_combat(self, scene_id: str) -> None:
        """Switch a scene back to exploration time."""
        self.clock.exit_combat(scene_id)

    @property
    def global_time(self) -> float:
        return self.clock.global_time

    async def run_one(self) -> tuple[str, TurnResult]:
        """Run one tick: advance the scene furthest behind in time.

        Returns (scene_id, TurnResult) for the scene that ran.
        """
        scene_id = self.clock.next_scene()
        session = self.scenes[scene_id]
        result = await session.run_turn()
        self.clock.tick(scene_id)
        return scene_id, result

    async def run(self, n: int) -> list[tuple[str, TurnResult]]:
        """Run n ticks across all scenes.

        Returns a list of (scene_id, TurnResult) for each tick.
        """
        results = []
        for _ in range(n):
            results.append(await self.run_one())
        return results
