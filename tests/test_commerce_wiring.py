"""Turn-loop wiring for buy/sell (engine.session._handle_commerce +
_current_shopkeeper). Buy is a quote->confirm exchange; sell settles in one step."""

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


def _chars(player_purse=100, keeper_purse=0):
    return {"player": _cs("player", player_purse), "maribel": _cs("maribel", keeper_purse)}


def _commerce(chars, items, text, pending, log=None):
    return _handle_commerce(
        intent_text=text, character_id="player", characters=chars, items=items,
        cs=chars["player"], turn_num=1, game_time=None,
        attack_log=log if log is not None else [], recent_events=[],
        shopkeeper="maribel", catalog=_catalog(), pending_purchases=pending)


class TestShopkeeperDetection:
    def test_present_vendor_is_the_shopkeeper(self):
        assert _current_shopkeeper(_chars(), {"player", "maribel"}, _catalog()) == "maribel"

    def test_no_shopkeeper_when_vendor_absent(self):
        assert _current_shopkeeper(_chars(), {"player"}, _catalog()) is None


class TestBuyQuoteConfirm:
    def test_quote_then_confirm_settles(self):
        chars, items, pend = _chars(100, 0), {}, {}
        log = []
        # 1. buy -> a quote, nothing settled, a standing offer recorded.
        assert _commerce(chars, items, "I buy the meat pie", pend, log) is True
        assert chars["player"].character.purse_cp == 100
        assert not items and "player" in pend
        assert any("OFFER" in l for l in log)
        # 2. "yes" -> the sale completes.
        log2 = []
        assert _commerce(chars, items, "yes", pend, log2) is True
        assert chars["player"].character.purse_cp == 96
        assert any(getattr(p, "id", "").startswith("meat_pie") for p in chars["player"].pack)
        assert "player" not in pend
        assert any("SETTLED" in l and "bought" in l for l in log2)

    def test_take_a_shop_good_also_quotes(self):
        chars, items, pend = _chars(100, 0), {}, {}
        assert _commerce(chars, items, "I'll take the meat pie", pend) is True
        assert "player" in pend and chars["player"].character.purse_cp == 100

    def test_decline_lapses_the_offer(self):
        chars, items, pend = _chars(100, 0), {}, {}
        _commerce(chars, items, "buy the meat pie", pend)
        assert "player" in pend
        log = []
        assert _commerce(chars, items, "nope", pend, log) is True
        assert chars["player"].character.purse_cp == 100
        assert not items and "player" not in pend
        assert any("lapse" in l for l in log)

    def test_unrelated_intent_lapses_the_offer(self):
        chars, items, pend = _chars(100, 0), {}, {}
        _commerce(chars, items, "buy the meat pie", pend)
        # an unrelated (non yes/no, non-commerce) intent lets the offer lapse.
        assert _commerce(chars, items, "I look at the shelves", pend) is True
        assert "player" not in pend and chars["player"].character.purse_cp == 100

    def test_broke_buyer_refused_at_confirm(self):
        chars, items, pend = _chars(2, 0), {}, {}
        _commerce(chars, items, "buy the meat pie", pend)     # quote (always offered)
        log = []
        _commerce(chars, items, "yes", pend, log)             # confirm -> can't pay
        assert chars["player"].character.purse_cp == 2
        assert not items
        assert any("afford" in l for l in log)

    def test_non_commerce_intent_not_handled(self):
        assert _commerce(_chars(), {}, "I look around the shop", {}) is False


class TestSellWiring:
    def test_sell_settles_in_one_step(self):
        dagger = Thing(id="dagger", name="Dagger", value_cp=200, owner="player", holder="player")
        pc = _cs("player", 0, inv=["dagger"]); pc.pack = [dagger]
        chars = {"player": pc, "maribel": _cs("maribel", 1000)}
        items = {"dagger": dagger}
        handled = _handle_commerce(
            intent_text="I sell my dagger", character_id="player", characters=chars,
            items=items, cs=pc, turn_num=1, game_time=None, attack_log=[],
            recent_events=[], shopkeeper="maribel", catalog=_catalog(), pending_purchases={})
        assert handled is True
        assert chars["player"].character.purse_cp == 100
        assert dagger.owner == "maribel" and "dagger" not in items
