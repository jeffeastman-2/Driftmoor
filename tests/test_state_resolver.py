"""Phase 3a tests: glyph sequence + secret-door state machine."""

from __future__ import annotations

from pathlib import Path

import pytest

from engine.state_resolver import (
    GLYPH_IDS,
    UNLOCK_SEQUENCE,
    initial_puzzle_state,
    process_press,
)
from models.contents_loader import load_contents


CONTENTS = Path("scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md")


@pytest.fixture
def items():
    return load_contents(CONTENTS)


@pytest.fixture
def state():
    return initial_puzzle_state()


def _press(items, state, glyph_id):
    return process_press(items[glyph_id], items, state)


class TestInitialState:
    def test_door_starts_closed(self, state):
        assert state["door_open"] is False
        assert state["glyph_sequence"] == []

    def test_glyph_ids_match_geometry(self, items):
        for gid in GLYPH_IDS:
            assert gid in items
        assert UNLOCK_SEQUENCE == [
            "trigger_glyph_top",
            "trigger_glyph_bottom",
            "trigger_glyph_middle",
        ]


class TestWrongOrder:
    def test_single_press_clicks(self, items, state):
        resp, fx = _press(items, state, "trigger_glyph_top")
        assert "click" in resp.lower()
        assert fx == []
        assert state["door_open"] is False
        assert state["glyph_sequence"] == ["trigger_glyph_top"]

    def test_wrong_two_presses(self, items, state):
        _press(items, state, "trigger_glyph_top")
        resp, fx = _press(items, state, "trigger_glyph_middle")
        assert "click" in resp.lower()
        assert fx == []
        assert state["door_open"] is False

    def test_full_wrong_sequence(self, items, state):
        for gid in ["trigger_glyph_bottom", "trigger_glyph_middle", "trigger_glyph_top"]:
            resp, fx = _press(items, state, gid)
        assert state["door_open"] is False
        assert fx == []


class TestUnlock:
    def test_correct_sequence_opens_door(self, items, state):
        _press(items, state, "trigger_glyph_top")
        _press(items, state, "trigger_glyph_bottom")
        resp, fx = _press(items, state, "trigger_glyph_middle")
        assert state["door_open"] is True
        assert state["glyph_sequence"] == []
        assert any(e["type"] == "door_open" for e in fx)
        # Response describes the stone grinding open.
        assert "grind" in resp.lower() or "open" in resp.lower()

    def test_unlock_after_wrong_attempts(self, items, state):
        # Wrong starts shouldn't poison a later correct run.
        _press(items, state, "trigger_glyph_middle")
        _press(items, state, "trigger_glyph_top")
        _press(items, state, "trigger_glyph_top")
        # Now correct sequence (the rolling 3-window will hold it):
        _press(items, state, "trigger_glyph_bottom")
        resp, fx = _press(items, state, "trigger_glyph_middle")
        # Last 3 = top, bottom, middle = unlock.
        assert state["door_open"] is True
        assert any(e["type"] == "door_open" for e in fx)


class TestCloseAfterOpen:
    def test_press_when_open_closes(self, items, state):
        # Open the door first.
        _press(items, state, "trigger_glyph_top")
        _press(items, state, "trigger_glyph_bottom")
        _press(items, state, "trigger_glyph_middle")
        assert state["door_open"] is True

        # Pressing any glyph now closes it.
        resp, fx = _press(items, state, "trigger_glyph_top")
        assert state["door_open"] is False
        assert state["glyph_sequence"] == []
        assert any(e["type"] == "door_close" for e in fx)
        assert "shut" in resp.lower() or "snap" in resp.lower() or "hairline" in resp.lower()

    def test_close_then_reopen(self, items, state):
        for gid in UNLOCK_SEQUENCE:
            _press(items, state, gid)
        assert state["door_open"] is True
        _press(items, state, "trigger_glyph_bottom")  # close
        assert state["door_open"] is False
        # Re-run sequence:
        for gid in UNLOCK_SEQUENCE:
            resp, fx = _press(items, state, gid)
        assert state["door_open"] is True


class TestNonGlyphPressables:
    def test_non_glyph_returns_authored_no_side_effects(self, items, state):
        # secret_burial_vault has examine/lift/damage but no press; should
        # return empty response and no side effects, leaving state intact.
        # Pick any non-glyph item and call process_press.
        vault = items.get("secret_burial_vault")
        assert vault is not None
        resp, fx = process_press(vault, items, state)
        assert fx == []
        assert state["glyph_sequence"] == []
        assert state["door_open"] is False
