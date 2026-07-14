"""Turn-loop wiring for buy/sell (engine.session._handle_commerce +
_current_shopkeeper). Exercises the handler with a minimal session stub."""

from types import SimpleNamespace as NS

from models.character import Character
from models.thing import Thing
from models.shop_catalog import ShopCatalog
from engine.session import _handle_commerce, _current_shopkeeper


def _cs(cid, purse=0, inv=None):
    """A CharacterSession stand-in complete enough for loadout.materialize_things."""
    c = Character(id=cid, name=cid.title(), race="Human", character_type="npc",
                  purse_cp=purse, inventory=list(inv or []))
    return NS(character=c, scene_handle="", pack=[], weapons=[], armor=None,
              wielded=set(), held_items=set(), things=[], episodic_memory=[])


def _catalog():
    return ShopCatalog([Thing(id="meat_pie", name="Meat pie", price="4 cp",
                              vendor_id="maribel")])


def _buy(cs, chars, items, text="I buy the meat pie", log=None):
    return _handle_commerce(
        intent_text=text, character_id="player", characters=chars, items=items,
        cs=cs, turn_num=1, game_time=None, attack_log=log if log is not None else [],
        recent_events=[], shopkeeper="maribel", catalog=_catalog())


class TestShopkeeperDetection:
    def test_present_vendor_is_the_shopkeeper(self):
        cat = _catalog()
        chars = {"player": _cs("player"), "maribel": _cs("maribel")}
        assert _current_shopkeeper(chars, {"player", "maribel"}, cat) == "maribel"

    def test_no_shopkeeper_when_vendor_absent(self):
        cat = _catalog()
        chars = {"player": _cs("player"), "maribel": _cs("maribel")}
        assert _current_shopkeeper(chars, {"player"}, cat) is None


class TestBuyWiring:
    def test_buy_gives_the_pie_and_moves_coin(self):
        chars = {"player": _cs("player", 100), "maribel": _cs("maribel", 0)}
        items, log = {}, []
        assert _buy(chars["player"], chars, items, log=log) is True
        assert chars["player"].character.purse_cp == 96
        assert chars["maribel"].character.purse_cp == 4
        assert any(getattr(p, "id", "").startswith("meat_pie") for p in chars["player"].pack)
        assert any(k.startswith("meat_pie") for k in items)
        assert any("COMMERCE" in l and "bought" in l for l in log)

    def test_broke_buyer_is_handled_but_refused(self):
        chars = {"player": _cs("player", 2), "maribel": _cs("maribel", 0)}
        items, log = {}, []
        assert _buy(chars["player"], chars, items, text="buy the meat pie", log=log) is True
        assert chars["player"].character.purse_cp == 2
        assert not items
        assert any("afford" in l for l in log)

    def test_non_commerce_intent_not_handled(self):
        chars = {"player": _cs("player", 100), "maribel": _cs("maribel", 0)}
        assert _buy(chars["player"], chars, {}, text="I look around the shop") is False

    def test_take_a_shop_good_buys_it(self):
        # "I'll take the meat pie" in the shop settles as a purchase.
        chars = {"player": _cs("player", 100), "maribel": _cs("maribel", 0)}
        items, log = {}, []
        assert _buy(chars["player"], chars, items, text="I'll take the meat pie", log=log) is True
        assert chars["player"].character.purse_cp == 96
        assert any(getattr(p, "id", "").startswith("meat_pie") for p in chars["player"].pack)
        assert any("SETTLED by the engine" in l for l in log)


class TestSellWiring:
    def test_sell_removes_item_and_pays(self):
        dagger = Thing(id="dagger", name="Dagger", value_cp=200,
                       owner="player", holder="player")
        pc = _cs("player", 0, inv=["dagger"]); pc.pack = [dagger]
        chars = {"player": pc, "maribel": _cs("maribel", 1000)}
        items, log = {"dagger": dagger}, []
        handled = _handle_commerce(
            intent_text="I sell my dagger", character_id="player", characters=chars,
            items=items, cs=pc, turn_num=1, game_time=None, attack_log=log,
            recent_events=[], shopkeeper="maribel", catalog=_catalog())
        assert handled is True
        assert chars["player"].character.purse_cp == 100    # half of 200
        assert chars["maribel"].character.purse_cp == 900
        assert dagger.owner == "maribel"
        assert "dagger" not in items
        assert all(getattr(p, "id", "") != "dagger" for p in pc.pack)
