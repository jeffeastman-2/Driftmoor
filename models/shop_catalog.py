"""Structured shop catalog + lazy materialization of shop goods.

Phase 4 of docs/economy-transactions-plan.md. The priced shop goods loaded by
``models.thing_loader.load_all_things`` (already carrying ``value_cp`` /
``listed_price_cp`` / ``owner`` from the Phase-1 market facet) are the catalog
*templates*. A shop's stock stays as light templates — not instantiated into the
live scene — until a player examines or buys, at which point ``materialize``
clones a template into a concrete ``Thing`` owned by the shopkeeper. Materializing
twice yields two independent Things, so buying two loaves gives you two loaves.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from models.thing import Thing
from models.thing_loader import load_all_things


@dataclass(frozen=True)
class CatalogEntry:
    """A lightweight, display-ready view of one for-sale good — enough to list a
    shop's stock (in a menu, a shelf tooltip, a prompt) without materializing a
    full Thing."""

    catalog_id: str
    name: str
    listed_price_cp: Optional[int]
    value_cp: Optional[int]
    category: str
    weight_lb: float
    shop_id: str  # the owning shopkeeper (vendor)

    @classmethod
    def from_thing(cls, t: Thing) -> "CatalogEntry":
        return cls(
            catalog_id=t.id,
            name=t.name or t.label or t.id,
            listed_price_cp=t.listed_price_cp,
            value_cp=t.value_cp,
            category=t.category,
            weight_lb=t.weight_lb,
            shop_id=t.owner or t.vendor_id or "",
        )


class ShopCatalog:
    """Index of shop-good *templates* by catalog id and by shop, plus lazy
    materialization of concrete instances."""

    def __init__(self, templates: list[Thing]):
        self._templates: dict[str, Thing] = {t.id: t for t in templates}
        self._counter: dict[str, int] = {}

    @classmethod
    def from_things_dir(cls, things_dir: Path) -> "ShopCatalog":
        """Build the catalog from the scenario's things directory. A template is
        any for-sale good: it has a vendor and a listed price."""
        goods = [
            t for t in load_all_things(things_dir)
            if t.vendor_id and t.listed_price_cp is not None
        ]
        return cls(goods)

    def get(self, catalog_id: str) -> Optional[Thing]:
        """The template for ``catalog_id`` (do not mutate it — materialize)."""
        return self._templates.get(catalog_id)

    def entries(self) -> list[CatalogEntry]:
        return [CatalogEntry.from_thing(t) for t in self._templates.values()]

    def entries_for(self, shop_id: str) -> list[CatalogEntry]:
        """The goods a shopkeeper openly advertises in their public shop.

        Priced stock kept in a private sub-place remains a valid Thing but is
        not part of the initial ``what do you have for sale?`` response.
        """
        return [
            CatalogEntry.from_thing(t) for t in self._templates.values()
            if (t.owner or t.vendor_id) == shop_id
            and (t.location_id or "").rstrip("/").split("/")[-1] != "living_loft"
        ]

    def materialize(
        self,
        catalog_id: str,
        *,
        owner: Optional[str] = None,
        zone: Optional[str] = None,
        position: object = None,
    ) -> Optional[Thing]:
        """Clone a template into a fresh, concrete Thing — owned by the shopkeeper
        (or the ``owner`` override), not yet held, optionally placed at
        ``zone``/``position``. Independent per call (unique id, fresh mutable
        state), so repeated calls yield distinct Things. ``None`` for an unknown
        catalog id."""
        tmpl = self._templates.get(catalog_id)
        if tmpl is None:
            return None
        n = self._counter.get(catalog_id, 0) + 1
        self._counter[catalog_id] = n
        inst = copy.deepcopy(tmpl)
        inst.id = f"{catalog_id}_i{n}"
        inst.holder = None
        inst.owner = owner if owner is not None else tmpl.owner
        inst.discovered_by = set()
        if zone is not None:
            inst.zone = zone
        if position is not None:
            inst.position = position
        return inst
