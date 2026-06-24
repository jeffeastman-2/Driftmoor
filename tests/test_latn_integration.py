"""Tests for the session<->LATN glue (engine.latn_integration).

LATN is the default resolution path for every actor; the shallow verb_resolver
remains the fallback when LATN doesn't parse/ground. Needs Engraf.
"""

from types import SimpleNamespace as NS

import pytest

pytest.importorskip("latn.lexer.vector_space")

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


def test_latn_grounds_from_parse():
    # LATN grounds the object straight from the free-text parse — no explicit
    # interaction_target needed.
    items, chars = _scene()
    r = latn_integration.resolve_item_interaction(
        intent_text="examine the shimmering patch", interaction_target=None,
        items=items, characters=chars, character_zone="GLADE")
    assert r is not None and r[0].id == "patch" and "shimmers" in r[1].response


def test_shallow_fallback_when_latn_does_not_ground():
    # When LATN can't ground (here "it" has no antecedent), fall back to the
    # shallow resolver keyed off the explicit interaction_target.
    items, chars = _scene()
    r = latn_integration.resolve_item_interaction(
        intent_text="look at it", interaction_target="shimmering patch",
        items=items, characters=chars, character_zone="GLADE")
    assert r is not None and r[0].id == "patch"


def test_npc_actor_also_uses_latn():
    # No human-only gate any more: an LLM NPC grounds via LATN too.
    items, chars = _scene()
    chars["amara"].player_transport = "llm"
    r = latn_integration.resolve_item_interaction(
        intent_text="examine the shimmering patch", interaction_target=None,
        items=items, characters=chars, character_zone="GLADE")
    assert r is not None and r[0].id == "patch"


def test_build_context_returns_lexicon_and_adapter():
    items, chars = _scene()
    lexicon, adapter = latn_integration.build_context(items, chars, "GLADE")
    assert lexicon is not None and adapter is not None


def test_infer_movement_target_grounds_feature():
    # "move to the <feature>" grounds the destination item (in the directional
    # PP, not the direct object) to its position.
    from models.space_time import Position
    items, chars = _scene()
    items["patch"].position = Position(x=12.0, y=34.0, z=0.0)
    dest = latn_integration.infer_movement_target(
        "move to the shimmering patch", items, chars, "GLADE", scene_geometry=None)
    assert dest == (12.0, 34.0, 0.0)
