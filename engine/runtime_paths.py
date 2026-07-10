"""Runtime state directory layout.

A single invocation of ``run_scene.py`` or ``run_all.py`` is one *session*.
Each session gets a unique, timestamped directory under the configured state
root; every scene's checkpoints, transcripts, story, and runtime map land in
a subdirectory named after the scene.

Layout::

    <state_root>/
        <session_id>/
            manifest.json
            <scene_name>/
                turn_0001.json
                ...
                <scene_name>_transcript.txt
                <scene_name>_story.txt
                <scene_name>_map.html

``<session_id>`` is ``YYYY-MM-DDTHHMMSS__<host>__<model-tag>``, where
``<model-tag>`` is taken from ``$LLM_FORCE_OLLAMA_MODEL`` if set, else
``mixed`` (the scene config picks per-agent providers).

Environment variables
---------------------
``DRIFTMOOR_STATE_ROOT``
    Absolute or relative path for the state root. Defaults to
    ``<repo>/runtime/state``. Set this to e.g.
    ``~/UltraWork/driftmoor/runs`` to land sessions on a NAS.

``DRIFTMOOR_SESSION_LABEL``
    Optional human-readable suffix appended to the session id (e.g.
    ``debug-spell-fix``). Useful when you want to find a run by purpose
    rather than by timestamp.

Resume
------
``find_latest_session_id()`` returns the most recent session id under the
state root and is used by ``run_all.py --resume``. Explicit session ids
can be passed via ``$DRIFTMOOR_SESSION_ID`` to pin resumes deterministically.
"""

from __future__ import annotations

import json
import os
import platform
import re
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Cached per-process session id. Computed lazily so tests can manipulate
# environment variables before the first call.
_session_id: str | None = None


def get_state_root() -> Path:
    """Return the state root directory, creating it if needed."""
    raw = os.environ.get("DRIFTMOOR_STATE_ROOT", "").strip()
    if raw:
        root = Path(raw).expanduser().resolve()
    else:
        root = _REPO_ROOT / "runtime" / "state"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _slugify(value: str) -> str:
    """Filesystem-safe slug. Replaces non-alphanumerics with '-'."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "x"


def _compute_session_id() -> str:
    explicit = os.environ.get("DRIFTMOOR_SESSION_ID", "").strip()
    if explicit:
        return _slugify(explicit)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    host = _slugify(platform.node().split(".")[0] or "host")
    model = os.environ.get("LLM_FORCE_OLLAMA_MODEL", "").strip() or "mixed"
    label = os.environ.get("DRIFTMOOR_SESSION_LABEL", "").strip()

    parts = [timestamp, host, _slugify(model)]
    if label:
        parts.append(_slugify(label))
    return "__".join(parts)


def current_session_id() -> str:
    """Return the cached session id for this process."""
    global _session_id
    if _session_id is None:
        _session_id = _compute_session_id()
    return _session_id


def reset_session_id() -> None:
    """Clear the cached session id. Intended for tests."""
    global _session_id
    _session_id = None


def get_session_dir() -> Path:
    """Return the directory for the current session, creating it on first
    access and writing a manifest with metadata.
    """
    session_dir = get_state_root() / current_session_id()
    first_time = not session_dir.exists()
    session_dir.mkdir(parents=True, exist_ok=True)
    if first_time:
        _write_manifest(session_dir)
    return session_dir


def get_scene_dir(scene_name: str) -> Path:
    """Return the per-scene subdirectory under the current session."""
    scene_dir = get_session_dir() / scene_name
    scene_dir.mkdir(parents=True, exist_ok=True)
    return scene_dir


def _write_manifest(session_dir: Path) -> None:
    manifest = {
        "session_id": current_session_id(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
        "env": {
            "OLLAMA_HOST": os.environ.get("OLLAMA_HOST", ""),
            "LLM_FORCE_OLLAMA_MODEL": os.environ.get("LLM_FORCE_OLLAMA_MODEL", ""),
            "DRIFTMOOR_STATE_ROOT": os.environ.get("DRIFTMOOR_STATE_ROOT", ""),
            "DRIFTMOOR_SESSION_LABEL": os.environ.get("DRIFTMOOR_SESSION_LABEL", ""),
        },
    }
    try:
        (session_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    except OSError:
        # Manifest is best-effort; don't crash a run for it.
        pass


def find_latest_session_id() -> str | None:
    """Return the most recent session id under the state root, or None."""
    root = get_state_root()
    candidates = [p for p in root.iterdir() if p.is_dir()]
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0].name


def print_startup_banner() -> None:
    """Print the active runtime configuration. Useful so users can see at
    a glance whether env vars from .env.local / .env.ultra took effect.
    """
    ollama_host = os.environ.get("OLLAMA_HOST", "").strip() or "http://localhost:11434 (default)"
    forced = os.environ.get("LLM_FORCE_OLLAMA_MODEL", "").strip()
    state_root = get_state_root()
    env_selector = os.environ.get("DRIFTMOOR_ENV_FILE", "").strip() or "(auto)"
    env_loaded = os.environ.get("DRIFTMOOR_ENV_FILES_LOADED", "").strip() or "(none found)"

    print("Driftmoor configuration:")
    print(f"  DRIFTMOOR_ENV_FILE     = {env_selector}")
    print(f"  env files loaded       = {env_loaded}")
    print(f"  OLLAMA_HOST            = {ollama_host}")
    if forced:
        print(f"  LLM_FORCE_OLLAMA_MODEL = {forced}  (every agent forced)")
    else:
        print(f"  LLM_FORCE_OLLAMA_MODEL = (unset; using scene-authored providers)")
    print(f"  DRIFTMOOR_STATE_ROOT   = {state_root}")
    print(f"  session_id             = {current_session_id()}")
    print()
