"""Turn cycle orchestrator connecting the four LLM roles.

Data flow per character (sequential within initiative order):

  1. PlayerLeft.generate_intent()   → ActionIntent
  2. PlayerRight.generate_action()  → CharacterOutput
  3. DMLeft.adjudicate()            → Adjudication
  4. DMRight.narrate()              → Narration

Each character sees all preceding narration from the same turn.
This is the fundamental design: sequential, not parallel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from engine.player_router import PlayerLeft, PlayerRight, RoleContext, ActionIntent, CharacterOutput
from engine.dm_agent import DMLeft, DMRight, Adjudication, Narration


# ---------------------------------------------------------------------------
# Result data types
# ---------------------------------------------------------------------------

@dataclass
class CharacterTurnResult:
    """Complete result for one character's turn through the 4-role pipeline."""
    character_id: str
    turn: int
    intent: ActionIntent
    output: CharacterOutput
    adjudication: Adjudication
    narration: Narration


@dataclass
class TurnResult:
    """Complete result for one full turn (all characters in initiative order)."""
    turn: int
    initiative_order: list[str]
    character_results: list[CharacterTurnResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Turn cycle
# ---------------------------------------------------------------------------

class TurnCycle:
    """Orchestrates the four LLM roles through a complete turn.

    Characters act sequentially in initiative order.
    Each character sees all preceding narration from the same turn.
    """

    def __init__(
        self,
        player_left: Optional[PlayerLeft] = None,
        player_right: Optional[PlayerRight] = None,
        dm_left: Optional[DMLeft] = None,
        dm_right: Optional[DMRight] = None,
    ):
        self.player_left = player_left or PlayerLeft()
        self.player_right = player_right or PlayerRight()
        self.dm_left = dm_left or DMLeft()
        self.dm_right = dm_right or DMRight()
        self.history: list[CharacterTurnResult] = []

    async def execute_character_turn(
        self,
        context: RoleContext,
        game_state_summary: str = "",
        geometry_summary: str = "",
        scene_history: str = "",
    ) -> CharacterTurnResult:
        """Execute one character's full turn through the 4-role pipeline."""
        # 1. Player-Left: generate intent
        intent = await self.player_left.generate_intent(context)

        # 2. Player-Right: generate in-character prose
        output = await self.player_right.generate_action(intent, context)

        # 3. DM-Left: adjudicate
        adjudication = await self.dm_left.adjudicate(
            output, game_state_summary, geometry_summary,
        )

        # 4. DM-Right: narrate
        narration = await self.dm_right.narrate(
            adjudication, output, scene_history,
        )

        result = CharacterTurnResult(
            character_id=context.character_id,
            turn=context.turn,
            intent=intent,
            output=output,
            adjudication=adjudication,
            narration=narration,
        )
        self.history.append(result)
        return result

    async def execute_turn(
        self,
        turn: int,
        initiative_order: list[str],
        contexts: dict[str, RoleContext],
        game_state_summary: str = "",
        geometry_summary: str = "",
    ) -> TurnResult:
        """Execute a full turn for all characters in initiative order."""
        turn_result = TurnResult(turn=turn, initiative_order=initiative_order)
        scene_history = ""

        for character_id in initiative_order:
            context = contexts[character_id]
            result = await self.execute_character_turn(
                context=context,
                game_state_summary=game_state_summary,
                geometry_summary=geometry_summary,
                scene_history=scene_history,
            )
            turn_result.character_results.append(result)

            # Accumulate visible narration for subsequent characters
            if result.narration.prose:
                scene_history += f"\n{result.narration.prose}"

        return turn_result
