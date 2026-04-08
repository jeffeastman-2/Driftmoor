"""Game state checkpoint and persistence.

Saves/loads complete game state after each turn:
  - Character conditions (neurochemical state)
  - Scene state (zones, history)
  - Turn results (intents, outputs, adjudications, narrations)
  - Metadata (timestamp, turn number, game time)

Checkpoints are JSON-serializable and location-agnostic.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from engine.scene_manager import TurnResult, CharacterTurnResult
from models.game_state import GameState


@dataclass
class GameCheckpoint:
    """A complete snapshot of game state at a given turn."""
    turn: int
    timestamp: str  # ISO 8601
    game_time: dict[str, Any]  # hour, minute, day, season
    characters: dict[str, dict[str, Any]]  # character_id → condition + metadata
    scene_state: dict[str, Any]  # zones, history summaries
    turn_results: list[dict[str, Any]]  # serialized TurnResult
    metadata: dict[str, Any] = None  # custom metadata (seed, scene name, etc.)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameCheckpoint:
        """Reconstruct from dict."""
        return cls(**data)


class CheckpointManager:
    """Manage game checkpoints (save/load)."""

    def __init__(self, checkpoint_dir: Path = Path("./checkpoints")):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def checkpoint_path(self, turn: int) -> Path:
        """Return path for a given turn's checkpoint."""
        return self.checkpoint_dir / f"turn_{turn:04d}.json"

    def save_checkpoint(self, checkpoint: GameCheckpoint) -> Path:
        """Save a checkpoint to disk."""
        path = self.checkpoint_path(checkpoint.turn)
        with open(path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2, default=str)
        return path

    def load_checkpoint(self, turn: int) -> Optional[GameCheckpoint]:
        """Load a checkpoint for a given turn."""
        path = self.checkpoint_path(turn)
        if not path.exists():
            return None
        with open(path, "r") as f:
            data = json.load(f)
        return GameCheckpoint.from_dict(data)

    def list_checkpoints(self) -> list[int]:
        """List all available checkpoint turn numbers."""
        checkpoints = sorted(self.checkpoint_dir.glob("turn_*.json"))
        turns = []
        for cp in checkpoints:
            try:
                turn = int(cp.stem.split("_")[1])
                turns.append(turn)
            except (IndexError, ValueError):
                continue
        return sorted(turns)

    def latest_checkpoint(self) -> Optional[GameCheckpoint]:
        """Load the most recent checkpoint."""
        turns = self.list_checkpoints()
        if not turns:
            return None
        return self.load_checkpoint(turns[-1])

    def delete_checkpoint(self, turn: int) -> None:
        """Delete a checkpoint."""
        path = self.checkpoint_path(turn)
        if path.exists():
            path.unlink()


class GameStatePersistence:
    """High-level interface: build checkpoints from game objects."""

    def __init__(self, checkpoint_dir: Path = Path("./checkpoints")):
        self.manager = CheckpointManager(checkpoint_dir)

    def create_checkpoint(
        self,
        turn: int,
        game_state: GameState,
        turn_results: TurnResult,
        metadata: Optional[dict[str, Any]] = None,
    ) -> GameCheckpoint:
        """Create a checkpoint from current game state and turn results."""
        # Serialize character conditions
        characters = {}
        for char_id, condition in game_state.characters.items():
            characters[char_id] = {
                "name": condition.character_name,
                "condition": asdict(condition.state),
                "baseline": asdict(condition.baseline),
            }

        # Serialize scene state (zones, simplified history)
        scene_state = {
            "name": game_state.scene.name,
            "zones": game_state.scene.zones,
            "character_count": sum(len(occupants) for occupants in game_state.scene.zones.values()),
        }

        # Serialize turn results
        turn_results_dict = []
        for char_result in turn_results.character_results:
            turn_results_dict.append({
                "character_id": char_result.character_id,
                "intent": asdict(char_result.intent) if char_result.intent else {},
                "output": asdict(char_result.output) if char_result.output else {},
                "adjudication": asdict(char_result.adjudication) if char_result.adjudication else {},
                "narration": asdict(char_result.narration) if char_result.narration else {},
            })

        checkpoint = GameCheckpoint(
            turn=turn,
            timestamp=datetime.now().isoformat(),
            game_time={
                "hour": getattr(game_state.game_time, "hour", 0),
                "minute": getattr(game_state.game_time, "minute", 0),
                "day": getattr(game_state.game_time, "day", 1),
                "season": getattr(game_state.game_time, "season", "autumn"),
            },
            characters=characters,
            scene_state=scene_state,
            turn_results=turn_results_dict,
            metadata=metadata or {},
        )
        return checkpoint

    def save(
        self,
        turn: int,
        game_state: GameState,
        turn_results: TurnResult,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Create and save a checkpoint."""
        checkpoint = self.create_checkpoint(turn, game_state, turn_results, metadata)
        return self.manager.save_checkpoint(checkpoint)

    def load(self, turn: int) -> Optional[GameCheckpoint]:
        """Load a checkpoint."""
        return self.manager.load_checkpoint(turn)

    def latest(self) -> Optional[GameCheckpoint]:
        """Load the latest checkpoint."""
        return self.manager.latest_checkpoint()

    def list_turns(self) -> list[int]:
        """List all checkpoint turns."""
        return self.manager.list_checkpoints()


class TurnSummary:
    """Generate human-readable summaries of turn results."""

    @staticmethod
    def summarize_character_turn(result: CharacterTurnResult) -> str:
        """Summarize one character's turn."""
        lines = []
        lines.append(f"## {result.character_id.upper()} (Turn {result.turn})")
        
        if result.intent:
            lines.append(f"\n**Intent:** {result.intent.action if hasattr(result.intent, 'action') else 'N/A'}")
        
        if result.output:
            if hasattr(result.output, 'spoken') and result.output.spoken:
                lines.append(f"\n**Spoken:** \"{result.output.spoken}\"")
            if hasattr(result.output, 'body_language') and result.output.body_language:
                lines.append(f"\n**Body Language:** {result.output.body_language}")
        
        if result.adjudication:
            if hasattr(result.adjudication, 'allowed') and result.adjudication.allowed:
                lines.append(f"\n✓ Action allowed")
            elif hasattr(result.adjudication, 'allowed'):
                lines.append(f"\n✗ Action blocked")
        
        if result.narration:
            if hasattr(result.narration, 'prose') and result.narration.prose:
                lines.append(f"\n**Narration:** {result.narration.prose[:200]}...")
        
        return "\n".join(lines)

    @staticmethod
    def summarize_turn(turn_result: TurnResult) -> str:
        """Summarize a full turn."""
        lines = [f"# TURN {turn_result.turn}"]
        lines.append(f"Initiative order: {', '.join(turn_result.initiative_order)}\n")
        
        for char_result in turn_result.character_results:
            lines.append(TurnSummary.summarize_character_turn(char_result))
            lines.append("")
        
        return "\n".join(lines)

    @staticmethod
    def summarize_checkpoint(checkpoint: GameCheckpoint) -> str:
        """Summarize a checkpoint."""
        lines = [f"# CHECKPOINT: Turn {checkpoint.turn}"]
        lines.append(f"Timestamp: {checkpoint.timestamp}\n")
        
        # Game time
        if checkpoint.game_time:
            gt = checkpoint.game_time
            lines.append(f"**Game Time:** {gt.get('season', 'N/A')} Day {gt.get('day', '?')}, "
                        f"{gt.get('hour', 0):02d}:{gt.get('minute', 0):02d}\n")
        
        # Character conditions
        lines.append("## Character Conditions")
        for char_id, char_data in checkpoint.characters.items():
            lines.append(f"\n### {char_data.get('name', char_id)}")
            if char_data.get('condition'):
                for dim, val in char_data['condition'].items():
                    lines.append(f"  {dim}: {val:.2f}")
        
        # Scene state
        lines.append(f"\n## Scene State\n{checkpoint.scene_state.get('name', 'Unknown')}")
        
        return "\n".join(lines)
