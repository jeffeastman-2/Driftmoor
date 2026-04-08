#!/usr/bin/env python3
"""Run a session in the Gilded Trinket — Seraphina browses, Tavian minds the shop."""

import asyncio
import sys
import time
from pathlib import Path

from engine.llm_bridge import make_call_llm
from engine.session import CharacterSession, run_session
from engine.player_router import PlayerLeft, PlayerRight
from engine.dm_agent import DMLeft, DMRight
from engine.scene_manager import RoleSet
from models.character import PlayerCharacter, NPC
from engine.transcript import elaborate_session_from_dir
from engine.narrator import generate_narrative_from_dir
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
        "seraphina": CharacterSession(
            character=PlayerCharacter(
                id="seraphina", name="Seraphina Duskwhisper", race="Half-Elf",
                character_type="player", character_class="Rogue",
                level=1, hp=9, ac=11, strength=8, dexterity=16,
                constitution=12, intelligence=14, wisdom=10, charisma=15,
                location="gilded_trinket",
            ),
            condition=CharacterCondition(
                character_id="seraphina",
                character_name="Seraphina",
                state=NeurochemicalState(
                    dopamine=0.65, cortisol=0.40, norepinephrine=0.60,
                    endorphins=0.50, serotonin=0.45, acetylcholine=0.75,
                    oxytocin=0.25,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.55, volatility=0.9),
                    "cortisol": DimensionProfile(baseline=0.40, volatility=0.8),
                    "acetylcholine": DimensionProfile(baseline=0.65, volatility=0.7),
                    "oxytocin": DimensionProfile(baseline=0.20, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/players/seraphina/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/players/seraphina/IDENTITY.md"),
            initial_scene=(
                "You push open the door of The Gilded Trinket. A bell chimes. "
                "Narrow, cluttered, dim oil lamp light. Shelves of rusty tools, "
                "old weapons, curios. A locked glass display case at the counter "
                "holds the more interesting items — you notice a tarnished silver ring "
                "with a dark stone that seems to catch the lamplight oddly. "
                "Behind the counter stands a tall, lean figure with faintly "
                "shimmering bronze scales and piercing green eyes that are "
                "already weighing you. Smells of dust and polish."
            ),
        ),
        "tavian": CharacterSession(
            character=NPC(
                id="tavian", name="Tavian Drakescale", race="Half-Dragon (Bronze)",
                character_type="npc",
                role="Pawnbroker, The Gilded Trinket",
                home_location="gilded_trinket",
                dexterity=12, intelligence=14, wisdom=13, charisma=14,
                hp=18, ac=13,
                knowledge=[
                    "The obelisk shard ring in the display case is dangerous — a villager pawned it after nightmares and compulsions",
                    "The cracked compass and stone amulet are genuinely magical",
                    "The map fragment shows part of the Drowned Isle coastline",
                    "His smuggling contacts could source rare items but he avoids using them",
                ],
                active_concerns=[
                    "The obelisk shard ring — what to do with it",
                    "His medallion — will not discuss or sell",
                    "His smuggling past resurfacing",
                ],
                location="gilded_trinket",
            ),
            condition=CharacterCondition(
                character_id="tavian",
                character_name="Tavian",
                state=NeurochemicalState(
                    dopamine=0.50, cortisol=0.35, norepinephrine=0.50,
                    endorphins=0.55, serotonin=0.60, acetylcholine=0.70,
                    oxytocin=0.30,
                ),
                profiles={
                    "dopamine": DimensionProfile(baseline=0.50, volatility=0.5),
                    "cortisol": DimensionProfile(baseline=0.30, volatility=0.6),
                    "serotonin": DimensionProfile(baseline=0.60, volatility=0.4),
                },
            ),
            soul=load_file(ROOT / "scenario/people/npcs/tavian/SOUL.md"),
            identity=load_file(ROOT / "scenario/people/npcs/tavian/IDENTITY.md"),
            initial_scene=(
                "The bell above the door chimes. A half-elf woman steps in — "
                "raven-black hair, dark leather armor, green eyes that are already "
                "scanning every shelf. She moves with the quiet economy of someone "
                "who knows how to move without being heard. Rogue, almost certainly. "
                "A faint scar on her right cheek. Silver crescent moon pendant at her throat. "
                "Her gaze lingers on the display case — specifically on the ring. "
                "The ring with the dark stone you have been trying to decide what to do with."
            ),
        ),
    }


def build_roles() -> dict[str, RoleSet]:
    """Seraphina on Claude, Tavian on GPT-4o."""
    seraphina_llm = make_call_llm("anthropic", "claude-sonnet-4-20250514")
    tavian_llm = make_call_llm("openai", "gpt-4o")

    return {
        "seraphina": RoleSet(
            player_left=PlayerLeft(call_llm=seraphina_llm),
            player_right=PlayerRight(call_llm=seraphina_llm),
            dm_left=DMLeft(call_llm=seraphina_llm),
            dm_right=DMRight(call_llm=seraphina_llm),
        ),
        "tavian": RoleSet(
            player_left=PlayerLeft(call_llm=tavian_llm),
            player_right=PlayerRight(call_llm=tavian_llm),
            dm_left=DMLeft(call_llm=tavian_llm),
            dm_right=DMRight(call_llm=tavian_llm),
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
    num_turns = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    checkpoint_dir = ROOT / "runtime" / "state" / "gilded_trinket"

    print(f"\nGILDED TRINKET — {num_turns} turns")
    print(f"Characters: Seraphina (Claude), Tavian (GPT-4o)")
    print(f"Checkpoints: {checkpoint_dir}\n")

    characters = build_characters()
    roles = build_roles()

    # Load scene context
    place_md = load_file(
        ROOT / "scenario/places/driftmoor/gilded_trinket/PLACE.md"
    )
    contents_md = load_file(
        ROOT / "scenario/places/driftmoor/gilded_trinket/CONTENTS.md"
    )
    obelisk_lore = load_file(ROOT / "scenario/things/obelisk_shards.md")
    game_state_summary = (
        "# Scene: The Gilded Trinket (Pawnshop)\n\n"
        f"{place_md}\n\n"
        f"{contents_md}\n\n"
        "# Relevant Lore (DM only)\n\n"
        f"{obelisk_lore}\n\n"
        "# Scene Notes\n\n"
        "This is an exploration/social scene in a pawnshop. No combat expected.\n"
        "Seraphina has an unexplained latent arcane ability — she may sense the "
        "obelisk shard's resonance where others would not.\n"
        "Tavian knows the ring is dangerous but has not decided what to do with it.\n"
        "The cracked compass and stone amulet are genuinely magical — Tavian knows.\n"
    )

    start = time.monotonic()
    result = await run_session(
        characters, roles,
        num_turns=num_turns,
        game_state_summary=game_state_summary,
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

    # Generate transcript and narrative
    print(f"\nGenerating transcript...")
    elaborate_session_from_dir(
        checkpoint_dir,
        output_path=checkpoint_dir / "transcript.txt",
        title="GILDED TRINKET — Seraphina, Tavian",
    )
    print(f"  Written to {checkpoint_dir / 'transcript.txt'}")

    print(f"Generating narrative...")
    story = await generate_narrative_from_dir(
        checkpoint_dir,
        provider="anthropic", model="claude-sonnet-4-20250514",
        title="The Gilded Trinket",
        output_path=checkpoint_dir / "story.txt",
    )
    print(f"  Written to {checkpoint_dir / 'story.txt'}")


if __name__ == "__main__":
    asyncio.run(main())
