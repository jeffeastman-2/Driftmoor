#!/usr/bin/env python3
"""Run all scenes for a single game session, advancing turn-by-turn in parallel.

All scenes do Turn 1 concurrently, then all do Turn 2, etc.  This mirrors
real-session pacing and keeps checkpoint timestamps consistent across scenes.

Every scene is given a fresh copy of SESSION_START so clock advances are
independent.  Edit SESSION_START below to change the session's opening time.

Usage:
    python run_all.py          # runs all scenes at their default_turns
    python run_all.py 6        # override default_turns for every scene
"""

import asyncio
import dataclasses
import shutil
import sys
import time
from pathlib import Path

from models.space_time import GameTime
from engine.scene_runner import configure_from_json, print_turn_result, ROOT
from engine.session import iter_session
from engine.transcript import elaborate_session_from_dir
from engine.narrator import generate_narrative_from_dir

SCENES_DIR = Path(__file__).parent / "scenes"

# ---------------------------------------------------------------------------
# Session start time — each scene gets a fresh copy of this
# ---------------------------------------------------------------------------
SESSION_START = GameTime(
    hour=19,
    minute=0,
    day=1,
    season="spring",
    turn_duration=10,
    absolute_turn=0,
)

SCENE_ORDER = [
    "beacon_church",
    "broken_lantern",
    "fey_glade",
    "gilded_trinket",
    "ironhoof_forge",
    "old_mill",
    "salt_and_iron",
]


# ---------------------------------------------------------------------------
# Per-scene runner
# ---------------------------------------------------------------------------

class SceneRunner:
    """Wraps a single scene's iter_session generator for step-by-step use."""

    def __init__(self, config, num_turns: int):
        self.config = config
        self.num_turns = num_turns
        self.checkpoint_dir = ROOT / "runtime" / "state" / config.scene_name
        self.done = False
        self._gen = None

    def init(self):
        """Wipe any previous run files so progress is unambiguous."""
        if self.checkpoint_dir.exists():
            shutil.rmtree(self.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Cleared: {self.checkpoint_dir}")

    @property
    def next_game_minutes(self) -> int | None:
        """Absolute game time of the upcoming turn, in minutes. None if no game_time."""
        gt = self.config.game_time
        if gt is None:
            return None
        return gt.day * 24 * 60 + gt.hour * 60 + gt.minute

    def _start(self):
        if self._gen is not None:
            return
        self._gen = iter_session(
            self.config.characters,
            self.config.roles,
            self.num_turns,
            game_state_summary=self.config.game_state_summary,
            geometry_summary=self.config.geometry_summary,
            checkpoint_dir=self.checkpoint_dir,
            game_time=self.config.game_time,
        )

    async def advance_from_to(self, start_minutes: int, end_minutes: int) -> list:
        """Snap the scene clock to start_minutes, then run turns until end_minutes.

        Called once per scheduler round.  Resetting the clock at entry means:
        - No clock drift between rounds
        - A melee that overshot last round's end_time is silently corrected
        - turn_duration is intentionally NOT reset, so melee carries across rounds

        Returns all TurnResults produced in this window.
        Scenes without game_time run exactly one turn per call.
        """
        self._start()
        gt = self.config.game_time
        if gt is not None:
            total = start_minutes
            gt.day    = total // (24 * 60)
            remainder = total % (24 * 60)
            gt.hour   = remainder // 60
            gt.minute = remainder % 60

        results = []
        while not self.done:
            t = self.next_game_minutes
            if t is not None and t >= end_minutes:
                break
            try:
                turn_result = await self._gen.__anext__()
                results.append(turn_result)
            except StopAsyncIteration:
                self.done = True
                break
            if gt is None:
                break  # no game_time — one step per round
        return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run_all(num_turns_override: int | None = None) -> None:
    available = {p.stem for p in SCENES_DIR.glob("*.json")}

    runners: list[SceneRunner] = []
    for scene_name in SCENE_ORDER:
        if scene_name not in available:
            print(f"WARNING: {scene_name}.json not found — skipping")
            continue
        json_path = SCENES_DIR / f"{scene_name}.json"
        # Each scene gets its own GameTime copy so clock advances don't interfere
        game_time = dataclasses.replace(SESSION_START)
        config = configure_from_json(json_path, game_time=game_time)
        num_turns = num_turns_override if num_turns_override is not None else config.default_turns
        runners.append(SceneRunner(config, num_turns))

    if not runners:
        print("No scenes found.")
        return

    print("Clearing previous run files...")
    for runner in runners:
        runner.init()

    total_start = time.monotonic()

    # Frontier scheduler: advance all scenes to the same target each round.
    # Target always moves by the exploration step (SESSION_START.turn_duration)
    # regardless of melee.  Scenes run as many turns as needed to reach the
    # target — melee turns burn through internally, then the scene returns.
    gt0 = SESSION_START
    frontier = gt0.day * 24 * 60 + gt0.hour * 60 + gt0.minute
    exploration_step = gt0.turn_duration  # minutes per exploration turn (10)

    while True:
        active = [r for r in runners if not r.done]
        if not active:
            break

        target = frontier + exploration_step
        th, tm = divmod(target % (24 * 60), 60)
        tday = target // (24 * 60)
        print(f"\n{'=' * 70}")
        print(f"  → Day {tday}  {th:02d}:{tm:02d}")
        print(f"{'=' * 70}")

        all_results = await asyncio.gather(*[r.advance_from_to(frontier, target) for r in active])

        for runner, turn_results in zip(active, all_results):
            for turn_result in turn_results:
                if len(active) > 1 or len(turn_results) > 1:
                    print(f"\n  ── {runner.config.title} ──")
                print_turn_result(turn_result)

        frontier = target

    elapsed = time.monotonic() - total_start
    print(f"\n{'=' * 70}")
    print(f"  ALL SCENES COMPLETE — {elapsed:.1f}s")
    print(f"{'=' * 70}")

    # Per-scene final output
    for runner in runners:
        config = runner.config
        print(f"\nGenerating transcript for {config.scene_name}...")
        elaborate_session_from_dir(
            runner.checkpoint_dir,
            output_path=runner.checkpoint_dir / "transcript.txt",
            title=config.transcript_title,
        )
        print(f"  Written to {runner.checkpoint_dir / 'transcript.txt'}")

        print(f"Generating narrative for {config.scene_name}...")
        await generate_narrative_from_dir(
            runner.checkpoint_dir,
            provider=config.narrative_provider,
            model=config.narrative_model,
            title=config.narrative_title,
            output_path=runner.checkpoint_dir / "story.txt",
        )
        print(f"  Written to {runner.checkpoint_dir / 'story.txt'}")


def main() -> None:
    num_turns = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(run_all(num_turns))


if __name__ == "__main__":
    main()

