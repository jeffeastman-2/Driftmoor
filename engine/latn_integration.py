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

import re
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
    # Possessions remain groundable after a scene transition even when they
    # were created at runtime and therefore have no row in the destination
    # scene's CONTENTS. Keep scene items authoritative on id collisions.
    context_items = dict(items or {})
    for cs in char_list:
        for thing in (getattr(cs, "pack", None) or []):
            iid = getattr(thing, "id", "")
            if iid:
                context_items.setdefault(iid, thing)
        for thing in (getattr(cs, "things", None) or []):
            iid = getattr(thing, "id", "")
            if iid:
                context_items.setdefault(iid, thing)
    item_list = list(context_items.values())
    zones = list(getattr(scene_geometry, "zones", {}) or {}) if scene_geometry is not None else []
    landmarks = list(getattr(scene_geometry, "landmarks", {}) or {}) if scene_geometry is not None else []
    venue_list = list(venues or [])
    catalog_list = list(catalog or [])
    lexicon = build_driftmoor_lexicon(
        char_list, item_list, zones=zones, landmarks=landmarks, venues=venue_list,
        catalog=catalog_list,
    )
    adapter = DriftmoorSceneAdapter(
        items=context_items, characters=characters, actor_zone=actor_zone,
        venues=venue_list, catalog=catalog_list,
        landmarks=(getattr(scene_geometry, "landmarks", {}) or {})
        if scene_geometry is not None else {})
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
        # Preserve an explicit buy/sell whose object is ambiguous or unmatched
        # so the commerce handler can respond honestly ("which fish?").  The
        # resolver itself still returns None for non-commerce desires such as
        # "I want to leave", so this does not weaken the object gate.
        return (verb, None)
    if verb == "buy":
        return ("buy", getattr(ent, "entry", None))
    return ("sell", getattr(ent, "item", None))


def resolve_query(intent_text, items, characters, actor_zone, catalog,
                  scene_geometry=None):
    """Answer a player's question from the world model, or None.

    LATN parses the interrogative and grounds its focus (``resolve_query_action``
    over the parallel SQ pass); this host glue turns the grounded focus into an
    answer string. Today it routes the SHOP CATALOG family -- "are your bolts for
    sale?", "what do you have for sale?" -- so shop questions are answered by the
    engine instead of the DM/LLM, no '?' or wh-word required. Questions that
    aren't about the catalog (where is X, how much gold) return None, so the
    caller falls back (annotated DM) until those sources are routed too.
    """
    from engine import latn_resolver
    from models.currency import format_coins

    query_text = (intent_text or "").strip()
    if len(query_text) >= 2 and query_text[0] in {'"', '“'} and query_text[-1] in {'"', '”'}:
        query_text = query_text[1:-1].strip()
    query_text = query_text.rstrip("?!.").strip().lower()

    lexicon, adapter = build_context(
        items or {}, characters or {}, actor_zone or "", scene_geometry,
        catalog=catalog)
    rq = latn_resolver.resolve_query_action(
        query_text, lexicon=lexicon, adapter=adapter)
    if rq is None:
        # Defensive punctuation-independent shop-question fallback.  Some LATN
        # grammar paths can reduce "what are you selling" as a statement when
        # there is no terminal question mark.  The atomic vectors still carry
        # the wh/sell semantics, so recognize that shape without requiring '?'.
        from engine.latn import (
            LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
            use_sp_policy, PermissiveSPPolicy,
        )
        executor = LATNLayerExecutor(adapter)
        with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
                use_sp_policy(PermissiveSPPolicy()):
            atoms = executor.execute_layer1(query_text)
        tokens = list(atoms.hypotheses[0].tokens) if atoms.hypotheses else []
        surfaces = {
            str(getattr(t, "word", "") or "").strip().lower()
            for t in tokens
        }
        asks_inventory = "what" in surfaces or bool(
            surfaces & {"anything", "something", "goods", "wares"}
        )
        if not (asks_inventory
                and any(latn_resolver._isa(t, "sell") or latn_resolver._isa(t, "buy")
                        for t in tokens)):
            return None
        if not catalog:
            return "Nothing is listed for sale here."
        listed = ", ".join(
            f"{e.name} ({format_coins(e.listed_price_cp)})" for e in catalog)
        return f"For sale: {listed}."

    # The focus names a specific for-sale good ("are your bolts for sale?") ->
    # confirm it and quote the listed price. Only when the focus actually NAMES
    # a thing: a subject pronoun ("what can I buy", "what do you have") has no
    # head noun and must not be treated as a good -- otherwise "I"/"you" grounds
    # loosely to some catalog entry and we'd answer about the wrong item instead
    # of listing the shop.
    focus_names_a_thing = bool((getattr(rq.focus_np, "noun", "") or "").strip())
    catalog_focus = [
        e for _s, e in rq.focus_entities
        if getattr(e, "kind", None) == "catalog"
    ]
    if catalog_focus and focus_names_a_thing:
        entry = getattr(catalog_focus[0], "entry", None)
        name = getattr(entry, "name", None) or getattr(catalog_focus[0], "name", "that")
        price = format_coins(getattr(entry, "listed_price_cp", None))
        return f"Yes — {name} is for sale at {price}."

    # ``how much is the tonic`` currently yields an SQ with ``wh_word=how``
    # but no focus NP.  Keep the answer authoritative by matching the remaining
    # content words against the actual catalog, accepting only one best entry.
    if rq.wh_word == "how" and re.search(r"\bmuch\b", query_text):
        query_words = set(re.findall(r"[a-z0-9]+", query_text))
        ranked = []
        for entry in catalog or []:
            name_words = set(re.findall(r"[a-z0-9]+", entry.name.lower()))
            score = len(query_words & name_words)
            if score:
                ranked.append((score, entry))
        if ranked:
            top = max(score for score, _entry in ranked)
            winners = [entry for score, entry in ranked if score == top]
            if len(winners) == 1:
                entry = winners[0]
                return (
                    f"Yes — {entry.name} is for sale at "
                    f"{format_coins(entry.listed_price_cp)}."
                )

    # A "what (do you have/sell)" with a shop present -> list the catalog. The
    # passed-in catalog is already the present shopkeeper's goods (empty when no
    # keeper is here), so a non-empty list means a shop is open.
    entries = list(catalog or [])
    if entries and rq.wh_word == "what":
        listed = ", ".join(
            f"{e.name} ({format_coins(e.listed_price_cp)})" for e in entries)
        return f"For sale: {listed}."

    # A recognized catalog question remains engine-answerable when the catalog
    # is empty.  Falling through would misleadingly ask the DM model to invent
    # stock (or produce silence when no model is configured).
    if not entries and rq.wh_word == "what" and re.search(
        r"\b(?:sell|sale|buy)\b", query_text
    ):
        return "Nothing is listed for sale here."

    # Yes/no inventory phrasing ("do you have anything to sell?") is the same
    # catalog request, not an invitation for the DM to invent merchandise.
    if not entries and re.search(
        r"\b(?:do|have|is|are)\b.*\b(?:anything|something|goods?|wares?)\b"
        r".*\b(?:sell|sale|buy)\b",
        query_text,
    ):
        return "Nothing is listed for sale here."

    return None


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


def resolve_venue_plan(intent_text, characters, actor_zone, venues,
                       scene_geometry=None):
    """Ordered LATN venue clauses, retaining their grounded scene names."""
    from engine import latn_resolver
    lexicon, adapter = build_context(
        {}, characters or {}, actor_zone or "", scene_geometry, venues=venues)
    plan = latn_resolver.resolve_venue_plan(
        intent_text or "", lexicon=lexicon, adapter=adapter)
    return [
        (kind, getattr(entity, "scene_name", None))
        for kind, entity in plan
    ]


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


def infer_movement_waypoints(
    intent_text: str,
    scene_geometry=None,
) -> Optional[list[tuple[float, float, str]]]:
    """Explicit literal-coordinate waypoints from a movement intent, as
    ``(x, y, zone)`` tuples in the order written, or None.

    Grounds via LATN's vector-NP/conjunction machinery (a bracket literal is
    its own NP; a comma-joined run is a coordinated NP like any other), so a
    single ``[x,y]`` and a multi-point ``[x1,y1], [x2,y2], [x3,y3]`` route
    resolve through the same call — no separate multi-coordinate regex.
    Zone is looked up per waypoint when geometry is available. Items/
    characters aren't needed (a literal never grounds against the scene), so
    this builds a minimal LATN context directly rather than going through
    ``build_context``.
    """
    from engine import latn_resolver
    lexicon, adapter = build_context({}, {}, "", scene_geometry)
    waypoints = latn_resolver.resolve_movement_waypoints(
        intent_text or "", lexicon=lexicon, adapter=adapter,
    )
    if not waypoints:
        return None
    out = []
    for x, y, *_rest in waypoints:
        zone = ""
        if scene_geometry is not None:
            from models.space_time import Position
            zone = (scene_geometry.zone_at(Position(x, y)) or "").upper()
        out.append((x, y, zone))
    return out


def infer_literal_destination(
    intent_text: str,
    scene_geometry=None,
) -> Optional[tuple[float, float, str]]:
    """The first literal coordinate named anywhere in the intent, as an
    ``(x, y, zone)`` tuple, or None — for callers (teleport spell-targeting)
    where the verb naming the destination isn't fixed the way "move"/"dash"
    is for ordinary movement, so ``infer_movement_waypoints``'s verb gate
    doesn't apply. Only ever a single point (a spell lands on one point).
    """
    from engine import latn_resolver
    lexicon, adapter = build_context({}, {}, "", scene_geometry)
    vector = latn_resolver.resolve_literal_destination(
        intent_text or "", lexicon=lexicon, adapter=adapter,
    )
    if vector is None:
        return None
    x, y, *_rest = vector
    zone = ""
    if scene_geometry is not None:
        from models.space_time import Position
        zone = (scene_geometry.zone_at(Position(x, y)) or "").upper()
    return (x, y, zone)


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
