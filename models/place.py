"""Place model for the Driftmoor RPG engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Place:
    """A location in the game world, from region down to individual room."""

    id: str
    name: str
    description: str = ""
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)
    who_is_here: list[str] = field(default_factory=list)
    place_raw: str = ""
    contents_raw: str = ""
    dynamic_state: dict[str, str] = field(default_factory=dict)
