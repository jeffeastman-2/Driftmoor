"""Direct Telegram Bot API transport for human players.

Replaces the file inbox/outbox + external bridge (OpenClaw) with in-process Bot
API calls: the turn loop sends prompts with ``sendMessage`` and waits for the
player's reply with ``getUpdates`` long-polling. No folders, no sidecar process.

Per-player config comes from the environment (tokens are secrets, so they do
NOT live in scene files). For character ``gilthaness``:

    BOT_TOKEN_GILTHANESS=...     # this player's OWN bot (see note below)
    CHAT_ID_GILTHANESS=...       # the player's Telegram user/chat id

A bare ``BOT_TOKEN`` / ``CHAT_ID`` is accepted as a single-player fallback.

IMPORTANT: ``getUpdates`` consumes a bot's updates globally, so each human
player needs their OWN bot token — one bot per player. The transport is cached
per character so its update offset advances monotonically across turns.

The methods are synchronous (plain ``requests``); the async turn loop calls them
via ``asyncio.to_thread`` so the long-poll never blocks the event loop.
"""

import os
import time
import requests

# Telegram hard limit is 4096; leave headroom for the chunk marker.
TELEGRAM_MAX_CHARS = 4000


def _split_for_telegram(text, limit=TELEGRAM_MAX_CHARS):
    """Split text into <=limit-char chunks, preferring paragraph then line
    boundaries (verbatim behavior from the original bridge)."""
    if len(text) <= limit:
        return [text]
    chunks, remaining = [], text
    while len(remaining) > limit:
        window = remaining[:limit]
        split_at = window.rfind("\n\n")
        if split_at < limit // 2:
            split_at = window.rfind("\n")
        if split_at < limit // 2:
            split_at = window.rfind(" ")
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


class TelegramTransport:
    """Send/receive for one player over a dedicated Telegram bot."""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = str(chat_id)
        self._offset = None  # last seen update_id; None until first poll

    def _api(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/{method}"

    def _get_updates(self, timeout: int):
        params = {"timeout": timeout}
        if self._offset is not None:
            params["offset"] = self._offset + 1
        r = requests.get(self._api("getUpdates"), params=params, timeout=timeout + 10)
        r.raise_for_status()
        return r.json().get("result", [])

    def send(self, text: str) -> bool:
        """Send a message, chunking if over Telegram's limit. Returns success."""
        chunks = _split_for_telegram(text)
        for i, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                chunk = f"[{i}/{len(chunks)}]\n{chunk}"
            try:
                r = requests.post(
                    self._api("sendMessage"),
                    json={"chat_id": self.chat_id, "text": chunk},
                    timeout=30,
                )
                r.raise_for_status()
            except Exception as e:  # noqa: BLE001 - log and report failure
                print(f"[telegram] send error (chat {self.chat_id}): {e}")
                return False
        return True

    def flush(self) -> None:
        """Discard any pending updates so the next poll only sees messages that
        arrive AFTER this point — the accept-after-prompt cutoff. Call right
        before sending a prompt."""
        try:
            for u in self._get_updates(timeout=0):
                self._offset = u["update_id"]
        except Exception as e:  # noqa: BLE001 - non-fatal; next poll re-syncs
            print(f"[telegram] flush error (chat {self.chat_id}): {e}")

    def poll_once(self, timeout: int = 30):
        """One long-poll. Return the first text message from this player's chat,
        or None if the poll returned nothing matching. Transient errors are
        swallowed (return None) so the caller just keeps polling."""
        try:
            updates = self._get_updates(timeout=timeout)
        except Exception as e:  # noqa: BLE001 - treat as "no reply yet"
            print(f"[telegram] poll error (chat {self.chat_id}): {e}")
            time.sleep(2)
            return None
        for u in updates:
            self._offset = u["update_id"]
            msg = u.get("message")
            if (msg and "text" in msg
                    and str(msg.get("from", {}).get("id")) == self.chat_id):
                return msg["text"]
        return None


_cache: dict[str, TelegramTransport] = {}


def _env(character_id: str, key: str):
    """Per-character env value (KEY_<CHARID>) with a bare KEY fallback."""
    return (os.environ.get(f"{key}_{character_id.upper()}")
            or os.environ.get(key))


def for_character(character_id: str):
    """Cached TelegramTransport for a character, or None if BOT_TOKEN/CHAT_ID
    are not configured. Cached so the update offset persists across turns."""
    tt = _cache.get(character_id)
    if tt is not None:
        return tt
    bot_token = _env(character_id, "BOT_TOKEN")
    chat_id = _env(character_id, "CHAT_ID")
    if not bot_token or not chat_id:
        return None
    tt = TelegramTransport(bot_token, chat_id)
    _cache[character_id] = tt
    return tt
