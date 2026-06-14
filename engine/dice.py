"""Dice / damage-expression rolling.

Extracted from engine.session (low-risk refactor) so combat (attack damage)
and geometry (boundary-crossing damage) share one implementation rather than
crossing cluster boundaries. Pure: only re + random.
"""

from __future__ import annotations

import random
import re


def _roll_damage_expr(expr: str) -> int:
    """Roll a damage expression such as '1d6', '2d4+2', or '1d8 slashing'.

    Ignores non-numeric descriptors (damage type words).
    Returns at least 0.
    """
    total = 0
    # Roll all dice terms: NdM
    for m in re.finditer(r'(\d+)\s*[dD]\s*(\d+)', expr):
        count, sides = int(m.group(1)), int(m.group(2))
        for _ in range(count):
            total += random.randint(1, sides)
    # Apply flat modifier: the +/- numbers not part of a dice term
    remainder = re.sub(r'\d+\s*[dD]\s*\d+', '', expr)
    for m in re.finditer(r'([+-]\s*\d+)', remainder):
        total += int(m.group(1).replace(' ', ''))
    # Plain integer with no sign (rare, e.g. just "5")
    plain = remainder.strip()
    if re.fullmatch(r'\d+', plain):
        total += int(plain)
    return max(0, total)
