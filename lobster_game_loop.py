#!/usr/bin/env python3
"""Lobster-compatible game loop for Driftmoor.

Wraps TurnCycle with state persistence and multi-turn execution.
Designed to be called from Lobster workflows.

Usage:
  python lobster_game_loop.py --turns 3 --scene fey_glade --seed 42
"""

import asyncio
import json
import sys
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

# Local imports
import sys
sys.path.insert(0, '/Users/Jeff/Python/Driftmoor')

from engine.scene_manager import TurnCycle, RoleContext
from engine.game_checkpoint import GameStatePersistence, TurnSummary
from models.game_state import GameState
from models.condition import CharacterCondition
from models.scene import Scene


class DriftmoorGameLoop:
    """Main game loop: initialize, run turns, checkpoint."""

    def __init__(
        self,
        scene_name: str = "fey_glade",
        num_turns: int = 3,
        checkpoint_dir: Path = Path("./checkpoints"),
        output_dir: Path = Path("./output"),
        seed: int = 42,
    ):
        self.scene_name = scene_name
        self.num_turns = num_turns
        self.checkpoint_dir = checkpoint_dir
        self.output_dir = output_dir
        self.seed = seed

        # Initialize managers
        self.persistence = GameStatePersistence(checkpoint_dir)
        self.turn_cycle = TurnCycle()

        # State will be initialized in setup()
        self.game_state: Optional[GameState] = None
        self.start_turn = 1

    def setup(self) -> None:
        """Initialize game state from scenario."""
        print(f"[SETUP] Initializing {self.scene_name} scenario...")

        if self.scene_name == "fey_glade":
            self.game_state = initialize_fey_glade(seed=self.seed)
        else:
            raise ValueError(f"Unknown scene: {self.scene_name}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[SETUP] Game state initialized")
        print(f"  Characters: {list(self.game_state.characters.keys())}")
        print(f"  Scene: {self.game_state.scene.name}")
        print(f"  Turns to run: {self.num_turns}")

    async def run_turn(self, turn_num: int) -> None:
        """Execute one full turn."""
        print(f"\n{'='*70}")
        print(f"TURN {turn_num}")
        print(f"{'='*70}\n")

        # Build contexts for each character
        contexts = {}
        for char_id, char_condition in self.game_state.characters.items():
            contexts[char_id] = RoleContext(
                character_id=char_id,
                character_name=char_condition.character_name,
                turn=turn_num,
                scene_name=self.game_state.scene.name,
                zone=self.game_state.scene.character_zone(char_id),
            )

        # Execute turn
        turn_result = await self.turn_cycle.execute_turn(
            turn=turn_num,
            initiative_order=self.game_state.initiative_order,
            contexts=contexts,
            game_state_summary=self._build_game_state_summary(),
            geometry_summary=self._build_geometry_summary(),
        )

        # Print turn summary
        print(TurnSummary.summarize_turn(turn_result))

        # Persist checkpoint
        checkpoint_path = self.persistence.save(
            turn=turn_num,
            game_state=self.game_state,
            turn_results=turn_result,
            metadata={"scene": self.scene_name, "seed": self.seed},
        )
        print(f"\n[CHECKPOINT] Saved to {checkpoint_path}")

        # Apply condition deltas (simplified for now)
        # TODO: DM-Left adjudication should feed condition deltas
        self._apply_condition_deltas(turn_result)

    async def run(self) -> None:
        """Run the full game loop."""
        self.setup()

        for turn_num in range(self.start_turn, self.start_turn + self.num_turns):
            try:
                await self.run_turn(turn_num)
            except Exception as e:
                print(f"[ERROR] Turn {turn_num} failed: {e}")
                import traceback
                traceback.print_exc()
                break

        # Final summary
        self._print_final_summary()

    def _build_game_state_summary(self) -> str:
        """Build a text summary of current game state for LLM context."""
        lines = [f"Scene: {self.game_state.scene.name}"]
        lines.append(f"Turn: {self.game_state.scene.turn}")
        lines.append("\nZone Occupancy:")
        for zone, occupants in self.game_state.scene.zones.items():
            people = ", ".join(occupants) if occupants else "(empty)"
            lines.append(f"  {zone}: {people}")
        return "\n".join(lines)

    def _build_geometry_summary(self) -> str:
        """Build a spatial summary for DM-Left adjudication."""
        # TODO: integrate with SPACE_TIME.md spatial geometry
        return "Fey Glade geometry: [simplified for now]"

    def _apply_condition_deltas(self, turn_result) -> None:
        """Apply neurochemical condition deltas from adjudication."""
        # TODO: parse adjudication results and apply deltas
        # For now, this is a placeholder
        pass

    def _print_final_summary(self) -> None:
        """Print end-of-game summary."""
        print(f"\n{'='*70}")
        print("GAME COMPLETE")
        print(f"{'='*70}")
        print(f"Turns executed: {self.num_turns}")
        print(f"Scene: {self.game_state.scene.name}")
        print(f"Checkpoints saved: {self.checkpoint_dir}")

        # Character final conditions
        print("\n## Final Character Conditions")
        for char_id, condition in self.game_state.characters.items():
            print(f"\n{condition.character_name}:")
            for dim in ["dopamine", "cortisol", "norepinephrine"]:
                val = getattr(condition.state, dim, 0.5)
                print(f"  {dim}: {val:.2f}")


async def main():
    parser = ArgumentParser(description="Driftmoor game loop")
    parser.add_argument("--turns", type=int, default=3, help="Number of turns to run")
    parser.add_argument("--scene", default="fey_glade", help="Scene name")
    parser.add_argument("--checkpoint-dir", default="./checkpoints", help="Checkpoint directory")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--resume-turn", type=int, default=0, help="Resume from this turn (0=new game)")

    args = parser.parse_args()

    game = DriftmoorGameLoop(
        scene_name=args.scene,
        num_turns=args.turns,
        checkpoint_dir=Path(args.checkpoint_dir),
        output_dir=Path(args.output_dir),
        seed=args.seed,
    )

    if args.resume_turn > 0:
        checkpoint = game.persistence.load(args.resume_turn)
        if checkpoint:
            print(f"[RESUME] Loaded checkpoint from turn {args.resume_turn}")
            game.start_turn = args.resume_turn + 1
        else:
            print(f"[ERROR] No checkpoint found for turn {args.resume_turn}")
            sys.exit(1)

    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
