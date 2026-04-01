"""Scene model for the Driftmoor RPG engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scene:
    """An active scene tied to a single place.

    A scene is created wherever at least one player character is present.
    It tracks participating characters and accumulates narrative entries.
    """

    id: str
    place_id: str
    character_ids: list[str] = field(default_factory=list)
    status: str = "active"          # "active", "paused", "resolved"
    turn_started: int = 0
    narrative: list[str] = field(default_factory=list)
