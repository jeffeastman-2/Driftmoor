"""Build Driftmoor's layered LATN lexicon.

The lexicon answers "what can be *said*" — it gives the tokenizer a word ->
VectorSpace table so an utterance tokenizes. (What can be *referred to* right
now is the scene adapter's job, separate.) It is **layered** via a ChainMap:

    function base  <  rpg  <  world          (precedence: first wins)

* **function base** — Engraf's shared ``FUNCTION_WORDS`` (the/a, prepositions
  with their spatial dims, conjunctions, negation, modals, wh-words, to-be,
  degree adverbs, punctuation). Reused verbatim; CAD content is excluded so
  "draw your sword" can't resolve "draw" to the CAD create verb.
* **rpg** — verb synonyms mapped onto the 5e action dims (object-interaction
  synonyms come from ``verb_resolver``'s lexicons; combat/movement/etc. added
  here) and faction adjectives mapped onto ``faction_*`` dims.
* **world** — character names (``proper_noun``), item-label and place-name
  nouns (+ their individual words so "the mace" tokenizes against "banded
  mace"), and character descriptor words (race/class/role) carrying their
  one-hot property dims.

Precedence note: the function base wins over rpg, which wins over world, so a
content word that coincides with a function word or action verb keeps its
grammatical/action reading (e.g. a rare creature literally named "May" won't
shadow the modal). Cross-collisions are uncommon; finer disambiguation is left
to a later multi-hypothesis pass.

Build requires the RPG dims to exist, so the builder registers them first
(idempotent). Activate per parse with ``engraf...use_lexicon(lex)``.
"""

from __future__ import annotations

import re
from collections import ChainMap
from typing import Iterable

from engine.latn_dimensions import (
    FACTION_VALUES,
    character_view,
    property_dim,
    register_driftmoor_dimensions,
)

# Verb synonyms for the 5e actions the current shallow resolver does not handle
# yet (combat / movement / defensive). The object-interaction synonyms are
# pulled live from verb_resolver's lexicons (single source of truth), so they
# are not duplicated here. Spell/target names ride NPs, not these.
_EXTRA_VERB_SYNONYMS: list[tuple[str, list[str]]] = [
    ("attack", ["attack", "strike", "hit", "swing", "swing at", "slash",
                "stab", "thrust", "shoot", "fire", "fire at", "loose", "lunge",
                "lunge at", "charge", "aim", "throw", "hurl"]),
    # A known spell name can also be used as the command itself ("teleport to
    # the bridge").  Register Teleport as a cast verb as well as matching it by
    # name in the spell resolver; this keeps the natural shorthand actionable.
    ("cast", ["cast", "invoke", "channel", "teleport"]),
    ("move", ["move", "go", "come", "walk", "approach", "advance", "step", "head",
              "follow", "continue", "proceed", "return", "climb"]),
    ("dash", ["dash", "sprint", "rush", "run"]),
    ("disengage", ["disengage", "withdraw", "retreat", "fall back", "flee", "escape"]),
    ("dodge", ["dodge", "evade"]),
    ("help", ["help", "aid", "assist"]),
    ("ready", ["ready", "prepare"]),
    ("hide", ["hide", "conceal", "sneak"]),
    # Plus conversational buy framings. These carry only the "buy" dim, so they
    # ground as a purchase ONLY when the object is one of the shopkeeper's
    # catalog goods (the object gate) — "I want to leave" / "looking for the
    # mayor" stay None rather than misfiring. Multi-word forms are <=3 tokens.
    # Base forms only; morphology derives buys/wants/needs. "purchases" stays --
    # it doesn't reduce to "purchase" via the inflector.
    ("buy", ["buy", "purchase", "purchases", "pay for",
             "want", "need", "looking for", "would like"]),
    ("sell", ["sell", "vend", "offload", "hawk", "pawn"]),
]

# Threshold-crossing verbs. Registered with a dual "move enter"/"move leave"
# reading (see _build_rpg_layer): "move" keeps them groundable as ordinary
# movement, while "enter"/"leave" flags an intent to cross a venue boundary.
# Multi-word forms stay <=3 tokens (the tokenizer's compound limit). "go"/"walk"
# alone remain plain movement, so "go to the tavern" walks to the door while
# "go inside the tavern" crosses in.
# Base (uninflected) forms only where LATN morphology derives the rest: a
# single-word -s/-ing form resolves to its root and inherits its dims, so
# "enters"/"entering"/"visits"/"leaves" ground move+enter/leave from "enter"/
# "visit"/"leave" (the -s verb inflection now yields leaves->leave even though
# the noun singularizer would read it as the plural of "leaf" -- both readings
# fork). Multi-word compounds ("goes inside") aren't single-word-reducible, so
# they stay.
_ENTER_VERB_WORDS: list[str] = [
    "enter", "go inside", "go in", "go into", "goes inside",
    "step inside", "step into", "steps inside", "walk inside", "walk into",
    "head inside", "head into", "duck inside",
    "venture inside", "visit",
]
_LEAVE_VERB_WORDS: list[str] = [
    "leave", "exit", "go outside",
    "goes outside", "go out", "head out", "step outside", "walk out",
]

# Bare affirmations / refusals to an offer (the quote->confirm reply).
_AFFIRM_WORDS: list[str] = [
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "aye", "deal",
    "agreed", "done", "please do", "go ahead", "i agree",
]
_DECLINE_WORDS: list[str] = [
    "no", "nope", "nah", "pass", "cancel", "decline", "never mind",
    "forget it", "no thanks", "not now", "no thank you",
]

# Money words carry a ``currency`` axis so a wealth question ("how much gold do
# I have") routes to the purse via isa. Bare "silver"/"copper" are omitted --
# they're item-material modifiers (a silver rope, a copper key); the unambiguous
# coin phrasings ("silver pieces", "sp") carry the axis instead.
_CURRENCY_WORDS: list[str] = [
    "gold", "money", "coin", "currency", "wealth", "cash",
    "gp", "sp", "cp", "gold piece", "gold pieces", "silver piece",
    "silver pieces", "copper piece", "copper pieces",
]

# Consumption verbs, split by which state they apply to so engine.manipulation
# can refuse a mismatch ("drink the bread"): eat-words -> solids, drink-words ->
# liquids, generic consume/swallow/ingest -> whichever the thing affords. Base
# forms ONLY: LATN's layer-1 morphology derives the inflections ("eats"/"drinks"/
# "quaffs" resolve to their root and inherit its dim). (LATN does not enforce
# subject-verb agreement -- "I eats the cake" grounds the same as "I eat" -- as
# a permissive intent parser should.)
_CONSUME_VERB_SYNONYMS: list[tuple[str, list[str]]] = [
    ("eat", ["eat", "devour", "bite", "chew", "munch"]),
    ("drink", ["drink", "quaff", "sip", "gulp", "swig"]),
    ("consume", ["consume", "swallow", "ingest"]),
]

# Kit-manipulation verb signals -> engine.manipulation.classify_verb picks the
# engine verb from the target's affordances (draw/hold on a weapon vs a pack,
# etc.). Base forms only (morphology derives inflections). The transfer verbs
# drop/stow/take stay in _TRANSFER_LEXICON -- classify_verb reads those too, so
# "put away"/"put down"/"pick up" aren't duplicated here. ("draw" = weapon-ready:
# draw/wield/unsheathe/brandish; "hold" = generic take-in-hand: get/hold/carry.)
_KIT_VERB_SYNONYMS: list[tuple[str, list[str]]] = [
    ("draw", ["draw", "wield", "unsheathe", "brandish"]),
    ("hold", ["get", "hold", "carry", "pull out", "produce"]),
    ("sheathe", ["sheathe", "holster"]),
    ("wear", ["wear", "don", "put on", "equip"]),
    ("remove", ["remove", "take off", "doff", "unequip"]),
]

_POSTURE_VERB_SYNONYMS: list[tuple[str, list[str]]] = [
    ("sit", ["sit", "sit down", "take a seat"]),
    ("stand", ["stand", "stand up", "rise", "get up"]),
    ("kneel", ["kneel", "crouch"]),
    ("prone", ["lie down", "lay down", "go prone"]),
]

# Setting proper nouns -- place/region names that occur in play but aren't a
# grounded scene entity (so the world layer doesn't derive them). Registered so
# they tokenize instead of being flagged unknown.
_SETTING_PROPER_NOUNS: list[str] = ["driftmoor"]

# Common content nouns likely in narration/play but not tied to a scene Item.
# "leaf" also gives "leaves" a noun reading: with the verb "leaves" already in
# _LEAVE_VERB_WORDS, the homograph now forks (noun leaf / verb leave) and the
# grammar keeps whichever parses -- "the leaves" (NP) vs "she leaves" (VP).
_COMMON_NOUNS: list[str] = [
    "leaf",
    # Conversational/shop/spell vocabulary which need not denote a live scene
    # entity, but must remain valid input to the parser and its honesty check.
    "sale", "spell", "day", "madam", "name", "knowledge",
]

# Standalone social openings are discourse acts, not world actions.  Giving
# them a grammatical reading prevents the unknown-word dialog from rejecting
# perfectly ordinary greetings; the DM/NPC conversation layer still answers.
_DISCOURSE_WORDS: list[str] = ["hi", "hello", "greetings"]

# Social and intentional prose frequently surrounds the actionable part of a
# player's line. These readings keep ordinary introductions from being treated
# as parser errors without pretending that every such word is itself an engine
# action. ``seek`` is a verb so morphology also recognizes ``seeking``.
_CONVERSATION_ADJECTIVES: list[str] = ["good"]
_CONVERSATION_VERBS: list[str] = ["seek", "tell", "see", "suggest"]

# Common item modifiers (material/type adjectives) that appear in natural
# references to goods but not always in the good's own name -- e.g. "crossbow
# bolts" for the good "Bolts (20)". Registered as bare adjectives so head-noun
# matching resolves the good; the adj reading is free (grounding is string-
# based). Renaming a good to carry its modifier auto-registers it too, via the
# world layer's modifier derivation. Kept to clear, low-collision modifiers.
_ITEM_MODIFIER_WORDS: list[str] = [
    "crossbow", "wooden", "iron", "steel", "silver", "silvered", "golden",
    "leather", "silk", "hemp", "glass", "bronze", "copper", "tin",
]

# Faction adjectives -> faction value whose one-hot dim they activate.
_FACTION_SYNONYMS: list[tuple[str, list[str]]] = [
    ("party", ["friendly", "allied", "ally"]),
    ("hostile", ["hostile", "enemy", "enemies"]),
    ("neutral", ["neutral"]),
]

# Direction adverbs mapped to world-axis vectors.
_DIRECTION_VOCAB: list[tuple[str, dict[str, float]]] = [
    ("north", {"locy": 1.0}),
    ("n", {"locy": 1.0}),
    ("south", {"locy": -1.0}),
    ("s", {"locy": -1.0}),
    ("east", {"locx": 1.0}),
    ("e", {"locx": 1.0}),
    ("west", {"locx": -1.0}),
    ("w", {"locx": -1.0}),
    ("up", {"locz": 1.0}),
    ("down", {"locz": -1.0}),
    # "Upstairs" is learned dynamically as a child-venue alias. "Downstairs"
    # means returning to the parent, so it needs scene-independent vocabulary.
    ("downstairs", {"locz": -1.0}),
]

# Explicit linear distance units (feet).
_DISTANCE_UNIT_VOCAB: list[tuple[str, dict[str, float]]] = [
    ("ft", {"unit_ft": 1.0}),
    ("feet", {"unit_ft": 1.0}),
    ("foot", {"unit_ft": 1.0}),
]


def _vf(pos: str, **dims):
    # Local import so importing this module doesn't require the parser until a
    # lexicon is actually built. Routed through engine.latn (the single LATN
    # import surface) so phase 3's engraf->latn move is a one-file change.
    from engine.latn import vector_from_features
    return vector_from_features(pos, **dims)


def _words(text: str) -> list[str]:
    """Lowercased alphanumeric words of ``text`` (drops punctuation/parens)."""
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]


def _phrase(text: str) -> str:
    """Normalized multi-word phrase: lowercased, single-spaced, no punctuation
    ("Trigger glyph (top)" -> "trigger glyph top")."""
    return " ".join(_words(text))


def _add_noun_text(layer: dict, text: str, *, pos: str = "noun", **dims) -> None:
    """Register ``text`` as a noun: each individual word, plus the whole
    phrase as a 2-3 word compound (the tokenizer's compound limit). Existing
    entries are not overwritten (so property-dim entries and the function base
    keep priority within this layer's own construction)."""
    if not text:
        return
    words = _words(text)
    for w in words:
        layer.setdefault(w, _vf(pos, **dims))
    if 2 <= len(words) <= 3:
        layer.setdefault(" ".join(words), _vf(pos, **dims))


def _build_rpg_layer() -> dict:
    from engine.verb_resolver import _VERB_LEXICON, _TRANSFER_LEXICON

    layer: dict = {}
    # Object-interaction + extra action verbs: each synonym -> the canonical
    # verb dim (the canonical IS the dim name). Multi-word synonyms become
    # compound keys, which the tokenizer matches (up to 3 words).
    for canonical, synonyms in (*_VERB_LEXICON, *_TRANSFER_LEXICON, *_EXTRA_VERB_SYNONYMS):
        for word in synonyms:
            layer[word.lower()] = _vf("verb", **{canonical: 1.0})
    # Threshold-crossing verbs carry BOTH "move" (so movement still grounds —
    # "enter the chamber" moves into a zone) and "enter"/"leave" (the crossing
    # signal that promotes a venue destination to a sub-scene transition). Set
    # after the loop so they win over any plain-"move" reading; multi-word forms
    # are compound keys the tokenizer matches (<=3 words).
    for word in _ENTER_VERB_WORDS:
        layer[word.lower()] = _vf("verb", move=1.0, enter=1.0)
    for word in _LEAVE_VERB_WORDS:
        layer[word.lower()] = _vf("verb", move=1.0, leave=1.0)
    # Bare yes/no answers to an offer carry an affirm/decline dimension so the
    # quote->confirm exchange reads them via isa (not a yes/no string match).
    for word in _AFFIRM_WORDS:
        layer[word.lower()] = _vf("adv", affirm=1.0)
    for word in _DECLINE_WORDS:
        layer[word.lower()] = _vf("adv", decline=1.0)
    # Money words -> nouns carrying the currency axis (wealth questions).
    for word in _CURRENCY_WORDS:
        layer[word.lower()] = _vf("noun", currency=1.0)
    for word in _DISCOURSE_WORDS:
        layer[word.lower()] = _vf("adv")
    for word in _CONVERSATION_ADJECTIVES:
        layer.setdefault(word.lower(), _vf("adj"))
    for word in _CONVERSATION_VERBS:
        layer.setdefault(word.lower(), _vf("verb"))
    # Consumption verbs -> eat/drink/consume dims (state-gated in manipulation).
    for canonical, words in _CONSUME_VERB_SYNONYMS:
        for word in words:
            layer[word.lower()] = _vf("verb", **{canonical: 1.0})
    # Kit-manipulation verb signals -> their dims.
    for canonical, words in _KIT_VERB_SYNONYMS:
        for word in words:
            layer[word.lower()] = _vf("verb", **{canonical: 1.0})
    for canonical, words in _POSTURE_VERB_SYNONYMS:
        for word in words:
            layer[word.lower()] = _vf("verb", **{canonical: 1.0})
    # Setting proper nouns + common content nouns. setdefault so a word already
    # carrying a reading (e.g. the verb "leaves") is not clobbered.
    for word in _SETTING_PROPER_NOUNS:
        layer.setdefault(word.lower(), _vf("proper_noun singular"))
    for word in _COMMON_NOUNS:
        layer.setdefault(word.lower(), _vf("noun singular"))
    # Faction adjectives -> faction_<value> dims.
    for value, words in _FACTION_SYNONYMS:
        dim = property_dim("faction", value)
        for word in words:
            layer[word.lower()] = _vf("adj", **{dim: 1.0})
    # Item modifiers -> bare adjectives; head-noun matching grounds the good.
    # setdefault so a word already carrying a reading (verb/faction) is not
    # overwritten by a plain-adjective one.
    for word in _ITEM_MODIFIER_WORDS:
        layer.setdefault(word.lower(), _vf("adj"))

    # Movement direction adverbs and distance units.
    for word, dims in _DIRECTION_VOCAB:
        layer[word.lower()] = _vf("adv", **dims)
    for word, dims in _DISTANCE_UNIT_VOCAB:
        layer[word.lower()] = _vf("noun", **dims)
    return layer


def _build_world_layer(characters: Iterable, items: Iterable, places: Iterable,
                       zones: Iterable = (), landmarks: Iterable = (),
                       venues: Iterable = (), catalog: Iterable = ()) -> dict:
    layer: dict = {}
    # Modifier-position words: every non-final word of a multi-word reference.
    # These get a dual "noun adj" reading at the end so multi-word references
    # ("rocky chamber", "secret passage", "banded mace") parse as adj* + noun
    # head instead of an un-headable noun-noun chain. Only genuine modifiers
    # get the extra reading (NOT every standalone noun) — blanket dual-typing
    # explodes the tokenizer's hypothesis beam on long prose and the valid
    # parse gets pruned. Grounding is string-based, so the adj reading is free.
    modifiers: set[str] = set()

    def _note(text: str) -> str:
        words = _words(text)
        modifiers.update(words[:-1])  # all but the head
        return text

    # Item labels (and ids as fallback) -> nouns + their component words. Also
    # pull every distance/lighting appearance-band description so an entity is
    # referrable by however it currently looks ("a low shadow" for a far
    # creature), per the layered-description model. (Distance-FILTERING of which
    # description is valid now is the perception-fed adapter's job, not the
    # lexicon's — the lexicon just makes them all tokenizable.)
    for it in items:
        label = getattr(it, "label", "") or getattr(it, "id", "") or ""
        _add_noun_text(layer, _note(label))
        # Band descriptions are prose ("a low shadow against the far wall"), not
        # "adj noun" labels — they're added for tokenizability but NOT fed to
        # the modifier set (their common nouns would over-dual-type and explode
        # the hypothesis beam on long prose). Structured labels/zones/places do
        # feed it, via _note.
        bands = getattr(it, "appearance_bands", None) or {}
        if isinstance(bands, dict):
            for desc in bands.values():
                _add_noun_text(layer, desc or "")

    # Place names -> nouns.
    for pl in places:
        _add_noun_text(layer, _note(getattr(pl, "name", "") or ""))

    # Zone names (from scene geometry) -> nouns + component words, so "the
    # rocky passage" / "echo chamber" tokenize. Grounding a zone NP to a
    # movement target (and visibility-filtering) is the adapter's job.
    for zname in zones:
        _add_noun_text(layer, _note(zname or ""))

    # Landmark names (scene_geometry.landmarks keys, e.g. "echo_chamber_arch",
    # "first_passage_mouth") -> nouns + component words, so "echo chamber arch"
    # / "first passage mouth" tokenize as movement targets. _words splits on
    # the underscores. Grounding a landmark NP to a position is the adapter's
    # job (2b, distance/visibility-filtered).
    for lname in landmarks:
        _add_noun_text(layer, _note(lname or ""))

    # Venue aliases (enterable child places) -> nouns + component words, as clean
    # compound tokens so "broken lantern" / "pawn shop" / "rooming house"
    # tokenize as units (not scattered into shared words like "shop"). Each
    # ``venue`` is (scene_name, aliases); the aliases are pre-cleaned by the
    # caller (leading articles and generic nouns dropped).
    for _vname, aliases in venues:
        for alias in aliases:
            _add_noun_text(layer, _note(alias or ""))

    # Shop catalog goods -> nouns + component words, so "buy the meat pie"
    # tokenizes even though the good isn't a materialized scene item yet.
    for entry in catalog:
        _add_noun_text(layer, _note(getattr(entry, "name", "") or ""))

    # Characters: names as proper nouns, then descriptor words carrying their
    # property dims (added last so they win over any plain-noun homograph from
    # a label, e.g. a "cleric" mentioned in some item's text).
    for c in characters:
        base = character_view(c)
        name = getattr(base, "name", "") or ""
        _add_noun_text(layer, name, pos="proper_noun")
        # scene_handle lives on the CharacterSession wrapper (how others see a
        # character before names are exchanged), falling back to the base.
        handle = getattr(c, "scene_handle", "") or getattr(base, "scene_handle", "") or ""
        _add_noun_text(layer, handle)
        # A player's authored spell names are live vocabulary.  Without this,
        # the unknown-word honesty dialog rejected perfectly valid commands
        # such as "cast Minor Illusion" before spell adjudication could explain
        # whether that spell is implemented.
        profile = getattr(base, "spellcasting", None)
        if profile is not None:
            spells = (
                list(getattr(profile, "cantrips", None) or [])
                + list(getattr(profile, "prepared", None) or [])
                + list(getattr(profile, "known", None) or [])
            )
            for spell in spells:
                _add_noun_text(layer, _note(getattr(spell, "name", "") or ""))
        for field, attr in (("race", "race"), ("class", "character_class"), ("role", "role")):
            value = getattr(base, attr, "") or ""
            dim = property_dim(field, value)
            if dim:
                # Dual "noun adj": a descriptor can head an NP ("the dwarf") or
                # modify one ("the dwarf cleric"), so the NP parser can use it
                # either way and the NP vector accumulates the property dim.
                for w in _words(value):
                    layer[w] = _vf("noun adj", **{dim: 1.0})
                if 2 <= len(_words(value)) <= 3:
                    layer[_phrase(value)] = _vf("noun adj", **{dim: 1.0})

    # Give modifier-position words a dual "noun adj" reading so they can modify
    # a following head ("rocky chamber"). Only plain nouns are re-typed: skip
    # proper-noun names and the property descriptors above (already adj, and we
    # must not clobber their dims).
    for w in modifiers:
        v = layer.get(w)
        if v is not None and v.isa("noun") and not v.isa("adj") and not v.isa("proper_noun"):
            layer[w] = _vf("noun adj")
    return layer


def build_driftmoor_lexicon(characters: Iterable = (), items: Iterable = (),
                            places: Iterable = (), zones: Iterable = (),
                            landmarks: Iterable = (), venues: Iterable = (),
                            catalog: Iterable = ()):
    """Build the layered Driftmoor lexicon. Registers the RPG dims first
    (idempotent), then returns an Engraf ``Lexicon`` over a ChainMap of
    world > rpg > function-base (Engraf's shared FUNCTION_WORDS).

    ``zones`` is the scene's zone names (scene_geometry.zones) and
    ``landmarks`` its landmark ids (scene_geometry.landmarks keys, e.g.
    "echo_chamber_arch") so movement targets like "the rocky passage" and
    "echo chamber arch" tokenize.
    """
    register_driftmoor_dimensions(characters)

    from engine.latn import FUNCTION_WORDS, Lexicon

    base = dict(FUNCTION_WORDS)
    rpg = _build_rpg_layer()
    world = _build_world_layer(characters, items, places, zones, landmarks, venues, catalog)
    # ChainMap lookup is first-wins; we want function/action backbone to take
    # precedence over world content homographs, so order base, rpg, world.
    return Lexicon(ChainMap(base, rpg, world))
