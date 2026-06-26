"""In-process web transport: async queues bridging the turn loop and a browser.

Mirrors ``TelegramTransport``'s role at the player-I/O seam (see
``engine.session._player_roles_via_transport``), but for an in-process web
client. The turn loop's prompt is put on the character's OUTBOUND queue (drained
by the web app's SSE stream); the player's typed reply arrives on the INBOUND
queue (filled by the web app's POST handler). No threads and no network library
— both sides share one asyncio event loop, so the loop simply ``await``s the
player's reply.
"""
from __future__ import annotations

import asyncio

_OUT: dict[str, asyncio.Queue] = {}
_IN: dict[str, asyncio.Queue] = {}


def _out(cid: str) -> asyncio.Queue:
    return _OUT.setdefault(cid, asyncio.Queue())


def _in(cid: str) -> asyncio.Queue:
    return _IN.setdefault(cid, asyncio.Queue())


class WebTransport:
    """Per-character handle used by the turn loop (the telegram-transport twin)."""

    def __init__(self, character_id: str) -> None:
        self.character_id = character_id

    async def send(self, text: str) -> None:
        await _out(self.character_id).put(text)

    async def receive(self) -> str:
        return await _in(self.character_id).get()


def for_character(character_id: str) -> WebTransport:
    return WebTransport(character_id)


# --- web-app facing helpers -------------------------------------------------

async def next_outbound(character_id: str) -> str:
    """Await the next message the turn loop wants to show this player."""
    return await _out(character_id).get()


def drain_outbound(character_id: str) -> list[str]:
    """All currently-queued outbound messages (non-blocking) — for the SSE loop
    to interleave DM/prompt lines with per-turn narration."""
    q = _out(character_id)
    out: list[str] = []
    while not q.empty():
        out.append(q.get_nowait())
    return out


def submit_inbound(character_id: str, text: str) -> None:
    """Hand the player's typed reply to the (awaiting) turn loop."""
    _in(character_id).put_nowait(text)


# Latest live (possibly mid-turn) character positions, published by the turn loop
# when it prompts a web player. Lets the web app show where everyone is *now* —
# including NPCs who already acted this turn — instead of lagging a turn behind
# the end-of-turn checkpoints the map is otherwise built from.
_POS: dict[str, tuple] = {}


def publish_positions(positions: dict | None) -> None:
    """Store the latest live positions (cid -> (x, y, zone))."""
    _POS.clear()
    for cid, p in (positions or {}).items():
        if p is not None:
            _POS[cid] = tuple(p)


def latest_positions() -> dict:
    """The most recent live positions the turn loop published (copy)."""
    return dict(_POS)


# Live per-character narration, published by the turn loop as each character
# acts so the web log can show progress during a slow turn instead of a blank
# screen until the whole turn completes. Drained (destructively) by the SSE
# loop; the authoritative per-turn replay still comes from the checkpoints.
_ACTIONS: list[dict] = []


def publish_action(entry: dict) -> None:
    """Queue one character's just-resolved narration for the web log."""
    _ACTIONS.append(entry)


def drain_actions() -> list[dict]:
    """All queued live narration entries (non-blocking, clears the queue)."""
    out = _ACTIONS[:]
    _ACTIONS.clear()
    return out


def reset(character_id: str | None = None) -> None:
    """Drop queues (between sessions / in tests)."""
    if character_id is None:
        _OUT.clear()
        _IN.clear()
        _POS.clear()
        _ACTIONS.clear()
    else:
        _OUT.pop(character_id, None)
        _IN.pop(character_id, None)
