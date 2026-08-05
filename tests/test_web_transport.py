"""Tests for the in-process web transport (engine/web_transport.py).

The web transport bridges the turn loop and a browser through two per-character
asyncio queues: the loop's prompts go OUT (drained by the SSE stream), the
player's typed replies come IN (fed by the POST handler). These tests exercise
that round-trip and the web-app-facing helpers without a running session.
"""
import asyncio

import pytest

from engine import web_transport as wt


@pytest.fixture(autouse=True)
def _clean():
    wt.reset()          # all characters
    yield
    wt.reset()


def test_publish_and_latest_positions():
    wt.publish_positions({"a": (1, 2, "X"), "b": (3, 4, "Y"), "c": None})
    assert wt.latest_positions() == {"a": (1, 2, "X"), "b": (3, 4, "Y")}  # None skipped
    wt.publish_positions({"a": (5, 6, "Z")})  # replaces, not merges
    assert wt.latest_positions() == {"a": (5, 6, "Z")}


def test_reset_clears_positions():
    wt.publish_positions({"a": (1, 2, "X")})
    wt.reset()
    assert wt.latest_positions() == {}


def test_publish_and_drain_actions():
    wt.publish_action({"turn": 1, "cid": "amara", "prose": "She steps forward."})
    wt.publish_action({"turn": 1, "cid": "thorgrim", "prose": "He raises his axe."})
    drained = wt.drain_actions()
    assert [a["cid"] for a in drained] == ["amara", "thorgrim"]
    assert wt.drain_actions() == []      # destructive — drained once


def test_reset_clears_actions():
    wt.publish_action({"turn": 1, "cid": "amara", "prose": "x"})
    wt.reset()
    assert wt.drain_actions() == []


def test_send_then_drain_outbound():
    async def go():
        h = wt.for_character("p")
        await h.send("What do you do?")
        await h.send("Still your move.")
        assert wt.drain_outbound("p") == ["What do you do?", "Still your move."]
        assert wt.drain_outbound("p") == []   # drained, non-blocking
    asyncio.run(go())


def test_submit_inbound_then_receive():
    async def go():
        h = wt.for_character("p")
        wt.submit_inbound("p", "I draw my dagger")
        assert await h.receive() == "I draw my dagger"
    asyncio.run(go())


def test_next_outbound_awaits_send():
    async def go():
        h = wt.for_character("p")

        async def producer():
            await asyncio.sleep(0.01)
            await h.send("ping")

        got, _ = await asyncio.gather(wt.next_outbound("p"), producer())
        assert got == "ping"
    asyncio.run(go())


def test_reset_single_character_isolated():
    async def go():
        wt.submit_inbound("a", "keep me")
        wt.submit_inbound("b", "drop me")
        wt.reset("b")
        # b's queue cleared; a's intact.
        assert wt.drain_outbound("b") == []
        assert await wt.for_character("a").receive() == "keep me"
    asyncio.run(go())


def test_queues_are_per_character():
    async def go():
        await wt.for_character("a").send("for-a")
        await wt.for_character("b").send("for-b")
        assert wt.drain_outbound("a") == ["for-a"]
        assert wt.drain_outbound("b") == ["for-b"]
    asyncio.run(go())


def test_flush_inbound_drops_stale_input():
    # A stray out-of-turn POST is discarded so the next receive() reads the
    # reply submitted *after* the prompt, never a stale one.
    wt.submit_inbound("p", "stale line typed out of turn")
    wt.flush_inbound("p")
    assert wt._in("p").empty()

    async def go():
        wt.submit_inbound("p", "fresh reply")
        assert await wt.for_character("p").receive() == "fresh reply"
    asyncio.run(go())


def test_awaiting_defaults_false_then_toggles():
    assert wt.is_awaiting("p") is False        # not their turn until prompted
    wt.set_awaiting("p", True)
    assert wt.is_awaiting("p") is True
    wt.set_awaiting("p", False)
    assert wt.is_awaiting("p") is False


def test_latest_prompt_defaults_empty_then_stores():
    # A reconnecting client needs a durable copy of the current outstanding
    # prompt — the outbound queue is one-shot and gone once drained into a
    # response stream, even one nobody ended up reading.
    assert wt.latest_prompt("p") == ""
    wt.publish_prompt("p", "You are at the door.")
    assert wt.latest_prompt("p") == "You are at the door."
    wt.publish_prompt("p", "")  # e.g. a suppressed web packet -- stored as-is
    assert wt.latest_prompt("p") == ""


def test_reset_clears_latest_prompt():
    wt.publish_prompt("p", "You are at the door.")
    wt.reset()
    assert wt.latest_prompt("p") == ""


def test_reset_single_character_clears_only_that_prompt():
    wt.publish_prompt("a", "prompt for a")
    wt.publish_prompt("b", "prompt for b")
    wt.reset("a")
    assert wt.latest_prompt("a") == ""
    assert wt.latest_prompt("b") == "prompt for b"


def test_awaiting_is_per_character():
    wt.set_awaiting("a", True)
    assert wt.is_awaiting("a") is True
    assert wt.is_awaiting("b") is False        # b unaffected


def test_reset_clears_awaiting():
    wt.set_awaiting("p", True)
    wt.reset()
    assert wt.is_awaiting("p") is False

    wt.set_awaiting("a", True)
    wt.set_awaiting("b", True)
    wt.reset("a")
    assert wt.is_awaiting("a") is False         # cleared
    assert wt.is_awaiting("b") is True          # untouched
