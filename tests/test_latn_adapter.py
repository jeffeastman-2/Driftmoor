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
from engine.latn import LATNLayerExecutor, use_lexicon


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


def test_name_grounds_through_the_full_parser():
    # Engraf's NP ATN now accepts a bare proper noun as an NP head, so a name
    # grounds end-to-end (lexicon -> parse -> adapter), no hand-built NP.
    lex, adapter, ex = _scene()
    assert _best(lex, adapter, ex, "Amara") == {"amara": pytest.approx(1.0)}


def test_recipient_and_object_ground_in_transfer():
    # The transfer case uses the VP structure at layer 4 (vp.noun_phrase =
    # object, vp.prepositions[].noun_phrase = recipient) with PermissiveVPPolicy
    # active so the non-CAD verb survives Layer-4 grounding.
    from engine.latn import use_vp_policy, PermissiveVPPolicy
    lex, adapter, ex = _scene()
    with use_lexicon(lex), use_vp_policy(PermissiveVPPolicy()):
        r = ex.execute_layer4("give the mace to Amara")
    grounded = set()
    for vp in r.verb_phrases:
        for np in [vp.noun_phrase, *[p.noun_phrase for p in vp.prepositions]]:
            if np:
                for _, ent in adapter.resolve_noun_phrase(np):
                    grounded.add(ent.entity_id)
    assert "amara" in grounded
    assert "banded_mace" in grounded


def test_pronoun_they_returns_all_entities():
    lex, adapter, ex = _scene()
    ids = {e.entity_id for e in adapter.resolve_pronoun("they")}
    assert {"amara", "kael", "borin", "banded_mace", "patch"} <= ids
