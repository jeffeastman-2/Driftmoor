#!/usr/bin/env python3
"""
Live LLM integration test — one character, one role, one turn.

Usage:
  python live_test.py                        # PlayerLeft only (default)
  python live_test.py --roles left           # PlayerLeft only
  python live_test.py --roles left,right     # PlayerLeft + PlayerRight
  python live_test.py --roles all            # All four roles
  python live_test.py --provider openai --model gpt-4o
  python live_test.py --character fennel --provider openai

Reads SOUL.md and IDENTITY.md from scenario/people/ for the character.
Prints the raw LLM response and parsed output.
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from engine.llm_bridge import make_call_llm
from engine.player_router import PlayerLeft, PlayerRight, RoleContext
from engine.dm_agent import DMLeft, DMRight
from engine.scene_manager import TurnCycle, RoleSet


# ---------------------------------------------------------------------------
# Character configs
# ---------------------------------------------------------------------------

CHARACTERS = {
    "aeliana": {
        "persona_dir": "scenario/people/players/aeliana",
        "condition_text": (
            "dopamine: 0.85, cortisol: 0.25, norepinephrine: 0.55, "
            "endorphins: 0.75, serotonin: 0.60, acetylcholine: 0.50, "
            "oxytocin: 0.50"
        ),
        "scene_context": (
            "You are on the trail approaching the Fey Glade. "
            "The air shimmers with unnatural warmth ahead. "
            "No sounds from the forest — unnaturally still. "
            "You sense something watching from the treeline."
        ),
    },
    "fennel": {
        "persona_dir": "scenario/people/npcs/kara",  # placeholder
        "condition_text": (
            "dopamine: 0.50, cortisol: 0.60, norepinephrine: 0.75, "
            "endorphins: 0.45, serotonin: 0.50, acetylcholine: 0.65, "
            "oxytocin: 0.30"
        ),
        "scene_context": (
            "You are in the glade near the pool. "
            "The pool glimmers with an eerie light. "
            "A figure approaches from the trail — an elf, armed. "
            "Something dark shifts in the treeline behind you."
        ),
    },
    "shadowbeast": {
        "persona_dir": None,  # no persona files; inline
        "condition_text": (
            "dopamine: 0.80, cortisol: 0.10, norepinephrine: 0.85, "
            "endorphins: 0.90, serotonin: 0.20, acetylcholine: 0.90, "
            "oxytocin: 0.00"
        ),
        "scene_context": (
            "You are in the forest at the boundary. "
            "Prey near the boundary — one alert, one near the pool. "
            "The shimmer pushes back. Hunger builds."
        ),
    },
}

DEFAULT_PROVIDERS = {
    "aeliana": ("xai", "grok-3"),
    "fennel": ("openai", "gpt-4o"),
    "shadowbeast": ("gemini", "gemini-2.5-flash"),
}


def load_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def build_context(character_id: str, root: Path) -> RoleContext:
    cfg = CHARACTERS[character_id]
    persona_dir = cfg.get("persona_dir")
    if persona_dir:
        soul = load_file(root / persona_dir / "SOUL.md")
        identity = load_file(root / persona_dir / "IDENTITY.md")
    else:
        soul = ""
        identity = ""
    return RoleContext(
        character_id=character_id,
        turn=1,
        condition_text=cfg["condition_text"],
        scene_context=cfg["scene_context"],
        soul=soul,
        identity=identity,
    )


def print_separator(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


async def run_live_test(
    character_id: str,
    provider: str,
    model: str,
    roles: list[str],
    root: Path,
):
    call_llm = make_call_llm(provider, model)
    context = build_context(character_id, root)

    print(f"Character:  {character_id}")
    print(f"Provider:   {provider}/{model}")
    print(f"Roles:      {', '.join(roles)}")
    print(f"Condition:  {context.condition_text[:60]}...")
    print(f"Scene:      {context.scene_context[:60]}...")

    # --- PlayerLeft ---
    if "left" in roles:
        print_separator("PLAYER-LEFT: Action Intent")
        pl = PlayerLeft(call_llm=call_llm)

        t0 = time.monotonic()
        intent = await pl.generate_intent(context)
        elapsed = time.monotonic() - t0

        print(f"Intent:              {intent.intent}")
        print(f"Movement target:     {intent.movement_target}")
        print(f"Interaction target:  {intent.interaction_target}")
        print(f"Time:                {elapsed:.1f}s")
    else:
        # Stub intent for downstream roles
        intent = None

    # --- PlayerRight ---
    if "right" in roles:
        print_separator("PLAYER-RIGHT: In-Character Prose")
        pr = PlayerRight(call_llm=call_llm)

        if intent is None:
            from engine.player_router import ActionIntent
            intent = ActionIntent(
                character_id=character_id, turn=1,
                intent="observe surroundings and hold position",
            )

        t0 = time.monotonic()
        output = await pr.generate_action(intent, context)
        elapsed = time.monotonic() - t0

        print(f"INTERNAL:\n{output.internal}\n")
        print(f"BODY LANGUAGE:\n{output.body_language}\n")
        print(f"SPOKEN:\n{output.spoken or '(silent)'}\n")
        print(f"ACTION:\n{output.action}\n")
        print(f"Time: {elapsed:.1f}s")
    else:
        output = None

    # --- DMLeft ---
    if "dmleft" in roles:
        print_separator("DM-LEFT: Adjudication")
        dl = DMLeft(call_llm=call_llm)

        if output is None:
            from engine.player_router import CharacterOutput
            output = CharacterOutput(
                character_id=character_id, turn=1,
                action="observe surroundings and hold position",
            )

        t0 = time.monotonic()
        adj = await dl.adjudicate(output, "", "")
        elapsed = time.monotonic() - t0

        print(f"Approved:         {adj.approved}")
        print(f"Modified action:  {adj.modified_action}")
        print(f"Position delta:   {adj.position_delta}")
        print(f"Condition deltas: {adj.condition_deltas}")
        print(f"Spatial events:   {adj.spatial_events}")
        print(f"Notes:            {adj.notes}")
        print(f"Time:             {elapsed:.1f}s")
    else:
        adj = None

    # --- DMRight ---
    if "dmright" in roles:
        print_separator("DM-RIGHT: Narration")
        dr = DMRight(call_llm=call_llm)

        if adj is None:
            from engine.dm_agent import Adjudication
            adj = Adjudication(character_id=character_id, turn=1, approved=True)
        if output is None:
            from engine.player_router import CharacterOutput
            output = CharacterOutput(
                character_id=character_id, turn=1,
                action="observe surroundings and hold position",
            )

        t0 = time.monotonic()
        narr = await dr.narrate(adj, output, "")
        elapsed = time.monotonic() - t0

        print(f"Prose:\n{narr.prose}\n")
        print(f"Time: {elapsed:.1f}s")

    print_separator("DONE")


def main():
    parser = argparse.ArgumentParser(
        description="Live LLM integration test — one character, one turn",
    )
    parser.add_argument(
        "--character", "-c", default="aeliana",
        choices=list(CHARACTERS.keys()),
        help="Character to test (default: aeliana)",
    )
    parser.add_argument(
        "--provider", "-p", default=None,
        help="LLM provider (default: per-character default)",
    )
    parser.add_argument(
        "--model", "-m", default=None,
        help="Model name (default: per-provider default)",
    )
    parser.add_argument(
        "--roles", "-r", default="left",
        help="Comma-separated roles: left,right,dmleft,dmright or 'all'",
    )
    args = parser.parse_args()

    # Resolve provider/model
    default_provider, default_model = DEFAULT_PROVIDERS[args.character]
    provider = args.provider or default_provider
    model = args.model or default_model

    # Parse roles
    if args.roles == "all":
        roles = ["left", "right", "dmleft", "dmright"]
    else:
        roles = [r.strip() for r in args.roles.split(",")]

    root = Path(__file__).resolve().parent

    asyncio.run(run_live_test(args.character, provider, model, roles, root))


if __name__ == "__main__":
    main()
