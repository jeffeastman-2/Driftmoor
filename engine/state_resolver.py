"""Phase 3a: state machine for the Echoing Caverns trigger-glyph puzzle.

The west wall of the Echo Chamber holds a hairline crack flanked by three
trigger glyphs (top, middle, bottom). Pressing the glyphs in the order
top -> bottom -> middle widens the crack into a passable hewn opening
(secret door). Pressing ANY glyph while the door is open snaps it shut
again. Any other order produces only a faint dry click.

The state machine lives outside the Item objects so it can stay scoped
to a single session and so we can extend it cleanly to other puzzles
later without sprinkling logic across ``models/item.py``.

This module does not import ``engine.session`` — the session loop calls
``process_press`` and applies the returned ``side_effects``.
"""

from __future__ import annotations

from typing import Optional

from models.item import Item


GLYPH_IDS = {
    "trigger_glyph_top",
    "trigger_glyph_middle",
    "trigger_glyph_bottom",
}

# top -> bottom -> middle opens the secret door.
UNLOCK_SEQUENCE: list[str] = [
    "trigger_glyph_top",
    "trigger_glyph_bottom",
    "trigger_glyph_middle",
]

CLICK_RESPONSE = (
    "A faint dry click sounds in the stone. No other effect. The glyph "
    "itself does not move; only the click distinguishes a press from a touch."
)

OPEN_RESPONSE = (
    "Stone grinds against stone as the hairline crack widens into a "
    "passable hewn opening in the west wall of the Echo Chamber. Cool, "
    "dry air sighs out from the dark beyond. Vibration carries through "
    "the surrounding rock."
)

CLOSE_RESPONSE = (
    "The crack snaps shut to a hairline again. Any character standing "
    "in the squeeze when this happens is shoved firmly to one side or "
    "the other (no damage, but no longer in the doorway). The west wall "
    "is once again unbroken stone."
)


def initial_puzzle_state() -> dict:
    """Per-session puzzle bookkeeping. Owned by the session loop."""
    return {
        "glyph_sequence": [],   # ids of recent glyph presses, oldest first
        "door_open": False,     # secret door state
    }


def _press_response_for_glyph(
    items: dict[str, Item], door_open: bool
) -> Optional[str]:
    """Look up the authored response for the appropriate condition.

    Falls back to the module-level constants when the authored text is
    not present (e.g. test fixtures with abbreviated CONTENTS.md).
    """
    target_cond = "open" if door_open else "closed"
    top = items.get("trigger_glyph_top")
    if top is None:
        return CLOSE_RESPONSE if door_open else CLICK_RESPONSE
    for inter in top.interactions:
        if inter.verb.lower() != "press":
            continue
        if target_cond in inter.condition.lower():
            return inter.response
    return CLOSE_RESPONSE if door_open else CLICK_RESPONSE


def process_press(
    item: Item,
    items: dict[str, Item],
    puzzle_state: dict,
) -> tuple[str, list[dict]]:
    """Apply a press to ``item`` and return ``(response, side_effects)``.

    Side effects are a list of dicts the session loop interprets:
      - ``{"type": "door_open"}``  — secret door just opened
      - ``{"type": "door_close"}`` — secret door just closed

    For pressables outside the glyph set, returns the authored ``press``
    interaction's response (if any) with no side effects, leaving glyph
    sequence/door state untouched.
    """
    if item.id not in GLYPH_IDS:
        inter = item.find_interaction("press")
        return (inter.response if inter else ""), []

    door_open = bool(puzzle_state.get("door_open", False))

    # Pressing while open: close + reset sequence regardless of which glyph.
    if door_open:
        puzzle_state["door_open"] = False
        puzzle_state["glyph_sequence"] = []
        response = _press_response_for_glyph(items, door_open=True) or CLOSE_RESPONSE
        return response, [{"type": "door_close"}]

    # Door is closed. Append press to sequence; keep only last 3.
    seq: list[str] = puzzle_state.setdefault("glyph_sequence", [])
    seq.append(item.id)
    if len(seq) > 3:
        del seq[: len(seq) - 3]

    if seq == UNLOCK_SEQUENCE:
        puzzle_state["door_open"] = True
        puzzle_state["glyph_sequence"] = []
        return OPEN_RESPONSE, [{"type": "door_open"}]

    # Wrong order so far: dry click.
    response = _press_response_for_glyph(items, door_open=False) or CLICK_RESPONSE
    return response, []
