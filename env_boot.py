"""Zero-dependency project .env loader.

Lets ``python run_scene.py`` / ``run_all.py`` pick up a project-root ``.env``
without having to ``source`` it first. Parses simple ``KEY=VALUE`` lines (an
optional leading ``export`` and surrounding quotes are stripped). Existing
environment values WIN, so an explicit ``export`` or a CLI override is never
clobbered. Call this before importing engine modules that read the environment.
"""

import os
from pathlib import Path


def load_project_dotenv(filename: str = ".env") -> int:
    """Load <project-root>/<filename> into os.environ (without overriding
    already-set vars). Returns the number of new vars set; 0 if absent."""
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
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded
