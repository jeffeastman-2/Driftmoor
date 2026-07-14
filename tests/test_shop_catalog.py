"""Shop catalog + lazy materialization (models.shop_catalog)."""

from pathlib import Path

from models.thing import Thing
from models.shop_catalog import ShopCatalog, CatalogEntry


def _catalog():
    # Hand-built, deterministic: two of maribel's goods, one of jorgen's.
    return ShopCatalog([
        Thing(id="meat_pie", name="Meat pie", price="4 cp", vendor_id="maribel"),
        Thing(id="sweet_roll", name="Sweet roll", price="3 cp", vendor_id="maribel"),
        Thing(id="rope", name="Rope, hempen", price="1 gp", vendor_id="jorgen"),
    ])


class TestCatalogIndex:
    def test_entries_for_shop(self):
        c = _catalog()
        maribel = {e.catalog_id for e in c.entries_for("maribel")}
        assert maribel == {"meat_pie", "sweet_roll"}
        assert {e.catalog_id for e in c.entries_for("jorgen")} == {"rope"}

    def test_entry_carries_price_and_shop(self):
        c = _catalog()
        pie = next(e for e in c.entries_for("maribel") if e.catalog_id == "meat_pie")
        assert isinstance(pie, CatalogEntry)
        assert pie.listed_price_cp == 4
        assert pie.value_cp == 4
        assert pie.shop_id == "maribel"

    def test_get_returns_template(self):
        c = _catalog()
        assert c.get("rope").listed_price_cp == 100
        assert c.get("nope") is None


class TestMaterialize:
    def test_materialize_makes_a_shop_owned_instance(self):
        c = _catalog()
        pie = c.materialize("meat_pie")
        assert pie is not None
        assert pie.owner == "maribel"       # the shopkeeper still owns it
        assert pie.holder is None           # sitting in the shop, unheld
        assert pie.listed_price_cp == 4
        assert pie.id != "meat_pie"         # a concrete instance, not the template

    def test_materialize_twice_yields_independent_things(self):
        c = _catalog()
        a = c.materialize("meat_pie")
        b = c.materialize("meat_pie")
        assert a.id != b.id
        a.holder = "player"                 # mutating one must not touch the other
        assert b.holder is None
        # ...and neither touched the template.
        assert c.get("meat_pie").holder is None

    def test_materialize_can_place_and_override_owner(self):
        c = _catalog()
        roll = c.materialize("sweet_roll", owner="thief", zone="ALLEY")
        assert roll.owner == "thief"
        assert roll.zone == "ALLEY"

    def test_materialize_unknown_is_none(self):
        assert _catalog().materialize("dragon") is None


class TestRealCatalog:
    def test_builds_from_scenario_and_a_shop_has_stock(self):
        c = ShopCatalog.from_things_dir(Path("scenario/things"))
        # jorgen runs the general store; he should have priced stock.
        jorgen = c.entries_for("jorgen")
        assert jorgen, "expected the general store to have for-sale goods"
        assert all(e.listed_price_cp is not None for e in jorgen)
        # every catalog entry materializes to a shop-owned Thing.
        sample = jorgen[0]
        inst = c.materialize(sample.catalog_id)
        assert inst.owner == "jorgen" and inst.holder is None
        assert inst.listed_price_cp == sample.listed_price_cp
