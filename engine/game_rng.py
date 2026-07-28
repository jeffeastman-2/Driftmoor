"""The single game RNG.

Dice, attack rolls, and boundary-crossing checks used to reach for the global
``random`` module directly. That made combat outcomes depend on whatever seed
``pytest-randomly`` (or the OS) happened to install -- so a test that asserts a
combat result was flaky across run orders even though it passed its own seeded
``rng``.

Route every roll through ``rng()`` instead. ``iter_session`` calls ``use_rng``
once with the session's ``rng`` (a seeded ``random.Random`` in tests, a fresh one
in play), so a given seed reproduces the same game.

NOTE: this is process-global, seeded per session -- fine for the single-session
case (tests, ordinary play). True per-session isolation under *concurrent*
scenes would need the rng threaded through the roll call sites; deferred, and no
worse than the global ``random`` it replaces.
"""

from __future__ import annotations

import random

_rng: random.Random = random.Random()


def rng() -> random.Random:
    """The active game RNG. Use this for every gameplay roll."""
    return _rng


def use_rng(r: random.Random | None) -> random.Random:
    """Install the session RNG (``None`` -> a fresh unseeded one). Returns it."""
    global _rng
    _rng = r if r is not None else random.Random()
    return _rng
