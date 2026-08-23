"""Tests for the generic puzzle state machine (engine.puzzles).

Mirrors the retired state-resolver tests but exercises the data-driven
``SequencePuzzle`` semantics: strict progress-reset (no rolling window),
solve effects, and post-solve reversal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.puzzles import SequencePuzzle, build_registry
from models.contents_loader import load_zone_puzzles
from models.puzzle import PuzzleEffect, PuzzleSpec


ZONES = Path("scenario/places/obelisk_reach/echoing_caverns/zones")

TOP = "trigger_glyph_top"
BOTTOM = "trigger_glyph_bottom"
MIDDLE = "trigger_glyph_middle"
SOLUTION = [TOP, BOTTOM, MIDDLE]


@pytest.fixture
def spec() -> PuzzleSpec:
    return PuzzleSpec(
        id="west_wall_glyph_sequence",
        kind="sequence",
        solution=list(SOLUTION),
        step_responses=["A dry click.", "A heavier grinding click."],
        solve_response="Stone grinds open.",
        solve_effects=[PuzzleEffect(type="door_open", broadcast="A door grinds open.")],
        reset_response="A flat, dead click. The sequence is lost.",
        reverse_response="The crack snaps shut.",
        reverse_effects=[PuzzleEffect(type="door_close", broadcast="An opening grinds shut.")],
        prompt="What do you do next?",
    )


@pytest.fixture
def puzzle(spec: PuzzleSpec) -> SequencePuzzle:
    return SequencePuzzle(spec)


class TestInitialState:
    def test_starts_unsolved(self, puzzle: SequencePuzzle):
        assert puzzle.solved is False
        assert puzzle.progress_summary() == "not yet started"

    def test_target_ids(self, puzzle: SequencePuzzle):
        assert puzzle.target_ids == set(SOLUTION)


class TestProgress:
    def test_correct_first_press_awaits_more(self, puzzle: SequencePuzzle):
        result = puzzle.handle(TOP)
        assert result.awaiting_input is True
        assert result.solved is False
        assert result.side_effects == []
        assert result.follow_up_prompt == "What do you do next?"
        assert "click" in result.response.lower()
        assert puzzle.progress_summary() == TOP

    def test_step_responses_advance(self, puzzle: SequencePuzzle):
        r1 = puzzle.handle(TOP)
        r2 = puzzle.handle(BOTTOM)
        assert r1.response == "A dry click."
        assert r2.response == "A heavier grinding click."
        assert r2.awaiting_input is True


class TestWrongOrder:
    def test_out_of_order_press_resets(self, puzzle: SequencePuzzle):
        puzzle.handle(TOP)
        result = puzzle.handle(MIDDLE)  # expected BOTTOM
        assert result.awaiting_input is False
        assert result.side_effects == []
        assert "lost" in result.response.lower() or "dead" in result.response.lower()
        assert puzzle.progress_summary() == "not yet started"
        assert puzzle.solved is False

    def test_wrong_start_does_not_poison_later_run(self, puzzle: SequencePuzzle):
        # Strict reset: a wrong press must clear progress entirely, unlike
        # the old rolling-window resolver.
        puzzle.handle(MIDDLE)  # wrong start, resets to 0
        for gid in SOLUTION:
            result = puzzle.handle(gid)
        assert result.solved is True
        assert puzzle.solved is True


class TestUnlock:
    def test_correct_sequence_solves(self, puzzle: SequencePuzzle):
        puzzle.handle(TOP)
        puzzle.handle(BOTTOM)
        result = puzzle.handle(MIDDLE)
        assert result.solved is True
        assert result.awaiting_input is False
        assert puzzle.solved is True
        assert any(e["type"] == "door_open" for e in result.side_effects)
        assert "open" in result.response.lower() or "grind" in result.response.lower()

    def test_solve_effect_carries_broadcast(self, puzzle: SequencePuzzle):
        puzzle.handle(TOP)
        puzzle.handle(BOTTOM)
        result = puzzle.handle(MIDDLE)
        door = next(e for e in result.side_effects if e["type"] == "door_open")
        assert door.get("broadcast")


class TestReverseAfterSolve:
    def test_press_when_solved_reverses(self, puzzle: SequencePuzzle):
        for gid in SOLUTION:
            puzzle.handle(gid)
        assert puzzle.solved is True

        result = puzzle.handle(TOP)
        assert puzzle.solved is False
        assert result.awaiting_input is False
        assert any(e["type"] == "door_close" for e in result.side_effects)
        assert puzzle.progress_summary() == "not yet started"

    def test_reverse_then_resolve(self, puzzle: SequencePuzzle):
        for gid in SOLUTION:
            puzzle.handle(gid)
        puzzle.handle(BOTTOM)  # reverse / close
        assert puzzle.solved is False
        for gid in SOLUTION:
            result = puzzle.handle(gid)
        assert puzzle.solved is True


class TestAbandon:
    def test_abandon_clears_unsolved_progress(self, puzzle: SequencePuzzle):
        puzzle.handle(TOP)
        puzzle.abandon()
        assert puzzle.progress_summary() == "not yet started"

    def test_abandon_preserves_solved(self, puzzle: SequencePuzzle):
        for gid in SOLUTION:
            puzzle.handle(gid)
        puzzle.abandon()
        assert puzzle.solved is True


class TestUnknownTarget:
    def test_non_target_is_not_consumed(self, puzzle: SequencePuzzle):
        result = puzzle.handle("secret_burial_vault")
        assert result.consumed is False
        assert result.side_effects == []
        assert puzzle.solved is False


class TestRegistryFromContents:
    def test_authored_puzzle_loads_and_solves(self):
        registry = build_registry(load_zone_puzzles(ZONES))
        assert registry.target_ids >= set(SOLUTION)
        assert registry.puzzle_for_item(TOP) is registry.puzzle_for_item(MIDDLE)

        registry.press(TOP)
        registry.press(BOTTOM)
        result = registry.press(MIDDLE)
        assert result.solved is True
        assert any(e["type"] == "door_open" for e in result.side_effects)

    def test_non_input_item_returns_unconsumed(self):
        registry = build_registry(load_zone_puzzles(ZONES))
        result = registry.press("secret_burial_vault")
        assert result.consumed is False
