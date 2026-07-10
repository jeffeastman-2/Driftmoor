"""Zero-dependency project .env loader.

Lets ``python run_scene.py`` / ``run_all.py`` pick up project-root env files
without having to ``source`` first. By default it loads, in order:

    .env -> .env.local -> .env.ultra

and only sets keys not already present in ``os.environ``. This means explicit
shell exports/CLI overrides always win. To force a specific file, set
``DRIFTMOOR_ENV_FILE`` (for example ``.env.ultra``).
"""

import os
from pathlib import Path


def _load_single_env_file(filename: str, protected_keys: set[str]) -> int:
    """Load <project-root>/<filename> into os.environ.

    Keys present in ``protected_keys`` (the process env before loading starts)
    are never overridden. Other keys may be set/updated so later env files can
    override earlier defaults.
    """
    path = Path(__file__).resolve().parent / filename
    if not path.exists():
        return 0
    loaded = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or key in protected_keys:
            continue
        if os.environ.get(key) != value:
            os.environ[key] = value
            loaded += 1
    return loaded


def load_project_dotenv(filename: str | None = None) -> int:
    """Load project env files into os.environ, preserving existing values.

    If ``filename`` is provided, only that file is loaded. Otherwise, loads
    either ``DRIFTMOOR_ENV_FILE`` (if set) or the default stack:
    ``.env``, ``.env.local``, ``.env.ultra``.
    """
    protected_keys = set(os.environ.keys())

    if filename:
        loaded = _load_single_env_file(filename, protected_keys)
        os.environ["DRIFTMOOR_ENV_FILES_LOADED"] = filename
        return loaded

    explicit = os.environ.get("DRIFTMOOR_ENV_FILE", "").strip()
    candidates = [explicit] if explicit else [".env", ".env.local", ".env.ultra"]

    total = 0
    loaded_files: list[str] = []
    for candidate in candidates:
        path = Path(__file__).resolve().parent / candidate
        if path.exists():
            loaded_files.append(candidate)
        total += _load_single_env_file(candidate, protected_keys)
    os.environ["DRIFTMOOR_ENV_FILES_LOADED"] = ",".join(loaded_files)
    return total
