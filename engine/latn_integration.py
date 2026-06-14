"""Glue between the session turn loop and the LATN resolver.

Builds the per-turn LATN context (lexicon + scene adapter) from the data the
turn loop already has (items, characters, the actor's zone) and exposes a
drop-in ``resolve_item_interaction`` that is LATN-first with a shallow
fallback.

GATED behind the DRIFTMOOR_LATN_RESOLVER env flag, default OFF: until it is
set, every call behaves exactly like the shallow ``verb_resolver`` — so the
wiring can land before the acceptance replay (parse-rate / grounding-rate /
disagreement-taxonomy vs the shallow resolver) gates the actual cutover.
Flip it on (``DRIFTMOOR_LATN_RESOLVER=1``) to exercise the LATN path.

The context is rebuilt per call for now (lexicon build is cheap); caching the
near-static lexicon per scene is a later optimization.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

from models.item import Interaction, Item


def latn_enabled() -> bool:
    return os.environ.get("DRIFTMOOR_LATN_RESOLVER", "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def build_context(items: dict, characters: dict, actor_zone: str):
    """Build (lexicon, adapter) for LATN resolution this turn.

    ``characters`` values may be CharacterSession or Character — both the
    lexicon builder and the adapter accept either (via character_view).
    """
    from engine.latn_lexicon import build_driftmoor_lexicon
    from engine.latn_adapter import DriftmoorSceneAdapter

    char_list = list(characters.values()) if hasattr(characters, "values") else list(characters)
    item_list = list(items.values()) if hasattr(items, "values") else list(items)
    lexicon = build_driftmoor_lexicon(char_list, item_list)
    adapter = DriftmoorSceneAdapter(items=items, characters=characters, actor_zone=actor_zone)
    return lexicon, adapter


def resolve_item_interaction(
    *,
    intent_text: str,
    interaction_target: Optional[str],
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
) -> Optional[Tuple[Item, Interaction]]:
    """LATN-first (flag-gated) resolution with shallow fallback.

    Same return contract as ``verb_resolver.resolve_item_interaction``, plus a
    ``characters`` argument (needed to build the adapter/lexicon). With the
    flag off — or when items/characters are missing — it is exactly the shallow
    resolver.
    """
    if latn_enabled() and items and characters:
        from engine import latn_resolver
        lexicon, adapter = build_context(items, characters, character_zone or "")
        return latn_resolver.resolve_item_interaction(
            intent_text,
            interaction_target=interaction_target,
            items=items,
            character_zone=character_zone,
            lexicon=lexicon,
            adapter=adapter,
        )
    from engine.verb_resolver import resolve_item_interaction as _shallow
    return _shallow(
        intent_text=intent_text,
        interaction_target=interaction_target,
        items=items,
        character_zone=character_zone,
    )
