"""Transitional shim: the scene ``Item`` model merged into ``models.thing.Thing``.

Historically Driftmoor had two possessable types — a rich scene ``Item`` (this
module) and a shop ``Thing``. They are now one ``Thing`` (see ``models.thing``).
This module re-exports ``Thing`` as ``Item`` plus the perception helpers so the
existing ``from models.item import Item, Interaction, apparent_size_band, ...``
call sites keep working while they are migrated to ``models.thing``. Remove this
shim at the end of the item-unification branch.
"""

from __future__ import annotations

from models.thing import (  # noqa: F401  (re-export)
    APPEARANCE_BAND_NAMES,
    DEFAULT_ITEM_SIZE_FT,
    SIZE_KEYWORDS_FT,
    _APPARENT_SIZE_BANDS,
    Interaction,
    Thing as Item,
    apparent_size_band,
)

__all__ = [
    "Item",
    "Interaction",
    "apparent_size_band",
    "SIZE_KEYWORDS_FT",
    "DEFAULT_ITEM_SIZE_FT",
    "APPEARANCE_BAND_NAMES",
    "_APPARENT_SIZE_BANDS",
]
