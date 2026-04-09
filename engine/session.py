"""Direct Python game loop — no Lobster, no OpenClaw.

Thin orchestrator that wires together TurnCycle, initiative,
conditions, and checkpointing. Human WhatsApp routing can be
re-added later when OpenClaw is stable.

Usage:
    result = await run_session(characters, character_roles, num_turns=3)
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from engine.initiative import roll_initiative
from engine.player_router import RoleContext
from engine.scene_manager import TurnCycle, TurnResult, RoleSet
from models.character import Character
from models.condition import CharacterCondition, render_condition


# ---------------------------------------------------------------------------
# Session data types
# ---------------------------------------------------------------------------

@dataclass
class CharacterSession:
    """Per-character state for a session."""
    character: Character
    condition: CharacterCondition
    soul: str
    identity: str
    initial_scene: str


@dataclass
class SessionResult:
    """Results from a complete session."""
    turns: list[TurnResult]
    final_conditions: dict[str, CharacterCondition]
    scene_history: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_context(
    cs: CharacterSession,
    turn: int,
    scene_history: str,
) -> RoleContext:
    """Build a RoleContext from session state."""
    scene = cs.initial_scene
    if scene_history:
        scene = f"{cs.initial_scene}\n\n{scene_history}"
    return RoleContext(
        character_id=cs.character.id,
        turn=turn,
        condition_text=render_condition(cs.condition),
        scene_context=scene,
        soul=cs.soul,
        identity=cs.identity,
    )


def _save_turn(
    checkpoint_dir: Path,
    turn: int,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
) -> Path:
    """Save a turn checkpoint as JSON."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / f"turn_{turn:04d}.json"

    data = {
        "turn": turn,
        "initiative_order": turn_result.initiative_order,
        "character_results": [
            {
                "character_id": cr.character_id,
                "turn": cr.turn,
                "intent": asdict(cr.intent),
                "output": asdict(cr.output),
                "adjudication": asdict(cr.adjudication),
                "narration": asdict(cr.narration),
            }
            for cr in turn_result.character_results
        ],
        "conditions": {
            char_id: cs.condition.state.to_dict()
            for char_id, cs in characters.items()
        },
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

async def run_session(
    characters: dict[str, CharacterSession],
    character_roles: dict[str, RoleSet],
    num_turns: int,
    *,
    game_state_summary: str = "",
    geometry_summary: str = "",
    checkpoint_dir: Optional[Path] = None,
    rng: Optional[random.Random] = None,
) -> SessionResult:
    """Run a game session — direct Python loop calling TurnCycle.

    Args:
        characters:         char_id → CharacterSession with character,
                            condition, soul, identity, initial_scene.
        character_roles:    char_id → RoleSet with LLM assignments.
        num_turns:          Number of turns to run.
        game_state_summary: Creature stat blocks, world rules, etc.
                            Passed to DMLeft for adjudication.
        geometry_summary:   Scene geometry (zones, boundaries, positions).
                            Passed to DMLeft for spatial adjudication.
        checkpoint_dir:     If set, save a JSON checkpoint per turn.
        rng:                Random instance for deterministic initiative.

    Returns:
        SessionResult with all turn results, final conditions, and
        accumulated scene history.
    """
    turn_cycle = TurnCycle(character_roles=character_roles)
    scene_history = ""
    turns: list[TurnResult] = []

    for turn_num in range(1, num_turns + 1):
        # Roll initiative
        char_list = [cs.character for cs in characters.values()]
        entries = roll_initiative(char_list, rng=rng)
        order = [e.character_id for e in entries]

        # Execute each character in initiative order, rebuilding context
        # just-in-time so each character sees within-turn narration from
        # characters who acted earlier in the same turn.
        turn_result = TurnResult(turn=turn_num, initiative_order=order)
        within_turn_history = ""

        for character_id in order:
            cs = characters[character_id]
            combined_history = scene_history
            if within_turn_history:
                combined_history = (
                    f"{scene_history}\n{within_turn_history}"
                    if scene_history else within_turn_history
                )

            context = _build_context(cs, turn_num, combined_history)
            cr = await turn_cycle.execute_character_turn(
                context=context,
                game_state_summary=game_state_summary,
                geometry_summary=geometry_summary,
                scene_history=within_turn_history,
            )
            turn_result.character_results.append(cr)

            # Build history entry: dialogue + narration
            history_entry = ""
            spoken = cr.output.spoken or ""
            if spoken.strip() and spoken.strip().lower() not in (
                "(silent)", "(silence)",
            ):
                history_entry += (
                    f'\n{cr.character_id} says: "{spoken.strip()}"'
                )
            if cr.narration.prose:
                history_entry += f"\n{cr.narration.prose}"
            if history_entry:
                within_turn_history += history_entry

        # Apply condition deltas from DMLeft adjudication
        for cr in turn_result.character_results:
            if cr.adjudication.condition_deltas:
                characters[cr.character_id].condition.apply_delta(
                    cr.adjudication.condition_deltas
                )
            # Accumulate dialogue + narration for next turn's context
            spoken = cr.output.spoken or ""
            history_entry = ""
            if spoken.strip() and spoken.strip().lower() not in (
                "(silent)", "(silence)",
            ):
                history_entry += (
                    f'\n{cr.character_id} says: "{spoken.strip()}"'
                )
            if cr.narration.prose:
                history_entry += f"\n{cr.narration.prose}"
            if history_entry:
                scene_history += history_entry

        turns.append(turn_result)

        # Persist checkpoint
        if checkpoint_dir:
            _save_turn(checkpoint_dir, turn_num, turn_result, characters)

    return SessionResult(
        turns=turns,
        final_conditions={
            char_id: cs.condition for char_id, cs in characters.items()
        },
        scene_history=scene_history.strip(),
    )
