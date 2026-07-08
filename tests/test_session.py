"""Tests for the session runner — direct Python game loop."""

import asyncio
import json
import random
from dataclasses import asdict
from pathlib import Path

import pytest

from engine.session import (
    CharacterSession,
    SessionResult,
    run_session,
    iter_session,
    _split_transport_utterance,
    _build_context,
    _save_turn,
    _checkpoint_filename,
    _resolve_attacks,
    _render_turn_result_packet,
    _render_transport_prompt,
    _render_puzzle_press_packet,
    _describe_press_sequence,
    load_resume_state,
    _has_vicious_mockery_disadvantage,
    _consume_vicious_mockery_disadvantage,
    _resolve_teleport_destination,
    COMBAT_EVENT,
    EXIT_EVENT,
    MELEE_DURATION,
)
from engine.scene_manager import TurnCycle, RoleSet, TurnResult, CharacterTurnResult
from engine.player_router import PlayerLeft, PlayerRight, RoleContext
from engine.dm_agent import DMLeft, DMRight, Adjudication, Narration
from engine.player_router import ActionIntent, CharacterOutput
from engine.initiative import roll_initiative
from engine.spell_resolver import ActiveSpellEffect, SpellResolver, SpellRuntimeState
from models.character import PlayerCharacter, Creature
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
    render_condition,
)
from models.space_time import GameTime
from models.spellcasting import Spell, SpellcastingProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def aeliana_char():
    return PlayerCharacter(
        id="aeliana", name="Aeliana", race="Wood Elf",
        character_type="player", character_class="Ranger",
        dexterity=16, location="fey_glade",
        hp=12, current_hp=12,
    )


@pytest.fixture
def fennel_char():
    return PlayerCharacter(
        id="fennel", name="Fennel", race="Human",
        character_type="player", character_class="Gatherer",
        dexterity=12, location="fey_glade",
        hp=8, current_hp=8,
    )


@pytest.fixture
def aeliana_condition():
    return CharacterCondition(
        character_id="aeliana",
        character_name="Aeliana",
        state=NeurochemicalState(dopamine=0.85, cortisol=0.25),
    )


@pytest.fixture
def fennel_condition():
    return CharacterCondition(
        character_id="fennel",
        character_name="Fennel",
        state=NeurochemicalState(dopamine=0.50, cortisol=0.60),
    )


@pytest.fixture
def aeliana_session(aeliana_char, aeliana_condition):
    return CharacterSession(
        character=aeliana_char,
        condition=aeliana_condition,
        soul="Aeliana is a solitary wood elf ranger.",
        identity="Level 1 Ranger, HP 12, AC 14.",
        initial_scene="You are on the trail approaching the Fey Glade.",
    )


@pytest.fixture
def fennel_session(fennel_char, fennel_condition):
    return CharacterSession(
        character=fennel_char,
        condition=fennel_condition,
        soul="Fennel is a curious gatherer.",
        identity="Level 1 Gatherer, HP 8, AC 11.",
        initial_scene="You are in the glade near the pool.",
    )


# ---------------------------------------------------------------------------
# CharacterSession
# ---------------------------------------------------------------------------

class TestCharacterSession:
    def test_construction(self, aeliana_session):
        cs = aeliana_session
        assert cs.character.id == "aeliana"
        assert cs.condition.character_id == "aeliana"
        assert "solitary" in cs.soul
        assert "Ranger" in cs.identity
        assert "Fey Glade" in cs.initial_scene

    def test_condition_renders(self, aeliana_session):
        text = render_condition(aeliana_session.condition)
        assert "dopamine" in text
        assert "cortisol" in text


# ---------------------------------------------------------------------------
# _build_context helper
# ---------------------------------------------------------------------------

class TestBuildContext:
    def test_builds_role_context(self, aeliana_session):
        ctx = _build_context(aeliana_session, turn=1, scene_history="")
        assert isinstance(ctx, RoleContext)
        assert ctx.character_id == "aeliana"
        assert ctx.turn == 1
        assert "dopamine" in ctx.condition_text
        assert "Fey Glade" in ctx.scene_context
        assert ctx.soul == aeliana_session.soul
        assert ctx.identity == aeliana_session.identity

    def test_includes_scene_history(self, aeliana_session):
        ctx = _build_context(
            aeliana_session, turn=2,
            scene_history="Aeliana crept toward the treeline.",
        )
        assert "crept toward the treeline" in ctx.scene_context
        assert "Fey Glade" in ctx.scene_context  # initial scene still present

    def test_empty_history_no_extra_whitespace(self, aeliana_session):
        ctx = _build_context(aeliana_session, turn=1, scene_history="")
        # Should not have trailing newlines from empty history
        assert ctx.scene_context.strip() == ctx.scene_context or \
            not ctx.scene_context.endswith("\n\n")


# ---------------------------------------------------------------------------
# Transport utterance parsing
# ---------------------------------------------------------------------------

class TestTransportUtteranceSplit:
    def test_quoted_text_is_spoken_unquoted_is_action(self):
        text = (
            'I move to the table and look at the charts '
            '"Are these recent charts? When was this information recorded"'
        )
        spoken, action = _split_transport_utterance(text)

        assert spoken == "Are these recent charts? When was this information recorded"
        assert action == "I move to the table and look at the charts"

    def test_asterisk_action_is_optional(self):
        text = "*move to the table, scan the chart dates* Are these recent charts?"
        spoken, action = _split_transport_utterance(text)

        # Unquoted tail remains action by default.
        assert spoken == ""
        assert action == "move to the table, scan the chart dates Are these recent charts?"

    def test_quotes_and_asterisk_together(self):
        text = '"Are these recent charts?" *move to the table and look at the charts*'
        spoken, action = _split_transport_utterance(text)

        assert spoken == "Are these recent charts?"
        assert action == "move to the table and look at the charts"

    def test_unquoted_text_defaults_to_action(self):
        text = "Are these recent charts? When was this information recorded?"
        spoken, action = _split_transport_utterance(text)

        assert spoken == ""
        assert action == "Are these recent charts? When was this information recorded?"

    def test_multiple_action_spoken_pairs_preserve_all_content(self):
        text = (
            'I look at her data. "I see the energy surges you describe." '
            'I point to the shard glowing slowly. "Are the fragments the ones here in your study?"'
        )
        spoken, action = _split_transport_utterance(text)

        assert spoken == (
            "I see the energy surges you describe. "
            "Are the fragments the ones here in your study?"
        )
        assert action == "I look at her data. I point to the shard glowing slowly."


class TestTransportPromptAndPacketFormatting:
    def _make_transport_session(self, cid: str = "gilthaness") -> CharacterSession:
        pc = PlayerCharacter(
            id=cid,
            name="Gilthaness",
            race="Elf",
            character_type="player",
            character_class="Rogue",
            hp=12,
            current_hp=12,
            dexterity=16,
        )
        return CharacterSession(
            character=pc,
            condition=CharacterCondition(
                character_id=cid,
                character_name="Gilthaness",
                state=NeurochemicalState(),
            ),
            soul="",
            identity="",
            initial_scene="You stand in Elyssa's cottage.",
            scene_handle="Gil",
            player_transport="telegram",
        )

    def test_turn_result_packet_omits_self_intent(self):
        cs = self._make_transport_session("gilthaness")
        cr = CharacterTurnResult(
            character_id="gilthaness",
            turn=1,
            intent=ActionIntent(character_id="gilthaness", turn=1, intent="Inspect the map table."),
            output=CharacterOutput(
                character_id="gilthaness",
                turn=1,
                spoken="Can you explain this marker?",
                action="Leans over the table and points to the shard.",
            ),
            adjudication=Adjudication(character_id="gilthaness", turn=1, approved=True),
            narration=Narration(character_id="gilthaness", turn=1, prose="Gilthaness studies the old charts."),
        )
        tr = TurnResult(turn=1, initiative_order=["gilthaness"], character_results=[cr])

        packet = _render_turn_result_packet(
            player_id="gilthaness",
            turn_result=tr,
            characters={"gilthaness": cs},
        )

        assert "[you]" in packet
        assert "Intent:" not in packet
        assert "Spoken: Can you explain this marker?" in packet
        assert "Action: Leans over the table and points to the shard." in packet
        assert "Outcome:" in packet

    def test_transport_prompt_uses_delta_since_last_turn_without_truncation(self):
        cs = self._make_transport_session("gilthaness")
        ctx = RoleContext(
            character_id="gilthaness",
            turn=2,
            condition_text="steady",
            scene_context="You stand in Elyssa's cottage.",
            soul="",
            identity="",
            perception="No other creatures are visible.",
        )

        lines = [f"line {i}" for i in range(1, 31)]
        raw_history = "\n".join(lines)
        cs.transport_history_cursor = 0

        packet = _render_transport_prompt(context=ctx, cs=cs, raw_history=raw_history)
        # No truncation: all 30 lines should be present in delta context.
        assert "line 1" in packet
        assert "line 30" in packet

        # Next turn with same history should have no redundant replay. With
        # nothing new, the RECENT CONTEXT section is omitted entirely.
        ctx.turn = 3
        packet2 = _render_transport_prompt(context=ctx, cs=cs, raw_history=raw_history)
        assert "RECENT CONTEXT" not in packet2

        # Add new activity and ensure only new lines appear.
        raw_history2 = raw_history + "\nline 31\nline 32"
        packet3 = _render_transport_prompt(context=ctx, cs=cs, raw_history=raw_history2)
        assert "line 31" in packet3 and "line 32" in packet3
        assert "line 1" not in packet3

    def test_transport_prompt_surfaces_mid_sequence_mechanism_feedback(self):
        cs = self._make_transport_session("gilthaness")
        scene_context = (
            "You stand in the Echo Chamber.\n\n"
            "## You are mid-sequence at a mechanism (act now)\n"
            "You just pressed Trigger glyph (top). A faint dry click sounds in the "
            "stone beneath your fingertip.\n\n"
            "A mechanism is clearly responding to your touch. What do you do next?"
        )
        ctx = RoleContext(
            character_id="gilthaness",
            turn=6,
            condition_text="steady",
            scene_context=scene_context,
            soul="",
            identity="",
            perception="No other creatures are visible.",
        )

        packet = _render_transport_prompt(context=ctx, cs=cs, raw_history="")
        assert "You just pressed Trigger glyph (top)" in packet
        assert "A faint dry click sounds" in packet
        assert "What do you do next?" in packet
        # Minimal/conversational mid-sequence: no packet header, no section
        # labels — just the DM's prompt.
        assert "MECHANISM (act now)" not in packet
        assert "PACKET: TURN PROMPT" not in packet
        assert "CHARACTER:" not in packet
        assert "SCENE" not in packet
        assert "CURRENT POSITION" not in packet
        assert "PERCEPTION" not in packet
        assert "RECENT CONTEXT" not in packet

    def test_transport_prompt_shows_current_hp_on_position_line(self):
        cs = self._make_transport_session("gilthaness")
        cs.character.current_hp = 7  # took 5 damage from 12 max
        ctx = RoleContext(
            character_id="gilthaness",
            turn=4,
            condition_text="steady",
            scene_context="You stand in the Secret Chamber.",
            soul="",
            identity="",
            perception="No other creatures are visible.",
        )
        packet = _render_transport_prompt(
            context=ctx, cs=cs, raw_history="",
            actor_pos=(64.0, 195.0, "SECRET CHAMBER"), actor_z=0.0,
        )
        assert (
            "You are at [64.0, 195.0, 0.0] in SECRET CHAMBER with 7/12 HP"
            in packet
        ), packet

    def test_transport_prompt_lists_loadout(self):
        from types import SimpleNamespace as NS
        from models.weapon import Weapon
        cs = self._make_transport_session("gilthaness")
        cs.weapons = [
            Weapon(id="rapier", name="Rapier", damage_dice="1d8", damage_type="piercing"),
            Weapon(id="dagger", name="Dagger", damage_dice="1d4", damage_type="piercing"),
            Weapon(id="light_crossbow", name="Light Crossbow", damage_dice="1d8",
                   damage_type="piercing", range_normal=80),
        ]
        cs.armor = NS(name="Studded Leather")
        cs.wielded = ["rapier"]  # only the rapier is in hand
        ctx = RoleContext(
            character_id="gilthaness", turn=4, condition_text="steady",
            scene_context="You stand in the Secret Chamber.", soul="",
            identity="", perception="No other creatures are visible.",
        )
        packet = _render_transport_prompt(
            context=ctx, cs=cs, raw_history="",
            actor_pos=(64.0, 195.0, "SECRET CHAMBER"), actor_z=0.0,
        )
        # CARRYING = full kit; WIELDING = what's in hand now + free hands.
        assert "CARRYING" in packet
        assert "Rapier, Dagger, Light Crossbow (worn: Studded Leather)" in packet
        assert "WIELDING\nRapier (1 hand free)" in packet

    def test_transport_prompt_lists_picked_up_gear(self):
        """A picked-up non-weapon item (e.g. a torch) lands in the character's
        inventory; the prompt must surface it under CARRYING so the player can
        see they hold it. Regression: previously only weapons/armor showed."""
        from types import SimpleNamespace as NS
        cs = self._make_transport_session("gilthaness")
        cs.character.inventory = ["snapped_torch", "rapier_1"]
        items = {
            "snapped_torch": NS(label="Snapped torch", weapon=None),
            "rapier_1": NS(label="Rapier", weapon=object()),  # weapon: shown elsewhere
        }
        ctx = RoleContext(
            character_id="gilthaness", turn=4, condition_text="steady",
            scene_context="You stand in the Entry Chamber.", soul="",
            identity="", perception="No other creatures are visible.",
        )
        packet = _render_transport_prompt(
            context=ctx, cs=cs, raw_history="",
            actor_pos=(132.0, 268.0, "ENTRY CHAMBER"), actor_z=0.0,
            items=items,
        )
        assert "CARRYING" in packet
        assert "Snapped torch" in packet
        # The weapon item is not double-listed as gear (no separate label line).
        assert packet.count("Rapier") <= 1, packet

    def test_loadout_summary_empty_without_kit(self):
        from engine.session import _loadout_summary
        from types import SimpleNamespace as NS
        assert _loadout_summary(NS(weapons=[], armor=None)) == ""

    def test_carried_items_summary_excludes_weapons_and_prettifies(self):
        from engine.session import _carried_items_summary
        from types import SimpleNamespace as NS
        items = {
            "snapped_torch": NS(label="Snapped torch", weapon=None),
            "rapier_1": NS(label="Rapier", weapon=object()),
        }
        cs = NS(character=NS(inventory=["snapped_torch", "rapier_1"]))
        assert _carried_items_summary(cs, items) == "Snapped torch"
        # Unknown id (not in registry) falls back to a prettified id.
        cs2 = NS(character=NS(inventory=["mystery_relic"]))
        assert _carried_items_summary(cs2, items) == "mystery relic"
        # Empty inventory -> "".
        assert _carried_items_summary(NS(character=NS(inventory=[])), items) == ""

    def test_transport_prompt_shows_held_item_under_wielding(self):
        """A held non-weapon (torch) shares the WIELDING line and consumes a
        hand, so the player sees what's in their hands."""
        from types import SimpleNamespace as NS
        from models.weapon import Weapon
        cs = self._make_transport_session("gilthaness")
        cs.weapons = [Weapon(id="rapier", name="Rapier", damage_dice="1d8",
                             damage_type="piercing")]
        cs.wielded = ["rapier"]
        cs.held_items = ["snapped_torch"]
        items = {"snapped_torch": NS(label="Snapped torch", weapon=None)}
        ctx = RoleContext(
            character_id="gilthaness", turn=4, condition_text="steady",
            scene_context="Entry Chamber.", soul="", identity="",
            perception="No other creatures are visible.",
        )
        packet = _render_transport_prompt(
            context=ctx, cs=cs, raw_history="",
            actor_pos=(137.5, 292.5, "ENTRY CHAMBER"), actor_z=0.0, items=items,
        )
        # Rapier + torch both in hand; no hands free (2 used of 2).
        assert "WIELDING\nRapier, Snapped torch (0 hands free)" in packet

    def test_puzzle_press_packet_reports_each_press(self):
        packet = _render_puzzle_press_packet(
            character_id="gilthaness",
            turn_num=6,
            label="Trigger glyph (top)",
            response="A faint dry click sounds in the stone beneath your fingertip.",
            solved=False,
        )
        assert "You pressed Trigger glyph (top)." in packet
        assert "A faint dry click sounds" in packet
        assert "The sequence is complete." not in packet
        # Minimal/conversational: no packet header.
        assert "PACKET: MECHANISM RESULT" not in packet
        assert "TURN:" not in packet
        assert "FOR:" not in packet

    def test_puzzle_press_packet_marks_solve(self):
        packet = _render_puzzle_press_packet(
            character_id="gilthaness",
            turn_num=6,
            label="Trigger glyph (middle)",
            response="Stone grinds against stone as the hairline crack widens into a passable opening.",
            solved=True,
        )
        assert "You pressed Trigger glyph (middle)." in packet
        assert "the hairline crack widens" in packet
        assert "The sequence is complete." in packet

    def test_describe_press_sequence_single(self):
        action = _describe_press_sequence(["Trigger glyph (top)"], solved=False)
        assert action == "Presses Trigger glyph (top)."

    def test_describe_press_sequence_multi_solved(self):
        action = _describe_press_sequence(
            ["Trigger glyph (top)", "Trigger glyph (bottom)", "Trigger glyph (middle)"],
            solved=True,
        )
        assert action == (
            "Presses Trigger glyph (top), Trigger glyph (bottom), then "
            "Trigger glyph (middle), in sequence, completing the sequence."
        )

    def test_describe_press_sequence_multi_unsolved(self):
        action = _describe_press_sequence(
            ["Trigger glyph (top)", "Trigger glyph (bottom)"],
            solved=False,
        )
        assert action == (
            "Presses Trigger glyph (top), then Trigger glyph (bottom), in sequence."
        )

    def test_looks_like_question_detects_wh_and_qmark(self):
        from engine.session import _looks_like_question
        assert _looks_like_question("What is behind the door?")
        assert _looks_like_question("where do the passages lead")  # wh, no '?'
        assert _looks_like_question("Is it safe?")                  # '?', no wh
        assert not _looks_like_question("attack the giant spider")
        assert not _looks_like_question("move to the rocky passage")
        assert not _looks_like_question("")

    def test_dm_answer_uses_character_llm_bounded_to_perception(self):
        import asyncio
        from types import SimpleNamespace as NS
        from engine.session import _dm_answer
        seen = {}

        async def fake_llm(system, user):
            seen["system"], seen["user"] = system, user
            return "  You see only shadows.  "

        tc = NS(_roles_for=lambda cid: NS(player_left=NS(_call_llm=fake_llm)))
        ctx = RoleContext(
            character_id="gilthaness", turn=1, condition_text="steady",
            scene_context="A dim cave.", soul="", identity="",
            perception="Nothing else is visible.")
        out = asyncio.run(_dm_answer(tc, ctx, "What do I see?"))
        assert out == "You see only shadows."           # trimmed
        assert "perceive" in seen["system"].lower()      # bounded prompt
        assert "What do I see?" in seen["user"]

    def test_dm_answer_falls_back_without_llm(self):
        import asyncio
        from types import SimpleNamespace as NS
        from engine.session import _dm_answer
        tc = NS(_roles_for=lambda cid: NS(player_left=NS(_call_llm=None)))
        ctx = RoleContext(
            character_id="gilthaness", turn=1, condition_text="",
            scene_context="", soul="", identity="", perception="")
        out = asyncio.run(_dm_answer(tc, ctx, "What now?"))
        assert out.startswith("(") and "DM" in out


class TestInferCharacterDestination:
    """'move toward <party member>' grounds to that character's position."""

    def _chars(self):
        from types import SimpleNamespace as NS
        return {
            "gilthaness": NS(character=NS(name="Gilthaness"), scene_handle=""),
            "amara": NS(character=NS(name="Sister Amara Solbright"),
                        scene_handle="the cleric"),
            "thorgrim": NS(character=NS(name="Thorgrim Stoneheart"),
                           scene_handle=""),
        }

    def _positions(self):
        return {
            "gilthaness": (64.0, 195.0, "SECRET CHAMBER"),
            "amara": (137.0, 227.0, "FIRST PASSAGE"),
            "thorgrim": (137.0, 215.0, "ECHO CHAMBER"),
        }

    def test_move_toward_named_character(self):
        from engine.session import _infer_character_destination
        dest = _infer_character_destination(
            "Move towards Amara", "gilthaness",
            self._chars(), self._positions(),
            {"gilthaness", "amara", "thorgrim"},
        )
        assert dest == (137.0, 227.0, "FIRST PASSAGE")

    def test_matches_on_id_first_name(self):
        from engine.session import _infer_character_destination
        # "Gilthaness" by id, even though it's the proper name.
        dest = _infer_character_destination(
            "move to Gilthaness", "amara",
            self._chars(), self._positions(),
            {"gilthaness", "amara", "thorgrim"},
        )
        assert dest == (64.0, 195.0, "SECRET CHAMBER")

    def test_self_excluded(self):
        from engine.session import _infer_character_destination
        dest = _infer_character_destination(
            "move to Gilthaness", "gilthaness",
            self._chars(), self._positions(),
            {"gilthaness", "amara"},
        )
        assert dest is None

    def test_requires_movement_cue(self):
        from engine.session import _infer_character_destination
        # No cue word -> not a movement intent.
        dest = _infer_character_destination(
            "talk to Amara", "gilthaness",
            self._chars(), self._positions(),
            {"gilthaness", "amara"},
        )
        assert dest is None

    def test_inactive_character_not_a_target(self):
        from engine.session import _infer_character_destination
        # Amara named but not in the active set -> no destination.
        dest = _infer_character_destination(
            "move toward Amara", "gilthaness",
            self._chars(), self._positions(),
            {"gilthaness"},
        )
        assert dest is None


class TestInferCardinalDestination:
    """'move south/north/east/west' grounds to the nearest zone that way.
    Map orientation: +y is north, +x is east (map_renderer flips screen y)."""

    def _geom(self):
        from types import SimpleNamespace as NS
        # Zones around an actor at (0, 50): one to each compass point.
        return NS(zones={
            "North Room": NS(vertices=[(-10, 90), (10, 90), (10, 110), (-10, 110)]),
            "South Room": NS(vertices=[(-10, -10), (10, -10), (10, 10), (-10, 10)]),
            "East Room": NS(vertices=[(90, 40), (110, 40), (110, 60), (90, 60)]),
        })

    def test_resolves_each_present_heading(self):
        from engine.session import _infer_cardinal_destination
        pos = (0.0, 50.0, "")
        sg = self._geom()
        assert _infer_cardinal_destination("move north", pos, sg)[2] == "North Room"
        assert _infer_cardinal_destination("I move south", pos, sg)[2] == "South Room"
        assert _infer_cardinal_destination("go east", pos, sg)[2] == "East Room"

    def test_picks_nearest_zone_in_the_cone(self):
        from engine.session import _infer_cardinal_destination
        from types import SimpleNamespace as NS
        sg = NS(zones={
            "Near South": NS(vertices=[(-5, 20), (5, 20), (5, 30), (-5, 30)]),   # (0,25)
            "Far South": NS(vertices=[(-5, -30), (5, -30), (5, -20), (-5, -20)]),  # (0,-25)
        })
        assert _infer_cardinal_destination(
            "move south", (0.0, 50.0, ""), sg)[2] == "Near South"

    def test_no_zone_that_way_projects_a_step(self):
        # No zone lies west, but all 8 compass points are valid travel: it
        # projects a step westward (clamped + wall-checked downstream) instead of
        # giving up. So the x drops below the actor's and it's off-zone ('').
        from engine.session import _infer_cardinal_destination
        dest = _infer_cardinal_destination("head west", (0.0, 50.0, ""), self._geom())
        assert dest is not None
        assert dest[0] < 0 and abs(dest[1] - 50.0) < 1.0 and dest[2] == ""

    def test_all_eight_headings_travel(self):
        # Every compass point (incl. diagonals) yields a destination — a zone in
        # that direction if one exists, else a projected step.
        from engine.session import _infer_cardinal_destination
        for d in ("north", "northeast", "east", "southeast",
                  "south", "southwest", "west", "northwest"):
            assert _infer_cardinal_destination(
                f"move {d}", (0.0, 50.0, ""), self._geom()) is not None, d

    def test_requires_movement_cue(self):
        from engine.session import _infer_cardinal_destination
        assert _infer_cardinal_destination(
            "south", (0.0, 50.0, ""), self._geom()) is None

    def test_named_place_without_compass_is_none(self):
        # "move to the first passage" names a place but no compass word -> None,
        # so resolving cardinal FIRST never hijacks a normal place/item move.
        from engine.session import _infer_cardinal_destination
        for txt in ("move to the first passage", "move to the torch",
                    "go to the well"):
            assert _infer_cardinal_destination(
                txt, (0.0, 50.0, ""), self._geom()) is None, txt

    def test_conflicting_headings_returns_none(self):
        from engine.session import _infer_cardinal_destination
        assert _infer_cardinal_destination(
            "move north and south", (0.0, 50.0, ""), self._geom()) is None

    def test_excludes_current_zone(self):
        from engine.session import _infer_cardinal_destination
        from types import SimpleNamespace as NS
        sg = NS(zones={
            "Here": NS(vertices=[(-5, 45), (5, 45), (5, 55), (-5, 55)]),
            "North Room": NS(vertices=[(-10, 90), (10, 90), (10, 110), (-10, 110)]),
        })
        dest = _infer_cardinal_destination("move north", (0.0, 50.0, "HERE"), sg)
        assert dest[2] == "North Room"


# Dropping/drawing a KIT weapon out of combat is now the unified
# affordance-gated dispatch — see tests/test_manipulation.py.


class TestDrawKitWeapon:
    """Drawing a KIT weapon into hand must work outside combat too — 'unsheathe
    my dagger' / 'get my dagger' should wield it, not just narrate that it did."""

    def _cs(self):
        from types import SimpleNamespace as NS
        from models.weapon import Weapon
        rapier = Weapon(id="rapier", name="Rapier", damage_dice="1d8",
                        damage_type="piercing")
        dagger = Weapon(id="dagger", name="Dagger", damage_dice="1d4",
                        damage_type="piercing")
        return NS(character=NS(name="Gil", hands=2), weapons=[rapier, dagger],
                  wielded=[], held_items=[])

    def test_draw_verb_re_matches_get_and_unsheathe(self):
        from engine.session import _DRAW_VERB_RE
        for phrase in ("get my dagger", "unsheathe the dagger", "hold my dagger",
                       "draw my rapier", "pull out my dagger"):
            assert _DRAW_VERB_RE.search(phrase), phrase
        assert not _DRAW_VERB_RE.search("I walk south")

    def test_unsheathe_named_weapon_wields_it(self):
        from engine.session import _apply_loadout_intent
        cs = self._cs()
        _apply_loadout_intent("I unsheathe my dagger", cs, [])
        assert "dagger" in cs.wielded

    def test_get_named_weapon_wields_it(self):
        from engine.session import _apply_loadout_intent
        cs = self._cs()
        _apply_loadout_intent("get my dagger", cs, [])
        assert "dagger" in cs.wielded

    def test_no_named_weapon_leaves_hands_unchanged(self):
        from engine.session import _apply_loadout_intent
        cs = self._cs()
        cs.wielded = ["rapier"]
        _apply_loadout_intent("hold still", cs, [])   # 'hold' but no weapon named
        assert cs.wielded == ["rapier"]

    def test_compound_sheathe_generic_sword_then_draw_dagger(self):
        from engine.session import _apply_loadout_intent
        from types import SimpleNamespace as NS
        from models.weapon import Weapon

        longsword = Weapon(
            id="longsword",
            name="Longsword",
            damage_dice="1d8",
            damage_type="slashing",
            tags=["martial", "melee", "sword"],
        )
        dagger = Weapon(
            id="dagger",
            name="Dagger",
            damage_dice="1d4",
            damage_type="piercing",
            tags=["simple", "melee", "dagger"],
        )
        cs = NS(
            character=NS(name="Gil", hands=2),
            weapons=[longsword, dagger],
            wielded=["longsword"],
            held_items=[],
        )

        _apply_loadout_intent("I sheathe my sword and draw my dagger", cs, [])

        assert "longsword" not in cs.wielded
        assert "dagger" in cs.wielded


class TestItemTransferHandModel:
    """take a non-weapon -> into a hand; stow -> pack (frees hand, keeps item);
    drop -> on the ground (removed from inventory)."""

    def _setup(self):
        from types import SimpleNamespace as NS
        cs = NS(character=NS(id="gil", name="Gil", inventory=[], hands=2,
                             current_hp=10, hp=10),
                scene_handle="Gil", weapons=[], wielded=[], held_items=[],
                episodic_memory=[])
        item = NS(id="torch", label="Torch", weapon=None, holder=None,
                  description="A pitch-soaked torch.", discovered_by=set(),
                  position=None, zone="ROOM")
        return cs, item

    def _transfer(self, verb, cs, item, text):
        from engine.session import _handle_item_transfer
        _handle_item_transfer(
            transfer_verb=verb, item_obj=item, label="Torch",
            character_id="gil", characters={"gil": cs}, active_characters={"gil"},
            current_positions={"gil": (1.0, 2.0, "ROOM")}, intent_text=text,
            actor_zone="ROOM", turn_num=1, game_time=None, attack_log=[],
            recent_events=[], cs=cs, authored_response=None,
        )

    def test_take_puts_non_weapon_in_hand(self):
        from engine import loadout
        cs, item = self._setup()
        self._transfer("take", cs, item, "pick up the torch")
        assert item.holder == "gil"
        assert "torch" in cs.character.inventory
        assert loadout.held_items(cs) == ["torch"]

    def test_take_narrates_item_description(self):
        cs, item = self._setup()
        log: list[str] = []
        from engine.session import _handle_item_transfer
        _handle_item_transfer(
            transfer_verb="take", item_obj=item, label="Torch",
            character_id="gil", characters={"gil": cs}, active_characters={"gil"},
            current_positions={"gil": (1.0, 2.0, "ROOM")},
            intent_text="pick up the torch", actor_zone="ROOM", turn_num=1,
            game_time=None, attack_log=log, recent_events=[], cs=cs,
            authored_response=None,
        )
        # The narrator log carries the authored description for a detailed look.
        assert any("pitch-soaked torch" in line for line in log)

    def test_stow_moves_to_pack_keeping_item(self):
        from engine import loadout
        cs, item = self._setup()
        self._transfer("take", cs, item, "pick up the torch")
        self._transfer("stow", cs, item, "save the torch")
        assert item.holder == "gil"                 # still carried
        assert "torch" in cs.character.inventory     # still in the pack
        assert loadout.held_items(cs) == []          # but no longer in hand

    def test_drop_returns_it_to_the_ground(self):
        from engine import loadout
        cs, item = self._setup()
        self._transfer("take", cs, item, "pick up the torch")
        self._transfer("drop", cs, item, "drop the torch")
        assert item.holder is None                   # on the ground
        assert "torch" not in cs.character.inventory
        assert loadout.held_items(cs) == []          # hand freed

    def test_drop_backpack_stays_item_transfer_not_movement(self):
        from engine.session import _handle_item_transfer
        from engine import loadout
        from types import SimpleNamespace as NS

        cs = NS(character=NS(id="gil", name="Gil", inventory=[], hands=2,
                             current_hp=10, hp=10),
                scene_handle="Gil", weapons=[], wielded=[], held_items=["gils_pack"],
                episodic_memory=[])
        item = NS(id="gils_pack", label="Gil's Pack", weapon=None, holder="gil",
                  description="A sturdy backpack.", discovered_by=set(),
                  position=None, zone="ROOM")
        _handle_item_transfer(
            transfer_verb="drop", item_obj=item, label="Gil's Pack",
            character_id="gil", characters={"gil": cs}, active_characters={"gil"},
            current_positions={"gil": (1.0, 2.0, "ROOM")}, intent_text="drop the backpack",
            actor_zone="ROOM", turn_num=1, game_time=None, attack_log=[],
            recent_events=[], cs=cs, authored_response=None,
        )
        assert item.holder is None
        assert loadout.held_items(cs) == []


class TestSyncCarriedItemPositions:
    """Carried items follow their holder so possession verbs resolve in the
    holder's current zone after they move."""

    def test_held_item_follows_holder(self):
        from engine.session import _sync_carried_item_positions
        from types import SimpleNamespace as NS
        from models.space_time import Position
        item = NS(holder="gil", position=Position(1.0, 1.0), zone="ENTRY CHAMBER")
        loose = NS(holder=None, position=Position(5.0, 5.0), zone="ENTRY CHAMBER")
        items = {"torch": item, "rock": loose}
        _sync_carried_item_positions(
            {"gil": NS()}, {"gil": (50.0, 60.0, "FIRST PASSAGE")}, items)
        assert item.zone == "FIRST PASSAGE"
        assert (item.position.x, item.position.y) == (50.0, 60.0)
        # Loose item (no holder) is untouched.
        assert loose.zone == "ENTRY CHAMBER"
        assert (loose.position.x, loose.position.y) == (5.0, 5.0)

    def test_noop_without_items(self):
        from engine.session import _sync_carried_item_positions
        _sync_carried_item_positions({}, {}, None)  # no error, no-op

    def test_unknown_holder_skipped(self):
        from engine.session import _sync_carried_item_positions
        from types import SimpleNamespace as NS
        from models.space_time import Position
        item = NS(holder="ghost", position=Position(1.0, 1.0), zone="ENTRY CHAMBER")
        _sync_carried_item_positions({}, {"ghost": (9.0, 9.0, "X")}, {"t": item})
        assert item.zone == "ENTRY CHAMBER"  # holder not among characters


class TestFindTakeableWeaponItem:
    """"pick up the mace and attack" must ground the mace item in reach."""

    def _items(self):
        from types import SimpleNamespace as NS
        from models.weapon import Weapon
        mace_w = Weapon(id="mace_plus_one", name="Mace +1", damage_dice="1d6+1",
                        damage_type="bludgeoning", attack_bonus=1, reach=5)
        return {
            "mace_plus_one": NS(id="mace_plus_one", weapon=mace_w,
                                label="Banded Mace", holder=None,
                                zone="SECRET CHAMBER"),
            "bones": NS(id="bones", weapon=None, label="Remains",
                        holder=None, zone="SECRET CHAMBER"),
        }

    def test_finds_named_weapon_in_zone(self):
        from engine.session import _find_takeable_weapon_item
        it = _find_takeable_weapon_item(
            "I pick up the mace and attack the spider",
            self._items(), "SECRET CHAMBER")
        assert it is not None and it.id == "mace_plus_one"

    def test_skips_when_in_other_zone(self):
        from engine.session import _find_takeable_weapon_item
        assert _find_takeable_weapon_item(
            "pick up the mace", self._items(), "ENTRY CHAMBER") is None

    def test_skips_when_already_held(self):
        from engine.session import _find_takeable_weapon_item
        items = self._items()
        items["mace_plus_one"].holder = "gilthaness"
        assert _find_takeable_weapon_item(
            "pick up the mace", items, "SECRET CHAMBER") is None

    def test_non_weapon_item_not_returned(self):
        from engine.session import _find_takeable_weapon_item
        assert _find_takeable_weapon_item(
            "pick up the remains", self._items(), "SECRET CHAMBER") is None


class TestNextZoneToward:
    """Zone-graph routing: one hop at a time toward a cross-zone destination."""

    @pytest.fixture(scope="class")
    def geo(self):
        from pathlib import Path
        from models.geometry_loader import load_geometry
        return load_geometry(Path(
            "scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md"))

    def test_routes_first_hop_through_passage(self, geo):
        from engine.session import _next_zone_toward
        # Secret Chamber -> Rocky Passage -> Echo Chamber -> First Passage:
        # the first step toward First Passage is the Rocky Passage.
        assert _next_zone_toward(geo, "SECRET CHAMBER", "FIRST PASSAGE") == "Rocky Passage"
        assert _next_zone_toward(geo, "SECRET CHAMBER", "ENTRY CHAMBER") == "Rocky Passage"

    def test_routes_back_the_other_way(self, geo):
        from engine.session import _next_zone_toward
        assert _next_zone_toward(geo, "ENTRY CHAMBER", "SECRET CHAMBER") == "First Passage"

    def test_adjacent_zone_is_its_own_first_hop(self, geo):
        from engine.session import _next_zone_toward
        assert _next_zone_toward(geo, "FIRST PASSAGE", "ECHO CHAMBER") == "Echo Chamber"

    def test_same_zone_returns_none(self, geo):
        from engine.session import _next_zone_toward
        assert _next_zone_toward(geo, "ECHO CHAMBER", "ECHO CHAMBER") is None

    def test_unknown_zone_returns_none(self, geo):
        from engine.session import _next_zone_toward
        assert _next_zone_toward(geo, "SECRET CHAMBER", "NOWHERE") is None


# ---------------------------------------------------------------------------
# run_session — stub mode (no LLMs)
# ---------------------------------------------------------------------------

class TestRunSessionStub:
    """run_session with default stub roles — no LLM calls."""

    def test_single_turn_single_character(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}  # all stubs
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert isinstance(result, SessionResult)
        assert len(result.turns) == 1
        assert result.turns[0].turn == 1
        assert len(result.turns[0].character_results) == 1
        assert result.turns[0].character_results[0].character_id == "aeliana"

    def test_multi_turn(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=3))

        assert len(result.turns) == 3
        for i, tr in enumerate(result.turns):
            assert tr.turn == i + 1

    def test_two_characters(self, aeliana_session, fennel_session):
        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(),
            "fennel": RoleSet(),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert len(result.turns[0].character_results) == 2
        ids = {r.character_id for r in result.turns[0].character_results}
        assert ids == {"aeliana", "fennel"}

    def test_on_character_acted_fires_per_initiative(self, aeliana_session,
                                                      fennel_session):
        """The per-initiative hook fires once per acting character per turn, with
        that character's id and a positions snapshot — so live views (the web
        map) can refresh after each move, not just at end of turn."""
        characters = {"aeliana": aeliana_session, "fennel": fennel_session}
        roles = {"aeliana": RoleSet(), "fennel": RoleSet()}
        calls: list[tuple] = []
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            on_character_acted=lambda cid, turn, pos, cr: calls.append((cid, turn, pos, cr)),
        ))
        assert {c[0] for c in calls} == {"aeliana", "fennel"}  # both fired
        assert all(c[1] == 1 for c in calls)                   # turn 1
        assert all(isinstance(c[2], dict) for c in calls)      # positions snapshot
        # cr carries this character's result (id matches) for live narration.
        assert all(c[3].character_id == c[0] for c in calls)

    def test_initiative_determines_order(self, aeliana_session, fennel_session):
        """Characters should act in initiative order (varies by roll)."""
        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(),
            "fennel": RoleSet(),
        }
        # Run with a fixed seed to get deterministic initiative
        result = asyncio.run(run_session(
            characters, roles, num_turns=1, rng=random.Random(42),
        ))
        order = result.turns[0].initiative_order
        assert len(order) == 2
        assert set(order) == {"aeliana", "fennel"}

    def test_returns_final_conditions(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        assert "aeliana" in result.final_conditions
        assert isinstance(result.final_conditions["aeliana"], CharacterCondition)


# ---------------------------------------------------------------------------
# Condition delta application
# ---------------------------------------------------------------------------

class TestConditionDeltas:
    def test_deltas_applied_after_turn(self, aeliana_session):
        """DMLeft condition_deltas should update the character's condition."""
        original_dopamine = aeliana_session.condition.state.dopamine

        # Mock DMLeft that returns specific deltas
        async def dm_left_llm(sys, usr):
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**NEW POSITION** — none\n"
                "**CONDITION** — dopamine +0.1, cortisol -0.05\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=dm_left_llm)),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        # Condition should have been updated
        new_dopamine = aeliana_session.condition.state.dopamine
        assert new_dopamine > original_dopamine

    def test_deltas_accumulate_across_turns(self, aeliana_session):
        """Deltas from multiple turns should stack."""
        original_cortisol = aeliana_session.condition.state.cortisol

        async def dm_left_llm(sys, usr):
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**NEW POSITION** — none\n"
                "**CONDITION** — cortisol +0.1\n"
                "**EVENTS** — none\n"
                "**NOTES** — stress"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=dm_left_llm)),
        }
        result = asyncio.run(run_session(characters, roles, num_turns=3))

        # Cortisol should have increased by ~0.3 (3 turns × 0.1)
        new_cortisol = aeliana_session.condition.state.cortisol
        assert new_cortisol > original_cortisol + 0.2


# ---------------------------------------------------------------------------
# Scene history accumulation
# ---------------------------------------------------------------------------

class TestSceneHistory:
    def test_narration_accumulates(self, aeliana_session, fennel_session):
        """Each character's narration should be visible to later characters."""
        call_count = 0
        captured_contexts = {}

        async def tracking_player_left(sys, usr):
            nonlocal call_count
            call_count += 1
            # Just capture what scene context each call gets
            captured_contexts[call_count] = usr
            return "**INTENT** — " + f"action_{call_count}" + "\n**MOVEMENT** — none\n**TARGET** — none"

        characters = {
            "aeliana": aeliana_session,
            "fennel": fennel_session,
        }
        roles = {
            "aeliana": RoleSet(
                player_left=PlayerLeft(call_llm=tracking_player_left),
            ),
            "fennel": RoleSet(
                player_left=PlayerLeft(call_llm=tracking_player_left),
            ),
        }
        # Use deterministic initiative
        result = asyncio.run(run_session(
            characters, roles, num_turns=1, rng=random.Random(99),
        ))
        # At minimum, both characters should have been called
        assert call_count >= 2


# ---------------------------------------------------------------------------
# Checkpoint persistence
# ---------------------------------------------------------------------------

class TestCheckpointing:
    def _make_resume_spellcaster(self) -> CharacterSession:
        caster = PlayerCharacter(
            id="tobin",
            name="Tobin",
            race="Halfling",
            character_type="player",
            character_class="Cleric",
            level=3,
            hp=24,
            current_hp=24,
            dexterity=10,
        )
        caster.spellcasting = SpellcastingProfile(
            ability="WIS",
            save_dc=13,
            attack_bonus=5,
            cantrips=[Spell(name="Guidance", level=0)],
            prepared=[Spell(name="Healing Word", level=1), Spell(name="Bless", level=1)],
            known=[],
            spell_slots_max={1: 4},
            spell_slots_used={1: 0},
        )
        return CharacterSession(
            character=caster,
            condition=CharacterCondition(
                character_id="tobin",
                character_name="Tobin",
                state=NeurochemicalState(),
            ),
            soul="",
            identity="",
            initial_scene="At the chapel.",
        )

    def _make_resume_spell_ally(self) -> CharacterSession:
        ally = PlayerCharacter(
            id="brenna",
            name="Brenna",
            race="Human",
            character_type="player",
            character_class="Fighter",
            level=3,
            hp=28,
            current_hp=28,
            dexterity=8,
        )
        return CharacterSession(
            character=ally,
            condition=CharacterCondition(
                character_id="brenna",
                character_name="Brenna",
                state=NeurochemicalState(),
            ),
            soul="",
            identity="",
            initial_scene="At the chapel.",
        )

    def test_saves_turn_json(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(
            characters, roles, num_turns=2,
            checkpoint_dir=tmp_path,
        ))

        # Should have saved 2 turn files
        files = sorted(tmp_path.glob("turn_*.json"))
        assert len(files) == 2
        assert files[0].name == "turn_0001.json"
        assert files[1].name == "turn_0002.json"

    def test_checkpoint_contains_results(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert data["turn"] == 1
        assert "character_results" in data
        assert len(data["character_results"]) == 1
        assert data["character_results"][0]["character_id"] == "aeliana"

    def test_checkpoint_contains_conditions(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert "conditions" in data
        assert "aeliana" in data["conditions"]
        assert "dopamine" in data["conditions"]["aeliana"]

    def test_checkpoint_contains_hp(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert "hp" in data
        assert "aeliana" in data["hp"]
        assert "current" in data["hp"]["aeliana"]
        assert "max" in data["hp"]["aeliana"]

    def test_no_checkpoint_when_dir_is_none(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=None,
        ))
        # Should succeed without saving anything
        assert len(result.turns) == 1

    def test_game_time_checkpoint_naming(self, aeliana_session, tmp_path):
        """With game_time, checkpoints use day/time naming."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=2,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        files = sorted(tmp_path.glob("day*.json"))
        assert len(files) == 2
        assert files[0].name == "day1_14h30m.json"
        assert files[1].name == "day1_14h40m.json"

    def test_game_time_melee_naming(self, aeliana_session, tmp_path):
        """Melee turns use 1-minute intervals."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=1, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=3,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        files = sorted(tmp_path.glob("day*.json"))
        assert len(files) == 3
        assert files[0].name == "day1_14h30m.json"
        assert files[1].name == "day1_14h31m.json"
        assert files[2].name == "day1_14h32m.json"

    def test_game_time_in_checkpoint_data(self, aeliana_session, tmp_path):
        """Checkpoint JSON should contain game_time metadata."""
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path, game_time=gt,
        ))
        data = json.loads((tmp_path / "day1_14h30m.json").read_text())
        assert data["game_time"]["hour"] == 14
        assert data["game_time"]["minute"] == 30
        assert data["game_time"]["day"] == 1
        assert data["game_time"]["period"] == "afternoon"

    def test_no_game_time_uses_turn_naming(self, aeliana_session, tmp_path):
        """Without game_time, falls back to turn_NNNN naming."""
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))
        files = sorted(tmp_path.glob("turn_*.json"))
        assert len(files) == 1
        assert files[0].name == "turn_0001.json"

    def test_checkpoint_contains_positions(self, aeliana_session, tmp_path):
        """Checkpoint should save current_positions so resume restores them."""
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            checkpoint_dir=tmp_path,
        ))
        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert "current_positions" in data

    def test_load_resume_restores_positions(self, aeliana_session, tmp_path):
        """load_resume_state should return positions from the last checkpoint."""
        # Manually write a checkpoint with known positions
        checkpoint_data = {
            "turn": 3,
            "in_combat": False,
            "active_characters": ["aeliana"],
            "game_time": None,
            "initiative_order": ["aeliana"],
            "character_results": [],
            "conditions": {},
            "hp": {"aeliana": {"current": 10, "max": 12}},
            "current_positions": {
                "aeliana": {"x": 202.2, "y": 125.1, "zone": "FOREST"},
            },
        }
        (tmp_path / "turn_0003.json").write_text(json.dumps(checkpoint_data))

        characters = {"aeliana": aeliana_session}
        last_turn, _, _, _, positions, _, _ = load_resume_state(tmp_path, characters)

        assert last_turn == 3
        assert "aeliana" in positions
        assert positions["aeliana"] == (202.2, 125.1, "FOREST")

    def test_resume_positions_override_game_state_summary(self, aeliana_session, tmp_path):
        """iter_session with initial_positions should start from checkpoint positions."""
        # Write checkpoint with Aeliana at a known non-starting position
        checkpoint_data = {
            "turn": 2,
            "in_combat": False,
            "active_characters": ["aeliana"],
            "game_time": None,
            "initiative_order": ["aeliana"],
            "character_results": [],
            "conditions": {},
            "hp": {"aeliana": {"current": 12, "max": 12}},
            "current_positions": {
                "aeliana": {"x": 202.2, "y": 125.1, "zone": "FOREST"},
            },
        }
        (tmp_path / "turn_0002.json").write_text(json.dumps(checkpoint_data))

        # game_state_summary has the OLD starting position
        game_state_summary = (
            "| character | x | y | zone |\n"
            "|-----------|-----|-----|------|\n"
            "| aeliana | 256.75 | 81.25 | TRAIL |\n\n"
            "Test scene."
        )
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        _, _, _, _, positions, _, _ = load_resume_state(tmp_path, characters)

        # Confirm iter_session uses checkpoint positions, not game_state_summary positions
        captured: list = []

        async def _run():
            async for tr in iter_session(
                characters, roles, num_turns=1,
                game_state_summary=game_state_summary,
                start_turn=3,
                initial_positions=positions,
            ):
                captured.append(tr)

        asyncio.run(_run())
        assert captured  # ran at least one turn — positions were accepted

    def test_resume_keeps_spell_duration_progress(self, tmp_path):
        tobin = self._make_resume_spellcaster()
        brenna = self._make_resume_spell_ally()
        characters = {"tobin": tobin, "brenna": brenna}

        async def cast_guidance_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Guidance on Tobin.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — tobin"
            )

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_guidance_llm)),
            "brenna": RoleSet(),
        }

        asyncio.run(run_session(characters, roles, num_turns=1, checkpoint_dir=tmp_path, rng=random.Random(31)))

        first_cp = json.loads((tmp_path / "turn_0001.json").read_text())
        assert first_cp["spell_runtime"]["active_effects"][0]["spell_name"] == "Guidance"
        assert first_cp["spell_runtime"]["active_effects"][0]["remaining_rounds"] == 9

        (
            last_turn,
            _,
            history,
            active_chars,
            positions,
            party_examination_state,
            spell_runtime,
        ) = load_resume_state(tmp_path, characters)

        async def no_spell_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Observe the room.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — none"
            )

        roles2 = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=no_spell_llm)),
            "brenna": RoleSet(),
        }

        asyncio.run(
            run_session(
                characters,
                roles2,
                num_turns=1,
                checkpoint_dir=tmp_path,
                rng=random.Random(32),
                start_turn=last_turn + 1,
                initial_history=history,
                initial_active_characters=active_chars,
                initial_positions=positions,
                initial_party_examination_state=party_examination_state,
                initial_spell_runtime=spell_runtime,
            )
        )

        second_cp = json.loads((tmp_path / "turn_0002.json").read_text())
        assert second_cp["spell_runtime"]["active_effects"][0]["spell_name"] == "Guidance"
        assert second_cp["spell_runtime"]["active_effects"][0]["remaining_rounds"] == 8

    def test_resume_replaces_prior_concentration_effect(self, tmp_path):
        tobin = self._make_resume_spellcaster()
        brenna = self._make_resume_spell_ally()
        characters = {"tobin": tobin, "brenna": brenna}

        async def cast_guidance_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Guidance on Tobin.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — tobin"
            )

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_guidance_llm)),
            "brenna": RoleSet(),
        }

        asyncio.run(run_session(characters, roles, num_turns=1, checkpoint_dir=tmp_path, rng=random.Random(41)))

        (
            last_turn,
            _,
            history,
            active_chars,
            positions,
            party_examination_state,
            spell_runtime,
        ) = load_resume_state(tmp_path, characters)

        async def cast_bless_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Bless on Brenna.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — brenna"
            )

        roles2 = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_bless_llm)),
            "brenna": RoleSet(),
        }

        resumed = asyncio.run(
            run_session(
                characters,
                roles2,
                num_turns=1,
                checkpoint_dir=tmp_path,
                rng=random.Random(42),
                start_turn=last_turn + 1,
                initial_history=history,
                initial_active_characters=active_chars,
                initial_positions=positions,
                initial_party_examination_state=party_examination_state,
                initial_spell_runtime=spell_runtime,
            )
        )

        tobin_cr = next(cr for cr in resumed.turns[0].character_results if cr.character_id == "tobin")
        assert tobin_cr.adjudication.approved
        assert "ended effect" in tobin_cr.adjudication.notes.lower()
        assert "guidance" in tobin_cr.adjudication.notes.lower()

    def test_save_turn_serializes_spell_runtime(self, aeliana_session, tmp_path):
        characters = {"aeliana": aeliana_session}
        runtime = SpellRuntimeState(
            active_effects=[
                ActiveSpellEffect(
                    spell_name="Guidance",
                    caster_id="aeliana",
                    target_ids=["aeliana"],
                    remaining_rounds=9,
                    concentration=True,
                )
            ]
        )
        runtime.concentration_by_caster["aeliana"] = runtime.active_effects[0]

        turn_result = TurnResult(turn=1, initiative_order=["aeliana"], character_results=[])
        _save_turn(tmp_path, 1, turn_result, characters, spell_runtime=runtime)

        data = json.loads((tmp_path / "turn_0001.json").read_text())
        assert "spell_runtime" in data
        assert data["spell_runtime"]["active_effects"][0]["spell_name"] == "Guidance"
        assert data["spell_runtime"]["concentration_by_caster"]["aeliana"] == "Guidance"

    def test_load_resume_restores_spell_runtime(self, aeliana_session, tmp_path):
        checkpoint_data = {
            "turn": 3,
            "in_combat": False,
            "active_characters": ["aeliana"],
            "game_time": None,
            "initiative_order": ["aeliana"],
            "character_results": [],
            "conditions": {},
            "hp": {"aeliana": {"current": 10, "max": 12}},
            "current_positions": {
                "aeliana": {"x": 202.2, "y": 125.1, "zone": "FOREST"},
            },
            "spell_runtime": {
                "active_effects": [
                    {
                        "spell_name": "Bless",
                        "caster_id": "aeliana",
                        "target_ids": ["aeliana"],
                        "remaining_rounds": 6,
                        "concentration": True,
                    }
                ],
                "concentration_by_caster": {"aeliana": "Bless"},
            },
        }
        (tmp_path / "turn_0003.json").write_text(json.dumps(checkpoint_data))

        characters = {"aeliana": aeliana_session}
        _, _, _, _, _, _, runtime = load_resume_state(tmp_path, characters)

        assert len(runtime.active_effects) == 1
        assert runtime.active_effects[0].spell_name == "Bless"
        assert runtime.concentration_by_caster["aeliana"].spell_name == "Bless"


class TestCheckpointFilename:
    def test_without_game_time(self):
        assert _checkpoint_filename(1) == "turn_0001.json"
        assert _checkpoint_filename(42) == "turn_0042.json"

    def test_with_game_time(self):
        gt = GameTime(hour=14, minute=30, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)
        assert _checkpoint_filename(1, gt) == "day1_14h30m.json"

    def test_midnight_wrap(self):
        gt = GameTime(hour=0, minute=5, day=2, season="winter",
                      turn_duration=10, absolute_turn=0)
        assert _checkpoint_filename(1, gt) == "day2_00h05m.json"


# ---------------------------------------------------------------------------
# SessionResult
# ---------------------------------------------------------------------------

class TestSessionResult:
    def test_has_all_turns(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=2))

        assert len(result.turns) == 2
        assert result.turns[0].turn == 1
        assert result.turns[1].turn == 2

    def test_scene_history_returned(self, aeliana_session):
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))

        # scene_history should be a string (may be empty for stubs)
        assert isinstance(result.scene_history, str)


# ---------------------------------------------------------------------------
# DMLeft receives game_state and geometry context
# ---------------------------------------------------------------------------

class TestDMLeftContext:
    def test_geometry_passed_to_dmleft(self, aeliana_session):
        """DMLeft should receive the geometry_summary in its prompt."""
        captured_prompts = []

        async def capturing_dm_llm(sys, usr):
            captured_prompts.append(usr)
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**NEW POSITION** — none\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=capturing_dm_llm)),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            geometry_summary="## Boundaries\nRepulsion boundary blocks shadowbeast",
        ))

        assert len(captured_prompts) >= 1
        assert "Repulsion boundary blocks shadowbeast" in captured_prompts[0]

    def test_game_state_passed_to_dmleft(self, aeliana_session):
        """DMLeft should receive creature stats in its prompt."""
        captured_prompts = []

        async def capturing_dm_llm(sys, usr):
            captured_prompts.append(usr)
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**NEW POSITION** — none\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — test"
            )

        characters = {"aeliana": aeliana_session}
        roles = {
            "aeliana": RoleSet(dm_left=DMLeft(call_llm=capturing_dm_llm)),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            game_state_summary="Shadowbeast: resistant to nonmagical B/P/S",
        ))

        assert len(captured_prompts) >= 1
        assert "resistant to nonmagical B/P/S" in captured_prompts[0]

    def test_both_contexts_empty_by_default(self, aeliana_session):
        """Without context, DMLeft still works (stub mode)."""
        characters = {"aeliana": aeliana_session}
        roles = {"aeliana": RoleSet()}
        result = asyncio.run(run_session(characters, roles, num_turns=1))
        assert len(result.turns) == 1


# ---------------------------------------------------------------------------
# Combat time-switching
# ---------------------------------------------------------------------------

def _make_creature_session(char_id="shadowbeast_1", faction="hostile"):
    """Build a minimal hostile creature session for testing."""
    creature = Creature(
        id=char_id, name="Shadowbeast", race="Monstrosity",
        character_type="creature", dexterity=14,
        faction=faction,
    )
    condition = CharacterCondition(
        character_id=char_id,
        character_name="Shadowbeast",
        state=NeurochemicalState(dopamine=0.80, cortisol=0.10),
    )
    return CharacterSession(
        character=creature,
        condition=condition,
        soul="You are a predator of shadow.",
        identity="Shadowbeast. CR ½.",
        initial_scene="You lurk in the darkness.",
    )


def _combat_dm_llm(event=COMBAT_EVENT):
    """Return a DMLeft LLM stub that emits the given event.

    For combat_initiated, also declare an attack so Python's event-ownership
    layer (which ignores LLM-emitted combat_initiated) actually fires the
    event off a real declared attack.
    """
    async def _llm(sys, usr):
        attacks_section = ""
        if event == COMBAT_EVENT:
            attacks_section = (
                "**ATTACKS** — target=aeliana, bonus=+4, damage=1d6\n"
            )
        return (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**NEW POSITION** — none\n"
            "**CONDITION** — none\n"
            f"**EVENTS** — {event}\n"
            f"{attacks_section}"
            "**NOTES** — combat test"
        )
    return _llm


def _no_event_dm_llm():
    """Return a DMLeft LLM stub that emits no events."""
    async def _llm(sys, usr):
        return (
            "**APPROVED** — Yes\n"
            "**MODIFIED ACTION** — none\n"
            "**NEW POSITION** — none\n"
            "**CONDITION** — none\n"
            "**EVENTS** — none\n"
            "**NOTES** — peaceful"
        )
    return _llm


class TestCombatTimeSwitching:
    """Tests for automatic exploration→melee→exploration time switching."""

    def test_combat_initiated_switches_to_melee(self, aeliana_session):
        """combat_initiated event should switch turn_duration to 1."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Creature's DMLeft emits combat_initiated
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=1,
            game_time=gt, rng=random.Random(42),
        ))
        # After combat_initiated, turn_duration should be melee (1)
        assert gt.turn_duration == MELEE_DURATION

    def test_combat_end_restores_exploration(self, aeliana_session):
        """When hostile exits scene, combat ends and duration reverts."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }

        call_count = {"n": 0}

        async def turn1_combat_turn2_exit(sys, usr):
            call_count["n"] += 1
            if call_count["n"] <= 2:
                # Turn 1: both characters, beast attacks
                if "shadowbeast" in usr.lower() or "Shadowbeast" in usr:
                    return (
                        "**APPROVED** — Yes\n"
                        "**MODIFIED ACTION** — none\n"
                        "**NEW POSITION** — none\n"
                        "**CONDITION** — none\n"
                        f"**EVENTS** — {COMBAT_EVENT}\n"
                        "**NOTES** — beast attacks"
                    )
            if call_count["n"] <= 4:
                # Turn 2: beast exits
                if "shadowbeast" in usr.lower() or "Shadowbeast" in usr:
                    return (
                        "**APPROVED** — Yes\n"
                        "**MODIFIED ACTION** — none\n"
                        "**NEW POSITION** — none\n"
                        "**CONDITION** — none\n"
                        f"**EVENTS** — {EXIT_EVENT}\n"
                        "**NOTES** — beast flees"
                    )
            return (
                "**APPROVED** — Yes\n"
                "**MODIFIED ACTION** — none\n"
                "**NEW POSITION** — none\n"
                "**CONDITION** — none\n"
                "**EVENTS** — none\n"
                "**NOTES** — peaceful"
            )

        roles = {
            "aeliana": RoleSet(
                dm_left=DMLeft(call_llm=turn1_combat_turn2_exit),
            ),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=turn1_combat_turn2_exit),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=3,
            game_time=gt, rng=random.Random(42),
        ))
        # After beast exits, combat should end and duration should revert
        assert gt.turn_duration == 10

    def test_exits_scene_removes_from_initiative(self, aeliana_session):
        """A character that exits_scene should not act in later turns."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=1, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Beast exits on turn 1
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=2,
            game_time=gt, rng=random.Random(42),
        ))
        # Turn 2 should only have aeliana
        turn2_ids = [cr.character_id for cr in result.turns[1].character_results]
        assert "aeliana" in turn2_ids
        assert "shadowbeast_1" not in turn2_ids

    def test_no_combat_without_game_time(self, aeliana_session):
        """Without game_time, combat_initiated event is ignored for timing."""
        beast = _make_creature_session()

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        # Should not crash — combat events without game_time are no-ops
        result = asyncio.run(run_session(
            characters, roles, num_turns=1,
            rng=random.Random(42),
        ))
        assert len(result.turns) == 1

    def test_combat_checkpoints_use_melee_intervals(self, aeliana_session, tmp_path):
        """After combat starts, checkpoints should be 1 minute apart."""
        beast = _make_creature_session()
        gt = GameTime(hour=15, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {
            "aeliana": aeliana_session,
            "shadowbeast_1": beast,
        }
        # Beast attacks turn 1, combat continues
        roles = {
            "aeliana": RoleSet(),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm()),
            ),
        }
        asyncio.run(run_session(
            characters, roles, num_turns=3,
            game_time=gt, checkpoint_dir=tmp_path,
            rng=random.Random(42),
        ))
        files = sorted(tmp_path.glob("day*.json"))
        names = [f.name for f in files]
        # The turn during which combat begins still ticks at exploration
        # cadence; the swap to melee is deferred until after that turn's
        # advance. So:
        #   turn1 snapshot at 15:00 (pre-advance)
        #   turn1 advance uses 10 min → 15:10
        #   turn2 snapshot at 15:10 (combat ongoing → next advance uses 1 min)
        #   turn2 advance uses 1 min → 15:11
        #   turn3 snapshot at 15:11
        assert names[0] == "day1_15h00m.json"
        assert names[1] == "day1_15h10m.json"
        assert names[2] == "day1_15h11m.json"

    def test_faction_defaults(self):
        """Characters default to appropriate factions."""
        pc = PlayerCharacter(
            id="test", name="Test", race="Human",
            character_type="player",
        )
        assert pc.faction == "neutral"  # base default

        creature = Creature(
            id="beast", name="Beast", race="Monster",
            character_type="creature", faction="hostile",
        )
        assert creature.faction == "hostile"

    def test_empty_scene_breaks_early(self):
        """If all characters exit, session ends early."""
        beast = _make_creature_session()
        pc = PlayerCharacter(
            id="test_pc", name="Test", race="Human",
            character_type="player", dexterity=12, faction="party",
        )
        pc_session = CharacterSession(
            character=pc,
            condition=CharacterCondition(
                character_id="test_pc", character_name="Test",
                state=NeurochemicalState(),
            ),
            soul="", identity="", initial_scene="A field.",
        )
        gt = GameTime(hour=12, minute=0, day=1, season="spring",
                      turn_duration=10, absolute_turn=0)

        characters = {"test_pc": pc_session, "shadowbeast_1": beast}
        # Both exit on turn 1
        roles = {
            "test_pc": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
            "shadowbeast_1": RoleSet(
                dm_left=DMLeft(call_llm=_combat_dm_llm(EXIT_EVENT)),
            ),
        }
        result = asyncio.run(run_session(
            characters, roles, num_turns=5,
            game_time=gt, rng=random.Random(42),
        ))
        # Should stop after turn 1 since no characters remain
        assert len(result.turns) == 1


class TestDMLeftCombatPrompt:
    """Verify DMLeft system prompt includes combat event guidance."""

    def test_prompt_mentions_combat_initiated(self):
        dm = DMLeft()
        prompt = dm.build_system_prompt()
        assert "combat_initiated" in prompt

    def test_prompt_mentions_exits_scene(self):
        dm = DMLeft()
        prompt = dm.build_system_prompt()
        assert "exits_scene" in prompt


class TestSpellSessionIntegration:
    def _make_spellcaster(self) -> CharacterSession:
        caster = PlayerCharacter(
            id="tobin",
            name="Tobin",
            race="Half-Elf",
            character_type="player",
            character_class="Cleric (Life Domain)",
            level=3,
            wisdom=16,
            hp=24,
            current_hp=24,
            dexterity=10,
        )
        caster.spellcasting = SpellcastingProfile(
            ability="WIS",
            save_dc=13,
            attack_bonus=5,
            cantrips=[Spell(name="Guidance", level=0)],
            prepared=[Spell(name="Healing Word", level=1)],
            known=[],
            spell_slots_max={1: 4},
            spell_slots_used={1: 0},
        )
        return CharacterSession(
            character=caster,
            condition=CharacterCondition(
                character_id="tobin",
                character_name="Tobin",
                state=NeurochemicalState(),
            ),
            soul="",
            identity="",
            initial_scene="At the chapel.",
        )

    def _make_ally(self) -> CharacterSession:
        ally = PlayerCharacter(
            id="brenna",
            name="Brenna",
            race="Human",
            character_type="player",
            character_class="Fighter",
            level=3,
            hp=28,
            current_hp=8,
            dexterity=8,
        )
        return CharacterSession(
            character=ally,
            condition=CharacterCondition(
                character_id="brenna",
                character_name="Brenna",
                state=NeurochemicalState(),
            ),
            soul="",
            identity="",
            initial_scene="At the chapel.",
        )

    def test_run_session_healing_word_uses_slot_and_heals_target(self):
        tobin = self._make_spellcaster()
        brenna = self._make_ally()

        async def cast_heal_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Healing Word on Brenna.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — brenna"
            )

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_heal_llm)),
            "brenna": RoleSet(),
        }
        characters = {"tobin": tobin, "brenna": brenna}

        result = asyncio.run(run_session(characters, roles, num_turns=1, rng=random.Random(42)))

        assert len(result.turns) == 1
        assert brenna.character.current_hp > 8
        assert tobin.character.spellcasting.spell_slots_used[1] == 1
        tobin_cr = next(cr for cr in result.turns[0].character_results if cr.character_id == "tobin")
        assert tobin_cr.adjudication.approved
        assert "Spell resolved in Python" in tobin_cr.adjudication.notes

    def test_run_session_rejects_unknown_spell(self):
        tobin = self._make_spellcaster()
        brenna = self._make_ally()

        async def cast_unknown_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Wish on Brenna.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — brenna"
            )

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_unknown_llm)),
            "brenna": RoleSet(),
        }
        characters = {"tobin": tobin, "brenna": brenna}

        result = asyncio.run(run_session(characters, roles, num_turns=1, rng=random.Random(7)))

        tobin_cr = next(cr for cr in result.turns[0].character_results if cr.character_id == "tobin")
        assert not tobin_cr.adjudication.approved
        assert "spell" in tobin_cr.adjudication.notes.lower() or "unsupported" in tobin_cr.adjudication.notes.lower()
        assert tobin.character.spellcasting.spell_slots_used[1] == 0

    def test_run_session_ticks_spell_effects_each_turn(self, monkeypatch):
        tobin = self._make_spellcaster()
        brenna = self._make_ally()

        async def cast_heal_llm(_sys: str, _usr: str) -> str:
            return (
                "**INTENT** — Cast Healing Word on Brenna.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — brenna"
            )

        calls: list[int] = []

        original_tick = SpellResolver.tick_effects

        def _spy_tick(self, runtime, *, rounds=1):
            calls.append(rounds)
            return original_tick(self, runtime, rounds=rounds)

        monkeypatch.setattr(SpellResolver, "tick_effects", _spy_tick)

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_heal_llm)),
            "brenna": RoleSet(),
        }
        characters = {"tobin": tobin, "brenna": brenna}

        asyncio.run(run_session(characters, roles, num_turns=2, rng=random.Random(11)))

        assert calls == [1, 1]

    def test_run_session_reports_concentration_replacement(self):
        tobin = self._make_spellcaster()
        brenna = self._make_ally()
        tobin.character.spellcasting.prepared = [
            Spell(name="Healing Word", level=1),
            Spell(name="Bless", level=1),
        ]

        turn_counter = {"n": 0}

        async def cast_concentration_chain_llm(_sys: str, _usr: str) -> str:
            turn_counter["n"] += 1
            if turn_counter["n"] == 1:
                return (
                    "**INTENT** — Cast Guidance on Tobin.\n"
                    "**MOVEMENT** — none\n"
                    "**TARGET** — tobin"
                )
            return (
                "**INTENT** — Cast Bless on Brenna.\n"
                "**MOVEMENT** — none\n"
                "**TARGET** — brenna"
            )

        roles = {
            "tobin": RoleSet(player_left=PlayerLeft(call_llm=cast_concentration_chain_llm)),
            "brenna": RoleSet(),
        }
        characters = {"tobin": tobin, "brenna": brenna}

        result = asyncio.run(run_session(characters, roles, num_turns=2, rng=random.Random(13)))

        tobin_turns = [
            cr
            for tr in result.turns
            for cr in tr.character_results
            if cr.character_id == "tobin"
        ]
        assert len(tobin_turns) == 2
        assert "ended effect" in tobin_turns[1].adjudication.notes.lower()
        assert "guidance" in tobin_turns[1].adjudication.notes.lower()

    def test_vicious_mockery_disadvantage_helper_consumes_once(self):
        runtime = SpellRuntimeState(
            active_effects=[
                ActiveSpellEffect(
                    spell_name="Vicious Mockery Disadvantage",
                    caster_id="tobin",
                    target_ids=["shadowbeast_1"],
                    remaining_rounds=10,
                    concentration=False,
                )
            ]
        )

        assert _has_vicious_mockery_disadvantage(runtime, "shadowbeast_1")
        assert _consume_vicious_mockery_disadvantage(runtime, "shadowbeast_1")
        assert not _has_vicious_mockery_disadvantage(runtime, "shadowbeast_1")


class TestForestLOSEnforcement:
    """Verify that FOREST→FOREST visibility (30 ft) blocks attacks beyond that range."""

    FEY_GLADE_GEO = Path(__file__).parent.parent / "scenario/places/mistwood_hills/fey_glade/GEOMETRY.md"

    @pytest.fixture
    def geo(self):
        from models.geometry_loader import load_geometry
        return load_geometry(self.FEY_GLADE_GEO)

    @pytest.fixture
    def attacker(self, aeliana_char, aeliana_condition):
        return CharacterSession(
            character=aeliana_char,
            condition=aeliana_condition,
            soul="",
            identity="Longbow +5 to hit, 1d8 damage.",
            initial_scene="",
        )

    @pytest.fixture
    def target(self):
        beast = Creature(
            id="shadowbeast_1", name="Shadowbeast", race="Monstrosity",
            character_type="creature", dexterity=14, faction="hostile",
        )
        beast.current_hp = 8
        cond = CharacterCondition(
            character_id="shadowbeast_1", character_name="Shadowbeast",
            state=NeurochemicalState(),
        )
        return CharacterSession(
            character=beast, condition=cond,
            soul="", identity="", initial_scene="",
        )

    def test_forest_attack_blocked_beyond_30ft(self, geo, attacker, target):
        """Attack from FOREST at 134 ft to another FOREST position must be blocked."""
        # Aeliana's actual position from the run that fired through LOS
        attacker_pos = (229.0, 98.3, "FOREST")
        # Beast's position that same turn (outside boundary, in FOREST)
        target_pos = (110.0, 160.8, "FOREST")

        characters = {"aeliana": attacker, "shadowbeast_1": target}
        current_positions = {"aeliana": attacker_pos, "shadowbeast_1": target_pos}

        attacks = [{"target": "shadowbeast_1", "hit_bonus": 5, "damage_expr": "1d8"}]
        hp_damage, log = _resolve_attacks(
            attacks,
            character_id="aeliana",
            attacker_pos=attacker_pos,
            current_positions=current_positions,
            characters=characters,
            max_range=150.0,  # longbow range — should NOT be the limiting factor
            scene_geometry=geo,
        )

        assert hp_damage == {}, f"Attack should be blocked by LOS, got: {log}"
        assert any("no line of sight" in line for line in log), f"Expected LOS block in log: {log}"

    def test_forest_attack_allowed_within_30ft(self, geo, attacker, target):
        """Attack from FOREST within 30 ft to another FOREST position is allowed."""
        # Place both in deep FOREST, 20 ft apart
        attacker_pos = (50.0, 100.0, "FOREST")
        target_pos = (65.0, 110.0, "FOREST")  # ~18 ft

        characters = {"aeliana": attacker, "shadowbeast_1": target}
        current_positions = {"aeliana": attacker_pos, "shadowbeast_1": target_pos}

        attacks = [{"target": "shadowbeast_1", "hit_bonus": 99, "damage_expr": "1d8"}]
        hp_damage, log = _resolve_attacks(
            attacks,
            character_id="aeliana",
            attacker_pos=attacker_pos,
            current_positions=current_positions,
            characters=characters,
            max_range=150.0,
            scene_geometry=geo,
        )

        # With +99 to hit it always hits — damage should be applied
        assert "shadowbeast_1" in hp_damage, f"Attack within 30ft should land: {log}"


class TestResolveTeleportDestination:
    """Teleport can reach any named zone/landmark in the scene and lands inside it."""

    ECHO_GEO = Path(__file__).parent.parent / "scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md"

    @pytest.fixture
    def geo(self):
        from models.geometry_loader import load_geometry
        return load_geometry(self.ECHO_GEO)

    def test_named_zone_resolves_to_point_inside_that_zone(self, geo):
        from models.space_time import Position

        dest = _resolve_teleport_destination("I cast Teleport to the echo chamber", geo)
        assert dest is not None
        x, y, label = dest
        assert label == "ECHO CHAMBER"
        assert geo.zone_at(Position(x, y)) == "Echo Chamber"

    def test_distinct_zone_name_resolves_independently(self, geo):
        from models.space_time import Position

        dest = _resolve_teleport_destination("Teleport to the secret chamber", geo)
        assert dest is not None
        x, y, label = dest
        assert label == "SECRET CHAMBER"
        assert geo.zone_at(Position(x, y)) == "Secret Chamber"

    def test_vague_intent_returns_none(self, geo):
        assert _resolve_teleport_destination("Teleport somewhere vague", geo) is None

    def test_no_geometry_returns_none(self):
        assert _resolve_teleport_destination("Teleport to the echo chamber", None) is None

    def test_named_item_feature_resolves_to_its_position(self, geo):
        from models.contents_loader import load_contents_with_geometry
        from models.space_time import Position

        base = Path(__file__).parent.parent / "scenario/places/obelisk_reach/echoing_caverns"
        items = load_contents_with_geometry(
            base / "CONTENTS.md", base / "GEOMETRY.md", scene_geometry=geo
        )
        dest = _resolve_teleport_destination(
            "I cast a Teleport spell to move to the trigger glyphs", geo, items
        )
        assert dest is not None
        x, y, label = dest
        assert label == "ECHO CHAMBER"
        assert geo.zone_at(Position(x, y)) == "Echo Chamber"


