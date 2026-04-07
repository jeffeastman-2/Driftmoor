"""Player-Left and Player-Right role implementations.

Player-Left:  Generates structured action intent from character state and context.
              In production, calls an LLM to reason about what the character should do.

Player-Right: Generates in-character prose (INTERNAL/BODY_LANGUAGE/SPOKEN/ACTION)
              from the action intent and character context.
              In production, calls an LLM to write the four-section response.

Both roles are async to support LLM API calls in production.
Stub implementations return minimal valid data without calling any LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class RoleContext:
    """Assembled context for a player role LLM call."""
    character_id: str
    turn: int
    condition_text: str   # Rendered neurochemical state
    scene_context: str    # Zone, occupancy, visible history
    soul: str             # SOUL.md content
    identity: str         # IDENTITY.md content


@dataclass
class ActionIntent:
    """Output of Player-Left: what the character intends to do."""
    character_id: str
    turn: int
    intent: str
    movement_target: Optional[tuple[float, float, float]] = None
    interaction_target: Optional[str] = None


@dataclass
class CharacterOutput:
    """Output of Player-Right: in-character structured prose."""
    character_id: str
    turn: int
    internal: str = ""
    body_language: str = ""
    spoken: str = ""
    action: str = ""


# ---------------------------------------------------------------------------
# Player-Left stub
# ---------------------------------------------------------------------------

class PlayerLeft:
    """Generates structured action intent from character state and context.

    Stub: returns a default hold-position intent.
    Override generate_intent() for LLM integration.
    """

    async def generate_intent(self, context: RoleContext) -> ActionIntent:
        return ActionIntent(
            character_id=context.character_id,
            turn=context.turn,
            intent="observe surroundings and hold position",
        )


# ---------------------------------------------------------------------------
# Player-Right stub
# ---------------------------------------------------------------------------

class PlayerRight:
    """Generates in-character prose from action intent.

    Stub: returns minimal prose echoing the intent.
    Override generate_action() for LLM integration.
    """

    async def generate_action(
        self, intent: ActionIntent, context: RoleContext,
    ) -> CharacterOutput:
        return CharacterOutput(
            character_id=context.character_id,
            turn=context.turn,
            internal=f"Considering: {intent.intent}",
            body_language="Alert, watchful.",
            spoken="",
            action=intent.intent,
        )
