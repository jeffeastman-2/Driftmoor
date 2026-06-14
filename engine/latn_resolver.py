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
from typing import List, Optional, Tuple

from models.item import Interaction, Item
from engine.latn_dimensions import VERB_DIMS
from engine.verb_resolver import _find_by_verb, _pick_by_condition, authored_transfer_response

# Object-interaction verbs resolve to an authored Interaction; transfer verbs
# change possession (and may carry an authored flavor response).
_INTERACTION_VERBS = {"examine", "search", "read", "press"}
_TRANSFER_VERBS = {"take", "drop", "give"}

_TIE_MARGIN = 1e-9


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


def _resolve_object(vp, adapter) -> Tuple[Optional[Item], bool]:
    """Ground the VP's object NP to an Item. Returns (item, ambiguous)."""
    np = getattr(vp, "noun_phrase", None)
    if np is None:
        return None, False
    items = _entities_of_kind(adapter.resolve_noun_phrase(np), "item")
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
    )

    from engraf.lexer.latn_layer_executor import extract_verb_phrases

    executor = LATNLayerExecutor(adapter)
    with use_lexicon(lexicon), use_vp_policy(PermissiveVPPolicy()):
        result = executor.execute_layer4(intent_text or "")

    # Use the single best parse, not VPs flattened across every hypothesis
    # (which double-counts). hypotheses are confidence-ordered.
    if not result.hypotheses:
        return []
    verb_phrases = extract_verb_phrases(result.hypotheses[0])

    # TODO(pronoun-anaphora): cross-clause pronouns — "pick up the mace AND
    # give IT to Amara". "it" is grounded eagerly at L2 against parse-time
    # recency, which can't see an antecedent created/referenced by an earlier
    # clause of the same sentence. This is a LATN-CORE problem, not ours:
    # native Engraf has it too ("create a box and move it to [1,2,3]" yields
    # 0 VPs — "it" doesn't ground, so the move VP fails policy and the parse
    # is dropped). Agreed model: a pronoun is ALWAYS a deferred *grounding
    # promise*, forced by the executor against the recency at force-time
    # (seeded with scene/turn referents, extended per clause). Root fix lives
    # in Engraf (resolve_pronoun / L2); this loop is the force-point/executor
    # on the Driftmoor side. Until then a pronoun object yields item=None.
    actions: List[ResolvedAction] = []
    for vp in verb_phrases:
        verb = _canonical_verb(vp)
        if verb is None:
            continue
        item, ambiguous = _resolve_object(vp, adapter)
        recipient = _resolve_recipient(vp, adapter) if verb in _TRANSFER_VERBS else None
        interaction = None
        if item is not None and verb in _INTERACTION_VERBS:
            interaction = _interaction_for(item, verb)
        elif item is not None and verb in _TRANSFER_VERBS:
            resp = authored_transfer_response(item, verb)
            if resp:
                interaction = Interaction(verb=verb, aliases=[], condition="", response=resp)
        actions.append(ResolvedAction(verb, item, interaction, recipient, ambiguous))
    return actions


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
