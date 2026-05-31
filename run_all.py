#!/usr/bin/env python3
"""Run all scenes for a single game session, advancing turn-by-turn in parallel.

All scenes do Turn 1 concurrently, then all do Turn 2, etc.  This mirrors
real-session pacing and keeps checkpoint timestamps consistent across scenes.

Every scene is given a fresh copy of SESSION_START so clock advances are
independent.  Edit SESSION_START below to change the session's opening time.

Usage:
    python run_all.py          # runs every scene in scenes/ at its default_turns
    python run_all.py 6        # override default_turns for every scene
"""

import asyncio
import dataclasses
import shutil
import sys
import time
from pathlib import Path

from models.space_time import GameTime
from engine.scene_runner import print_turn_result, ROOT, _write_runtime_map
from engine.md_loader import configure_from_md
from engine.session import (
    _broadcast_session_complete_to_transports,
    _has_telegram_transport,
    iter_session,
    load_resume_state,
)
from engine.transcript import elaborate_session_from_dir
from engine.narrator import generate_narrative_from_dir
from engine.runtime_paths import get_scene_dir, get_session_dir

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

# ---------------------------------------------------------------------------
# Per-scene runner
# ---------------------------------------------------------------------------

class SceneRunner:
    """Wraps a single scene's iter_session generator for step-by-step use."""

    def __init__(self, config, num_turns: int):
        self.config = config
        self.num_turns = num_turns
        self.checkpoint_dir = get_scene_dir(config.scene_name)
        self.done = False
        self.completed_turns = 0
        self._gen = None
        self._start_turn = 1
        self._initial_history = ""
        self._initial_active_characters: set[str] | None = None
        self._checkpoint_positions: dict = {}
        self._party_examination_state: dict = {}

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
        (
            last_turn,
            last_game_minutes,
            history,
            active_chars,
            checkpoint_positions,
            party_examination_state,
        ) = load_resume_state(
            self.checkpoint_dir, self.config.characters
        )
        if last_turn == 0:
            print(f"  {self.config.scene_name}: no checkpoints found — starting fresh")
        else:
            print(f"  {self.config.scene_name}: resuming after turn {last_turn}")
        self._start_turn = last_turn + 1
        self._initial_history = history
        self._initial_active_characters = active_chars
        self._checkpoint_positions = checkpoint_positions
        self._party_examination_state = party_examination_state
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
            items=self.config.items or None,
            character_pronouns=self.config.character_pronouns or None,
            initial_active_characters=self._initial_active_characters,
            initial_positions=self._checkpoint_positions or None,
            initial_party_examination_state=self._party_examination_state or None,
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
        assert self._gen is not None
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
    # Discover scenes: flat .md files in scenes/
    available = {p.stem for p in SCENES_DIR.iterdir()
                 if p.is_file() and p.suffix == ".md"}

    scene_order = [scene_filter] if scene_filter else sorted(available)
    single_scene = scene_filter is not None

    runners: list[SceneRunner] = []
    for scene_name in scene_order:
        if scene_name not in available:
            print(f"WARNING: {scene_name} not found — skipping")
            continue
        # Single-scene mode preserves config-file game_time (pass None).
        game_time = None if single_scene else dataclasses.replace(SESSION_START)

        md_path = SCENES_DIR / f"{scene_name}.md"
        config = configure_from_md(md_path, game_time=game_time, self_dm=self_dm)
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
            runner.completed_turns += len(turn_results)
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

        if config.geometry_path is not None and config.geometry_path.exists():
            _write_runtime_map(
                geometry_path=config.geometry_path,
                scene_name=scene_name,
                checkpoint_dir=runner.checkpoint_dir,
            )

    for runner in runners:
        if _has_telegram_transport(runner.config.characters):
            await _broadcast_session_complete_to_transports(
                completed_turns=runner.completed_turns,
                characters=runner.config.characters,
            )


def main() -> None:
    import os
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    resume = "--resume" in sys.argv
    self_dm = "--self-dm" in sys.argv

    # Resume must reuse the most recent session id rather than mint a new
    # one. Set the env var BEFORE any code calls current_session_id().
    if resume and not os.environ.get("DRIFTMOOR_SESSION_ID"):
        from engine.runtime_paths import find_latest_session_id
        latest = find_latest_session_id()
        if latest is None:
            print("  --resume: no prior session found under state root")
            sys.exit(1)
        os.environ["DRIFTMOOR_SESSION_ID"] = latest
        print(f"  --resume: continuing session {latest}")

    scene_filter = None
    if "--scene" in sys.argv:
        idx = sys.argv.index("--scene")
        if idx + 1 < len(sys.argv):
            scene_filter = sys.argv[idx + 1]
            args = [a for a in args if a != scene_filter]
    if "--ollama-host" in sys.argv:
        idx = sys.argv.index("--ollama-host")
        if idx + 1 >= len(sys.argv):
            print("--ollama-host requires a URL argument")
            sys.exit(1)
        import os
        os.environ["OLLAMA_HOST"] = sys.argv[idx + 1]
        args = [a for a in args if a != sys.argv[idx + 1]]
    if "--all-ollama" in sys.argv:
        idx = sys.argv.index("--all-ollama")
        if idx + 1 >= len(sys.argv):
            print("--all-ollama requires a MODEL argument (e.g. gemma4:latest)")
            sys.exit(1)
        import os
        os.environ["LLM_FORCE_OLLAMA_MODEL"] = sys.argv[idx + 1]
        args = [a for a in args if a != sys.argv[idx + 1]]

    from engine.runtime_paths import print_startup_banner
    print_startup_banner()

    num_turns = int(args[0]) if args else None
    asyncio.run(run_all(num_turns, resume=resume, scene_filter=scene_filter, self_dm=self_dm))


if __name__ == "__main__":
    main()

