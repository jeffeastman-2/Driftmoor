"""Tests for the session transcript elaborator."""

import json
import pytest
from pathlib import Path

from engine.transcript import elaborate_turn, elaborate_session


# ---------------------------------------------------------------------------
# Minimal turn data for testing (mirrors checkpoint JSON structure)
# ---------------------------------------------------------------------------

def _turn_data(turn: int, characters: list[dict]) -> dict:
    return {
        "turn": turn,
        "initiative_order": [c["character_id"] for c in characters],
        "character_results": characters,
        "conditions": {},
    }


def _char_result(
    char_id: str,
    turn: int = 1,
    intent: str = "Move forward.",
    spoken: str = "",
    approved: bool = True,
    prose: str = "Something happens.",
    condition_deltas: dict | None = None,
    spatial_events: list | None = None,
    modified_action: str = "none.",
) -> dict:
    return {
        "character_id": char_id,
        "turn": turn,
        "intent": {
            "character_id": char_id,
            "turn": turn,
            "intent": intent,
            "movement_target": None,
            "interaction_target": None,
        },
        "output": {
            "character_id": char_id,
            "turn": turn,
            "internal": "Thinking hard.",
            "body_language": "Tense.",
            "spoken": spoken,
            "action": "Does the thing.",
        },
        "adjudication": {
            "character_id": char_id,
            "turn": turn,
            "approved": approved,
            "modified_action": modified_action,
            "position_delta": None,
            "condition_deltas": condition_deltas or {},
            "spatial_events": spatial_events or [],
            "notes": "All good.",
        },
        "narration": {
            "character_id": char_id,
            "turn": turn,
            "prose": prose,
            "visible_to": [],
        },
    }


# =========================================================================
# elaborate_turn
# =========================================================================

class TestElaborateTurn:
    def test_includes_turn_header(self):
        data = _turn_data(1, [_char_result("aeliana")])
        text = elaborate_turn(data)
        assert "TURN 1" in text

    def test_includes_initiative_order(self):
        data = _turn_data(1, [
            _char_result("aeliana"),
            _char_result("fennel"),
        ])
        text = elaborate_turn(data)
        assert "aeliana" in text
        assert "fennel" in text

    def test_includes_character_name(self):
        data = _turn_data(1, [_char_result("aeliana")])
        text = elaborate_turn(data)
        assert "AELIANA" in text

    def test_includes_narration_prose(self):
        data = _turn_data(1, [
            _char_result("aeliana", prose="The elf steps forward carefully.")
        ])
        text = elaborate_turn(data)
        assert "The elf steps forward carefully." in text

    def test_includes_spoken_dialogue(self):
        data = _turn_data(1, [
            _char_result("aeliana", spoken='"Stop right there."')
        ])
        text = elaborate_turn(data)
        assert "Stop right there" in text

    def test_silent_character_no_spoken_section(self):
        data = _turn_data(1, [_char_result("aeliana", spoken="")])
        text = elaborate_turn(data)
        assert "Speaks:" not in text

    def test_denied_action_noted(self):
        data = _turn_data(1, [
            _char_result("aeliana", approved=False,
                         modified_action="Cannot cross the barrier.")
        ])
        text = elaborate_turn(data)
        assert "Cannot cross the barrier" in text

    def test_condition_deltas_shown(self):
        data = _turn_data(1, [
            _char_result("aeliana", condition_deltas={"cortisol": 0.2})
        ])
        text = elaborate_turn(data)
        assert "cortisol" in text

    def test_spatial_events_shown(self):
        data = _turn_data(1, [
            _char_result("aeliana", spatial_events=["enters_pool"])
        ])
        text = elaborate_turn(data)
        assert "enters_pool" in text

    def test_spatial_events_none_filtered(self):
        data = _turn_data(1, [
            _char_result("aeliana", spatial_events=["none."])
        ])
        text = elaborate_turn(data)
        assert "Events:" not in text


# =========================================================================
# elaborate_session
# =========================================================================

class TestElaborateSession:
    def test_multiple_turns(self):
        turns = [
            _turn_data(1, [_char_result("aeliana", turn=1, prose="Turn one.")]),
            _turn_data(2, [_char_result("aeliana", turn=2, prose="Turn two.")]),
        ]
        text = elaborate_session(turns)
        assert "TURN 1" in text
        assert "TURN 2" in text
        assert "Turn one." in text
        assert "Turn two." in text

    def test_session_header(self):
        turns = [_turn_data(1, [_char_result("aeliana")])]
        text = elaborate_session(turns, title="Fey Glade Encounter")
        assert "Fey Glade Encounter" in text

    def test_from_checkpoint_dir(self, tmp_path):
        for i in range(1, 3):
            data = _turn_data(i, [
                _char_result("aeliana", turn=i, prose=f"Turn {i} narration.")
            ])
            (tmp_path / f"turn_{i:04d}.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
        text = elaborate_session_from_dir(tmp_path)
        assert "TURN 1" in text
        assert "TURN 2" in text
        assert "Turn 1 narration." in text
        assert "Turn 2 narration." in text

    def test_from_checkpoint_dir_sorted(self, tmp_path):
        """Turns should appear in order even if files are read out of order."""
        for i in [3, 1, 2]:
            data = _turn_data(i, [
                _char_result("aeliana", turn=i, prose=f"T{i}.")
            ])
            (tmp_path / f"turn_{i:04d}.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
        text = elaborate_session_from_dir(tmp_path)
        t1 = text.index("TURN 1")
        t2 = text.index("TURN 2")
        t3 = text.index("TURN 3")
        assert t1 < t2 < t3

    def test_writes_to_file(self, tmp_path):
        data = _turn_data(1, [_char_result("aeliana")])
        (tmp_path / "turn_0001.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        out = tmp_path / "transcript.txt"
        elaborate_session_from_dir(tmp_path, output_path=out)
        assert out.exists()
        assert "TURN 1" in out.read_text(encoding="utf-8")


# Need to import after defining tests so the test file parses cleanly
from engine.transcript import elaborate_session_from_dir
