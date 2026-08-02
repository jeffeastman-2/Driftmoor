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


def _weapon_catalog():
    # A good whose plain name omits a modifier a player would naturally use
    # ("crossbow bolts" for "Bolts (20)") -- exercises head-noun matching.
    return ShopCatalog([
        Thing(id="bolts_20", name="Bolts (20)", price="1 gp", vendor_id="jorgen"),
    ])


def _fish_catalog():
    return ShopCatalog([
        Thing(id="fresh_fish", name="Fresh fish (per lb)", price="2 cp",
              vendor_id="kessla"),
        Thing(id="salted_fish", name="Salted fish (per lb)", price="4 cp",
              vendor_id="kessla"),
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

    def test_ambiguous_buy_is_preserved_for_shop_clarification(self):
        entries = _fish_catalog().entries_for("kessla")
        for text in ("buy fish", "can I buy some fish"):
            assert resolve_commerce(text, {}, {}, "", entries) == ("buy", None)

    def test_consuming_a_catalog_good_routes_through_purchase(self):
        cat = ShopCatalog([
            Thing(id="ale", name="Driftmoor Ale", price="4 cp", vendor_id="tess"),
        ])
        result = resolve_commerce(
            "drink the ale", {}, {}, "", cat.entries_for("tess"))
        assert result is not None
        assert result[0] == "buy" and result[1].catalog_id == "ale"

    def test_owned_consumable_wins_over_same_shop_catalog_good(self):
        cat = ShopCatalog([
            Thing(id="food", name="Preserved food (week's supply)",
                  price="5 sp", vendor_id="jedrin"),
        ])
        owned = Thing(
            id="food_i1", name="Preserved food (week's supply)",
            owner="player", holder="player")
        assert resolve_commerce(
            "I eat some food", {owned.id: owned}, {}, "",
            cat.entries_for("jedrin")) is None

    def test_sell_grounds_owned_item(self):
        dagger = Thing(id="dagger", label="dagger", zone="", owner="player")
        res = resolve_commerce("I sell my dagger", {"dagger": dagger}, {}, "", [])
        assert res is not None
        verb, item = res
        assert verb == "sell" and item.id == "dagger"

    def test_non_commerce_is_none(self):
        entries = _catalog().entries_for("maribel")
        assert resolve_commerce("I look at the pie", {}, {}, "", entries) is None

    def test_conversational_buy_framings_ground(self):
        # Polite/indirect phrasings ground as a buy without an imperative verb.
        entries = _catalog().entries_for("maribel")
        for s in ("I want the meat pie", "I need a meat pie",
                  "I am looking for a meat pie", "I would like the meat pie"):
            res = resolve_commerce(s, {}, {}, "", entries)
            assert res is not None and res[0] == "buy" and res[1].catalog_id == "meat_pie", s

    def test_desire_verb_without_a_good_is_not_commerce(self):
        # The object gate: a desire/seek verb with no catalog object stays None
        # (no misfiring "buy something unclear").
        entries = _catalog().entries_for("maribel")
        for s in ("I want to leave", "I am looking for the way out",
                  "I would like to talk to the baker"):
            assert resolve_commerce(s, {}, {}, "", entries) is None, s

    def test_trailing_tokens_after_object_still_ground(self):
        # A stray token after the object -- politeness, adverb, punctuation, or a
        # modal question wrapper -- must not block VP formation (the LATN VP-ATN
        # after_np reduce fix), so these all still ground as a buy.
        entries = _weapon_catalog().entries_for("jorgen")
        for s in ("buy bolts please", "buy bolts now", "buy the bolts quickly",
                  "buy bolts, thank you", "can I buy some bolts please"):
            res = resolve_commerce(s, {}, {}, "", entries)
            assert res is not None and res[0] == "buy" and res[1].catalog_id == "bolts_20", s

    def test_modifier_before_head_noun_grounds(self):
        # "crossbow bolts" reaches the good "Bolts (20)" via head-noun matching,
        # even though the good's name has no "crossbow".
        entries = _weapon_catalog().entries_for("jorgen")
        for s in ("buy crossbow bolts", "buy some crossbow bolts",
                  "I'd like to buy some crossbow bolts",
                  "I am looking for some crossbow bolts"):
            res = resolve_commerce(s, {}, {}, "", entries)
            assert res is not None and res[0] == "buy" and res[1].catalog_id == "bolts_20", s

    def test_take_a_shop_good_is_a_buy(self):
        # loose phrasing in a shop routes to commerce, not the LLM.
        entries = _catalog().entries_for("maribel")
        res = resolve_commerce("I'll take the meat pie", {}, {}, "", entries)
        assert res is not None and res[0] == "buy" and res[1].catalog_id == "meat_pie"

    def test_grab_a_shop_good_is_a_buy(self):
        entries = _catalog().entries_for("maribel")
        res = resolve_commerce("grab the sweet roll", {}, {}, "", entries)
        assert res[0] == "buy" and res[1].catalog_id == "sweet_roll"

    def test_take_a_non_shop_thing_is_not_commerce(self):
        # taking a possession (not shop stock) is a normal take, not a purchase.
        dagger = Thing(id="dagger", label="dagger", zone="", owner="player")
        entries = _catalog().entries_for("maribel")
        assert resolve_commerce("I take my dagger", {"dagger": dagger}, {}, "", entries) is None


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


class TestResponse:
    def test_affirmations_read_as_affirm(self):
        from engine.latn_integration import resolve_response
        for w in (
            "yes", "yeah", "sure", "ok", "deal", "go ahead", "agreed",
            '"yes"', "“yes”", '*“yes”*',
        ):
            assert resolve_response(w, {}, "") == "affirm", w

    def test_refusals_read_as_decline(self):
        from engine.latn_integration import resolve_response
        for w in ("nope", "never mind", "pass", "cancel", "decline"):
            assert resolve_response(w, {}, "") == "decline", w

    def test_non_answer_is_none(self):
        from engine.latn_integration import resolve_response
        assert resolve_response("I look around", {}, "") is None


def test_how_much_query_quotes_unique_authoritative_catalog_item():
    from engine.latn_integration import resolve_query
    catalog = [
        CatalogEntry("hair_tonic", "Hair tonic", 100, 100, "mundane", 0.0, "arlan"),
    ]
    assert resolve_query(
        '"How much is the tonic?"', {}, {}, "", catalog
    ) == "Yes — Hair tonic is for sale at 1 gp."
