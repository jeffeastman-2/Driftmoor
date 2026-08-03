"""LATN-backed intent resolution (phase 2a, step 4).

Parses a character's free-text intent with the LATN parser and dispatches on
the *parsed structure* instead of keyword/substring matching:

* canonical verb  <- the verb phrase's intent dimension (vp.vector.isa(...))
* object          <- the VP's noun phrase, grounded via the SceneAdapter
* recipient       <- the "to"-PP's noun phrase (a grounded character), for
                     transfer verbs (give/take/drop)

Conjunctive intents ("pick up the mace and hand it to Amara") yield multiple
ResolvedActions (Engraf flattens the verb-phrase conjunction at layer 4).

The shallow ``engine.verb_resolver`` stays the FALLBACK: when the parse fails
or grounds nothing, ``resolve_item_interaction`` defers to it, so LATN can only
improve resolution, never lose it. Ambiguity is handled here (not in the
adapter): a top-score tie in grounding refuses to guess (today's behavior); a
human front end (2b) can instead disambiguate off the same ranked list.

Parses are wrapped in ``use_lexicon`` + ``use_vp_policy(PermissiveVPPolicy())``
so the Driftmoor lexicon is active and non-CAD verbs survive Layer-4 grounding.
"""

from __future__ import annotations

from dataclasses import dataclass
import functools
import re
from typing import List, Optional, Tuple

from models.item import Interaction, Item
from engine.latn_dimensions import VERB_DIMS
from engine.verb_resolver import _find_by_verb, _pick_by_condition, authored_transfer_response

# Object-interaction verbs resolve to an authored Interaction; transfer verbs
# change possession (and may carry an authored flavor response).
_INTERACTION_VERBS = {"examine", "search", "read", "open", "press"}
_TRANSFER_VERBS = {"take", "drop", "give"}
# Locomotion verbs whose object/PP names a destination, not a thing to act on.
_MOVEMENT_VERBS = {"move", "dash"}

_LATN_NUM_WORDS: dict[str, float] = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "eleven": 11.0,
    "twelve": 12.0,
    "thirteen": 13.0,
    "fourteen": 14.0,
    "fifteen": 15.0,
    "sixteen": 16.0,
    "seventeen": 17.0,
    "eighteen": 18.0,
    "nineteen": 19.0,
    "twenty": 20.0,
    "thirty": 30.0,
    "forty": 40.0,
    "fifty": 50.0,
    "sixty": 60.0,
    "seventy": 70.0,
    "eighty": 80.0,
    "ninety": 90.0,
    "hundred": 100.0,
}

_TIE_MARGIN = 1e-9

# The affordance a verb *attends to* when grounding its object (the QK step:
# verbs attend affordances). Used as a SOFT tiebreak in `_resolve_object` —
# when several candidates ground and only some afford the verb, prefer those;
# never eliminate a sole candidate, so this can only sharpen disambiguation,
# never lose a grounding. Adjective->effect attention is a later refinement.
def _verb_affordances() -> dict:
    from models.thing import HOLDABLE, PRESSABLE, READABLE
    return {"read": READABLE, "press": PRESSABLE, "take": HOLDABLE, "drop": HOLDABLE}


@dataclass
class ResolvedAction:
    """One parsed, grounded action from an intent."""
    verb: str                                  # canonical verb dim (identity/name)
    item: Optional[Item] = None
    interaction: Optional[Interaction] = None
    recipient_id: Optional[str] = None         # character id (transfer verbs)
    ambiguous: bool = False                     # grounding tie -> refused to guess
    vector: object = None                       # the action's LATN vector, for isa tests


def _unique_winner(pairs: List[Tuple[float, object]]):
    """Top entity unless the top two are tied (then None — refuse to guess)."""
    if not pairs:
        return None
    pairs = sorted(pairs, key=lambda p: p[0], reverse=True)
    if len(pairs) == 1 or (pairs[0][0] - pairs[1][0]) > _TIE_MARGIN:
        return pairs[0][1]
    return None


def _canonical_verb(vp) -> Optional[str]:
    vec = getattr(vp, "vector", None)
    if vec is None:
        return None
    for dim in VERB_DIMS:
        if vec.isa(dim):
            return dim
    return None


def _vec_isa(vec, *dims) -> bool:
    """True if the LATN vector carries any of ``dims``. This is the vector-space
    membership test that replaces string-matching a collapsed canonical verb — a
    multi-dimension verb (e.g. "enter" = move+enter) is caught for every
    dimension it holds, not just the first one _canonical_verb would name."""
    return vec is not None and any(vec.isa(d) for d in dims)


def _vp_isa(vp, *dims) -> bool:
    """`_vec_isa` on a verb phrase's action vector."""
    return _vec_isa(getattr(vp, "vector", None), *dims)


def _entities_of_kind(ranked, kind):
    return [(s, e) for s, e in ranked if getattr(e, "kind", None) == kind]


def _prefer_affordance(items, verb):
    """Soft affordance tiebreak: when ``verb`` attends to an affordance and SOME
    (but not all) grounded candidates afford it, keep only those. Never empties a
    non-empty list, so a sole grounding is untouched — this only breaks ties in
    favour of the candidate that actually affords the verb ("press the lever",
    not "press the mural")."""
    aff = _verb_affordances().get(verb or "")
    if aff is None or len(items) < 2:
        return items
    matching = [
        (s, e) for s, e in items
        if aff in (getattr(getattr(e, "item", None), "affordances", None) or set())
    ]
    return matching or items


def _resolve_object(vp, adapter, verb=None) -> Tuple[Optional[Item], bool]:
    """Ground the VP's object NP to an Item. Returns (item, ambiguous). When a
    ``verb`` is given, its attended affordance breaks ties among candidates."""
    np = getattr(vp, "noun_phrase", None)
    if np is None:
        return None, False
    items = _entities_of_kind(adapter.resolve_noun_phrase(np), "item")
    items = _prefer_affordance(items, verb)
    winner = _unique_winner(items)
    if winner is not None:
        return winner.item, False
    return None, len(items) > 1  # >1 with no winner == a tie we refused


def _resolve_recipient(vp, adapter) -> Optional[str]:
    """Ground the 'to'-PP's NP to a recipient character id (transfer verbs)."""
    for pp in getattr(vp, "prepositions", None) or []:
        is_to = pp.preposition == "to" or (pp.vector and pp.vector.isa("directional_target"))
        if not is_to or getattr(pp, "noun_phrase", None) is None:
            continue
        chars = _entities_of_kind(adapter.resolve_noun_phrase(pp.noun_phrase), "character")
        winner = _unique_winner(chars)
        if winner is not None:
            return winner.entity_id
    return None


def _interaction_for(item: Item, verb: str) -> Optional[Interaction]:
    """Authored Interaction for verb on item, mirroring the shallow resolver's
    examine fallback (flavor-only items still get a one-time examine response)."""
    matches = _find_by_verb(item, verb)
    if not matches and verb != "examine":
        matches = _find_by_verb(item, "examine")
    if matches:
        return _pick_by_condition(matches, item.state)
    if verb == "examine":
        text = (item.description or "").strip() or (
            f"You examine the {item.label or item.id}, but find nothing further of note."
        )
        return Interaction(verb="examine", aliases=[], condition="", response=text)
    return None


def _default_action_lexicon():
    """Scene-independent Driftmoor lexicon for verb detection. Built fresh per
    call (cheap) rather than cached: the action dims are scene-independent, but a
    module-level cache would capture whatever global lexicon/dimension state
    happened to be active at first build, coupling otherwise-independent callers.
    Registering the RPG dims here is idempotent."""
    from engine.latn_lexicon import build_driftmoor_lexicon
    return build_driftmoor_lexicon([], [])


def intent_has_action(intent_text: str, *dims: str, lexicon=None) -> bool:
    """True when a verb in the intent carries one of the given action dims.

    A lightweight LATN check that replaces regex keyword detection: the verb
    vocabulary lives in the lexicon (``isa`` a dim), not a hand-maintained
    pattern. Tokenizes at layer 1 -- atomic, but the tokenizer still matches a
    multi-word verb key ("swing at") -- and tests each token; no scene grounding
    needed, so callers that only have the text can use it. Pass ``lexicon`` to
    reuse a scene lexicon and skip the per-call build."""
    if not (intent_text or "").strip() or not dims:
        return False
    from engine.latn import LATNLayerExecutor, use_lexicon
    lex = lexicon if lexicon is not None else _default_action_lexicon()
    executor = LATNLayerExecutor()
    with use_lexicon(lex):
        result = executor.execute_layer1(intent_text)
    tokens = list(result.hypotheses[0].tokens) if result.hypotheses else []
    return any(any(_isa(t, d) for d in dims) for t in tokens)


def intent_action_dims(intent_text: str, dims, lexicon=None) -> set:
    """The subset of ``dims`` that a verb in the intent carries (one tokenize).

    Same LATN-first idea as ``intent_has_action`` but returns which dims are
    present, so a caller testing several verb signals (e.g. classify_verb's
    draw/hold/sheathe/wear/remove) tokenizes once instead of per dim."""
    dims = tuple(dims)
    if not (intent_text or "").strip() or not dims:
        return set()
    from engine.latn import LATNLayerExecutor, use_lexicon
    lex = lexicon if lexicon is not None else _default_action_lexicon()
    executor = LATNLayerExecutor()
    with use_lexicon(lex):
        result = executor.execute_layer1(intent_text)
    tokens = list(result.hypotheses[0].tokens) if result.hypotheses else []
    return {d for d in dims if any(_isa(t, d) for t in tokens)}


def resolve_actions(intent_text: str, *, lexicon, adapter) -> List[ResolvedAction]:
    """Parse ``intent_text`` and return the grounded actions it describes.

    The new, list-returning API (one entry per verb phrase; conjunctions yield
    several). Verbs outside the object-interaction / transfer scope (attack,
    cast, move, ...) are still returned with their canonical verb so a caller
    can route them, but carry no item/interaction here.
    """
    from engine.latn import (
        LATNLayerExecutor,
        use_lexicon,
        use_vp_policy,
        PermissiveVPPolicy,
        use_sp_policy,
        PermissiveSPPolicy,
    )

    executor = LATNLayerExecutor(adapter)
    # Parse at Layer 5 (full sentences) so a human's "I give the mace to Amara"
    # yields an SP with a subject + a complete predicate VP, not just a loose
    # VP fragment. PermissiveSPPolicy keeps any hypothesis that formed an SP
    # (the SP analog of PermissiveVPPolicy) so L5 recall matches L4 while adding
    # sentence structure. The subject (sp.subject) is the actor; we ignore it
    # for now — the acting character is known from turn context — and revisit
    # when party-directed commands ("Thorgrim, take the torch") need it.
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")

    # Each sentence phrase's predicate is a full VP (a conjunction predicate
    # flattens to several). PP-attachment ambiguity yields variant SPs for the
    # same clause — e.g. "I give the mace to Amara" produces one SP with the
    # "to"-PP on the subject and one with it on the predicate — so we dedup on
    # (verb, object) and PREFER the variant that grounded a recipient.
    #
    # TODO(pronoun-anaphora): cross-clause pronouns — "pick up the mace AND
    # give IT to Amara". "it" is grounded eagerly at L2 against parse-time
    # recency, which can't see an antecedent created/referenced by an earlier
    # clause of the same sentence. This is a LATN-CORE problem, not ours:
    # native Engraf has it too ("create a box and move it to [1,2,3]" yields
    # 0 VPs — "it" doesn't ground, so the move VP fails policy and the parse
    # is dropped). Agreed model: a pronoun is ALWAYS a deferred *grounding
    # promise*, forced by the executor against the recency at force-time
    # (seeded with scene/turn referents, extended per clause). Root fix lives
    # in Engraf (resolve_pronoun / L2). Until then a pronoun object yields
    # item=None.
    merged: "dict[tuple, ResolvedAction]" = {}
    for sp in (getattr(result, "sentence_phrases", None) or []):
        for vp in _predicate_vps(sp):
            verb = _canonical_verb(vp)          # canonical NAME (for lookups/keys)
            if verb is None:
                continue
            item, ambiguous = _resolve_object(vp, adapter, verb)
            recipient = _resolve_recipient(vp, adapter) if _vp_isa(vp, *_TRANSFER_VERBS) else None
            key = (verb, item.id if item is not None else None)
            prev = merged.get(key)
            if prev is None:
                merged[key] = ResolvedAction(
                    verb, item, None, recipient, ambiguous, getattr(vp, "vector", None))
            else:
                # Same clause seen via another PP-attachment variant: keep the
                # recipient if this variant found one, and don't let a variant
                # without grounding override a grounded one.
                if prev.recipient_id is None and recipient is not None:
                    prev.recipient_id = recipient
                prev.ambiguous = prev.ambiguous and ambiguous

    actions: List[ResolvedAction] = []
    for action in merged.values():
        if action.item is not None and _vec_isa(action.vector, *_INTERACTION_VERBS):
            action.interaction = _interaction_for(action.item, action.verb)
        elif action.item is not None and _vec_isa(action.vector, *_TRANSFER_VERBS):
            resp = authored_transfer_response(action.item, action.verb)
            if resp:
                action.interaction = Interaction(
                    verb=action.verb, aliases=[], condition="", response=resp)
        actions.append(action)
    return actions


def _predicate_vps(sp):
    """The predicate VP(s) of a sentence phrase. A conjunction predicate
    ("take the torch and light it") flattens to several; a plain predicate is
    a single VP. Non-VP predicates yield nothing."""
    from latn.pos.conjunction_phrase import ConjunctionPhrase
    from latn.pos.verb_phrase import VerbPhrase

    pred = getattr(sp, "predicate", None)
    if isinstance(pred, ConjunctionPhrase):
        return [p for p in pred.phrases if isinstance(p, VerbPhrase)]
    if isinstance(pred, VerbPhrase):
        return [pred]
    return []


def _destination_np(vp):
    """The NP naming a movement destination: the directional ('to') PP's object
    if present, else the verb phrase's direct object. ("move to the X" puts the
    destination in the PP; "approach the X" may put it directly.)"""
    for pp in getattr(vp, "prepositions", None) or []:
        is_to = pp.preposition == "to" or (pp.vector and pp.vector.isa("directional_target"))
        if is_to and getattr(pp, "noun_phrase", None) is not None:
            return pp.noun_phrase
    return getattr(vp, "noun_phrase", None)


def resolve_movement_target(intent_text: str, *, lexicon, adapter) -> Optional[Item]:
    """Ground a movement intent's destination ("move to the tally scratches")
    to a scene item and return it; the caller maps its position to a movement
    target. Returns None when the intent isn't a movement verb or the
    destination grounds to no unique item. (Zone/landmark destinations are left
    to the caller's shallow geometry inference.)"""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
    for sp in (getattr(result, "sentence_phrases", None) or []):
        for vp in _predicate_vps(sp):
            if not _vp_isa(vp, *_MOVEMENT_VERBS):
                continue
            np = _destination_np(vp)
            if np is None:
                continue
            items = _entities_of_kind(adapter.resolve_noun_phrase(np), "item")
            winner = _unique_winner(items)
            if winner is not None:
                return winner.item
    return None


def resolve_venue_action(intent_text: str, *, lexicon, adapter):
    """Detect a venue-crossing intent and ground its target.

    Returns ``("enter", venue_entity_or_None)`` when a predicate verb ``isa
    "enter"`` (the threshold-crossing rider on movement), grounding its object /
    destination NP to a unique venue entity; ``("leave", None)`` when a verb
    ``isa "leave"``; ``None`` otherwise (plain movement like "go to the tavern"
    carries neither rider, so it walks to the door without crossing in). The
    ``None`` venue on an enter means the name grounded to no unique venue — the
    caller declines rather than guessing."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
    for sp in (getattr(result, "sentence_phrases", None) or []):
        for vp in _predicate_vps(sp):
            vec = getattr(vp, "vector", None)
            if vec is None:
                continue
            if vec.isa("leave"):
                return ("leave", None)
            if vec.isa("enter"):
                np = _destination_np(vp)
                if np is None:
                    return ("enter", None)
                venues = _entities_of_kind(adapter.resolve_noun_phrase(np), "venue")
                return ("enter", _unique_winner(venues))
    return None


def resolve_commerce_action(intent_text: str, *, lexicon, adapter):
    """Detect a buy/sell intent and ground its object.

    Returns ``("buy", catalog_entity_or_None)`` when a predicate verb is ``buy``,
    grounding its object NP to a unique shop catalog entry; ``("sell",
    item_entity_or_None)`` when the verb is ``sell``, grounding to a unique scene
    item; ``None`` otherwise. A ``None`` entity means the name grounded to nothing
    unique — the caller declines rather than guessing which good."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
    for sp in (getattr(result, "sentence_phrases", None) or []):
        for vp in _predicate_vps(sp):
            vec = getattr(vp, "vector", None)
            if vec is None:
                continue
            if vec.isa("sell"):
                np = _destination_np(vp)
                if np is None:
                    return ("sell", None)
                items = _entities_of_kind(adapter.resolve_noun_phrase(np), "item")
                return ("sell", _unique_winner(items))
            # A "buy" verb, or a "take" (grab / pick up / pocket …) whose object
            # is a shop good, is a purchase — so loose phrasing like "I'll take
            # the mace" in a shop routes to commerce instead of the LLM. Test the
            # vector's action dimensions directly (isa), not a collapsed verb
            # string, so a multi-dimension verb still registers. A take of a
            # non-catalog thing is left to the normal take/steal path (None).
            if (vec.isa("buy") or vec.isa("take") or vec.isa("eat")
                    or vec.isa("drink") or vec.isa("consume")):
                np = _destination_np(vp)
                if np is None:
                    return ("buy", None) if vec.isa("buy") else None
                if vec.isa("eat") or vec.isa("drink") or vec.isa("consume"):
                    # If the player already possesses a matching consumable,
                    # this is use, not another shop order.  Possessions and the
                    # current catalog share the adapter, so explicitly give the
                    # former routing priority.
                    owned = _entities_of_kind(
                        adapter.resolve_noun_phrase(np), "item")
                    if owned:
                        return None
                cat = _entities_of_kind(adapter.resolve_noun_phrase(np), "catalog")
                if cat:
                    return ("buy", _unique_winner(cat))
                # No catalog match at all is not commerce ("looking for the way
                # out").  A non-empty but tied catalog list above deliberately
                # returns ("buy", None), allowing the host to ask which good.
                return None
    return None


@dataclass
class ResolvedQuery:
    """A grounded interrogative: what was asked and what its focus refers to.

    LATN says the *shape* of the question (the wh lexeme or a yes/no flag, the
    queried focus NP and its grounded entities, and any prepositional relation);
    the host decides how to answer from its world model -- the same
    grounding-vs-answering split the action resolvers use."""

    wh_word: Optional[str]
    is_yesno: bool
    focus_np: object
    focus_entities: list        # ranked (score, entity) pairs for the focus NP
    prepositional_phrases: list
    predicate: object = None


@dataclass
class ResolvedStateQuery:
    """An engine-owned question classified by LATN semantics."""

    kind: str
    query: ResolvedQuery
    focus_entity: object = None


@dataclass
class ResolvedWorldQuery:
    """A spatial/perception question with an optional grounded world focus."""

    kind: str
    focus_entity: object = None


def resolve_query_action(intent_text: str, *, lexicon, adapter):
    """Detect an interrogative (the parallel SQ pass) and ground its focus.

    Returns a ``ResolvedQuery`` when the line parses as a question -- grounding
    the queried focus NP through the adapter -- or ``None`` when it isn't a
    question (SQ only fires on a wh-word or an inverted to-be, so statements and
    commands fall through here to the normal action path)."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
    questions = getattr(result, "question_phrases", None) or []
    if not questions:
        return None
    q = questions[0]
    focus = getattr(q, "focus", None)
    grounded = adapter.resolve_noun_phrase(focus) if focus is not None else []
    return ResolvedQuery(
        wh_word=getattr(q, "wh_word", None),
        is_yesno=getattr(q, "is_yesno", False),
        focus_np=focus,
        focus_entities=list(grounded or []),
        prepositional_phrases=list(getattr(q, "prepositional_phrases", None) or []),
        predicate=getattr(q, "predicate", None),
    )


def resolve_state_query(intent_text: str, *, lexicon, adapter) -> Optional[ResolvedStateQuery]:
    """Classify identity/location/time/place-definition questions semantically."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
        atoms = executor.execute_layer1(intent_text or "")
    questions = getattr(result, "question_phrases", None) or []
    if not questions:
        return None
    q = questions[0]
    focus = getattr(q, "focus", None)
    grounded = list(adapter.resolve_noun_phrase(focus) or []) if focus is not None else []
    resolved = ResolvedQuery(
        wh_word=getattr(q, "wh_word", None),
        is_yesno=getattr(q, "is_yesno", False),
        focus_np=focus,
        focus_entities=grounded,
        prepositional_phrases=list(getattr(q, "prepositional_phrases", None) or []),
        predicate=getattr(q, "predicate", None),
    )
    tokens = list(atoms.hypotheses[0].tokens) if atoms.hypotheses else []
    first_person = any(_isa(token, "first_person") for token in tokens)
    perception = any(_isa(token, "perceive") for token in tokens)
    local_presence = any(_isa(token, "local_presence") for token in tokens)
    knows_person = any(_isa(token, "know_person") for token in tokens)
    if resolved.wh_word == "who" and (perception or local_presence):
        return ResolvedStateQuery("visible_people", resolved)
    if resolved.wh_word == "who" and first_person:
        return ResolvedStateQuery("identity", resolved)
    if resolved.wh_word == "who" and focus is not None:
        people = _entities_of_kind(grounded, "character")
        person = _unique_winner(people)
        if person is not None:
            return ResolvedStateQuery("person_identity", resolved, person)
        # A grammatical WHO question with a referential focus is still
        # engine-owned when the known-person registry cannot ground it.
        return ResolvedStateQuery("unknown_person", resolved)
    if resolved.wh_word == "where" and first_person:
        return ResolvedStateQuery("location", resolved)
    if resolved.wh_word == "what" and any(_isa(token, "query_time") for token in tokens):
        return ResolvedStateQuery("time", resolved)
    if resolved.wh_word == "what":
        people = _entities_of_kind(grounded, "character")
        person = _unique_winner(people)
        if person is not None:
            return ResolvedStateQuery("person_definition", resolved, person)
        venues = _entities_of_kind(grounded, "venue")
        venue = _unique_winner(venues)
        if venue is not None:
            return ResolvedStateQuery("place_definition", resolved, venue)
    if resolved.is_yesno and knows_person and focus is not None:
        people = _entities_of_kind(grounded, "character")
        person = _unique_winner(people)
        return ResolvedStateQuery(
            "acquaintance_true" if person is not None else "acquaintance_false",
            resolved, person,
        )
    if resolved.is_yesno and focus is not None:
        people = _entities_of_kind(grounded, "character")
        person = _unique_winner(people)
        complements = list(
            getattr(resolved.predicate, "complement_phrases", None) or [])
        if person is not None and complements:
            wanted = getattr(complements[0], "vector", None)
            actual = getattr(person, "vector", None)
            if wanted is not None and actual is not None:
                matches = wanted.semantic_similarity(actual) > 0.0
                return ResolvedStateQuery(
                    "person_property_true" if matches else "person_property_false",
                    resolved, person,
                )
    return None


def resolve_world_query(intent_text: str, *, lexicon, adapter) -> Optional[ResolvedWorldQuery]:
    """Resolve perception, geography, and existence without surface patterns."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        layer5 = executor.execute_layer5(intent_text or "")
        layer1 = executor.execute_layer1(intent_text or "")
    tokens = list(layer1.hypotheses[0].tokens) if layer1.hypotheses else []
    questions = getattr(layer5, "question_phrases", None) or []
    if not questions:
        return None

    q = questions[0]
    grounded = list(adapter.resolve_noun_phrase(q.focus) or []) if q.focus is not None else []
    world_grounded = [
        pair for pair in grounded
        if getattr(pair[1], "kind", "") in {"landmark", "venue"}
    ]
    focus = _unique_winner(world_grounded)
    wh_word = getattr(q, "wh_word", None)
    yesno = bool(getattr(q, "is_yesno", False))
    perception = any(_isa(token, "perceive") for token in tokens)
    first_person = any(_isa(token, "first_person") for token in tokens)
    if perception and first_person:
        return ResolvedWorldQuery("perception_target" if focus else "perception_list", focus)
    if perception and yesno and focus is not None:
        return ResolvedWorldQuery("perception_target", focus)
    if wh_word == "where" and focus is not None:
        return ResolvedWorldQuery("geography", focus)
    if yesno and focus is not None:
        return ResolvedWorldQuery("existence", focus)
    return None


def resolve_self_query(intent_text: str, *, lexicon, adapter) -> Optional[str]:
    """Classify a first-person question about the speaker's own state.

    Returns ``"wealth"`` or ``"possessions"`` only when the question carries
    actual possession semantics. A first-person perception question such as
    "what do I see?" returns None and continues to the external-view path."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
        # Atomic (per-word) tokens carry the first_person/currency dims before
        # NP/VP composition folds them into a phrase vector.
        atoms = executor.execute_layer1(intent_text or "")
    if not (getattr(result, "question_phrases", None) or []):
        return None  # not a question
    tokens = list(atoms.hypotheses[0].tokens) if atoms.hypotheses else []
    if not any(_isa(t, "first_person") for t in tokens):
        return None  # about someone/something else, not the speaker
    # "Can I get a shave?" has possession-like GET semantics, but when its SQ
    # focus grounds to a catalog entity it is a commerce query, not a request
    # to enumerate the actor's current inventory.
    question = (getattr(result, "question_phrases", None) or [None])[0]
    focus = getattr(question, "focus", None)
    grounded_focus = adapter.resolve_noun_phrase(focus) if focus is not None else []
    if (_entities_of_kind(grounded_focus, "catalog")
            and any(_isa(t, "hold") or _isa(t, "take") or _isa(t, "buy")
                    for t in tokens)):
        return None
    # A first-person purchase question ("what can I buy") is about the shop's
    # stock, not the speaker. Likewise "what can you sell me" asks what the
    # addressed merchant offers; only "what can I sell" asks about my goods.
    # Defer the former shapes to the catalog resolver.
    if (any(_isa(t, "buy") for t in tokens)
            and not any(_isa(t, "sell") for t in tokens)):
        return None
    if (any(_isa(t, "sell") for t in tokens)
            and any(str(getattr(t, "word", "")).lower() in {"you", "your"}
                    for t in tokens)):
        return None
    possession = any(
        _isa(t, "possess") or _isa(t, "hold") or _isa(t, "sell")
        for t in tokens
    )
    if not possession:
        return None
    return "wealth" if any(_isa(t, "currency") for t in tokens) else "possessions"


def resolve_perception_query(intent_text: str, *, lexicon, adapter) -> bool:
    """True for a first-person external-view question such as "what do I see?"."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")
        atoms = executor.execute_layer1(intent_text or "")
    tokens = list(atoms.hypotheses[0].tokens) if atoms.hypotheses else []
    words = [str(getattr(token, "word", "")).lower() for token in tokens]
    # LATN's current SQ pass emits a Question for WH forms but not yet for
    # auxiliary-led yes/no forms ("can I ...?", "do I ...?"). Keep the
    # semantic requirements below and admit that grammatical question shape.
    yesno_shape = (
        (intent_text or "").strip().endswith("?")
        and bool(words)
        and words[0] in {"am", "are", "can", "could", "did", "do", "does", "is"}
    )
    if not ((getattr(result, "question_phrases", None) or []) or yesno_shape):
        return False
    perspective = (
        any(_isa(token, "first_person") for token in tokens)
        or (len(words) >= 2 and words[0] in {"is", "are"} and words[1] == "there")
    )
    return perspective and any(_isa(token, "perceive") for token in tokens)


def _isa(tok, dim) -> bool:
    return tok is not None and tok.isa(dim)


def resolve_response(intent_text: str, *, lexicon, adapter) -> Optional[str]:
    """Read a bare yes/no answer to an offer: ``"affirm"`` / ``"decline"`` / None,
    by testing the intent's tokens for the affirm/decline dimensions (isa), not a
    yes/no string match. Used by the quote->confirm commerce exchange to read the
    buyer's reply."""
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )
    # Player transports preserve prose punctuation, including Markdown emphasis
    # and quotation marks.  Those wrappers are not part of the answer itself:
    # ``"yes"`` and ``*“yes”*`` must ground exactly like bare ``yes``.
    answer = (intent_text or "").strip()
    answer = answer.strip("*_` ")
    answer = answer.strip("\"'“”‘’ ")
    answer = answer.strip("*_` ")
    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(answer)
    l4 = getattr(result, "layer4_result", None)
    for hyp in (getattr(l4, "hypotheses", None) or []):
        for tok in getattr(hyp, "tokens", None) or []:
            if _vec_isa(tok, "affirm"):
                return "affirm"
            if _vec_isa(tok, "decline"):
                return "decline"
    return None


def _token_surface(word: str) -> str:
    """Surface form for a LATN token word (unwraps NP(...))."""
    w = (word or "").strip().lower()
    m = re.match(r"np\((.+)\)$", w)
    return (m.group(1) if m else w).strip()


def _number_from_latn_token(tok) -> Optional[float]:
    """Numeric value carried by a LATN token vector, when present."""
    try:
        if not tok.isa("number"):
            return None
    except Exception:
        return None

    # LATN prints non-zero dimensions like "..., number=10.00, ...".
    dims = ""
    try:
        dims = tok.non_zero_dims() or ""
    except Exception:
        dims = ""
    m = re.search(r"\bnumber=([0-9]+(?:\.[0-9]+)?)\b", dims)
    if m is not None:
        return float(m.group(1))

    # Fallback: NP(10) style token surface.
    s = _token_surface(getattr(tok, "word", ""))
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", s):
        return float(s)
    return _LATN_NUM_WORDS.get(s)


def _parse_mixed_number_words(words: list[str]) -> Optional[float]:
    """Parse mixed digit/word number phrases (e.g. "25", "twenty five")."""
    if not words:
        return None
    if len(words) == 1 and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", words[0]):
        return float(words[0])

    total = 0.0
    current = 0.0
    saw = False
    for w in words:
        if w == "and":
            continue
        if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", w):
            # Numeric token in phrase: treat as a complete current term.
            current += float(w)
            saw = True
            continue
        val = _LATN_NUM_WORDS.get(w)
        if val is None:
            return None
        saw = True
        if val == 100.0:
            current = max(1.0, current) * 100.0
        elif val >= 20.0 and (val % 10.0) == 0.0:
            current += val
        else:
            current += val
    total += current
    return total if saw else None


def resolve_movement_distance(intent_text: str, *, lexicon, adapter) -> Optional[float]:
    """LATN-first extraction of explicit movement distance in feet.

    Returns a distance when intent text expresses a movement with a feet-unit
    quantity (e.g. "move north ten feet", "dash 15 ft"). Returns None when no
    movement+distance can be derived from LATN output.
    """
    from engine.latn import (
        LATNLayerExecutor, use_lexicon, use_vp_policy, PermissiveVPPolicy,
        use_sp_policy, PermissiveSPPolicy,
    )

    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()), \
            use_sp_policy(PermissiveSPPolicy()):
        result = executor.execute_layer5(intent_text or "")

    # Accept movement either from full VP structure (preferred) or from layer-4
    # tokenization when no sentence phrase survives policy.
    is_movement = False
    for sp in (getattr(result, "sentence_phrases", None) or []):
        for vp in _predicate_vps(sp):
            if _vp_isa(vp, *_MOVEMENT_VERBS):
                is_movement = True
                # The distance may be captured as the movement VP's object NP
                # ("move ten feet north" -> VP object NP(ten foot), carrying
                # unit_ft + number). Read it from the VP -- this uses the richer
                # parse rather than depending on the tokens staying loose.
                _np = getattr(vp, "noun_phrase", None)
                _vec = getattr(_np, "vector", None)
                if _vec is not None:
                    try:
                        if _vec.isa("unit_ft"):
                            _d = _number_from_latn_token(_vec)
                            if _d is not None:
                                return _d
                    except Exception:
                        pass
                break
        if is_movement:
            break

    l4 = getattr(result, "layer4_result", None)
    hypotheses = list(getattr(l4, "hypotheses", None) or [])
    if not is_movement:
        for hyp in hypotheses:
            for tok in getattr(hyp, "tokens", None) or []:
                # A layer-4 token is itself a VectorSpace, so test its dimensions
                # (catches walk/go/head via the move dim, not just literal
                # "move"/"dash").
                if _vec_isa(tok, *_MOVEMENT_VERBS):
                    is_movement = True
                    break
            if is_movement:
                break
    if not is_movement:
        return None

    for hyp in hypotheses:
        tokens = list(getattr(hyp, "tokens", None) or [])
        # LATN may compose quantity+unit into one NP token
        # (e.g., "NP(ten foot)" with number + unit_ft dims).
        for tok in tokens:
            try:
                if tok.isa("unit_ft") and tok.isa("number"):
                    direct = _number_from_latn_token(tok)
                    if direct is not None:
                        return direct
            except Exception:
                pass

        for i, tok in enumerate(tokens):
            unit = _token_surface(getattr(tok, "word", ""))
            is_unit = False
            try:
                is_unit = tok.isa("unit_ft")
            except Exception:
                is_unit = False
            if unit not in {"ft", "feet", "foot"} and not is_unit:
                continue
            phrase: list[str] = []
            j = i - 1
            while j >= 0:
                prev = tokens[j]
                surface = _token_surface(getattr(prev, "word", ""))
                num = _number_from_latn_token(prev)
                if num is not None:
                    # Keep original lexical surface where possible so phrases
                    # like "twenty five" stay compositional.
                    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", surface):
                        phrase.append(surface)
                    else:
                        phrase.append(surface)
                    j -= 1
                    continue
                if surface in _LATN_NUM_WORDS or surface == "and":
                    phrase.append(surface)
                    j -= 1
                    continue
                break
            if not phrase:
                continue
            parsed = _parse_mixed_number_words(list(reversed(phrase)))
            if parsed is not None:
                return parsed
    return None


def resolve_item_interaction(
    intent_text: str,
    *,
    interaction_target: Optional[str],
    items: Optional[dict],
    character_zone: Optional[str],
    lexicon=None,
    adapter=None,
) -> Optional[Tuple[Item, Interaction]]:
    """LATN-first, shallow-fallback single-interaction resolution.

    Drop-in compatible with ``verb_resolver.resolve_item_interaction``: when a
    lexicon+adapter are supplied and the parse yields an item with an
    interaction, return the first such (item, interaction); otherwise defer to
    the shallow resolver. This is the seam the session loop calls.
    """
    if lexicon is not None and adapter is not None:
        for action in resolve_actions(intent_text, lexicon=lexicon, adapter=adapter):
            if action.item is not None and action.interaction is not None:
                return action.item, action.interaction
    from engine.verb_resolver import resolve_item_interaction as _shallow
    return _shallow(
        intent_text=intent_text,
        interaction_target=interaction_target,
        items=items,
        character_zone=character_zone,
    )
