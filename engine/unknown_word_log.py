"""Persistent log of words the LATN lexicon didn't recognize during play.

When a human player's line can't be grounded and the parser-honesty diagnostic
flags out-of-vocabulary words, they're recorded here -- so vocabulary gaps get
captured as they happen and can be reviewed and filled later, without anyone
having to remember them mid-game. This is a passive side-channel: grounding, the
clarify sub-dialog, and the turn are all unaffected by whether logging succeeds.

The log is a single JSON object keyed by the unknown word:

    {
      "eat": {
        "count": 3,
        "first_seen": "2026-07-24T18:20:05+00:00",
        "last_seen":  "2026-07-24T18:41:12+00:00",
        "suggestions": ["seat", "ear"],
        "examples": ["I eat the meat pie"],
        "scenes": ["driftmoor"]
      },
      ...
    }

Path defaults to ``runtime/unknown_words.json`` (override with
``DRIFTMOOR_UNKNOWN_WORDS_LOG``). Reviewing it is how "eat" gets added to the
lexicon later.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional

_DEFAULT_LOG = Path("runtime") / "unknown_words.json"
_MAX_EXAMPLES = 5


def log_path() -> Path:
    """Where the unknown-word log lives (env-overridable)."""
    return Path(os.environ.get("DRIFTMOOR_UNKNOWN_WORDS_LOG", str(_DEFAULT_LOG)))


def log_unknown_words(
    words: Iterable[str],
    *,
    intent_text: str = "",
    scene: str = "",
    suggestions: Optional[Mapping[str, Iterable[str]]] = None,
    path: Optional[Path] = None,
) -> None:
    """Record each unknown word, merging into any existing entry.

    ``words`` are the out-of-vocabulary tokens (from ``diagnostics.diagnose``);
    ``suggestions`` maps a word to its near-spellings. Never raises -- a logging
    failure must not disturb play.
    """
    normalized = [w.strip().lower() for w in (words or []) if w and w.strip()]
    if not normalized:
        return
    target = Path(path) if path is not None else log_path()
    sugg = {k.strip().lower(): list(v or []) for k, v in (suggestions or {}).items()}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    example = (intent_text or "").strip()
    scene = (scene or "").strip()
    try:
        data = _load(target)
        for word in normalized:
            entry = data.get(word) or {
                "count": 0, "first_seen": now, "last_seen": now,
                "suggestions": [], "examples": [], "scenes": [],
            }
            entry["count"] = int(entry.get("count", 0)) + 1
            entry["last_seen"] = now
            entry.setdefault("first_seen", now)
            for lst, value in (
                ("suggestions", None),
                ("examples", example),
                ("scenes", scene),
            ):
                items = list(entry.get(lst) or [])
                if lst == "suggestions":
                    for s in sugg.get(word, []):
                        if s and s not in items:
                            items.append(s)
                elif value and value not in items:
                    items.append(value)
                entry[lst] = items[-_MAX_EXAMPLES:] if lst == "examples" else items
            data[word] = entry
        _save(target, data)
    except Exception:  # noqa: BLE001 - logging is best-effort, never fatal
        return


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, ValueError):
        return {}


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replace so a crash mid-write can't corrupt the log.
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True, ensure_ascii=False)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
