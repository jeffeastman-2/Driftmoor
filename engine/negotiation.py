"""Bounded, engine-owned shop haggling policy.

This is the v0.1 monetary-counteroffer slice of the larger reusable negotiation
plan.  It deliberately stays deterministic: the authored merchant personality
sets a reservation floor, while richer checks, disposition shifts, barter, and
multi-round bargaining remain later extensions.
"""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class HagglePolicy:
    max_discount: float = 0.0

    def minimum_price(self, ask_cp: int) -> int:
        # Round upward: a reservation price must never accidentally exceed the
        # authored maximum discount because of fractional copper.
        return max(1, math.ceil(int(ask_cp) * (1.0 - self.max_discount)))


@dataclass(frozen=True)
class CounterofferResult:
    accepted: bool
    agreed_cp: int | None = None
    counter_cp: int | None = None


_MERCHANT_POLICIES = {
    # Authored: DC 13 and a 10–20% reduction; he genuinely enjoys haggling.
    "kelem": HagglePolicy(max_discount=0.20),
    # These merchants permit modest movement in their authored inventory notes.
    "lytha": HagglePolicy(max_discount=0.10),
    "darrin": HagglePolicy(max_discount=0.10),
    "tavian": HagglePolicy(max_discount=0.10),
    # Jorgen expects a fair price, though a good approach may earn a token cut.
    "jorgen": HagglePolicy(max_discount=0.05),
}


def merchant_haggle_policy(shopkeeper_id: str, *, category: str = "") -> HagglePolicy:
    policy = _MERCHANT_POLICIES.get((shopkeeper_id or "").lower(), HagglePolicy())
    # Kelem's magical stock has a harder authored DC; for this deterministic
    # v0.1 slice, express that as half his mundane flexibility.
    if (shopkeeper_id or "").lower() == "kelem" and category == "magical":
        return HagglePolicy(max_discount=0.10)
    return policy


def evaluate_counteroffer(*, ask_cp: int, offered_cp: int,
                          policy: HagglePolicy) -> CounterofferResult:
    ask = max(1, int(ask_cp))
    offer = int(offered_cp)
    floor = policy.minimum_price(ask)
    if offer >= ask:
        return CounterofferResult(True, agreed_cp=ask)
    if offer >= floor:
        return CounterofferResult(True, agreed_cp=offer)
    if floor < ask:
        return CounterofferResult(False, counter_cp=floor)
    return CounterofferResult(False)

