"""Immediate non-combat question/answer scheduling."""

import asyncio
from types import SimpleNamespace as NS

from engine.social_exchange import (
    SocialExchangeSchedule,
    directed_social_target,
    generate_social_reply,
)


def _cs(cid, *, transport="llm", name=None, handle=""):
    return NS(
        character=NS(id=cid, name=name or cid.title()),
        player_transport=transport,
        scene_handle=handle,
        soul=f"Soul of {cid}",
        identity=f"Identity of {cid}",
    )


def test_sole_visible_npc_is_inferred_for_question():
    chars = {"gil": _cs("gil", transport="web"), "kelem": _cs("kelem")}
    assert directed_social_target(
        "Do you have any special deals?", speaker_id="gil",
        visible_ids={"kelem"}, characters=chars,
    ) == "kelem"


def test_named_npc_wins_when_several_are_visible():
    chars = {
        "gil": _cs("gil", transport="web"),
        "kelem": _cs("kelem", name="Kelem Dustcloak", handle="Kelem"),
        "tav": _cs("tav", name="Tavian Drakescale", handle="Tav"),
    }
    assert directed_social_target(
        "Kelem, do you have any special deals?", speaker_id="gil",
        visible_ids={"kelem", "tav"}, characters=chars,
    ) == "kelem"


def test_ambiguous_question_does_not_choose_arbitrary_npc():
    chars = {"kelem": _cs("kelem"), "tav": _cs("tav")}
    assert directed_social_target(
        "What do you know?", speaker_id="gil",
        visible_ids={"kelem", "tav"}, characters=chars,
    ) is None


def test_other_human_is_never_spoken_for_by_model():
    chars = {"other": _cs("other", transport="web")}
    assert directed_social_target(
        "Can you help me?", speaker_id="gil",
        visible_ids={"other"}, characters=chars,
    ) is None


def test_immediate_reply_consumes_one_exploration_slot_but_not_combat_slot():
    schedule = SocialExchangeSchedule()
    schedule.mark_response("kelem")
    assert schedule.suppress_slot("kelem", in_combat=False)
    assert not schedule.suppress_slot("kelem", in_combat=False)
    schedule.mark_response("kelem")
    assert not schedule.suppress_slot("kelem", in_combat=True)
    assert not schedule.consumed


def test_generated_reply_is_dialogue_only_and_uses_target_persona():
    calls = []

    async def llm(system, user):
        calls.append((system, user))
        return '**SPOKEN**: "Bundles, mystery bags, and favorable terms for shards."'

    roles = NS(player_right=NS(_call_llm=llm), player_left=NS(_call_llm=None))
    cycle = NS(_roles_for=lambda _cid: roles)
    reply = asyncio.run(generate_social_reply(
        turn_cycle=cycle, target_id="kelem", target_cs=_cs("kelem"),
        speaker_handle="Gilthaness",
        utterance="Do you have any special deals?", scene_context="Inside the shop.",
    ))
    assert reply == "Bundles, mystery bags, and favorable terms for shards."
    assert "Soul of kelem" in calls[0][0]
    assert "no narration" in calls[0][0].lower()

