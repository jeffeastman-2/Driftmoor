#!/usr/bin/env python3
"""Run a 2-turn session with real LLMs — Aeliana, Fennel, Shadowbeast."""

import asyncio
import os
import sys
import time
from pathlib import Path

from engine.llm_bridge import make_call_llm
from engine.session import CharacterSession, run_session
from engine.player_router import PlayerLeft, PlayerRight
from engine.dm_agent import DMLeft, DMRight
from engine.scene_manager import RoleSet
from models.character import PlayerCharacter, Creature
from models.condition import (
    CharacterCondition,
    NeurochemicalState,
    DimensionProfile,
)

ROOT = Path(__file__).parent


def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def build_characters() -> dict[str, CharacterSession]:
    return {
        "aeliana": CharacterSession(
            character=PlayerCharacter(
                id="aeliana", name="Aeliana Moonglade", race="Wood Elf",
                character_type="player", character_class="Ranger",
                level=1, hp=12, ac=14, dexterity=16, wisdom=15,
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="aeliana",
                character_name="Aeliana",
                state=NeurochemicalState(
                    dopamine=0.85, cortisol=0.25, norepinephrine=0.55,
                    endorphins=0.75, serotonin=0.60, acetylcholine=0.50,
                    oxytocin=0.50,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.55, volatility=0.8),
                    "cortisol": DimensionProfile(baseline=0.35, volatility=0.6),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/aeliana/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/aeliana/IDENTITY.md"),
            initial_scene=(
                "You are on the trail approaching the Fey Glade. "
                "The air shimmers with unnatural warmth ahead. "
                "No sounds from the forest — unnaturally still. "
                "You sense something watching from the treeline."
            ),
        ),
        "fennel": CharacterSession(
            character=PlayerCharacter(
                id="fennel", name="Fennel", race="Human",
                character_type="player", character_class="Gatherer",
                level=1, hp=8, ac=11, dexterity=12, wisdom=14,
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="fennel",
                character_name="Fennel",
                state=NeurochemicalState(
                    dopamine=0.50, cortisol=0.60, norepinephrine=0.75,
                    endorphins=0.45, serotonin=0.50, acetylcholine=0.65,
                    oxytocin=0.30,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=1.0),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=1.2),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/fennel/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/fennel/IDENTITY.md"),
            initial_scene=(
                "You are in the glade near the pool. "
                "The pool glimmers with an eerie light. "
                "A figure approaches from the trail — an elf, armed. "
                "Something dark shifts in the treeline behind you."
            ),
        ),
        "shadowbeast_1": CharacterSession(
            character=Creature(
                id="shadowbeast_1", name="Shadowbeast",
                race="Medium Monstrosity", character_type="creature",
                alignment="Neutral Evil",
                hp=16, ac=12, speed="40 ft", challenge="½",
                strength=6, dexterity=14, constitution=13,
                intelligence=6, wisdom=10, charisma=8,
                skills=["Stealth +4 (+6 in dim light/darkness)"],
                damage_resistances=["Bludgeoning, Piercing, Slashing from nonmagical weapons"],
                damage_vulnerabilities=["Radiant"],
                condition_immunities=["Charmed", "Frightened"],
                senses=["Darkvision 60 ft.", "Passive Perception 13"],
                features=[
                    "Shadow Stealth: In dim light/darkness, Hide as bonus action",
                    "Sunlight Sensitivity: Disadvantage on attacks and Perception in sunlight",
                ],
                actions=[
                    "Multiattack: two claw attacks",
                    "Claw: +4 to hit, 8 (2d4+2) slashing",
                    "Shadow Swipe (Recharge 5-6): 10ft radius, DC 12 DEX, 7 (2d6) necrotic + slow",
                ],
                tactics="Ambush from shadows, target weaker members, retreat if outnumbered",
                location="fey_glade",
            ),
            condition=CharacterCondition(
                character_id="shadowbeast_1",
                character_name="Shadowbeast",
                state=NeurochemicalState(
                    dopamine=0.80, cortisol=0.10, norepinephrine=0.85,
                    endorphins=0.90, serotonin=0.20, acetylcholine=0.90,
                    oxytocin=0.00,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.70, volatility=0.5),
                    "cortisol": DimensionProfile(baseline=0.10, volatility=0.3),
                    "oxytocin": DimensionProfile(baseline=0.00, volatility=0.0),
                },
            ),
            soul=(
                "You are the SHADOWBEAST — a predator of shadow and instinct. "
                "You do not think in words. You sense heat, motion, pressure, "
                "the shimmer of the boundary that contains you. "
                "Communicate through sensation-language: vibration, scent-trails, "
                "thermal impressions. Never use human speech or abstract reasoning."
            ),
            identity=(
                "Shadowbeast. CR ½. HP 16. AC 12 (semi-corporeal). Speed 40ft. "
                "STR 6 DEX 14 CON 13 INT 6 WIS 10 CHA 8. "
                "Shadow Stealth: Hide as bonus action in dim light/darkness. "
                "Sunlight Sensitivity: disadvantage on attacks in sunlight. "
                "Multiattack: two claw attacks. Claw: +4, 2d4+2 slashing. "
                "Shadow Swipe (Recharge 5-6): 10ft radius, DC 12 DEX, 2d6 necrotic + slow. "
                "Resistant to nonmagical B/P/S. Vulnerable to radiant. "
                "Immune to charmed, frightened."
            ),
            initial_scene=(
                "You are in the forest at the boundary. "
                "Prey near the boundary — one alert, one near the pool. "
                "The shimmer pushes back. Hunger builds."
            ),
        ),
    }


def build_roles() -> dict[str, RoleSet]:
    """Build RoleSets with real LLMs — one provider per character."""
    aeliana_llm = make_call_llm("xai", "grok-3")
    fennel_llm = make_call_llm("openai", "gpt-4o")
    shadowbeast_llm = make_call_llm("gemini", "gemini-2.5-flash")

    return {
        "aeliana": RoleSet(
            player_left=PlayerLeft(call_llm=aeliana_llm),
            player_right=PlayerRight(call_llm=aeliana_llm),
            dm_left=DMLeft(call_llm=aeliana_llm),
            dm_right=DMRight(call_llm=aeliana_llm),
        ),
        "fennel": RoleSet(
            player_left=PlayerLeft(call_llm=fennel_llm),
            player_right=PlayerRight(call_llm=fennel_llm),
            dm_left=DMLeft(call_llm=fennel_llm),
            dm_right=DMRight(call_llm=fennel_llm),
        ),
        "shadowbeast_1": RoleSet(
            player_left=PlayerLeft(call_llm=shadowbeast_llm),
            player_right=PlayerRight(call_llm=shadowbeast_llm),
            dm_left=DMLeft(call_llm=shadowbeast_llm),
            dm_right=DMRight(call_llm=shadowbeast_llm),
        ),
    }


def print_turn_result(turn_result):
    print(f"\n{'=' * 70}")
    print(f"  TURN {turn_result.turn}  —  Initiative: {', '.join(turn_result.initiative_order)}")
    print(f"{'=' * 70}")

    for cr in turn_result.character_results:
        print(f"\n  --- {cr.character_id.upper()} ---")
        print(f"  Intent:     {cr.intent.intent}")
        if cr.intent.movement_target:
            print(f"  Move to:    {cr.intent.movement_target}")
        if cr.intent.interaction_target:
            print(f"  Interact:   {cr.intent.interaction_target}")
        if cr.output.spoken and cr.output.spoken.lower() not in ("(silent)", "(silence)", ""):
            print(f"  Spoken:     \"{cr.output.spoken}\"")
        else:
            print(f"  Spoken:     (silent)")
        print(f"  Approved:   {cr.adjudication.approved}")
        if cr.adjudication.condition_deltas:
            deltas = ", ".join(
                f"{k}: {v:+.2f}" for k, v in cr.adjudication.condition_deltas.items()
            )
            print(f"  Deltas:     {deltas}")
        if cr.adjudication.spatial_events:
            print(f"  Events:     {cr.adjudication.spatial_events}")
        print(f"\n  Narration:")
        print(f"  {cr.narration.prose}")


async def main():
    num_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    checkpoint_dir = ROOT / "runtime" / "state" / "session_run"

    print(f"\nDRIFTMOOR SESSION — {num_turns} turns")
    print(f"Characters: Aeliana (Grok), Fennel (GPT-4o), Shadowbeast_1 (Gemini)")
    print(f"Checkpoints: {checkpoint_dir}\n")

    characters = build_characters()
    roles = build_roles()

    start = time.monotonic()
    result = await run_session(
        characters, roles,
        num_turns=num_turns,
        checkpoint_dir=checkpoint_dir,
    )
    elapsed = time.monotonic() - start

    for turn_result in result.turns:
        print_turn_result(turn_result)

    print(f"\n{'=' * 70}")
    print(f"  SESSION COMPLETE — {num_turns} turns in {elapsed:.1f}s")
    print(f"{'=' * 70}")

    # Print final conditions
    print(f"\nFinal conditions:")
    for char_id, condition in result.final_conditions.items():
        d = condition.state.dopamine
        c = condition.state.cortisol
        n = condition.state.norepinephrine
        print(f"  {char_id:15s}  dop={d:.2f}  cor={c:.2f}  nor={n:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
