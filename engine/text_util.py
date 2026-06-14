"""Small generic text helpers shared across the engine.

Extracted from engine.session so both the turn loop and the persistence layer
(via _shared_exam_key) can use them without crossing module boundaries. Pure.
"""

from __future__ import annotations

import re
from typing import Optional


def _normalize_target_name(target: Optional[str]) -> str:
    """Normalize item target text for loop-key comparisons."""
    if not target:
        return ""
    s = target.lower().strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()
