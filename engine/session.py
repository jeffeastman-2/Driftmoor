"""Direct Python game loop — no Lobster, no OpenClaw.

Thin orchestrator that wires together TurnCycle, initiative,
conditions, and checkpointing. Human WhatsApp routing can be
re-added later when OpenClaw is stable.

Usage:
    result = await run_session(characters, character_roles, num_turns=3)
"""

from __future__ import annotations

import json
import re
import random
from collections import deque
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
MAX_MELEE_ROUNDS = 20  # safety cap — melee rounds never count against num_turns


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
    scene_handle: str = ""  # How others see this character before names are exchanged


@dataclass
class SessionResult:
    """Results from a complete session."""
    turns: list[TurnResult]
    final_conditions: dict[str, CharacterCondition]
    scene_history: str


# ---------------------------------------------------------------------------
# Position tracking helpers
# ---------------------------------------------------------------------------

def _parse_positions_table(game_state_summary: str) -> dict[str, tuple[float, float, str]]:
    """Extract the character position table from game_state_summary.

    Expects a markdown table with columns: character | x | y | zone.
    Returns a dict of char_id → (x, y, zone).  Skips the header row.
    """
    positions: dict[str, tuple[float, float, str]] = {}
    pattern = r'\|\s*(\w+)\s*\|\s*(-?\d+\.?\d*)\s*\|\s*(-?\d+\.?\d*)\s*\|\s*(\w+)\s*\|'
    for m in re.finditer(pattern, game_state_summary):
        char_id, x, y, zone = m.group(1), m.group(2), m.group(3), m.group(4)
        if char_id.lower() == "character":
            continue  # header row
        positions[char_id] = (float(x), float(y), zone.upper())
    return positions


def _update_positions_in_summary(
    game_state_summary: str,
    positions: dict[str, tuple[float, float, str]],
) -> str:
    """Replace the position table in game_state_summary with current values.

    Rebuilds the ``| character | x | y | zone |`` table with live positions so
    the DM always sees where characters actually are rather than turn-0 values.
    """
    if not positions:
        return game_state_summary
    rows = ["| character | x | y | zone |", "|-----------|-----|-----|------|"]
    for char_id, (x, y, zone) in positions.items():
        rows.append(f"| {char_id} | {x} | {y} | {zone} |")
    new_table = "\n".join(rows)
    # Replace the existing table (header + any number of data rows)
    updated = re.sub(
        r'\| character \| x \| y \| zone \|.*?(?=\n#|\n\n|\Z)',
        new_table,
        game_state_summary,
        flags=re.DOTALL,
    )
    return updated


def _speed_to_feet(speed_str: str) -> float:
    """Parse a D&D speed string (e.g. '40 ft', '30 ft.') into feet.

    Coordinates are in feet so no conversion is needed — just extract the number.
    Returns feet per round. Defaults to 30.0 if unparseable.
    """
    m = re.search(r'(\d+)', speed_str or "")
    return float(m.group(1)) if m else 30.0


def _clamp_position(
    proposed: tuple[float, float, str],
    origin: tuple[float, float, str],
    max_feet: float,
) -> tuple[float, float, str]:
    """Clamp *proposed* to within *max_feet* of *origin*.

    If the proposed displacement exceeds max_feet, scales it back along
    the same direction so the character moves at most max_feet.
    The zone from *proposed* is preserved — zone assignment belongs to the DM.
    """
    import math
    ox, oy = origin[0], origin[1]
    px, py = proposed[0], proposed[1]
    dx, dy = px - ox, py - oy
    dist = math.hypot(dx, dy)
    if dist <= max_feet or dist == 0:
        return proposed
    scale = max_feet / dist
    return (round(ox + dx * scale, 1), round(oy + dy * scale, 1), proposed[2])


# ---------------------------------------------------------------------------
# DM Ledger
# ---------------------------------------------------------------------------

_PERMANENT_TRIGGERS = {"boundary_crossed", "combat_initiated", "exits_scene"}


class DMLedger:
    """Engine-authoritative event log injected into every DM adjudication prompt.

    Solves the stateless-LLM state-tracking problem: the engine owns all
    authoritative facts (positions, combat status, crossing outcomes) and
    presents them to the DM as a verified ledger rather than leaving the DM
    to re-derive them from ambiguous prose.

    Structure:
      Permanent Events  — first-time significant events kept forever
      Recent Turns      — sliding window of last 4 turns
      Current State     — live snapshot rebuilt every turn
    """

    def __init__(self) -> None:
        self.permanent_events: list[str] = []
        self._recent_turns: deque[list[str]] = deque(maxlen=4)
        self._current_turn: list[str] = []

    def record(self, cr: "CharacterTurnResult", game_time=None) -> None:  # noqa: F821
        """Record one character result into the current-turn buffer."""
        from engine.scene_manager import CharacterTurnResult  # local to avoid circular  # noqa: F401

        timestamp = (
            f"{game_time.hour}:{game_time.minute:02d}"
            if game_time else f"t{cr.turn}"
        )
        adj = cr.adjudication

        # Action summary (first 70 chars)
        action = (cr.output.action or "")[:70].rstrip()

        # Dice result — "N vs DC M SUCCESS/FAILED"
        dice_str = ""
        roll_m = re.search(
            r'(\d+)\s+(?:vs?\.?\s+)?dc\s*:?\s*(\d+)', adj.notes, re.IGNORECASE
        )
        if roll_m:
            r, d = int(roll_m.group(1)), int(roll_m.group(2))
            dice_str = f" | d20={r} vs DC={d} {'SUCCESS' if r >= d else 'FAILED'}"

        # Position
        pos_str = ""
        if adj.new_position:
            x, y, zone = adj.new_position
            pos_str = f" | pos x={x},y={y},{zone}"

        # Events
        events = [
            e.strip().rstrip(".")
            for e in adj.spatial_events
            if e.strip().lower() not in ("none", "none.", "")
        ]
        events_str = f" | {', '.join(events)}" if events else ""

        status = "APPROVED" if adj.approved else "BLOCKED"
        line = (
            f"{timestamp} | {cr.character_id} | {action}"
            f"{dice_str} | {status}{pos_str}{events_str}"
        )
        self._current_turn.append(line)

        # Permanent events: boundary crossings, combat start, exits
        for event in events:
            key = event.lower()
            if any(t in key for t in _PERMANENT_TRIGGERS):
                perm = f"{timestamp} | {cr.character_id} | {event.upper()}{pos_str}"
                if perm not in self.permanent_events:
                    self.permanent_events.append(perm)

    def flush_turn(self) -> None:
        """Move current-turn entries into the recent-turns sliding window."""
        if self._current_turn:
            self._recent_turns.append(list(self._current_turn))
            self._current_turn = []

    def render(
        self,
        current_positions: dict[str, tuple[float, float, str]],
        in_combat: bool,
        game_time=None,
        characters: dict | None = None,
    ) -> str:
        """Return the full ledger block for insertion at the top of a DM prompt."""
        lines: list[str] = ["## DM Ledger (engine-verified — do not contradict)\n"]

        if self.permanent_events:
            lines.append("### Permanent Events")
            lines.extend(self.permanent_events)
            lines.append("")

        all_recent = [ln for turn in self._recent_turns for ln in turn]
        all_recent.extend(self._current_turn)
        if all_recent:
            lines.append("### Recent Turns")
            lines.extend(all_recent)
            lines.append("")

        lines.append("### Current State")
        for char_id, (x, y, zone) in current_positions.items():
            side = "INSIDE barrier" if zone.upper() == "GLADE" else "outside barrier"
            hp_str = ""
            if characters and char_id in characters:
                char = characters[char_id].character
                curr = getattr(char, "current_hp", char.hp)
                hp_str = f" | HP {curr}/{char.hp}"
            lines.append(f"- {char_id}: x={x}, y={y}, zone={zone} ({side}){hp_str}")
        lines.append(f"- Combat: {'ACTIVE' if in_combat else 'INACTIVE'}")
        if game_time:
            lines.append(
                f"- Game time: {game_time.hour}:{game_time.minute:02d}"
                f" | period: {game_time.period}"
            )

        return "\n".join(lines)


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
    in_combat: bool = False,
) -> Path:
    """Save a turn checkpoint as JSON."""
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    path = checkpoint_dir / _checkpoint_filename(turn, game_time)

    data = {
        "turn": turn,
        "in_combat": in_combat,
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
        "hp": {
            char_id: {
                "current": getattr(cs.character, "current_hp", cs.character.hp),
                "max": cs.character.hp,
            }
            for char_id, cs in characters.items()
        },
    }
    path.write_text(json.dumps(data, indent=2, default=str))
    return path


# ---------------------------------------------------------------------------
# Resume helpers
# ---------------------------------------------------------------------------

def load_resume_state(
    checkpoint_dir: Path,
    characters: dict[str, CharacterSession],
) -> tuple[int, int | None, str]:
    """Read a checkpoint directory and prepare state for resuming a session.

    Patches ``characters`` conditions in-place from the last checkpoint so
    characters start the next session with their ending emotional state.

    Returns:
        (last_turn, last_game_minutes, scene_history)
        - last_turn: the highest turn number found (0 if none)
        - last_game_minutes: absolute game minutes from the last checkpoint's
          game_time (None if no game_time was recorded)
        - scene_history: full reconstructed narrative/dialogue history so
          characters remember what happened in prior turns
    """
    from models.condition import NeurochemicalState

    files = sorted(
        (p for p in checkpoint_dir.glob("*.json") if not p.stem.endswith("transcript")),
        key=lambda p: p.name,
    )
    if not files:
        return 0, None, ""

    scene_history = ""
    last_turn = 0
    last_game_minutes: int | None = None

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        last_turn = data["turn"]

        gt = data.get("game_time")
        if gt:
            last_game_minutes = gt["day"] * 24 * 60 + gt["hour"] * 60 + gt["minute"]

        # Reconstruct history using the same logic as iter_session
        for cr_data in data.get("character_results", []):
            char_id = cr_data["character_id"]
            spoken = (cr_data["output"].get("spoken") or "").strip()
            prose = (cr_data["narration"].get("prose") or "").strip()
            entry = ""
            if spoken and spoken.lower() not in ("(silent)", "(silence)"):
                entry += f'\n{char_id} says: "{spoken}"'
            if prose:
                entry += f"\n{prose}"
            scene_history += entry

    # Restore conditions from the last checkpoint
    last_data = json.loads(files[-1].read_text(encoding="utf-8"))
    for char_id, state_dict in last_data.get("conditions", {}).items():
        if char_id in characters:
            characters[char_id].condition.state = NeurochemicalState.from_dict(state_dict)

    return last_turn, last_game_minutes, scene_history


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
    start_turn: int = 1,
    initial_history: str = "",
) -> AsyncIterator[TurnResult]:
    """Async generator — yields one TurnResult per turn.

    Handles all per-turn state internally (scene history, combat tracking,
    condition mutations, checkpointing, clock advancement).  After each turn
    is fully processed the result is yielded so callers can interleave
    multiple independent sessions turn-by-turn.

    Use ``run_session`` for the common single-scene case.

    ``start_turn`` and ``initial_history`` support resuming a previous session:
    turn numbering begins at ``start_turn`` and characters are seeded with the
    reconstructed history from prior turns so they remember what happened.
    """
    turn_cycle = TurnCycle(character_roles=character_roles)
    scene_history = initial_history

    # Combat state
    in_combat = False
    pre_combat_duration: int | None = None
    active_characters: set[str] = set(characters.keys())

    story_turns_remaining = num_turns
    melee_rounds_remaining = MAX_MELEE_ROUNDS
    turn_num = start_turn

    # Live position tracking — updated from DM-approved NEW POSITION each turn
    current_positions: dict[str, tuple[float, float, str]] = _parse_positions_table(
        game_state_summary
    )

    # DM ledger — authoritative event log injected into every DM prompt
    ledger = DMLedger()

    while True:
        combat_at_start = in_combat
        if combat_at_start:
            if melee_rounds_remaining <= 0:
                break
        else:
            if story_turns_remaining <= 0:
                break

        # Roll initiative — only for characters still in the scene
        char_list = [
            cs.character for cid, cs in characters.items()
            if cid in active_characters
        ]
        if not char_list:
            break

        entries = roll_initiative(char_list, rng=rng)
        order = [e.character_id for e in entries]

        # Rebuild the position table with live positions for this turn
        turn_game_state = _update_positions_in_summary(game_state_summary, current_positions)

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
                game_state_summary=turn_game_state,
                geometry_summary=geometry_summary,
                scene_history=within_turn_history,
                dm_ledger=ledger.render(current_positions, in_combat, game_time, characters=characters),
            )
            turn_result.character_results.append(cr)

            # Update live position from approved DM adjudication.
            # Primary: structured NEW POSITION field.
            # Fallback: extract x/y coordinates mentioned anywhere in NOTES
            # (DM often writes coords in prose but forgets the structured field).
            if cr.adjudication.approved:
                raw_pos: tuple[float, float, str] | None = None
                if cr.adjudication.new_position is not None:
                    raw_pos = cr.adjudication.new_position
                else:
                    notes = cr.adjudication.notes
                    x_m = re.search(r'\bx\s*=\s*(-?\d+\.?\d*)', notes, re.IGNORECASE)
                    y_m = re.search(r'\by\s*=\s*(-?\d+\.?\d*)', notes, re.IGNORECASE)
                    if x_m and y_m:
                        prev_zone = current_positions.get(character_id, ('', '', ''))[2]
                        zone_m = re.search(
                            r'\b(GLADE|TRAIL|FOREST|CLEARING|POOL)\b', notes, re.IGNORECASE
                        )
                        zone = zone_m.group(1).upper() if zone_m else prev_zone
                        raw_pos = (float(x_m.group(1)), float(y_m.group(1)), zone)

                if raw_pos is not None:
                    # Clamp to character's speed (coordinates are in feet)
                    char = characters[character_id].character
                    speed_ft = _speed_to_feet(getattr(char, "speed", "30 ft"))
                    origin = current_positions.get(character_id)
                    if origin is not None:
                        raw_pos = _clamp_position(raw_pos, origin, speed_ft)
                    current_positions[character_id] = raw_pos

            # Record result in DM ledger (later chars in this turn see it)
            ledger.record(cr, game_time)

            # Apply HP damage immediately so ledger shows current HP
            # for subsequent characters in this turn's initiative order
            if cr.adjudication.approved:
                for target_id, dmg in cr.adjudication.hp_damage.items():
                    if target_id not in characters:
                        continue
                    char = characters[target_id].character
                    if hasattr(char, "current_hp"):
                        char.current_hp = max(0, char.current_hp - dmg)
                        if char.current_hp <= 0:
                            active_characters.discard(target_id)
                            current_positions.pop(target_id, None)

            # Check for exits_scene — remove from active set mid-turn
            if EXIT_EVENT in cr.adjudication.spatial_events:
                active_characters.discard(character_id)
                current_positions.pop(character_id, None)

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
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += (
                    f'\n{handle} says: "{spoken.strip()}"'
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
                cs = characters[cr.character_id]
                handle = cs.scene_handle or cr.character_id
                history_entry += (
                    f'\n{handle} says: "{spoken.strip()}"'
                )
            if cr.narration.prose:
                history_entry += f"\n{cr.narration.prose}"
            if history_entry:
                scene_history += history_entry

        # Move current-turn ledger entries into the sliding window
        ledger.flush_turn()

        # Persist checkpoint
        if checkpoint_dir:
            _save_turn(checkpoint_dir, turn_num, turn_result, characters, game_time, in_combat=in_combat)

        # Advance game clock
        if game_time:
            game_time.advance(1)

        # Count this turn against the appropriate budget
        if combat_at_start:
            melee_rounds_remaining -= 1
        else:
            story_turns_remaining -= 1
        turn_num += 1

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

