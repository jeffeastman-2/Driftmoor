"""In-turn unknown-word clarification sub-dialog (engine.session).

Pure helper: the transport `ask` and the lexicon-backed `diagnose` are injected,
so this needs no live scene. Verifies the loop asks only on unknowns, re-checks
the rephrase, and is bounded."""

import asyncio

from engine.session import (
    _ambiguous_driftmoor_venues,
    _clarify_ambiguous_venue,
    _clarify_unknown_words,
    _format_ambiguous_venue_prompt,
    _format_unknown_word_prompt,
    _filter_presented_unknowns,
)


class _Ask:
    """A scripted transport: hands back queued replies, records the prompts."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    async def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else ""


def _seq_diagnose(*results):
    """A diagnose stand-in that returns each result in turn (last one sticks)."""
    state = {"i": 0}

    def diag(_text):
        r = results[min(state["i"], len(results) - 1)]
        state["i"] += 1
        return r
    return diag


def _run(text, diag, ask):
    return asyncio.run(_clarify_unknown_words(text, ask=ask, diagnose_fn=diag))


class TestPrompt:
    def test_single_unknown_with_suggestion(self):
        msg = _format_unknown_word_prompt([("crosbow", ["crossbow"])])
        assert "crosbow" in msg and "crossbow" in msg and "the word" in msg

    def test_multiple_unknowns(self):
        msg = _format_unknown_word_prompt([("floober", []), ("grommit", ["grommet"])])
        assert "some of those words" in msg and "floober" in msg and "grommit" in msg

    def test_words_previously_spoken_by_the_game_are_not_unknown(self):
        unknowns = [("conduit", []), ("glyphs", []), ("unrelated", [])]
        history = "Elyssa says the glyphs suggest a conduit, not a boundary."
        assert _filter_presented_unknowns(unknowns, history) == [
            ("unrelated", [])
        ]


class TestClarifyLoop:
    def test_no_unknowns_returns_immediately(self):
        ask = _Ask()
        out = _run("buy the bolts", _seq_diagnose([]), ask)
        assert out == "buy the bolts"
        assert ask.prompts == []                      # never bothered the player

    def test_clears_after_one_rephrase(self):
        ask = _Ask("buy crossbow bolts")
        out = _run("buy crosbow bolts",
                   _seq_diagnose([("crosbow", ["crossbow"])], []), ask)
        assert out == "buy crossbow bolts"
        assert len(ask.prompts) == 1 and "crossbow" in ask.prompts[0]

    def test_empty_reply_stops_with_current_text(self):
        ask = _Ask("")                                # player gives up
        out = _run("buy crosbow bolts", _seq_diagnose([("crosbow", [])]), ask)
        assert out == "buy crosbow bolts"
        assert len(ask.prompts) == 1

    def test_bounded_after_max_rounds(self):
        ask = _Ask("still off", "and off", "off again", "never asked")
        out = _run("first", _seq_diagnose([("x", [])]), ask)   # always unknown
        assert out == "off again"                     # last reply within 3 rounds
        assert len(ask.prompts) == 3


class TestVenueClarification:
    def test_cottage_lists_the_two_matching_destinations(self):
        choices = _ambiguous_driftmoor_venues(
            "I enter the cottage", "places/driftmoor"
        )
        assert {scene for scene, _label in choices} == {
            "elyssa_cottage", "weavers_cottage"
        }
        prompt = _format_ambiguous_venue_prompt(choices)
        assert "ambiguous" in prompt and "Elyssa" in prompt and "Weaver" in prompt

    def test_short_answer_becomes_an_enter_intent(self):
        ask = _Ask("Elyssa's cottage")
        out = asyncio.run(_clarify_ambiguous_venue(
            "I enter the cottage", ask=ask,
            candidates=(("elyssa_cottage", "Elyssa's Cottage"),
                        ("weavers_cottage", "Weaver's Cottage")),
        ))
        assert out == "enter Elyssa's cottage"


class TestGroundingGate:
    """The gate that decides whether the clarification runs at all: a line the
    engine can act on is never interrogated about vocabulary."""

    def _grounds(self, s):
        from models.shop_catalog import ShopCatalog
        from engine.session import _DRIFTMOOR_PLACES_ROOT, _player_intent_grounds
        from engine.latn_integration import build_context
        entries = ShopCatalog.from_things_dir(
            _DRIFTMOOR_PLACES_ROOT.parent.parent / "things").entries_for("jorgen")
        lex, adp = build_context({}, {}, "", None, venues=(), catalog=entries)
        return _player_intent_grounds(
            s, lexicon=lex, adapter=adp, items={}, characters={},
            actor_zone="", entries=entries)

    def test_grounded_lines_gate_off_the_clarification(self):
        # A recognized action -- even a buy buried in prose with unknown framing
        # words ("look"/"ask") -- counts as grounded.
        for s in ("buy bolts",
                  "I look around and ask, I am looking for some crossbow bolts",
                  "examine the orb", "go to the well"):
            assert self._grounds(s) is True, s

    def test_ungrounded_lines_let_the_clarification_run(self):
        for s in ("xyzzy plugh", "I ponder my fate"):
            assert self._grounds(s) is False, s
