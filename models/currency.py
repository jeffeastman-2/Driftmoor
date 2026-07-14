"""Coin arithmetic for the town economy.

Money is a single integer count of **copper pieces** (``_cp``) everywhere in the
engine — never a float, never separate coin piles. One integer means change is
always exact. Denominations are a *display formatter*, not a data model.

5e denominations (copper-valued): cp=1, sp=10, ep=50, gp=100, pp=1000.
"""

from __future__ import annotations

import re
from typing import Optional

# Denomination → its value in copper. Both the abbreviation and the full word.
_DENOM: dict[str, int] = {
    "cp": 1, "copper": 1,
    "sp": 10, "silver": 10,
    "ep": 50, "electrum": 50,
    "gp": 100, "gold": 100,
    "pp": 1000, "platinum": 1000,
}

_PAIR_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(cp|sp|ep|gp|pp|copper|silver|electrum|gold|platinum)\b",
    re.IGNORECASE,
)
# A digit-dash-digit range ("2-5 gp") is ambiguous — decline to guess.
_RANGE_RE = re.compile(r"\d\s*[-–—]\s*\d")
# Words that mark an unpriceable / non-numeric value.
_VAGUE_RE = re.compile(r"var(y|ies)|arrangement|negotiab|barter|priceless|trade", re.IGNORECASE)


def parse_coins(s: Optional[str]) -> Optional[int]:
    """Parse an authored price string to an integer copper amount, or ``None``.

    "5 gp" → 500, "1 gp 4 sp" → 140, "7 cp" → 7, "1.5 gp" → 150.
    Ranges ("2-5 gp"), vague values ("Varies", "by arrangement"), empty strings,
    and anything without a recognized ``<number> <denomination>`` pair → ``None``.
    """
    if not s:
        return None
    t = s.strip()
    if not t or _RANGE_RE.search(t) or _VAGUE_RE.search(t):
        return None
    pairs = _PAIR_RE.findall(t)
    if not pairs:
        return None
    total = 0.0
    for num, denom in pairs:
        total += float(num) * _DENOM[denom.lower()]
    return int(round(total))


def format_coins(cp: Optional[int]) -> str:
    """Format a copper amount for display in gp/sp/cp. 140 → "1 gp 4 sp";
    0 → "0 cp"; ``None`` → "" (unknown/unpriced). ep/pp collapse into gp/cp so
    the display stays to the three denominations shops actually quote."""
    if cp is None:
        return ""
    n = int(cp)
    if n == 0:
        return "0 cp"
    sign = "-" if n < 0 else ""
    n = abs(n)
    gp, rem = divmod(n, 100)
    sp, c = divmod(rem, 10)
    parts: list[str] = []
    if gp:
        parts.append(f"{gp} gp")
    if sp:
        parts.append(f"{sp} sp")
    if c:
        parts.append(f"{c} cp")
    return sign + " ".join(parts)
