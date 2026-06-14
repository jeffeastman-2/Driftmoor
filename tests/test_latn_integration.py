"""Tests for the session<->LATN glue (engine.latn_integration).

Verifies the flag gate routes to the LATN path when on and the shallow
verb_resolver when off, both producing a valid resolution. Needs Engraf.
"""

from types import SimpleNamespace as NS

import pytest

pytest.importorskip("engraf.lexer.vector_space")

from models.character import PlayerCharacter
from models.item import Interaction, Item
from engine import latn_integration


def _scene():
    chars = {"amara": NS(character=PlayerCharacter(
        id="amara", name="Amara", race="High Elf", character_type="player",
        character_class="Cleric", faction="party"), scene_handle="")}
    patch = Item(id="patch", label="shimmering patch", zone="GLADE",
                 interactions=[Interaction(verb="examine", aliases=[], condition="",
                                           response="It shimmers faintly.")])
    items = {"patch": patch, "banded_mace": Item(id="banded_mace", label="banded mace", zone="GLADE")}
    return items, chars


def test_flag_off_uses_shallow_resolver(monkeypatch):
    monkeypatch.delenv("DRIFTMOOR_LATN_RESOLVER", raising=False)
    assert latn_integration.latn_enabled() is False
    items, chars = _scene()
    # shallow path keys off the explicit interaction_target
    r = latn_integration.resolve_item_interaction(
        intent_text="look at it", interaction_target="shimmering patch",
        items=items, characters=chars, character_zone="GLADE")
    assert r is not None and r[0].id == "patch"


def test_flag_on_uses_latn_path(monkeypatch):
    monkeypatch.setenv("DRIFTMOOR_LATN_RESOLVER", "1")
    assert latn_integration.latn_enabled() is True
    items, chars = _scene()
    # LATN path grounds from the parse (no interaction_target needed)
    r = latn_integration.resolve_item_interaction(
        intent_text="examine the shimmering patch", interaction_target=None,
        items=items, characters=chars, character_zone="GLADE")
    assert r is not None and r[0].id == "patch" and "shimmers" in r[1].response


def test_build_context_returns_lexicon_and_adapter():
    items, chars = _scene()
    lexicon, adapter = latn_integration.build_context(items, chars, "GLADE")
    assert lexicon is not None and adapter is not None
