#!/usr/bin/env python3
"""Run any scene by name.

Usage:
    python run_scene.py <scene_name> [turns] [--resume] [--ollama-host URL]

Examples:
    python run_scene.py fey_glade
    python run_scene.py gilded_trinket 6
    python run_scene.py echoing_caverns --ollama-host http://ultra:11434
    python run_scene.py elyssa_cottage 4 --resume
"""

import asyncio
import os
import sys
from pathlib import Path


def main():
    scenes_dir = Path(__file__).parent / "scenes"
    available = sorted(
        p.stem for p in scenes_dir.iterdir()
        if p.is_file() and p.suffix == ".md"
    )

    argv = list(sys.argv[1:])
    resume = "--resume" in argv
    if resume:
        argv = [a for a in argv if a != "--resume"]

    # Resume must reuse an existing session id instead of creating a new one.
    # If not pinned explicitly, default to the latest available session.
    if resume and not os.environ.get("DRIFTMOOR_SESSION_ID"):
        from engine.runtime_paths import find_latest_session_id

        latest = find_latest_session_id()
        if latest is None:
            print("--resume: no prior session found under state root")
            sys.exit(1)
        os.environ["DRIFTMOOR_SESSION_ID"] = latest
        print(f"--resume: continuing session {latest}")

    if "--ollama-host" in argv:
        i = argv.index("--ollama-host")
        if i + 1 >= len(argv):
            print("--ollama-host requires a URL argument")
            sys.exit(1)
        os.environ["OLLAMA_HOST"] = argv[i + 1]
        del argv[i:i + 2]
    if "--all-ollama" in argv:
        i = argv.index("--all-ollama")
        if i + 1 >= len(argv):
            print("--all-ollama requires a MODEL argument (e.g. gemma4:latest)")
            sys.exit(1)
        os.environ["LLM_FORCE_OLLAMA_MODEL"] = argv[i + 1]
        del argv[i:i + 2]

    from engine.runtime_paths import print_startup_banner
    print_startup_banner()

    if not argv:
        print("Usage: python run_scene.py <scene_name> [turns] [--resume] [--ollama-host URL] [--all-ollama MODEL]")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    scene_name = argv[0]
    num_turns = int(argv[1]) if len(argv) > 1 else None

    config_path = scenes_dir / f"{scene_name}.md"
    if not config_path.exists():
        print(f"Unknown scene: {scene_name}")
        print(f"Available scenes: {', '.join(available)}")
        sys.exit(1)

    from engine.md_loader import configure_from_md
    from engine.scene_runner import run_scene
    config = configure_from_md(config_path)
    asyncio.run(run_scene(config, num_turns, resume=resume))


if __name__ == "__main__":
    main()
