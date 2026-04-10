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
from typing import AsyncIterator, Optional

from engine.initiative import roll_initiative
from engine.player_router import RoleContext
from engine.scene_manager import TurnCycle, TurnResult, RoleSet
from models.character import Character
from models.condition import CharacterCondition, render_condition
from models.space_time import GameTime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMBAT_EVENT = "combat_initiated"
EXIT_EVENT = "exits_scene"
MELEE_DURATION = 1  # minutes per combat turn


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


def _checkpoint_filename(turn: int, game_time: Optional[GameTime] = None) -> str:
    """Build checkpoint filename from game time or turn number."""
    if game_time is not None:
        return f"day{game_time.day}_{game_time.hour:02d}h{game_time.minute:02d}m.json"
    return f"turn_{turn:04d}.json"


def _save_turn(
    checkpoint_dir: Path,
    turn: int,
    turn_result: TurnResult,
    characters: dict[str, CharacterSession],
    game_time: Optional[GameTime] = None,
) -> Path:
    """Save a turn checkpoint as JSON."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / _checkpoint_filename(turn, game_time)

    data = {
        "turn": turn,
        "game_time": {
            "hour": game_time.hour,
            "minute": game_time.minute,
            "day": game_time.day,
            "season": game_time.season,
            "period": game_time.period,
        } if game_time else None,
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

async def iter_session(
    characters: dict[str, CharacterSession],
    character_roles: dict[str, RoleSet],
    num_turns: int,
    *,
    game_state_summary: str = "",
    geometry_summary: str = "",
    checkpoint_dir: Optional[Path] = None,
    game_time: Optional[GameTime] = None,
    rng: Optional[random.Random] = None,
) -> AsyncIterator[TurnResult]:
    """Async generator — yields one TurnResult per turn.

    Handles all per-turn state internally (scene history, combat tracking,
    condition mutations, checkpointing, clock advancement).  After each turn
    is fully processed the result is yielded so callers can interleave
    multiple independent sessions turn-by-turn.

    Use ``run_session`` for the common single-scene case.
    """
    turn_cycle = TurnCycle(character_roles=character_roles)
    scene_history = ""

    # Combat state
    in_combat = False
    pre_combat_duration: int | None = None
    active_characters: set[str] = set(characters.keys())

    for turn_num in range(1, num_turns + 1):
        # Roll initiative — only for characters still in the scene
        char_list = [
            cs.character for cid, cs in characters.items()
            if cid in active_characters
        ]
        if not char_list:
            break

        entries = roll_initiative(char_list, rng=rng)
        order = [e.character_id for e in entries]

        # Execute each character in initiative order, rebuilding context
        # just-in-time so each character sees within-turn narration from
        # characters who acted earlier in the same turn.
        turn_result = TurnResult(turn=turn_num, initiative_order=order)
        within_turn_history = ""

        for character_id in order:
            if character_id not in active_characters:
                continue

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

            # Check for exits_scene — remove from active set mid-turn
            if EXIT_EVENT in cr.adjudication.spatial_events:
                active_characters.discard(character_id)

            # Check for combat_initiated — switch to melee time
            if (COMBAT_EVENT in cr.adjudication.spatial_events
                    and not in_combat and game_time is not None):
                in_combat = True
                pre_combat_duration = game_time.turn_duration
                game_time.turn_duration = MELEE_DURATION

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

        # Persist checkpoint
        if checkpoint_dir:
            _save_turn(checkpoint_dir, turn_num, turn_result, characters, game_time)

        # Advance game clock
        if game_time:
            game_time.advance(1)

        # Check for combat end: no hostile still facing a non-hostile
        if in_combat and game_time is not None:
            hostiles_active = any(
                cs.character.faction == "hostile"
                for cid, cs in characters.items()
                if cid in active_characters
            )
            non_hostiles_active = any(
                cs.character.faction != "hostile"
                for cid, cs in characters.items()
                if cid in active_characters
            )
            if not (hostiles_active and non_hostiles_active):
                in_combat = False
                game_time.turn_duration = pre_combat_duration or 10
                pre_combat_duration = None

        yield turn_result


async def run_session(
    characters: dict[str, CharacterSession],
    character_roles: dict[str, RoleSet],
    num_turns: int,
    *,
    game_state_summary: str = "",
    geometry_summary: str = "",
    checkpoint_dir: Optional[Path] = None,
    game_time: Optional[GameTime] = None,
    rng: Optional[random.Random] = None,
) -> SessionResult:
    """Run a complete game session and return all results.

    Wraps ``iter_session`` for the common single-scene case.  Use
    ``iter_session`` directly when you need to interleave multiple scenes
    turn-by-turn (e.g. ``run_all.py``).
    """
    turns: list[TurnResult] = []
    async for turn_result in iter_session(
        characters, character_roles, num_turns,
        game_state_summary=game_state_summary,
        geometry_summary=geometry_summary,
        checkpoint_dir=checkpoint_dir,
        game_time=game_time,
        rng=rng,
    ):
        turns.append(turn_result)

    return SessionResult(
        turns=turns,
        final_conditions={
            char_id: cs.condition for char_id, cs in characters.items()
        },
        scene_history="",
    )

