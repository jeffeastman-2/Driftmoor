"""Tests for DriftmoorSceneAdapter grounding (engine.latn_adapter).

Needs Engraf (the parser); skipped if it isn't importable. Exercises the full
chain lexicon -> tokenize -> NP -> adapter.resolve_noun_phrase.
"""

from types import SimpleNamespace as NS

import pytest

pytest.importorskip("engraf.lexer.vector_space")

from models.character import PlayerCharacter
from models.item import Item
from engine.latn_adapter import DriftmoorSceneAdapter
from engine.latn_lexicon import build_driftmoor_lexicon
from engine.latn import LATNLayerExecutor, use_lexicon, vector_from_features
from engraf.pos.noun_phrase import NounPhrase


def _pc(cid, name, race, cls):
    return NS(character=PlayerCharacter(id=cid, name=name, race=race,
                                        character_type="player",
                                        character_class=cls, faction="party"),
              scene_handle="")


def _scene():
    chars = {"amara": _pc("amara", "Amara", "High Elf", "Cleric"),
             "kael": _pc("kael", "Kael", "Dwarf", "Fighter"),
             "borin": _pc("borin", "Borin", "Dwarf", "Cleric")}
    items = {"banded_mace": Item(id="banded_mace", label="banded mace", zone="GLADE"),
             "patch": Item(id="patch", label="shimmering patch", zone="GLADE")}
    lex = build_driftmoor_lexicon([c.character for c in chars.values()], list(items.values()))
    adapter = DriftmoorSceneAdapter(items=items, characters=chars, actor_zone="GLADE")
    return lex, adapter, LATNLayerExecutor(adapter)


def _best(lex, adapter, ex, sentence):
    with use_lexicon(lex):
        r = ex.execute_layer2(sentence)
    scores = {}
    for np in r.noun_phrases:
        for score, ent in adapter.resolve_noun_phrase(np):
            scores[ent.entity_id] = max(scores.get(ent.entity_id, 0.0), float(score))
    return scores


def test_multi_descriptor_discriminates():
    lex, adapter, ex = _scene()
    scores = _best(lex, adapter, ex, "the dwarf cleric")
    # the dwarf cleric matches both race and class -> borin outranks the
    # partial matches (a high-elf cleric, a dwarf fighter)
    assert scores["borin"] > scores["amara"]
    assert scores["borin"] > scores["kael"]


def test_single_descriptor_keeps_ties_honest():
    lex, adapter, ex = _scene()
    cleric = _best(lex, adapter, ex, "the cleric")
    assert cleric["amara"] == pytest.approx(1.0)
    assert cleric["borin"] == pytest.approx(1.0)   # honest tie, no collapse
    assert "kael" not in cleric                      # the fighter doesn't match


def test_items_match_by_label_string_and_zone():
    lex, adapter, ex = _scene()
    assert "banded_mace" in _best(lex, adapter, ex, "the banded mace")
    assert "banded_mace" in _best(lex, adapter, ex, "the mace")  # substring


def test_adapter_name_matches_proper_noun_np():
    # The NP-grammar gap (bare proper nouns don't yet form NPs) is upstream in
    # Engraf; the adapter's name matching itself is correct when handed a
    # proper-noun NP. Verify that directly.
    lex, adapter, ex = _scene()
    np = NounPhrase("amara")
    np.noun = "amara"
    tok = vector_from_features("proper_noun")
    tok.word = "amara"
    np.consumed_tokens = [tok]
    np.vector = vector_from_features("proper_noun")
    ranked = adapter.resolve_noun_phrase(np)
    assert ranked and ranked[0][1].entity_id == "amara"


def test_pronoun_they_returns_all_entities():
    lex, adapter, ex = _scene()
    ids = {e.entity_id for e in adapter.resolve_pronoun("they")}
    assert {"amara", "kael", "borin", "banded_mace", "patch"} <= ids
