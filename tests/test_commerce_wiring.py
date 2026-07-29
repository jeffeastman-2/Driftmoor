"""Turn-loop wiring for buy/sell (engine.session._handle_commerce +
_current_shopkeeper). A buy is a quote->confirm *sub-dialog inside one turn*:
the shopkeeper names a price and the buyer's next reply (read through the
``negotiate`` transport callback) settles or lapses it. Sells settle in one step."""

import asyncio
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


class _Reply:
    """A scripted negotiator: returns a fixed reply and records every quote sent."""

    def __init__(self, reply: str):
        self.reply = reply
        self.prompts: list[str] = []

    async def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply


def _commerce(chars, items, text, negotiate=None, log=None):
    return asyncio.run(_handle_commerce(
        intent_text=text, character_id="player", characters=chars, items=items,
        cs=chars["player"], turn_num=1, game_time=None,
        attack_log=log if log is not None else [], recent_events=[],
        shopkeeper="maribel", catalog=_catalog(), negotiate=negotiate))


class TestShopkeeperDetection:
    def test_present_vendor_is_the_shopkeeper(self):
        assert _current_shopkeeper(_chars(), {"player", "maribel"}, _catalog()) == "maribel"

    def test_no_shopkeeper_when_vendor_absent(self):
        assert _current_shopkeeper(_chars(), {"player"}, _catalog()) is None


class TestBuyQuoteConfirm:
    def test_quote_then_confirm_settles(self):
        chars, items = _chars(100, 0), {}
        say_yes, log = _Reply("yes"), []
        # A buy quotes a price (via the transport) then settles on "yes" — one turn.
        assert _commerce(chars, items, "I buy the meat pie", say_yes, log) is True
        assert say_yes.prompts and "meat pie" in say_yes.prompts[0].lower()
        assert chars["player"].character.purse_cp == 96
        assert chars["maribel"].character.purse_cp == 4
        assert any(getattr(p, "id", "").startswith("meat_pie") for p in chars["player"].pack)
        bought = next(p for p in chars["player"].pack if p.id.startswith("meat_pie"))
        assert bought.id in chars["player"].held_items
        assert any("SETTLED" in l and "bought" in l for l in log)

    def test_take_a_shop_good_also_quotes(self):
        chars, items = _chars(100, 0), {}
        say_yes = _Reply("sure")
        assert _commerce(chars, items, "I'll take the meat pie", say_yes) is True
        assert say_yes.prompts
        assert chars["player"].character.purse_cp == 96

    def test_decline_lapses_the_offer(self):
        chars, items = _chars(100, 0), {}
        log = []
        assert _commerce(chars, items, "buy the meat pie", _Reply("no"), log) is True
        assert chars["player"].character.purse_cp == 100
        assert not items and not chars["player"].pack
        assert any("lapse" in l for l in log)

    def test_unrelated_reply_lapses_the_offer(self):
        chars, items = _chars(100, 0), {}
        # A reply that isn't a yes/no lets the offer lapse (nothing changes hands).
        assert _commerce(chars, items, "buy the meat pie", _Reply("I look around")) is True
        assert chars["player"].character.purse_cp == 100 and not chars["player"].pack

    def test_broke_buyer_refused_at_confirm(self):
        chars, items = _chars(2, 0), {}
        log = []
        _commerce(chars, items, "buy the meat pie", _Reply("yes"), log)   # confirm, can't pay
        assert chars["player"].character.purse_cp == 2
        assert not items
        assert any("afford" in l for l in log)

    def test_non_commerce_intent_not_handled(self):
        # Not a commerce intent at all: handled=False, no quote ever sent.
        say = _Reply("yes")
        assert _commerce(_chars(), {}, "I look around the shop", say) is False
        assert not say.prompts


class TestSellWiring:
    def test_sell_settles_in_one_step(self):
        dagger = Thing(id="dagger", name="Dagger", value_cp=200, owner="player", holder="player")
        pc = _cs("player", 0, inv=["dagger"]); pc.pack = [dagger]
        chars = {"player": pc, "maribel": _cs("maribel", 1000)}
        items = {"dagger": dagger}
        handled = asyncio.run(_handle_commerce(
            intent_text="I sell my dagger", character_id="player", characters=chars,
            items=items, cs=pc, turn_num=1, game_time=None, attack_log=[],
            recent_events=[], shopkeeper="maribel", catalog=_catalog(), negotiate=None))
        assert handled is True
        assert chars["player"].character.purse_cp == 100
        assert dagger.owner == "maribel" and "dagger" not in items
