"""Turn cycle orchestrator connecting the four LLM roles.

Data flow per character (sequential within initiative order):

  1. PlayerLeft.generate_intent()   → ActionIntent
  2. PlayerRight.generate_action()  → CharacterOutput
  3. DMLeft.adjudicate()            → Adjudication
  4. DMRight.narrate()              → Narration

Each character sees all preceding narration from the same turn.
This is the fundamental design: sequential, not parallel.

Provider routing is per-character.  Pass a dict[str, RoleSet] to
TurnCycle to give Aeliana Grok, Fennel ChatGPT, etc.  Characters
not in the dict fall back to the shared defaults.
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


@dataclass
class RoleSet:
    """Full set of four LLM roles for one character."""
    player_left: PlayerLeft = field(default_factory=PlayerLeft)
    player_right: PlayerRight = field(default_factory=PlayerRight)
    dm_left: DMLeft = field(default_factory=DMLeft)
    dm_right: DMRight = field(default_factory=DMRight)


# ---------------------------------------------------------------------------
# Turn cycle
# ---------------------------------------------------------------------------

class TurnCycle:
    """Orchestrates the four LLM roles through a complete turn.

    Characters act sequentially in initiative order.
    Each character sees all preceding narration from the same turn.

    Provider routing:
      - Shared defaults via player_left/player_right/dm_left/dm_right kwargs.
      - Per-character overrides via character_roles dict[str, RoleSet].
      - When a character has an entry in character_roles, those roles are
        used; otherwise the shared defaults apply.
    """

    def __init__(
        self,
        player_left: Optional[PlayerLeft] = None,
        player_right: Optional[PlayerRight] = None,
        dm_left: Optional[DMLeft] = None,
        dm_right: Optional[DMRight] = None,
        character_roles: Optional[dict[str, RoleSet]] = None,
    ):
        self.player_left = player_left or PlayerLeft()
        self.player_right = player_right or PlayerRight()
        self.dm_left = dm_left or DMLeft()
        self.dm_right = dm_right or DMRight()
        self.character_roles: dict[str, RoleSet] = character_roles or {}
        self.history: list[CharacterTurnResult] = []

    def _roles_for(self, character_id: str) -> RoleSet:
        """Return the RoleSet for a character (per-character or defaults)."""
        if character_id in self.character_roles:
            return self.character_roles[character_id]
        return RoleSet(
            player_left=self.player_left,
            player_right=self.player_right,
            dm_left=self.dm_left,
            dm_right=self.dm_right,
        )

    async def adjudicate_turn(
        self,
        context: RoleContext,
        game_state_summary: str = "",
        geometry_summary: str = "",
        scene_history: str = "",
        dm_ledger: str = "",
    ) -> tuple[ActionIntent, CharacterOutput, Adjudication]:
        """Run steps 1-3: Player-Left, Player-Right, DM-Left.

        Returns the raw materials for Python resolution before narration.
        Call narrate_turn() afterwards with the engine's resolution_log.
        """
        roles = self._roles_for(context.character_id)

        # 1. Player-Left: generate intent
        intent = await roles.player_left.generate_intent(context)

        # 2. Player-Right: generate in-character prose
        output = await roles.player_right.generate_action(intent, context)

        # 3. DM-Left: adjudicate
        adjudication = await roles.dm_left.adjudicate(
            output, game_state_summary, geometry_summary, dm_ledger=dm_ledger,
        )

        return intent, output, adjudication

    async def player_roles(
        self,
        context: RoleContext,
    ) -> tuple[ActionIntent, CharacterOutput]:
        """Run steps 1-2 only: Player-Left intent + Player-Right prose.

        Used by the combat resolver path where DM-Left is bypassed.
        """
        roles = self._roles_for(context.character_id)
        intent = await roles.player_left.generate_intent(context)
        output = await roles.player_right.generate_action(intent, context)
        return intent, output

    async def player_right_from_intent(
        self,
        context: RoleContext,
        intent: ActionIntent,
    ) -> CharacterOutput:
        """Run Player-Right only, using an externally supplied intent.

        This is used for human-input transports (e.g. Telegram) where intent
        arrives outside Player-Left but must still be rendered into structured
        character output before DM adjudication.
        """
        roles = self._roles_for(context.character_id)
        return await roles.player_right.generate_action(intent, context)

    async def dm_adjudicate(
        self,
        output: CharacterOutput,
        game_state_summary: str = "",
        geometry_summary: str = "",
        scene_history: str = "",
        dm_ledger: str = "",
    ) -> Adjudication:
        """Run step 3 only: DM-Left adjudication.

        Used when the combat resolver is not active (non-combat or no weapons).
        """
        roles = self._roles_for(output.character_id)
        return await roles.dm_left.adjudicate(
            output, game_state_summary, geometry_summary, dm_ledger=dm_ledger,
        )

    async def narrate_turn(
        self,
        intent: ActionIntent,
        output: CharacterOutput,
        adjudication: Adjudication,
        scene_history: str,
        resolution_log: list[str] | None = None,
        character_pronouns: dict[str, str] | None = None,
        perception: str | None = None,
    ) -> CharacterTurnResult:
        """Run step 4: DM-Right narrates the Python-resolved outcome.

        Pass resolution_log from _resolve_attacks so DM-Right knows what
        the engine actually allowed (hits, misses, blocked LOS, etc.).
        Pass perception to constrain narration to what the acting
        character can actually see/hear/sense (prevents omniscient prose
        like 'the beast watches the two figures in the glade' when the
        acting character cannot perceive one of them).
        """
        roles = self._roles_for(adjudication.character_id)

        # 4. DM-Right: narrate the engine-resolved outcome
        narration = await roles.dm_right.narrate(
            adjudication, output, scene_history,
            resolution_log=resolution_log,
            character_pronouns=character_pronouns,
            perception=perception,
        )

        result = CharacterTurnResult(
            character_id=adjudication.character_id,
            turn=adjudication.turn,
            intent=intent,
            output=output,
            adjudication=adjudication,
            narration=narration,
        )
        self.history.append(result)
        return result

    async def execute_character_turn(
        self,
        context: RoleContext,
        game_state_summary: str = "",
        geometry_summary: str = "",
        scene_history: str = "",
        dm_ledger: str = "",
    ) -> CharacterTurnResult:
        """Execute one character's full turn through the 4-role pipeline.

        Convenience wrapper around adjudicate_turn() + narrate_turn() with no
        Python resolution step (used by tests and simple callers).
        For the game loop use adjudicate_turn → Python resolution → narrate_turn.
        """
        intent, output, adjudication = await self.adjudicate_turn(
            context, game_state_summary, geometry_summary,
            scene_history, dm_ledger,
        )
        return await self.narrate_turn(intent, output, adjudication, scene_history)

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
