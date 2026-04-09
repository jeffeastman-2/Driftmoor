#!/usr/bin/env python3
"""Run any scene by name.

Usage:
    python run_scene.py <scene_name> [turns]

Examples:
    python run_scene.py fey_glade
    python run_scene.py gilded_trinket 6
"""

import asyncio
import importlib
import sys
from pathlib import Path


def main():
    scenes_dir = Path(__file__).parent / "scenes"
    available = sorted(
        p.stem for p in scenes_dir.glob("*.py") if p.stem != "__init__"
    )

    if len(sys.argv) < 2:
        print(f"Usage: python run_scene.py <scene_name> [turns]")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    scene_name = sys.argv[1]
    num_turns = int(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        module = importlib.import_module(f"scenes.{scene_name}")
    except ModuleNotFoundError:
        print(f"Unknown scene: {scene_name}")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    config = module.configure()

    from engine.scene_runner import run_scene
    asyncio.run(run_scene(config, num_turns))


if __name__ == "__main__":
    main()
