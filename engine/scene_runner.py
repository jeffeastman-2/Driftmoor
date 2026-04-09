"""Common scene runner — shared logic for all scene configurations."""

import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from engine.session import CharacterSession, run_session
from engine.scene_manager import RoleSet
from engine.transcript import elaborate_session_from_dir
from engine.narrator import generate_narrative_from_dir

ROOT = Path(__file__).resolve().parent.parent


def load_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


@dataclass
class SceneConfig:
    scene_name: str
    title: str
    narrative_title: str
    transcript_title: str
    character_summary: str
    characters: dict[str, CharacterSession]
    roles: dict[str, RoleSet]
    game_state_summary: str
    geometry_summary: str = ""
    default_turns: int = 4
    narrative_provider: str = "anthropic"
    narrative_model: str = "claude-sonnet-4-20250514"


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


async def run_scene(config: SceneConfig, num_turns: int | None = None):
    """Run a scene: execute turns, print results, generate transcript + narrative."""
    if num_turns is None:
        num_turns = config.default_turns

    checkpoint_dir = ROOT / "runtime" / "state" / config.scene_name

    # Clear previous run
    if checkpoint_dir.exists():
        shutil.rmtree(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{config.title} — {num_turns} turns")
    print(f"Characters: {config.character_summary}")
    print(f"Checkpoints: {checkpoint_dir}\n")

    start = time.monotonic()
    result = await run_session(
        config.characters, config.roles,
        num_turns=num_turns,
        game_state_summary=config.game_state_summary,
        geometry_summary=config.geometry_summary,
        checkpoint_dir=checkpoint_dir,
    )
    elapsed = time.monotonic() - start

    for turn_result in result.turns:
        print_turn_result(turn_result)

    print(f"\n{'=' * 70}")
    print(f"  SESSION COMPLETE — {num_turns} turns in {elapsed:.1f}s")
    print(f"{'=' * 70}")

    print(f"\nFinal conditions:")
    for char_id, condition in result.final_conditions.items():
        d = condition.state.dopamine
        c = condition.state.cortisol
        n = condition.state.norepinephrine
        print(f"  {char_id:15s}  dop={d:.2f}  cor={c:.2f}  nor={n:.2f}")

    print(f"\nGenerating transcript...")
    elaborate_session_from_dir(
        checkpoint_dir,
        output_path=checkpoint_dir / "transcript.txt",
        title=config.transcript_title,
    )
    print(f"  Written to {checkpoint_dir / 'transcript.txt'}")

    print(f"Generating narrative...")
    await generate_narrative_from_dir(
        checkpoint_dir,
        provider=config.narrative_provider, model=config.narrative_model,
        title=config.narrative_title,
        output_path=checkpoint_dir / "story.txt",
    )
    print(f"  Written to {checkpoint_dir / 'story.txt'}")
