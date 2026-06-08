"""Runtime puzzle state machines.

A :class:`Puzzle` owns its own state machine. The session loop never
inspects sequence progress or door state directly — it presses a target
through the puzzle and applies the returned :class:`PuzzleResult`. This
keeps all puzzle logic inside the type rather than sprinkled through the
turn loop.

The authored definition (ordered solution, per-step responses, solve and
reverse effects) is parsed elsewhere into a :class:`models.puzzle.PuzzleSpec`;
:func:`build_registry` turns specs into live puzzle objects and indexes
them by their input item ids.

Supported kinds:
    sequence  — an ordered run of presses; entering the solution in order
                solves the puzzle, an out-of-order press resets progress,
                and pressing any target again once solved reverses it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from models.puzzle import PuzzleEffect, PuzzleSpec


@dataclass
class PuzzleResult:
    """Outcome of pressing a target through a puzzle.

    Attributes:
        response: DM-authoritative text for the acting character.
        side_effects: Effect dicts the session loop interprets — at minimum
            ``{"type": ...}``; may also carry ``{"broadcast": <text>}`` for
            world events other characters perceive. The ``type`` values are
            kept compatible with ``engine.activation.check_activations``
            (which looks for ``"door_open"``).
        awaiting_input: True when the puzzle advanced one step and now wants
            another press from the *same* actor this turn (the focused
            exchange). False when the press solved, reset, or reversed the
            puzzle — i.e. the exchange should end.
        follow_up_prompt: Question to put to the actor when
            ``awaiting_input`` is True ("What do you do next?").
        solved: True when this press completed the solution.
        consumed: True when the press was a recognised puzzle input (so the
            loop knows the puzzle handled it rather than a plain pressable).
    """

    response: str = ""
    side_effects: list[dict] = field(default_factory=list)
    awaiting_input: bool = False
    follow_up_prompt: str = ""
    solved: bool = False
    consumed: bool = True


class Puzzle(ABC):
    """Base class for stateful, item-driven puzzles."""

    def __init__(self, spec: PuzzleSpec):
        self.id = spec.id
        self.spec = spec

    @property
    def target_ids(self) -> set[str]:
        """Item ids this puzzle responds to."""
        return self.spec.target_ids()

    @property
    @abstractmethod
    def solved(self) -> bool:
        """Whether the puzzle is in its solved/open state."""

    @abstractmethod
    def handle(self, item_id: str) -> PuzzleResult:
        """Apply a press of ``item_id`` and advance the state machine."""

    @abstractmethod
    def abandon(self) -> None:
        """Drop any in-progress (unsolved) state without side effects.

        Called when a focused exchange ends because the actor did something
        other than press the next target. Solved state is preserved.
        """

    @abstractmethod
    def progress_summary(self) -> str:
        """Human-readable progress, for context/pressure blocks."""


def _effects_to_dicts(effects: list[PuzzleEffect]) -> list[dict]:
    """Convert authored effects into the loop's side-effect dicts."""
    out: list[dict] = []
    for eff in effects:
        d: dict = {"type": eff.type}
        if eff.broadcast:
            d["broadcast"] = eff.broadcast
        out.append(d)
    return out


class SequencePuzzle(Puzzle):
    """Ordered-press state machine.

    State is a single integer ``_progress`` (count of correct presses so
    far) plus a ``_solved`` flag. All transitions live here:

      - solved + any press      -> reverse (close), reset progress, end.
      - correct next press       -> advance; if it completes the solution,
                                    solve (open) and end; otherwise emit the
                                    step response and keep the exchange open.
      - out-of-order press       -> reset progress to 0, emit reset, end.
    """

    def __init__(self, spec: PuzzleSpec):
        super().__init__(spec)
        self._progress = 0
        self._solved = False

    @property
    def solved(self) -> bool:
        return self._solved

    def _step_response(self, index: int) -> str:
        """Response for the ``index``-th correct press (0-based, non-final)."""
        steps = self.spec.step_responses
        if not steps:
            return "A faint click sounds, as if a mechanism stirs."
        if index < len(steps):
            return steps[index]
        return steps[-1]

    def handle(self, item_id: str) -> PuzzleResult:
        if item_id not in self.target_ids:
            return PuzzleResult(consumed=False)

        # Already solved: any press reverses (e.g. snaps the door shut).
        if self._solved:
            self._solved = False
            self._progress = 0
            return PuzzleResult(
                response=self.spec.reverse_response,
                side_effects=_effects_to_dicts(self.spec.reverse_effects),
                awaiting_input=False,
                solved=False,
            )

        solution = self.spec.solution
        expected = solution[self._progress] if self._progress < len(solution) else None

        if item_id == expected:
            self._progress += 1
            if self._progress >= len(solution):
                # Final correct press solves the puzzle.
                self._solved = True
                self._progress = 0
                return PuzzleResult(
                    response=self.spec.solve_response,
                    side_effects=_effects_to_dicts(self.spec.solve_effects),
                    awaiting_input=False,
                    solved=True,
                )
            # Correct but not final: stay in the focused exchange.
            return PuzzleResult(
                response=self._step_response(self._progress - 1),
                awaiting_input=True,
                follow_up_prompt=self.spec.prompt,
            )

        # Out-of-order press: abandon progress, end the exchange.
        self._progress = 0
        return PuzzleResult(
            response=self.spec.reset_response,
            awaiting_input=False,
        )

    def abandon(self) -> None:
        if not self._solved:
            self._progress = 0

    def progress_summary(self) -> str:
        if self._solved:
            return "solved"
        if self._progress == 0:
            return "not yet started"
        pressed = self.spec.solution[: self._progress]
        return " -> ".join(pressed)


_PUZZLE_KINDS = {
    "sequence": SequencePuzzle,
}


def build_puzzle(spec: PuzzleSpec) -> Puzzle:
    """Construct a live :class:`Puzzle` from a spec."""
    cls = _PUZZLE_KINDS.get((spec.kind or "sequence").lower())
    if cls is None:
        raise ValueError(f"Unknown puzzle kind {spec.kind!r} for puzzle {spec.id!r}")
    return cls(spec)


class PuzzleRegistry:
    """Per-session collection of live puzzles, indexed by input item id.

    Threaded through the turn loop in place of the old ``puzzle_state``
    dict. The loop asks the registry which puzzle (if any) owns a pressed
    item and delegates the press; the registry holds no scene-specific
    logic of its own.
    """

    def __init__(self, puzzles: Optional[list[Puzzle]] = None):
        self._puzzles: list[Puzzle] = list(puzzles or [])
        self._by_item: dict[str, Puzzle] = {}
        for puzzle in self._puzzles:
            for item_id in puzzle.target_ids:
                self._by_item[item_id] = puzzle

    @property
    def target_ids(self) -> set[str]:
        """All item ids that act as puzzle inputs."""
        return set(self._by_item)

    def puzzle_for_item(self, item_id: str) -> Optional[Puzzle]:
        """Return the puzzle owning ``item_id``, or None."""
        return self._by_item.get(item_id)

    def press(self, item_id: str) -> PuzzleResult:
        """Delegate a press to the owning puzzle.

        Returns an unconsumed result when no puzzle owns the item.
        """
        puzzle = self._by_item.get(item_id)
        if puzzle is None:
            return PuzzleResult(consumed=False)
        return puzzle.handle(item_id)

    def __bool__(self) -> bool:
        return bool(self._puzzles)


def build_registry(specs: dict[str, PuzzleSpec]) -> PuzzleRegistry:
    """Build a :class:`PuzzleRegistry` from parsed puzzle specs."""
    return PuzzleRegistry([build_puzzle(spec) for spec in (specs or {}).values()])
