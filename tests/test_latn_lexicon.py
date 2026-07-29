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
    # LATN owns the grammatical preposition; Driftmoor's resolver interprets
    # the surface word "to" when selecting a recipient.
    assert t["to"].isa("prep")
    assert t["banded mace"].isa("noun")          # multi-word label compound
    assert t["dwarf"].isa("race_dwarf")
    assert t["cleric"].isa("class_cleric")

    # surface-verb convergence: synonyms hit the canonical action dim
    assert _tok_map(lex, "shoot the fighter")["shoot"].isa("attack")
    assert _tok_map(lex, "pick up the mace")["pick up"].isa("take")  # compound synonym
    assert _tok_map(lex, "break the seal on the letter")["break the seal"].isa("open")

    # function base still present (prepositions/determiners reused from Engraf)
    assert _tok_map(lex, "examine the shimmering patch")["the"].isa("det")


def test_inflected_verbs_derive_from_base_forms():
    # The vocab lists carry base forms only; LATN's layer-1 morphology grounds
    # the inflections, so "enters"/"buys"/"coins" inherit their roots' dims.
    # Guards against re-adding the redundant -s/-ing entries that were swept.
    pytest.importorskip("latn.lexer.vector_space")
    from engine.latn_lexicon import build_driftmoor_lexicon
    lex = build_driftmoor_lexicon([], [])

    def has(sentence, *dims):
        toks = _tok_map(lex, sentence).values()
        return any(all(t.isa(d) for d in dims) for t in toks)

    def has_across_hypotheses(sentence, *dims):
        # Scan every layer-1 hypothesis (not just the best): a homograph reading
        # is present even when another reading ranks first.
        from latn.lexer.lexicon import use_lexicon
        from latn.lexer.latn_tokenizer_layer1 import latn_tokenize_layer1
        with use_lexicon(lex):
            hyps = latn_tokenize_layer1(sentence)
        return any(all(t.isa(d) for d in dims)
                   for h in hyps for t in h.tokens)

    assert has("she enters the tavern", "move", "enter")   # <- "enter"
    assert has("the guard buys bolts", "buy")              # <- "buy"
    assert has("she wants a dagger", "buy")                # <- "want"
    assert has("how much coins do I have", "currency")     # <- "coin"
    # "leaves" is now a homograph (noun "leaf" + verb "leave"), so the verb
    # reading rides alongside the noun -- present among the hypotheses.
    assert has_across_hypotheses("he leaves the shop", "move", "leave")


def test_setting_and_common_nouns_registered():
    # "leaf" (common noun) and "Driftmoor" (setting proper noun) tokenize instead
    # of being flagged unknown; adding "leaf" makes "leaves" a live homograph.
    pytest.importorskip("latn.lexer.vector_space")
    from engine.latn_lexicon import build_driftmoor_lexicon
    from latn.lexer.lexicon import use_lexicon
    from latn.lexer.latn_tokenizer_layer1 import latn_tokenize_layer1
    lex = build_driftmoor_lexicon([], [])

    assert _tok_map(lex, "a leaf")["leaf"].isa("noun")
    dtok = _tok_map(lex, "driftmoor")["driftmoor"]
    assert dtok.isa("proper_noun") and not dtok.isa("unknown")
    # "leaves" forks into a noun and a verb reading.
    with use_lexicon(lex):
        pos = {("noun" if h.tokens[0].isa("noun") else
                "verb" if h.tokens[0].isa("verb") else "?")
               for h in latn_tokenize_layer1("leaves")}
    assert "noun" in pos and "verb" in pos, pos


def test_conversation_commerce_and_spell_words_are_known():
    pytest.importorskip("latn.lexer.vector_space")
    from engine.latn_lexicon import build_driftmoor_lexicon
    lex = build_driftmoor_lexicon([], [])

    assert not _tok_map(lex, "hello")["hello"].isa("unknown")
    assert _tok_map(lex, "for sale")["sale"].isa("noun")
    assert _tok_map(lex, "a spell")["spell"].isa("noun")
    assert _tok_map(lex, "teleport")["teleport"].isa("cast")


def test_downstairs_is_known_as_a_parentward_direction():
    pytest.importorskip("latn.lexer.vector_space")
    from engine.latn_lexicon import build_driftmoor_lexicon
    lex = build_driftmoor_lexicon([], [])

    downstairs = _tok_map(lex, "go downstairs")["downstairs"]
    assert downstairs.isa("adv")
    # isa() tests positive activation, so inspect the vector for negative Z.
    assert "locz=-1.00" in downstairs.non_zero_dims()


def test_authored_character_spell_names_are_world_vocabulary():
    pytest.importorskip("latn.lexer.vector_space")
    from models.spellcasting import Spell, SpellcastingProfile
    from engine.latn_lexicon import build_driftmoor_lexicon

    caster = _Ch(name="Gil")
    caster.spellcasting = SpellcastingProfile(
        ability="INT", known=[Spell(name="Minor Illusion", level=0)])
    lex = build_driftmoor_lexicon([caster], [])
    assert not _tok_map(lex, "cast minor illusion")["minor illusion"].isa("unknown")
