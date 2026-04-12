"""Tests for the narrative story generator prompt building."""

import pytest

from engine.narrator import build_narrative_prompt, extract_scene_material, _chunk_turns


# ---------------------------------------------------------------------------
# Helpers — same checkpoint structure as test_transcript.py
# ---------------------------------------------------------------------------

def _char_result(
    char_id: str,
    turn: int = 1,
    intent: str = "Move forward.",
    spoken: str = "",
    prose: str = "Something happens.",
    action: str = "Does the thing.",
    body_language: str = "Tense.",
    internal: str = "Thinking.",
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
            "internal": internal,
            "body_language": body_language,
            "spoken": spoken,
            "action": action,
        },
        "adjudication": {
            "character_id": char_id,
            "turn": turn,
            "approved": True,
            "modified_action": "none.",
            "new_position": None,
            "condition_deltas": {},
            "spatial_events": [],
            "notes": "",
        },
        "narration": {
            "character_id": char_id,
            "turn": turn,
            "prose": prose,
            "visible_to": [],
        },
    }


def _turn_data(turn: int, characters: list[dict]) -> dict:
    return {
        "turn": turn,
        "initiative_order": [c["character_id"] for c in characters],
        "character_results": characters,
        "conditions": {},
    }


# =========================================================================
# extract_scene_material
# =========================================================================

class TestExtractSceneMaterial:
    def test_extracts_narration(self):
        turns = [_turn_data(1, [
            _char_result("aeliana", prose="The elf steps forward."),
        ])]
        material = extract_scene_material(turns)
        assert "The elf steps forward." in material

    def test_extracts_dialogue(self):
        turns = [_turn_data(1, [
            _char_result("fennel", spoken='"Stop there."'),
        ])]
        material = extract_scene_material(turns)
        assert "Stop there" in material

    def test_extracts_body_language(self):
        turns = [_turn_data(1, [
            _char_result("aeliana", body_language="Crouches behind a root."),
        ])]
        material = extract_scene_material(turns)
        assert "Crouches behind a root." in material

    def test_silent_characters_no_dialogue_line(self):
        turns = [_turn_data(1, [
            _char_result("aeliana", spoken=""),
        ])]
        material = extract_scene_material(turns)
        assert "says:" not in material.lower()

    def test_multiple_turns_in_order(self):
        turns = [
            _turn_data(1, [_char_result("aeliana", turn=1, prose="First.")]),
            _turn_data(2, [_char_result("aeliana", turn=2, prose="Second.")]),
        ]
        material = extract_scene_material(turns)
        assert material.index("First.") < material.index("Second.")

    def test_multiple_characters_per_turn(self):
        turns = [_turn_data(1, [
            _char_result("aeliana", prose="Aeliana acts."),
            _char_result("fennel", prose="Fennel acts."),
        ])]
        material = extract_scene_material(turns)
        assert "Aeliana acts." in material
        assert "Fennel acts." in material


# =========================================================================
# build_narrative_prompt
# =========================================================================

class TestBuildNarrativePrompt:
    def test_system_prompt_contains_instructions(self):
        system, user = build_narrative_prompt("Some material.")
        assert "narrative" in system.lower() or "story" in system.lower()

    def test_user_prompt_contains_material(self):
        system, user = build_narrative_prompt("The elf steps forward.")
        assert "The elf steps forward." in user

    def test_title_included_when_provided(self):
        system, user = build_narrative_prompt(
            "Material.", title="The Fey Glade"
        )
        assert "The Fey Glade" in user

    def test_system_prompt_requests_prose(self):
        system, user = build_narrative_prompt("Material.")
        # Should ask for prose fiction, not game mechanics
        assert "prose" in system.lower() or "fiction" in system.lower()


# =========================================================================
# _chunk_turns
# =========================================================================

def _turn_with_time(turn: int, hour: int, period: str = "dusk", day: int = 1) -> dict:
    return {
        "turn": turn,
        "game_time": {"hour": hour, "minute": 0, "day": day, "season": "spring", "period": period},
        "initiative_order": [],
        "character_results": [],
        "conditions": {},
    }


class TestChunkTurns:
    def test_empty_returns_empty(self):
        assert _chunk_turns([]) == []

    def test_fewer_than_n_returns_single_chunk(self):
        turns = [_turn_with_time(1, 19), _turn_with_time(2, 19)]
        chunks = _chunk_turns(turns, n=4)
        assert len(chunks) == 1
        assert len(chunks[0][1]) == 2

    def test_exactly_n_returns_single_chunk(self):
        turns = [_turn_with_time(i, 19) for i in range(1, 5)]
        chunks = _chunk_turns(turns, n=4)
        assert len(chunks) == 1

    def test_more_than_n_creates_multiple_chunks(self):
        turns = [_turn_with_time(i, 19) for i in range(1, 6)]
        chunks = _chunk_turns(turns, n=4)
        assert len(chunks) == 2
        assert len(chunks[0][1]) == 4
        assert len(chunks[1][1]) == 1

    def test_label_includes_hour_and_period(self):
        turns = [_turn_with_time(1, 19, period="dusk")]
        chunks = _chunk_turns(turns, n=4)
        label = chunks[0][0]
        assert "19:00" in label
        assert "Dusk" in label

    def test_label_uses_first_turn_in_chunk(self):
        # Chunk starts at hour 19 even though turn 5 is hour 20
        turns = [_turn_with_time(i, 19) for i in range(1, 5)] + [_turn_with_time(5, 20)]
        chunks = _chunk_turns(turns, n=4)
        assert "19:00" in chunks[0][0]
        assert "20:00" in chunks[1][0]

    def test_day_2_label_includes_day(self):
        turns = [_turn_with_time(1, 8, day=2)]
        chunks = _chunk_turns(turns, n=4)
        assert "Day 2" in chunks[0][0]

    def test_day_1_label_omits_day(self):
        turns = [_turn_with_time(1, 19, day=1)]
        chunks = _chunk_turns(turns, n=4)
        assert "Day 1" not in chunks[0][0]

    def test_no_game_time_uses_turn_range_label(self):
        turns = [_turn_data(1, []), _turn_data(2, []), _turn_data(3, [])]
        chunks = _chunk_turns(turns, n=4)
        assert len(chunks) == 1
        assert "1" in chunks[0][0] and "3" in chunks[0][0]

    def test_many_melee_rounds_still_chunk_by_n(self):
        # 20 melee turns all at same hour — should produce 5 chunks of 4, not 1 huge group
        turns = [_turn_with_time(i, 19, period="dusk") for i in range(1, 21)]
        chunks = _chunk_turns(turns, n=4)
        assert len(chunks) == 5
