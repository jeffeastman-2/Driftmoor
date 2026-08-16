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
from engine.latn import (
    LATNLayerExecutor,
    use_lexicon,
    use_sp_policy,
    use_vp_policy,
    PermissiveSPPolicy,
    PermissiveVPPolicy,
)
from engine.latn_adapter import DriftmoorSceneAdapter
from engine.latn_lexicon import build_driftmoor_lexicon


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


@pytest.mark.parametrize("command", [
    "I touch the tracks",
    "I measure the tracks",
])
def test_physical_inspection_verbs_resolve_authored_tracks(command):
    cfg = __import__(
        "engine.md_loader", fromlist=["configure_from_place_path"]
    ).configure_from_place_path("places/driftmoor/stables")
    chars = _scene()[1]

    result = latn_integration.resolve_item_interaction(
        intent_text=command,
        interaction_target=None,
        items=cfg.items,
        characters=chars,
        character_zone="STABLES",
        scene_geometry=cfg.scene_geometry,
    )

    assert result is not None
    item, interaction = result
    assert item.id == "clawed_tracks"
    assert interaction.verb == "touch"
    assert "adult hand" in interaction.response


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


def test_build_context_includes_runtime_pack_possessions_after_transition():
    from models.thing import Thing
    from engine.latn_resolver import resolve_actions

    _items, chars = _scene()
    ale = Thing(id="driftmoor_ale_i1", name="Driftmoor Ale",
                holder="amara", owner="amara")
    chars["amara"].pack = [ale]
    chars["amara"].things = [ale]
    lexicon, adapter = latn_integration.build_context({}, chars, "MEETING_ROOM")

    actions = resolve_actions(
        "drink the ale", lexicon=lexicon, adapter=adapter)
    assert actions
    assert any(action.item is ale for action in actions)


# --- resolve_query: LATN answers shop questions, DM gets out of the picture ---

def _shop_catalog():
    from models.thing import Thing
    from models.shop_catalog import ShopCatalog
    return ShopCatalog([
        Thing(id="bolts_20", name="Bolts (20)", price="1 gp", vendor_id="jorgen"),
    ]).entries_for("jorgen")


def test_resolve_query_answers_yesno_for_sale():
    # A to-be-led yes/no question, no '?' and no wh-word, is answered from the
    # catalog by the engine -- the SQ pass grounds "your bolts" to the good.
    entries = _shop_catalog()
    ans = latn_integration.resolve_query(
        "are your bolts for sale", {}, {}, "", catalog=entries)
    assert ans is not None and "Bolts (20)" in ans and "1 gp" in ans


def test_resolve_query_lists_catalog_for_what():
    entries = _shop_catalog()
    ans = latn_integration.resolve_query(
        "what do you have for sale", {}, {}, "", catalog=entries)
    assert ans is not None and "Bolts (20)" in ans


def test_resolve_query_what_can_i_buy_lists_catalog():
    # The focus is the subject pronoun "I", which must NOT be mistaken for a
    # named good (it grounds loosely to a catalog entry); a "what" shop question
    # lists the catalog instead of answering about one wrong item.
    entries = _shop_catalog()
    ans = latn_integration.resolve_query(
        "what can I buy", {}, {}, "", catalog=entries)
    assert ans is not None and ans.startswith("For sale:") and "Bolts (20)" in ans


def test_resolve_query_what_can_you_sell_me_lists_catalog():
    entries = _shop_catalog()
    for question in (
        "what can you sell me",
        "What can you sell me?",
        '"What can you sell me?"',
        '"What are you selling?"',
    ):
        ans = latn_integration.resolve_query(
            question, {}, {}, "", catalog=entries)
        assert ans is not None and ans.startswith("For sale:") and "Bolts (20)" in ans


@pytest.mark.parametrize(
    "question",
    [
        "what do you have to sell me?",
        "what do you have for sale?",
        "what do you have to sell?",
        "do you have anything to sell?",
    ],
)
def test_resolve_query_answers_empty_catalog_without_dm_fallback(question):
    ans = latn_integration.resolve_query(
        question, {}, {}, "", catalog=[]
    )
    assert ans == "Nothing is listed for sale here."


def test_resolve_query_declines_non_question():
    # A command is not a question: resolve_query returns None so the caller
    # routes it to the action resolver, not an answer.
    entries = _shop_catalog()
    assert latn_integration.resolve_query(
        "buy bolts", {}, {}, "", catalog=entries) is None


def test_resolve_query_declines_unrouted_question():
    # A question that isn't about the catalog returns None (-> annotated DM
    # fallback) until geometry/self sources are routed.
    entries = _shop_catalog()
    assert latn_integration.resolve_query(
        "where is the tavern", {}, {}, "", catalog=entries) is None


def test_infer_movement_target_grounds_feature():
    # "move to the <feature>" grounds the destination item (in the directional
    # PP, not the direct object) to its position.
    from models.space_time import Position
    items, chars = _scene()
    items["patch"].position = Position(x=12.0, y=34.0, z=0.0)
    dest = latn_integration.infer_movement_target(
        "move to the shimmering patch", items, chars, "GLADE", scene_geometry=None)
    assert dest == (12.0, 34.0, 0.0)


def test_infer_movement_distance_reads_word_number():
    items, chars = _scene()
    dist = latn_integration.infer_movement_distance(
        "I move north ten feet", items, chars, "GLADE", scene_geometry=None)
    assert dist == 10.0


def test_infer_movement_distance_reads_numeric_ft():
    items, chars = _scene()
    dist = latn_integration.infer_movement_distance(
        "I move east 15 ft", items, chars, "GLADE", scene_geometry=None)
    assert dist == 15.0


def test_direction_and_feet_tokens_have_semantic_dims():
    lex = build_driftmoor_lexicon([], [], zones=[], landmarks=[])
    adapter = DriftmoorSceneAdapter(items={}, characters={}, actor_zone="")
    exe = LATNLayerExecutor(adapter)

    with use_lexicon(lex), use_vp_policy(PermissiveVPPolicy()), use_sp_policy(PermissiveSPPolicy()):
        res = exe.execute_layer5("I move ten feet north")

    l4 = getattr(res, "layer4_result", None)
    assert l4 is not None
    hyp = (getattr(l4, "hypotheses", None) or [None])[0]
    assert hyp is not None
    toks = list(getattr(hyp, "tokens", None) or [])
    north = next((t for t in toks if t.word.lower() == "north"), None)
    assert north is not None
    assert north.isa("locy")
    assert "locy=1.00" in north.non_zero_dims()

    # The feet unit carries the unit_ft semantic dim. Depending on the parse it
    # rides either a top-level token ("feet"/"NP(ten foot)") or -- now that a
    # trailing token ("north") no longer blocks the VP -- the movement VP's
    # object NP. Accept it wherever it lands; the semantic dim is what matters
    # (and infer_movement_distance reads it either way).
    def _carries_unit_ft():
        if any(t.isa("unit_ft") for t in toks):
            return True
        for sp in (getattr(res, "sentence_phrases", None) or []):
            vec = getattr(getattr(sp, "predicate", None), "noun_phrase", None)
            vec = getattr(vec, "vector", None)
            if vec is not None and vec.isa("unit_ft"):
                return True
        return False

    assert _carries_unit_ft()
