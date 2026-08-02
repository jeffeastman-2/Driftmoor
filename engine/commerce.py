"""Buy/sell settlement — the coin leg of shop transactions.

Phase 7 of docs/economy-transactions-plan.md. The LATN layer grounds a buy to a
shop CatalogEntry and a sell to an owned Thing (engine.latn_integration.
resolve_commerce); this module settles the agreed exchange through the one
transfer primitive (engine.item_transfer.transfer_thing), with clear refusal
reasons. Buy settlement accepts an engine-approved negotiated price; the
negotiation policy itself lives in ``engine.negotiation``. Sells use a fixed
fraction of value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from engine.item_transfer import transfer_thing


# A shop pays this fraction of a good's value when buying it from a player (the
# bid/ask spread — buy low, sell high). 0.5 = half of market value.
BUY_RATE = 0.5


@dataclass
class CommerceResult:
    """Outcome of a buy/sell. ``reason`` is empty on success, else a machine code
    ("not_for_sale", "cannot_afford", "not_sellable", "not_owned", "shop_broke",
    "unknown"). ``thing`` is the transferred Thing on success; ``price_cp`` is the
    coin that (would have) changed hands."""

    ok: bool
    reason: str = ""
    thing: object = None
    price_cp: int = 0


def settle_buy(entry, *, buyer_id: str, shopkeeper_id: str, catalog,
               characters: dict, agreed_price_cp: Optional[int] = None) -> CommerceResult:
    """Player buys ``entry`` from the shopkeeper at its listed price. Materializes
    a fresh Thing from the catalog, then moves it (and the coin) via the transfer
    primitive. Refuses if the good isn't for sale or the buyer can't afford it."""
    listed = getattr(entry, "listed_price_cp", None)
    price = agreed_price_cp if agreed_price_cp is not None else listed
    if listed is not None and price is not None:
        # A buyer may negotiate downward, never silently turn settlement into an
        # overpayment or a free/negative transfer.
        price = min(int(listed), max(1, int(price)))
    if price is None:
        return CommerceResult(False, "not_for_sale")
    buyer = _char(characters, buyer_id)
    if buyer is None or not buyer.can_afford(price):
        return CommerceResult(False, "cannot_afford", price_cp=price)
    thing = catalog.materialize(entry.catalog_id, owner=shopkeeper_id)
    if thing is None:
        return CommerceResult(False, "unknown", price_cp=price)
    r = transfer_thing(
        thing, from_id=shopkeeper_id, to_id=buyer_id, characters=characters,
        move_ownership=True, coin_cp=price)
    if not r.ok:
        return CommerceResult(False, r.reason, price_cp=price)
    return CommerceResult(True, thing=thing, price_cp=price)


def settle_sell(thing, *, seller_id: str, shopkeeper_id: str,
                characters: dict) -> CommerceResult:
    """Player sells ``thing`` to the shopkeeper for a fraction of its value.
    Refuses an unpriceable good, one the seller doesn't own, or a shopkeeper who
    can't cover the bid."""
    value = getattr(thing, "value_cp", None)
    if value is None:
        return CommerceResult(False, "not_sellable")
    if getattr(thing, "owner", None) != seller_id:
        return CommerceResult(False, "not_owned")
    bid = max(1, round(value * BUY_RATE))
    shop = _char(characters, shopkeeper_id)
    if shop is None or not shop.can_afford(bid):
        return CommerceResult(False, "shop_broke", price_cp=bid)
    r = transfer_thing(
        thing, from_id=seller_id, to_id=shopkeeper_id, characters=characters,
        move_ownership=True, coin_cp=bid)
    if not r.ok:
        return CommerceResult(False, r.reason, price_cp=bid)
    return CommerceResult(True, thing=thing, price_cp=bid)


def _char(characters: dict, cid: Optional[str]):
    cs = characters.get(cid) if cid else None
    return getattr(cs, "character", None) if cs else None
