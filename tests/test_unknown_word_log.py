"""The persistent unknown-word log (engine.unknown_word_log)."""

import json
from pathlib import Path

from engine.unknown_word_log import log_unknown_words


def test_logs_words_with_context(tmp_path):
    log = tmp_path / "unknown_words.json"
    log_unknown_words(
        ["Eat", "flibber"], intent_text="I Eat the pie",
        scene="places/driftmoor", suggestions={"flibber": ["fibber"]}, path=log)
    data = json.loads(log.read_text())
    # normalized to lowercase keys
    assert set(data) == {"eat", "flibber"}
    assert data["eat"]["count"] == 1
    assert "I Eat the pie" in data["eat"]["examples"]
    assert data["flibber"]["suggestions"] == ["fibber"]
    assert data["eat"]["scenes"] == ["places/driftmoor"]


def test_accumulates_across_calls(tmp_path):
    log = tmp_path / "unknown_words.json"
    log_unknown_words(["flibber"], intent_text="one", path=log)
    log_unknown_words(["flibber"], intent_text="two", path=log)
    data = json.loads(log.read_text())
    assert data["flibber"]["count"] == 2
    assert data["flibber"]["examples"] == ["one", "two"]


def test_empty_and_blank_are_noops(tmp_path):
    log = tmp_path / "unknown_words.json"
    log_unknown_words([], path=log)
    log_unknown_words(["", "   "], path=log)
    assert not log.exists()


def test_logging_never_raises_on_bad_path(tmp_path):
    # A directory where a file is expected must not crash the caller.
    bad = tmp_path / "adir"
    bad.mkdir()
    log_unknown_words(["word"], path=bad)  # should swallow the error
