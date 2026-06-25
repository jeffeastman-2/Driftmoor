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
