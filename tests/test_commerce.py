"""Buy/sell verbs (LATN grounding) + settlement (engine.commerce)."""

from types import SimpleNamespace as NS

from models.character import Character
from models.thing import Thing
from models.shop_catalog import ShopCatalog, CatalogEntry
from engine import commerce
from engine.latn_integration import resolve_commerce


def _cs(cid, purse=0, inv=None):
    c = Character(id=cid, name=cid.title(), race="Human", character_type="npc",
                  purse_cp=purse, inventory=list(inv or []))
    return NS(character=c, scene_handle="")


def _catalog():
    return ShopCatalog([
        Thing(id="meat_pie", name="Meat pie", price="4 cp", vendor_id="maribel"),
        Thing(id="sweet_roll", name="Sweet roll", price="3 cp", vendor_id="maribel"),
    ])


class TestGrounding:
    def test_buy_grounds_catalog_entry(self):
        entries = _catalog().entries_for("maribel")
        res = resolve_commerce("I buy the meat pie", {}, {}, "", entries)
        assert res is not None
        verb, ent = res
        assert verb == "buy" and ent.catalog_id == "meat_pie"

    def test_buy_distinguishes_goods(self):
        entries = _catalog().entries_for("maribel")
        _, ent = resolve_commerce("buy the sweet roll", {}, {}, "", entries)
        assert ent.catalog_id == "sweet_roll"

    def test_sell_grounds_owned_item(self):
        dagger = Thing(id="dagger", label="dagger", zone="", owner="player")
        res = resolve_commerce("I sell my dagger", {"dagger": dagger}, {}, "", [])
        assert res is not None
        verb, item = res
        assert verb == "sell" and item.id == "dagger"

    def test_non_commerce_is_none(self):
        entries = _catalog().entries_for("maribel")
        assert resolve_commerce("I look at the pie", {}, {}, "", entries) is None


class TestSettleBuy:
    def _entry(self, cat, cid):
        return next(e for e in cat.entries_for("maribel") if e.catalog_id == cid)

    def test_buy_moves_pie_and_coin(self):
        cat = _catalog()
        chars = {"maribel": _cs("maribel", 0), "player": _cs("player", 100)}
        r = commerce.settle_buy(self._entry(cat, "meat_pie"), buyer_id="player",
                                shopkeeper_id="maribel", catalog=cat, characters=chars)
        assert r.ok and r.price_cp == 4
        assert r.thing.owner == "player" and r.thing.holder == "player"
        assert chars["player"].character.purse_cp == 96
        assert chars["maribel"].character.purse_cp == 4

    def test_buy_refused_when_broke(self):
        cat = _catalog()
        chars = {"maribel": _cs("maribel"), "player": _cs("player", 2)}
        r = commerce.settle_buy(self._entry(cat, "meat_pie"), buyer_id="player",
                                shopkeeper_id="maribel", catalog=cat, characters=chars)
        assert not r.ok and r.reason == "cannot_afford"
        assert chars["player"].character.purse_cp == 2

    def test_buy_not_for_sale(self):
        entry = CatalogEntry(catalog_id="heirloom", name="Heirloom",
                             listed_price_cp=None, value_cp=500, category="",
                             weight_lb=0.0, shop_id="maribel")
        chars = {"maribel": _cs("maribel"), "player": _cs("player", 1000)}
        r = commerce.settle_buy(entry, buyer_id="player", shopkeeper_id="maribel",
                                catalog=_catalog(), characters=chars)
        assert not r.ok and r.reason == "not_for_sale"

    def test_buy_two_pies_are_independent(self):
        cat = _catalog()
        chars = {"maribel": _cs("maribel", 0), "player": _cs("player", 100)}
        a = commerce.settle_buy(self._entry(cat, "meat_pie"), buyer_id="player",
                                shopkeeper_id="maribel", catalog=cat, characters=chars)
        b = commerce.settle_buy(self._entry(cat, "meat_pie"), buyer_id="player",
                                shopkeeper_id="maribel", catalog=cat, characters=chars)
        assert a.thing.id != b.thing.id
        assert chars["player"].character.purse_cp == 92   # paid 4 twice


class TestSettleSell:
    def test_sell_moves_item_and_coin_at_half_value(self):
        dagger = Thing(id="d", name="Dagger", value_cp=200, owner="player", holder="player")
        chars = {"maribel": _cs("maribel", 1000), "player": _cs("player", 0, inv=["d"])}
        r = commerce.settle_sell(dagger, seller_id="player", shopkeeper_id="maribel",
                                 characters=chars)
        assert r.ok and r.price_cp == 100          # 200 * BUY_RATE (0.5)
        assert dagger.owner == "maribel"
        assert chars["player"].character.purse_cp == 100
        assert chars["maribel"].character.purse_cp == 900

    def test_sell_refused_unpriceable(self):
        junk = Thing(id="j", name="Junk", owner="player")   # no value_cp
        chars = {"maribel": _cs("maribel", 1000), "player": _cs("player")}
        r = commerce.settle_sell(junk, seller_id="player", shopkeeper_id="maribel",
                                 characters=chars)
        assert not r.ok and r.reason == "not_sellable"

    def test_sell_refused_not_owned(self):
        dagger = Thing(id="d", name="Dagger", value_cp=200, owner="someone_else")
        chars = {"maribel": _cs("maribel", 1000), "player": _cs("player")}
        r = commerce.settle_sell(dagger, seller_id="player", shopkeeper_id="maribel",
                                 characters=chars)
        assert not r.ok and r.reason == "not_owned"

    def test_sell_refused_when_shop_broke(self):
        dagger = Thing(id="d", name="Dagger", value_cp=200, owner="player", holder="player")
        chars = {"maribel": _cs("maribel", 10), "player": _cs("player", 0, inv=["d"])}
        r = commerce.settle_sell(dagger, seller_id="player", shopkeeper_id="maribel",
                                 characters=chars)
        assert not r.ok and r.reason == "shop_broke"
        assert dagger.owner == "player"            # nothing moved
