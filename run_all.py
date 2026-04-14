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
from engine.md_loader import configure_from_md
from engine.session import iter_session, load_resume_state
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
        self._start_turn = 1
        self._initial_history = ""

    def init(self):
        """Wipe any previous run files so progress is unambiguous."""
        if self.checkpoint_dir.exists():
            shutil.rmtree(self.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Cleared: {self.checkpoint_dir}")

    def resume_init(self) -> int | None:
        """Load the last checkpoint to resume where the previous run ended.

        Patches character conditions in-place and seeds scene history so
        characters remember prior turns.  Does NOT delete any existing files.

        Returns the last game_minutes recorded (None if no game_time), so the
        caller can derive the correct frontier to resume from.
        """
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        last_turn, last_game_minutes, history = load_resume_state(
            self.checkpoint_dir, self.config.characters
        )
        if last_turn == 0:
            print(f"  {self.config.scene_name}: no checkpoints found — starting fresh")
        else:
            print(f"  {self.config.scene_name}: resuming after turn {last_turn}")
        self._start_turn = last_turn + 1
        self._initial_history = history
        return last_game_minutes

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
            start_turn=self._start_turn,
            initial_history=self._initial_history,
            scene_geometry=self.config.scene_geometry,
            character_pronouns=self.config.character_pronouns or None,
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

MAX_CONCURRENT = 3  # max scenes running simultaneously

async def run_all(
    num_turns_override: int | None = None,
    resume: bool = False,
    scene_filter: str | None = None,
    self_dm: bool = False,
) -> None:
    # Discover scenes: CONFIG.md folders (preferred) and legacy .json files
    available_md   = {p.name for p in SCENES_DIR.iterdir()
                      if p.is_dir() and (p / "CONFIG.md").exists()}
    available_json = {p.stem for p in SCENES_DIR.glob("*.json")}
    available      = available_md | available_json

    scene_order = [scene_filter] if scene_filter else SCENE_ORDER
    single_scene = scene_filter is not None

    runners: list[SceneRunner] = []
    for scene_name in scene_order:
        if scene_name not in available:
            print(f"WARNING: {scene_name} not found — skipping")
            continue
        # Single-scene mode preserves config-file game_time (pass None).
        game_time = None if single_scene else dataclasses.replace(SESSION_START)

        md_path = SCENES_DIR / scene_name / "CONFIG.md"
        if md_path.exists():
            config = configure_from_md(md_path, game_time=game_time, self_dm=self_dm)
        else:
            config = configure_from_json(
                SCENES_DIR / f"{scene_name}.json", game_time=game_time
            )
        num_turns = num_turns_override if num_turns_override is not None else config.default_turns
        runners.append(SceneRunner(config, num_turns))

    if not runners:
        print("No scenes found.")
        return

    if resume:
        print("Resuming previous run...")
        last_minutes_per_scene = [r.resume_init() for r in runners]
        # Derive shared frontier: latest game_time across all scenes + one step.
        # Scenes without game_time return None; ignore them for the frontier.
        timed = [m for m in last_minutes_per_scene if m is not None]
        if timed:
            exploration_step = SESSION_START.turn_duration
            frontier = max(timed) + exploration_step
        else:
            gt0 = SESSION_START
            frontier = gt0.day * 24 * 60 + gt0.hour * 60 + gt0.minute
            exploration_step = gt0.turn_duration
    else:
        print("Clearing previous run files...")
        for runner in runners:
            runner.init()
        # For a single scene, derive frontier from its own game_time.
        if single_scene and runners and runners[0].config.game_time is not None:
            gt0 = runners[0].config.game_time
        else:
            gt0 = SESSION_START
        frontier = gt0.day * 24 * 60 + gt0.hour * 60 + gt0.minute
        exploration_step = gt0.turn_duration

    total_start = time.monotonic()
    sem = asyncio.Semaphore(MAX_CONCURRENT)

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

        async def _run_one(runner: SceneRunner) -> tuple:
            async with sem:
                return runner, await runner.advance_from_to(frontier, target)

        all_results = await asyncio.gather(*[_run_one(r) for r in active])
        for runner, turn_results in all_results:
            print(f"\n  ── {runner.config.title} ──")
            for turn_result in turn_results:
                print_turn_result(turn_result)

        frontier = target

    elapsed = time.monotonic() - total_start
    print(f"\n{'=' * 70}")
    print(f"  ALL SCENES COMPLETE — {elapsed:.1f}s")
    print(f"{'=' * 70}")

    # Per-scene final output
    for runner in runners:
        config = runner.config
        scene_name = config.scene_name
        print(f"\nGenerating transcript for {scene_name}...")
        elaborate_session_from_dir(
            runner.checkpoint_dir,
            output_path=runner.checkpoint_dir / f"{scene_name}_transcript.txt",
            title=config.transcript_title,
        )
        print(f"  Written to {runner.checkpoint_dir / f'{scene_name}_transcript.txt'}")

        print(f"Generating narrative for {scene_name}...")
        await generate_narrative_from_dir(
            runner.checkpoint_dir,
            provider=config.narrative_provider,
            model=config.narrative_model,
            title=config.narrative_title,
            character_pronouns=config.character_pronouns or None,
            output_path=runner.checkpoint_dir / f"{scene_name}_story.txt",
        )
        print(f"  Written to {runner.checkpoint_dir / f'{scene_name}_story.txt'}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    resume = "--resume" in sys.argv
    self_dm = "--self-dm" in sys.argv
    scene_filter = None
    if "--scene" in sys.argv:
        idx = sys.argv.index("--scene")
        if idx + 1 < len(sys.argv):
            scene_filter = sys.argv[idx + 1]
            args = [a for a in args if a != scene_filter]
    num_turns = int(args[0]) if args else None
    asyncio.run(run_all(num_turns, resume=resume, scene_filter=scene_filter, self_dm=self_dm))


if __name__ == "__main__":
    main()

