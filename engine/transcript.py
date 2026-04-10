"""Session transcript elaborator — turn checkpoints → readable narrative.

Reads the per-turn JSON checkpoints produced by run_session() and
produces a single plain-text transcript showing what happened each
turn: initiative order, each character's narration, dialogue,
adjudication notes, and condition shifts.

Usage:
    from engine.transcript import elaborate_session_from_dir
    text = elaborate_session_from_dir(Path("runtime/state/session_run"))
    # or write directly:
    elaborate_session_from_dir(path, output_path=Path("transcript.txt"))
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


def _format_character(cr: dict) -> str:
    """Format one character's turn into readable text."""
    lines: list[str] = []
    char_id = cr["character_id"]
    lines.append(f"  {char_id.upper()}")

    # Intent
    intent_text = cr["intent"]["intent"]
    lines.append(f"    Intent: {intent_text}")

    # Spoken dialogue (skip silent)
    spoken = cr["output"].get("spoken", "")
    if spoken and spoken.strip().lower() not in ("", "(silent)", "(silence)"):
        lines.append(f"    Speaks: {spoken.strip()}")

    # Adjudication
    adj = cr["adjudication"]
    if not adj["approved"]:
        mod = adj.get("modified_action", "")
        lines.append(f"    DENIED — {mod}")

    # Condition deltas
    deltas = adj.get("condition_deltas", {})
    if deltas:
        parts = [f"{k}: {v:+.2f}" for k, v in deltas.items()]
        lines.append(f"    Condition: {', '.join(parts)}")

    # Spatial events (filter out "none." entries)
    events = adj.get("spatial_events", [])
    real_events = [e for e in events if e.strip().lower() not in ("none.", "none", "")]
    if real_events:
        lines.append(f"    Events: {', '.join(real_events)}")

    # Narration (the main readable output)
    prose = cr["narration"]["prose"]
    if prose:
        lines.append("")
        lines.append(f"    {prose}")

    lines.append("")
    return "\n".join(lines)


def elaborate_turn(turn_data: dict) -> str:
    """Convert a single turn's checkpoint data into readable text."""
    turn_num = turn_data["turn"]
    order = turn_data["initiative_order"]

    lines: list[str] = []
    lines.append(f"{'=' * 72}")
    lines.append(f"  TURN {turn_num}  —  Initiative: {', '.join(order)}")
    lines.append(f"{'=' * 72}")
    lines.append("")

    for cr in turn_data["character_results"]:
        lines.append(_format_character(cr))

    return "\n".join(lines)


def elaborate_session(
    turns: list[dict],
    *,
    title: str = "SESSION TRANSCRIPT",
) -> str:
    """Convert a list of turn checkpoint dicts into a full transcript."""
    lines: list[str] = []
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")

    for turn_data in turns:
        lines.append(elaborate_turn(turn_data))

    return "\n".join(lines)


def elaborate_session_from_dir(
    checkpoint_dir: Path,
    *,
    output_path: Optional[Path] = None,
    title: str = "SESSION TRANSCRIPT",
) -> str:
    """Read all checkpoint JSON files from a directory and produce a transcript.

    Supports both legacy ``turn_0001.json`` naming and game-time
    ``day1_14h30m.json`` naming.  Files are sorted by their embedded
    turn number so order is always correct.

    Args:
        checkpoint_dir: Directory containing checkpoint JSON files.
        output_path:    If provided, write the transcript to this file.
        title:          Title for the transcript header.

    Returns:
        The full transcript as a string.
    """
    # Collect both naming conventions
    files = set(checkpoint_dir.glob("turn_*.json")) | set(checkpoint_dir.glob("day*.json"))
    turns = []
    for f in sorted(files):
        data = json.loads(f.read_text(encoding="utf-8"))
        turns.append(data)
    turns.sort(key=lambda d: d["turn"])

    text = elaborate_session(turns, title=title)

    if output_path:
        output_path.write_text(text, encoding="utf-8")

    return text
