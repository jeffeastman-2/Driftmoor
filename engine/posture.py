"""Persistent, LATN-classified character posture actions."""

from __future__ import annotations

import math
import re
from typing import Optional

POSTURE_DIMS = ("sit", "stand", "kneel", "prone")
POSTURE_BY_DIM = {
    "sit": "seated",
    "stand": "standing",
    "kneel": "kneeling",
    "prone": "prone",
}


def resolve_posture(intent_text: str) -> Optional[str]:
    """Return the requested persistent posture, using LATN verb dimensions."""
    from engine.latn_resolver import intent_action_dims

    dims = intent_action_dims(intent_text or "", POSTURE_DIMS)
    for dim in POSTURE_DIMS:
        if dim in dims:
            return POSTURE_BY_DIM[dim]
    return None


def posture_landmark_target(
    intent_text: str,
    posture: str | None,
    scene_geometry,
    actor_position: tuple | None,
) -> tuple[float, float, str] | None:
    """Ground optional furniture in a posture phrase to the nearest landmark."""
    if posture != "seated" or scene_geometry is None:
        return None
    words = set(re.findall(r"[a-z0-9]+", (intent_text or "").lower()))
    furniture = words & {"chair", "seat", "bench", "stool", "throne", "bed"}
    if not furniture:
        return None
    ax, ay = (float(actor_position[0]), float(actor_position[1])) if actor_position else (0.0, 0.0)
    candidates = []
    for name, pos in scene_geometry.landmarks.items():
        name_words = set(re.findall(r"[a-z0-9]+", name.lower()))
        if furniture & name_words:
            candidates.append((math.hypot(pos.x - ax, pos.y - ay), name, pos))
    if not candidates:
        return None
    _distance, _name, pos = min(candidates)
    zone = (scene_geometry.zone_at(pos) or "").upper()
    return (float(pos.x), float(pos.y), zone)


def apply_posture(cs, posture: str) -> None:
    """Commit posture and synchronize the mechanical prone condition."""
    cs.posture = posture
    conditions = getattr(cs.character, "conditions", None)
    if conditions is None:
        return
    conditions[:] = [c for c in conditions if str(c).lower() != "prone"]
    if posture == "prone":
        conditions.append("prone")


def settle_posture(
    cs, posture: str, current_position: tuple | None,
    target: tuple | None = None, reach_ft: float = 5.0,
) -> bool:
    """Apply posture only after reaching optional furniture."""
    if target is not None:
        if current_position is None:
            return False
        if math.hypot(
            float(current_position[0]) - float(target[0]),
            float(current_position[1]) - float(target[1]),
        ) > reach_ft:
            return False
    apply_posture(cs, posture)
    return True
