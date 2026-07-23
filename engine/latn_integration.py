"""Glue between the session turn loop and the LATN resolver.

Builds the per-turn LATN context (lexicon + scene adapter) from the data the
turn loop already has (items, characters, the actor's zone, scene geometry) and
exposes drop-in resolution helpers that are LATN-first with a shallow
``verb_resolver`` fallback.

LATN is the default path for EVERY actor (human and NPC); the shallow resolver
remains the safety net whenever LATN doesn't parse or ground, so resolution can
only match-or-improve, never regress. (Earlier cutover flags —
DRIFTMOOR_LATN_RESOLVER and a human-only gate — were removed once NPC prompts
became terse VPs that LATN handles.)

The context is rebuilt per call for now (lexicon build is cheap); caching the
near-static lexicon per scene is a later optimization.
"""

from __future__ import annotations

from typing import Optional, Tuple

from models.item import Interaction, Item


def build_context(items: dict, characters: dict, actor_zone: str,
                  scene_geometry=None, venues=None, catalog=None):
    """Build (lexicon, adapter) for LATN resolution this turn.

    ``characters`` values may be CharacterSession or Character — both the
    lexicon builder and the adapter accept either (via character_view).
    ``scene_geometry`` (when supplied) contributes its zone and landmark names
    to the lexicon so movement targets like "the rocky passage" / "echo
    chamber arch" tokenize — matching the acceptance harness. ``venues`` is an
    iterable of ``(scene_name, aliases)`` for the enterable child places, fed to
    both the lexicon (so multi-word venue names tokenize) and the adapter (so
    they ground) — used by venue-transition resolution.
    """
    from engine.latn_lexicon import build_driftmoor_lexicon
    from engine.latn_adapter import DriftmoorSceneAdapter

    char_list = list(characters.values()) if hasattr(characters, "values") else list(characters)
    item_list = list(items.values()) if hasattr(items, "values") else list(items)
    zones = list(getattr(scene_geometry, "zones", {}) or {}) if scene_geometry is not None else []
    landmarks = list(getattr(scene_geometry, "landmarks", {}) or {}) if scene_geometry is not None else []
    venue_list = list(venues or [])
    catalog_list = list(catalog or [])
    lexicon = build_driftmoor_lexicon(
        char_list, item_list, zones=zones, landmarks=landmarks, venues=venue_list,
        catalog=catalog_list,
    )
    adapter = DriftmoorSceneAdapter(
        items=items, characters=characters, actor_zone=actor_zone,
        venues=venue_list, catalog=catalog_list)
    return lexicon, adapter


def resolve_commerce(intent_text, items, characters, actor_zone, catalog,
                     scene_geometry=None):
    """LATN buy/sell resolution. Returns ``("buy", catalog_entry)`` /
    ``("sell", item)`` / ``None`` (not a commerce intent, or nothing unique
    grounded — caller declines). The grounded object is the CatalogEntry (buy)
    or the scene Item (sell), or None on an ambiguous/unmatched name."""
    from engine import latn_resolver
    lexicon, adapter = build_context(
        items or {}, characters or {}, actor_zone or "", scene_geometry,
        catalog=catalog)
    res = latn_resolver.resolve_commerce_action(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if res is None:
        return None
    verb, ent = res
    if ent is None:
        # Verb read as commerce but the object didn't ground to a real good
        # (e.g. "looking for the way out"): the object gate declines it rather
        # than reporting a buy of nothing.
        return None
    if verb == "buy":
        return ("buy", getattr(ent, "entry", None))
    return ("sell", getattr(ent, "item", None))


def resolve_response(intent_text, characters, actor_zone):
    """LATN read of a bare yes/no reply: "affirm" / "decline" / None."""
    from engine import latn_resolver
    lexicon, adapter = build_context({}, characters or {}, actor_zone or "")
    return latn_resolver.resolve_response(
        intent_text or "", lexicon=lexicon, adapter=adapter)


def resolve_venue_transition(intent_text, characters, actor_zone, venues,
                             scene_geometry=None):
    """LATN venue-transition resolution. Returns ``("enter", scene_name)`` when
    an enter intent grounds a unique child venue, ``("leave", None)`` for an
    exit intent, or ``None`` (not a crossing intent, or the venue name grounded
    to nothing unique — the caller declines rather than guessing). ``scene_name``
    may be None on an ambiguous/unmatched enter."""
    from engine import latn_resolver
    lexicon, adapter = build_context(
        {}, characters or {}, actor_zone or "", scene_geometry, venues=venues)
    res = latn_resolver.resolve_venue_action(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    if res is None:
        return None
    kind, ent = res
    if kind == "leave":
        return ("leave", None)
    return ("enter", getattr(ent, "scene_name", None))


def resolve_item_interaction(
    *,
    intent_text: str,
    interaction_target: Optional[str],
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
    scene_geometry=None,
) -> Optional[Tuple[Item, Interaction]]:
    """LATN-first resolution with shallow fallback.

    Same return contract as ``verb_resolver.resolve_item_interaction``, plus a
    ``characters`` argument (needed to build the adapter/lexicon) and an optional
    ``scene_geometry`` (its zones/landmarks feed the lexicon). When
    items/characters are missing it is exactly the shallow resolver.
    """
    if items and characters:
        from engine import latn_resolver
        lexicon, adapter = build_context(
            items, characters, character_zone or "", scene_geometry,
        )
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


def infer_interaction_target(
    intent_text: str,
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
    scene_geometry=None,
) -> Optional[str]:
    """LATN-first interaction-target inference, shallow fallback.

    Same role and return (an item label/id, or None) as
    ``verb_resolver.infer_interaction_target`` — derive the object the actor is
    acting on when the model left ``interaction_target`` empty — plus the
    ``characters``/``scene_geometry`` needed to build the parser context. The
    LATN adapter is zone-filtered (built with ``character_zone``), mirroring the
    shallow resolver's in-zone requirement. With missing items/characters it is
    exactly the shallow inference.
    """
    if items and characters:
        from engine import latn_resolver
        lexicon, adapter = build_context(
            items, characters, character_zone or "", scene_geometry,
        )
        # Only an INTERACTION/transfer verb's object is an interaction target;
        # a movement verb's grounded NP is a destination, not something to
        # examine (so "move deeper through the passage" must not backfill an
        # obelisk as the interaction target).
        interaction_verbs = latn_resolver._INTERACTION_VERBS | latn_resolver._TRANSFER_VERBS
        for action in latn_resolver.resolve_actions(
            intent_text or "", lexicon=lexicon, adapter=adapter,
        ):
            if action.item is not None and action.verb in interaction_verbs:
                return action.item.label or action.item.id
    from engine.verb_resolver import infer_interaction_target as _shallow
    return _shallow(intent_text or "", items, character_zone)


def resolve_recipient(
    intent_text: str,
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
    scene_geometry=None,
) -> Optional[str]:
    """LATN recipient (a character id) for a transfer like "give X to Y", or
    None when nothing grounds — so the caller falls back to its own shallow
    recipient resolution. Recipients are grounded by vector similarity over the
    character property dims (race/class/role) plus name/handle match — stronger
    than token overlap."""
    if items and characters:
        from engine import latn_resolver
        lexicon, adapter = build_context(
            items, characters, character_zone or "", scene_geometry,
        )
        for action in latn_resolver.resolve_actions(
            intent_text or "", lexicon=lexicon, adapter=adapter,
        ):
            if action.recipient_id is not None:
                return action.recipient_id
    return None


def infer_movement_target(
    intent_text: str,
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
    scene_geometry=None,
):
    """LATN-first movement destination as an (x, y, z) tuple, or None. Grounds
    "move to the <item>" to a scene item's position so a feature/landmark named
    in free text becomes an actual destination. Returns None when the intent
    isn't movement or nothing grounds — so the caller falls back to its shallow
    zone/landmark geometry inference.

    Unlike interaction grounding, the destination is NOT zone-filtered: you move
    *toward* a thing you can see across a threshold (the sarcophagus in the next
    chamber), which lives in another zone. Perception already limits what the
    player can name to what they perceive, so this stays "move to what you can
    see"; a strict can-see gate is the 2b perception-fed adapter's job."""
    if items and characters:
        from engine import latn_resolver
        # actor_zone="" -> no zone filter, so cross-zone destinations ground.
        lexicon, adapter = build_context(items, characters, "", scene_geometry)
        item = latn_resolver.resolve_movement_target(
            intent_text or "", lexicon=lexicon, adapter=adapter,
        )
        pos = getattr(item, "position", None) if item is not None else None
        if pos is not None:
            return (pos.x, pos.y, pos.z)
    return None


def infer_movement_distance(
    intent_text: str,
    items: Optional[dict],
    characters: Optional[dict],
    character_zone: Optional[str],
    scene_geometry=None,
) -> Optional[float]:
    """LATN-first explicit movement distance in feet, or None.

    Uses LATN layer output to read quantities such as "ten feet" in movement
    intents. Returns None when LATN cannot derive a movement+distance pair.
    """
    from engine import latn_resolver

    # Distance extraction is lexical/structural and does not require grounded
    # entities, so build context even when items/characters are empty.
    _items = items or {}
    _characters = characters or {}
    lexicon, adapter = build_context(
        _items, _characters, character_zone or "", scene_geometry,
    )
    return latn_resolver.resolve_movement_distance(
        intent_text or "", lexicon=lexicon, adapter=adapter,
    )
