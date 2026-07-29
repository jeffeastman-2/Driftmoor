"""Tests for LATN-backed intent resolution (engine.latn_resolver).

Needs Engraf; skipped if unavailable. Exercises parse -> dispatch -> ground
for examine/transfer/conjunction/ambiguity, plus the shallow fallback.
"""

from types import SimpleNamespace as NS

import pytest

pytest.importorskip("latn.lexer.vector_space")

from models.character import PlayerCharacter
from models.item import Interaction, Item
from engine.latn_lexicon import build_driftmoor_lexicon
from engine.latn_adapter import DriftmoorSceneAdapter
from engine.latn_resolver import resolve_actions, resolve_item_interaction


def _pc(cid, name, race, cls):
    return NS(character=PlayerCharacter(id=cid, name=name, race=race,
                                        character_type="player",
                                        character_class=cls, faction="party"),
              scene_handle="")


def _scene(extra_items=None):
    chars = {"amara": _pc("amara", "Amara", "High Elf", "Cleric")}
    patch = Item(id="patch", label="shimmering patch", zone="GLADE",
                 interactions=[Interaction(verb="examine", aliases=[], condition="",
                                           response="It shimmers faintly.")])
    items = {"patch": patch, "banded_mace": Item(id="banded_mace", label="banded mace", zone="GLADE")}
    if extra_items:
        items.update(extra_items)
    lex = build_driftmoor_lexicon([c.character for c in chars.values()], list(items.values()))
    adapter = DriftmoorSceneAdapter(items=items, characters=chars, actor_zone="GLADE")
    return lex, adapter, items


def test_examine_resolves_authored_interaction():
    lex, adapter, _ = _scene()
    acts = resolve_actions("examine the shimmering patch", lexicon=lex, adapter=adapter)
    assert len(acts) == 1
    a = acts[0]
    assert a.verb == "examine" and a.item.id == "patch"
    assert a.interaction and "shimmers" in a.interaction.response


def test_open_and_read_resolve_authored_interactions():
    letter = Item(
        id="letter", label="sealed letter", zone="GLADE",
        interactions=[
            Interaction(verb="open", aliases=["unseal"], condition="",
                        response="The wax breaks."),
            Interaction(verb="read", aliases=[], condition="",
                        response="The route is revealed."),
        ],
    )
    lex, adapter, _ = _scene(extra_items={"letter": letter})
    opened = resolve_actions("unseal the letter", lexicon=lex, adapter=adapter)
    read = resolve_actions("read the letter", lexicon=lex, adapter=adapter)
    assert opened[0].interaction and opened[0].interaction.verb == "open"
    assert read[0].interaction and read[0].interaction.verb == "read"


def test_intent_has_action_reads_verb_dims():
    from engine.latn_resolver import intent_has_action
    # Attack vocabulary lives in the lexicon, not a keyword regex.
    assert intent_has_action("attack the goblin", "attack")
    assert intent_has_action("swing at the orc", "attack")   # regex missed this
    assert intent_has_action("loose an arrow", "attack")     # and this
    assert not intent_has_action("I walk north", "attack")
    # cast / search dims too
    assert intent_has_action("cast fireball", "cast")
    assert intent_has_action("invoke the ward", "cast")
    assert intent_has_action("teleport", "cast")
    assert intent_has_action("look around", "search", "examine")
    assert intent_has_action("scan the room", "search", "examine")
    assert not intent_has_action("cast fireball", "search", "examine")
    assert not intent_has_action("", "attack")


def test_consumption_verbs_ground_as_actions():
    # "eat"/"drink" carry the consume dim, so they ground instead of being
    # flagged as unknown (execution stays in manipulation.py). A verb without a
    # dim ("ride") still doesn't ground.
    pie = Item(id="meat_pie", label="meat pie", zone="GLADE")
    lex, adapter, _ = _scene(extra_items={"meat_pie": pie})
    assert resolve_actions("eat the meat pie", lexicon=lex, adapter=adapter)
    assert resolve_actions("drink the potion", lexicon=lex, adapter=adapter)
    assert not resolve_actions("ride the meat pie", lexicon=lex, adapter=adapter)
    # Only base forms are registered; LATN morphology derives the inflections,
    # so an -s form still grounds (guards against re-adding redundant -s entries).
    assert resolve_actions("eats the meat pie", lexicon=lex, adapter=adapter)
    assert resolve_actions("she quaffs the potion", lexicon=lex, adapter=adapter)


def test_transfer_resolves_object_and_recipient():
    lex, adapter, _ = _scene()
    acts = resolve_actions("give the mace to Amara", lexicon=lex, adapter=adapter)
    assert len(acts) == 1
    a = acts[0]
    assert a.verb == "give" and a.item.id == "banded_mace" and a.recipient_id == "amara"


def test_conjunction_yields_multiple_actions():
    lex, adapter, _ = _scene()
    acts = resolve_actions("pick up the mace and examine the patch", lexicon=lex, adapter=adapter)
    verbs = [(a.verb, a.item.id if a.item else None) for a in acts]
    assert ("take", "banded_mace") in verbs
    assert ("examine", "patch") in verbs
    assert len(acts) == 2


def test_ambiguous_object_refuses_to_guess():
    extra = {"g1": Item(id="g1", label="trigger glyph", zone="GLADE"),
             "g2": Item(id="g2", label="warding glyph", zone="GLADE")}
    lex, adapter, _ = _scene(extra)
    acts = resolve_actions("examine the glyph", lexicon=lex, adapter=adapter)
    assert len(acts) == 1
    assert acts[0].item is None and acts[0].ambiguous is True


def test_shallow_fallback_when_no_latn_context():
    _, _, items = _scene()
    # No lexicon/adapter -> defers to the shallow resolver, which uses the
    # explicit interaction_target.
    r = resolve_item_interaction("look at it", interaction_target="shimmering patch",
                                 items=items, character_zone="GLADE")
    assert r is not None and r[0].id == "patch"


def test_latn_first_compat_wrapper():
    lex, adapter, items = _scene()
    r = resolve_item_interaction("examine the patch", interaction_target=None,
                                 items=items, character_zone="GLADE",
                                 lexicon=lex, adapter=adapter)
    assert r is not None and r[0].id == "patch" and "shimmers" in r[1].response
