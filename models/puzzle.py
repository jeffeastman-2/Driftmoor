"""Puzzle specification dataclasses.

These are *pure data* objects parsed from a ``## Puzzles`` block in a
scene's CONTENTS.md. They carry no behaviour — the runtime state machine
that interprets a spec lives in ``engine.puzzles``. Keeping the spec in
``models`` mirrors the ``models.item`` / ``engine.state_resolver`` split:
authored facts are data; the machine that runs them is engine code.

See ``specs/CONTENTS.md`` for the authoring format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PuzzleEffect:
    """A side effect a puzzle emits when a step fires.

    Attributes:
        type: Machine-readable effect kind (e.g. ``"door_open"``,
            ``"door_close"``). Consumed by the session loop and by
            ``engine.activation.check_activations``.
        broadcast: Optional world-event text appended to ``recent_events``
            so *other* characters perceive the consequence (e.g. a creature
            feeling the vibration of a door grinding open). Empty when the
            effect should not be broadcast.
    """

    type: str
    broadcast: str = ""


@dataclass
class PuzzleSpec:
    """Authored definition of a single puzzle.

    Currently one ``kind`` is supported: ``"sequence"`` — an ordered series
    of item presses (the ``solution``) that must be entered in order. Each
    correct-but-not-final press emits the matching ``step_responses`` entry;
    the final correct press emits ``solve_response`` plus ``solve_effects``.

    Attributes:
        id: Unique puzzle id (the ``### <id>`` heading).
        kind: Puzzle type discriminator. Only ``"sequence"`` for now.
        solution: Ordered list of item ids forming the unlock sequence.
        step_responses: Terse response text for each correct, non-final
            press. ``step_responses[i]`` is shown after the ``(i+1)``-th
            correct press. Length should be ``len(solution) - 1``; a shorter
            list reuses its last entry, an empty list falls back to a
            generic click.
        solve_response: Response text emitted by the final correct press.
        solve_effects: Effects emitted on solve (e.g. ``door_open``).
        reset_response: Response text emitted by an out-of-order press,
            which abandons the in-progress sequence.
        reverse_response: Response text emitted when a target is pressed
            while the puzzle is already solved (e.g. closing the door).
        reverse_effects: Effects emitted on reverse (e.g. ``door_close``).
        prompt: The follow-up question shown to the acting character during
            the focused exchange ("What do you do next?").
    """

    id: str
    kind: str = "sequence"
    solution: list[str] = field(default_factory=list)
    step_responses: list[str] = field(default_factory=list)
    solve_response: str = ""
    solve_effects: list[PuzzleEffect] = field(default_factory=list)
    reset_response: str = ""
    reverse_response: str = ""
    reverse_effects: list[PuzzleEffect] = field(default_factory=list)
    prompt: str = "What do you do next?"

    def target_ids(self) -> set[str]:
        """Item ids that act as inputs to this puzzle."""
        return set(self.solution)
