"""DM-Left and DM-Right role implementations.

DM-Left:  Adjudicates character actions against game rules and spatial state.
          Validates movement, checks boundaries, computes condition deltas
          and spatial events. In production, calls an LLM with DM context.

DM-Right: Narrates adjudicated actions into scene prose visible to
          other characters. In production, calls an LLM to write narrative.

Both roles are async to support LLM API calls in production.
Stub implementations return minimal valid data without calling any LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from engine.player_router import CharacterOutput


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Adjudication:
    """Output of DM-Left: rules enforcement and state changes."""
    character_id: str
    turn: int
    approved: bool = True
    modified_action: Optional[str] = None
    position_delta: Optional[tuple[float, float, float]] = None
    condition_deltas: dict[str, float] = field(default_factory=dict)
    spatial_events: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Narration:
    """Output of DM-Right: narrative prose."""
    character_id: str
    turn: int
    prose: str = ""
    visible_to: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# DM-Left stub
# ---------------------------------------------------------------------------

class DMLeft:
    """Adjudicates character actions against game rules and spatial state.

    Stub: approves all actions with no state changes.
    Override adjudicate() for LLM integration.
    """

    async def adjudicate(
        self,
        character_output: CharacterOutput,
        game_state_summary: str,
        geometry_summary: str,
    ) -> Adjudication:
        return Adjudication(
            character_id=character_output.character_id,
            turn=character_output.turn,
            approved=True,
        )


# ---------------------------------------------------------------------------
# DM-Right stub
# ---------------------------------------------------------------------------

class DMRight:
    """Narrates adjudicated actions into scene prose.

    Stub: returns a minimal one-line narration.
    Override narrate() for LLM integration.
    """

    async def narrate(
        self,
        adjudication: Adjudication,
        character_output: CharacterOutput,
        scene_history: str,
    ) -> Narration:
        action_text = character_output.action or "(no action)"
        return Narration(
            character_id=adjudication.character_id,
            turn=adjudication.turn,
            prose=f"{character_output.character_id} {action_text}.",
            visible_to=[],
        )
