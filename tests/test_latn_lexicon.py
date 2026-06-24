"""Tests for the Driftmoor LATN lexicon builder (engine.latn_lexicon).

Pure text helpers run anywhere; the build/tokenize tests need Engraf and are
skipped if it isn't importable.
"""

from dataclasses import dataclass

import pytest

from engine.latn_lexicon import _words, _phrase


@dataclass
class _Ch:
    name: str = ""
    race: str = ""
    character_class: str = ""
    role: str = ""
    scene_handle: str = ""


@dataclass
class _It:
    id: str = ""
    label: str = ""


def test_words_and_phrase_drop_punctuation():
    assert _words("Trigger glyph (top)") == ["trigger", "glyph", "top"]
    assert _phrase("Trigger glyph (top)") == "trigger glyph top"
    assert _words("") == []


def _tok_map(lex, sentence):
    from latn.lexer.lexicon import use_lexicon
    from latn.lexer.latn_tokenizer_layer1 import latn_tokenize_best
    with use_lexicon(lex):
        return {t.word: t for t in latn_tokenize_best(sentence)}


def test_lexicon_tokenizes_actions_recipients_and_descriptors():
    pytest.importorskip("latn.lexer.vector_space")
    from engine.latn_lexicon import build_driftmoor_lexicon

    chars = [_Ch(name="Amara", race="High Elf", character_class="Cleric", role="Smith"),
             _Ch(name="Kael", race="Dwarf", character_class="Fighter")]
    items = [_It(id="banded_mace", label="banded mace"),
             _It(id="patch", label="shimmering patch")]
    lex = build_driftmoor_lexicon(chars, items)

    t = _tok_map(lex, "give the banded mace to the dwarf cleric")
    assert t["give"].isa("give")
    assert t["to"]["directional_target"] != 0.0
    assert t["banded mace"].isa("noun")          # multi-word label compound
    assert t["dwarf"].isa("race_dwarf")
    assert t["cleric"].isa("class_cleric")

    # surface-verb convergence: synonyms hit the canonical action dim
    assert _tok_map(lex, "shoot the fighter")["shoot"].isa("attack")
    assert _tok_map(lex, "pick up the mace")["pick up"].isa("take")  # compound synonym

    # function base still present (prepositions/determiners reused from Engraf)
    assert _tok_map(lex, "examine the shimmering patch")["the"].isa("det")
