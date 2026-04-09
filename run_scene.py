#!/usr/bin/env python3
"""Run any scene by name.

Usage:
    python run_scene.py <scene_name> [turns]

Examples:
    python run_scene.py fey_glade
    python run_scene.py gilded_trinket 6
"""

import asyncio
import sys
from pathlib import Path


def main():
    scenes_dir = Path(__file__).parent / "scenes"
    available = sorted(
        p.stem for p in scenes_dir.glob("*.json")
    )

    if len(sys.argv) < 2:
        print(f"Usage: python run_scene.py <scene_name> [turns]")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    scene_name = sys.argv[1]
    num_turns = int(sys.argv[2]) if len(sys.argv) > 2 else None

    json_path = scenes_dir / f"{scene_name}.json"
    if not json_path.exists():
        print(f"Unknown scene: {scene_name}")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    from engine.scene_runner import configure_from_json, run_scene
    config = configure_from_json(json_path)
    asyncio.run(run_scene(config, num_turns))


if __name__ == "__main__":
    main()
