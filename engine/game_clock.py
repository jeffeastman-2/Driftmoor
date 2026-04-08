"""GameClock and SceneClock — global time synchronisation for multi-scene play.

Each scene runs on its own SceneClock with a time_cursor and heartbeat.
The GameClock orchestrates which scene advances next (always the one
furthest behind in time).

Combat scenes tick at 6s (one D&D round). Exploration scenes tick at
a configurable rate (default 600s / 10 minutes). This naturally "pauses" exploration
scenes during combat — the combat scene takes many small ticks to
catch up to where the exploration scene already is.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class TimeScale:
    """Standard heartbeat durations in seconds."""
    COMBAT: float = 6.0
    EXPLORATION: float = 600.0


@dataclass
class SceneClock:
    """Time state for a single scene."""

    scene_id: str
    time_cursor: float = 0.0
    heartbeat: float = TimeScale.EXPLORATION
    _exploration_heartbeat: float = field(init=False, repr=False)
    _in_combat: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self._exploration_heartbeat = self.heartbeat

    def tick(self) -> None:
        """Advance the scene clock by one heartbeat."""
        self.time_cursor += self.heartbeat

    def enter_combat(self) -> None:
        """Switch to combat time (6s rounds)."""
        if not self._in_combat:
            self._exploration_heartbeat = self.heartbeat
        self._in_combat = True
        self.heartbeat = TimeScale.COMBAT

    def exit_combat(self) -> None:
        """Return to exploration time."""
        self._in_combat = False
        self.heartbeat = self._exploration_heartbeat

    @property
    def in_combat(self) -> bool:
        return self._in_combat


class GameClock:
    """Global clock managing multiple scene clocks.

    The orchestrator calls next_scene() to find which scene should
    advance, runs that scene's turn, then calls tick() to advance
    that scene's time cursor.
    """

    def __init__(self) -> None:
        self.scenes: dict[str, SceneClock] = {}

    def add_scene(
        self,
        scene_id: str,
        *,
        time_cursor: float = 0.0,
        heartbeat: float = TimeScale.EXPLORATION,
    ) -> SceneClock:
        """Register a new scene with the global clock."""
        sc = SceneClock(
            scene_id=scene_id,
            time_cursor=time_cursor,
            heartbeat=heartbeat,
        )
        self.scenes[scene_id] = sc
        return sc

    def remove_scene(self, scene_id: str) -> None:
        """Remove a scene from the clock."""
        del self.scenes[scene_id]

    def next_scene(self) -> str:
        """Return the scene_id of the scene furthest behind in time."""
        if not self.scenes:
            raise ValueError("No scenes registered")
        return min(self.scenes.values(), key=lambda s: s.time_cursor).scene_id

    def tick(self, scene_id: str) -> None:
        """Advance a scene's clock by its heartbeat."""
        self.scenes[scene_id].tick()

    def enter_combat(self, scene_id: str) -> None:
        """Switch a scene to combat time."""
        self.scenes[scene_id].enter_combat()

    def exit_combat(self, scene_id: str) -> None:
        """Switch a scene back to exploration time."""
        self.scenes[scene_id].exit_combat()

    @property
    def global_time(self) -> float:
        """The minimum time cursor across all scenes.

        This is the "real" elapsed time — no scene is behind this point.
        """
        if not self.scenes:
            return 0.0
        return min(s.time_cursor for s in self.scenes.values())
