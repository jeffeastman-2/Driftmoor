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
    property_dim,
    register_driftmoor_dimensions,
)

# Verb synonyms for the 5e actions the current shallow resolver does not handle
# yet (combat / movement / defensive). The object-interaction synonyms are
# pulled live from verb_resolver's lexicons (single source of truth), so they
# are not duplicated here. Spell/target names ride NPs, not these.
_EXTRA_VERB_SYNONYMS: list[tuple[str, list[str]]] = [
    ("attack", ["attack", "strike", "hit", "swing", "swing at", "slash",
                "stab", "shoot", "fire", "fire at", "loose", "lunge", "lunge at"]),
    ("cast", ["cast", "invoke", "channel"]),
    ("move", ["move", "go", "walk", "approach", "advance", "step", "head"]),
    ("dash", ["dash", "sprint", "rush", "run"]),
    ("disengage", ["disengage", "withdraw", "retreat", "fall back"]),
    ("dodge", ["dodge", "evade"]),
    ("help", ["help", "aid", "assist"]),
    ("ready", ["ready", "prepare"]),
    ("hide", ["hide", "conceal", "sneak"]),
]

# Faction adjectives -> faction value whose one-hot dim they activate.
_FACTION_SYNONYMS: list[tuple[str, list[str]]] = [
    ("party", ["friendly", "allied", "ally"]),
    ("hostile", ["hostile", "enemy", "enemies"]),
    ("neutral", ["neutral"]),
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
            layer[word.lower()] = _vf(f"verb action {canonical}")
    # Faction adjectives -> faction_<value> dims.
    for value, words in _FACTION_SYNONYMS:
        dim = property_dim("faction", value)
        for word in words:
            layer[word.lower()] = _vf("adj", **{dim: 1.0})
    return layer


def _build_world_layer(characters: Iterable, items: Iterable, places: Iterable) -> dict:
    layer: dict = {}

    # Item labels (and ids as fallback) -> nouns + their component words.
    for it in items:
        label = getattr(it, "label", "") or getattr(it, "id", "") or ""
        _add_noun_text(layer, label)

    # Place names -> nouns.
    for pl in places:
        _add_noun_text(layer, getattr(pl, "name", "") or "")

    # Characters: names as proper nouns, then descriptor words carrying their
    # property dims (added last so they win over any plain-noun homograph from
    # a label, e.g. a "cleric" mentioned in some item's text).
    for c in characters:
        name = getattr(c, "name", "") or ""
        _add_noun_text(layer, name, pos="proper_noun")
        handle = getattr(c, "scene_handle", "") or ""
        _add_noun_text(layer, handle)
        for field, attr in (("race", "race"), ("class", "character_class"), ("role", "role")):
            value = getattr(c, attr, "") or ""
            dim = property_dim(field, value)
            if dim:
                for w in _words(value):
                    layer[w] = _vf("noun", **{dim: 1.0})
                if 2 <= len(_words(value)) <= 3:
                    layer[_phrase(value)] = _vf("noun", **{dim: 1.0})
    return layer


def build_driftmoor_lexicon(characters: Iterable = (), items: Iterable = (), places: Iterable = ()):
    """Build the layered Driftmoor lexicon. Registers the RPG dims first
    (idempotent), then returns an Engraf ``Lexicon`` over a ChainMap of
    world > rpg > function-base (Engraf's shared FUNCTION_WORDS).
    """
    register_driftmoor_dimensions(characters)

    from engine.latn import FUNCTION_WORDS, Lexicon

    base = dict(FUNCTION_WORDS)
    rpg = _build_rpg_layer()
    world = _build_world_layer(characters, items, places)
    # ChainMap lookup is first-wins; we want function/action backbone to take
    # precedence over world content homographs, so order base, rpg, world.
    return Lexicon(ChainMap(base, rpg, world))
