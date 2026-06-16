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


def test_actor_eligible_gates_on_transport():
    # LATN runs only for human-transport actors; LLM NPCs (and missing/None
    # transport) are gated to the shallow resolver. None actor_id (direct
    # callers / headless tests) is eligible so the flag alone governs them.
    chars = {
        "gil": NS(player_transport="telegram"),
        "npc": NS(player_transport="llm"),
        "npc_default": NS(),  # no player_transport -> treated as llm
    }
    assert latn_integration._actor_eligible("gil", chars) is True
    assert latn_integration._actor_eligible("npc", chars) is False
    assert latn_integration._actor_eligible("npc_default", chars) is False
    assert latn_integration._actor_eligible(None, chars) is True
    assert latn_integration._actor_eligible("missing", chars) is False


def test_flag_on_npc_actor_stays_shallow(monkeypatch):
    # Flag on, but the acting character is an LLM NPC -> the LATN parse path is
    # skipped, so the shallow resolver (which needs an explicit target) runs and
    # cannot resolve from free text alone.
    monkeypatch.setenv("DRIFTMOOR_LATN_RESOLVER", "1")
    items, chars = _scene()
    chars["amara"].player_transport = "llm"
    r = latn_integration.resolve_item_interaction(
        intent_text="examine the shimmering patch", interaction_target=None,
        items=items, characters=chars, character_zone="GLADE", actor_id="amara")
    assert r is None


def test_flag_on_human_actor_uses_latn(monkeypatch):
    # Same intent, but a human-transport actor -> LATN grounds it from the parse.
    monkeypatch.setenv("DRIFTMOOR_LATN_RESOLVER", "1")
    items, chars = _scene()
    chars["amara"].player_transport = "telegram"
    r = latn_integration.resolve_item_interaction(
        intent_text="examine the shimmering patch", interaction_target=None,
        items=items, characters=chars, character_zone="GLADE", actor_id="amara")
    assert r is not None and r[0].id == "patch"
