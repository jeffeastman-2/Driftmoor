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
import re
from typing import List, Optional, Tuple

from models.item import Interaction, Item
from engine.latn_dimensions import VERB_DIMS
from engine.verb_resolver import _find_by_verb, _pick_by_condition, authored_transfer_response

# Object-interaction verbs resolve to an authored Interaction; transfer verbs
# change possession (and may carry an authored flavor response).
_INTERACTION_VERBS = {"examine", "search", "read", "press"}
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
    verb: str                                  # canonical verb dim
    item: Optional[Item] = None
    interaction: Optional[Interaction] = None
    recipient_id: Optional[str] = None         # character id (transfer verbs)
    ambiguous: bool = False                     # grounding tie -> refused to guess


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
            verb = _canonical_verb(vp)
            if verb is None:
                continue
            item, ambiguous = _resolve_object(vp, adapter, verb)
            recipient = _resolve_recipient(vp, adapter) if verb in _TRANSFER_VERBS else None
            key = (verb, item.id if item is not None else None)
            prev = merged.get(key)
            if prev is None:
                merged[key] = ResolvedAction(verb, item, None, recipient, ambiguous)
            else:
                # Same clause seen via another PP-attachment variant: keep the
                # recipient if this variant found one, and don't let a variant
                # without grounding override a grounded one.
                if prev.recipient_id is None and recipient is not None:
                    prev.recipient_id = recipient
                prev.ambiguous = prev.ambiguous and ambiguous

    actions: List[ResolvedAction] = []
    for action in merged.values():
        if action.item is not None and action.verb in _INTERACTION_VERBS:
            action.interaction = _interaction_for(action.item, action.verb)
        elif action.item is not None and action.verb in _TRANSFER_VERBS:
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
            if _canonical_verb(vp) not in _MOVEMENT_VERBS:
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
            if _canonical_verb(vp) in _MOVEMENT_VERBS:
                is_movement = True
                break
        if is_movement:
            break

    l4 = getattr(result, "layer4_result", None)
    hypotheses = list(getattr(l4, "hypotheses", None) or [])
    if not is_movement:
        for hyp in hypotheses:
            for tok in getattr(hyp, "tokens", None) or []:
                w = _token_surface(getattr(tok, "word", ""))
                if w in _MOVEMENT_VERBS:
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
