"""The transfer primitive (engine.item_transfer.transfer_thing).

Moves any subset of {ownership, possession, coin} between two parties, atomically.
"""

from types import SimpleNamespace as NS

from models.character import Character
from models.thing import Thing
from engine.item_transfer import transfer_coins, transfer_thing


def _cs(cid, purse=0, inv=None):
    """A minimal CharacterSession stand-in: `.character` is a real Character."""
    c = Character(id=cid, name=cid.title(), race="Human", character_type="npc",
                  purse_cp=purse, inventory=list(inv or []))
    return NS(character=c, scene_handle="")


class TestPossessionAndOwnership:
    def test_give_moves_ownership_and_possession(self):
        mace = Thing(id="mace", name="Mace", holder="alice", owner="alice")
        chars = {"alice": _cs("alice", inv=["mace"]), "bob": _cs("bob")}
        r = transfer_thing(mace, from_id="alice", to_id="bob",
                           characters=chars, move_ownership=True)
        assert r.ok
        assert mace.holder == "bob" and mace.owner == "bob"
        assert "mace" in chars["bob"].character.inventory
        assert "mace" not in chars["alice"].character.inventory

    def test_drop_releases_possession_keeps_ownership(self):
        pack = Thing(id="pack", name="Pack", holder="alice", owner="alice")
        chars = {"alice": _cs("alice", inv=["pack"])}
        r = transfer_thing(pack, from_id="alice", to_id=None, characters=chars,
                           move_ownership=False, target_pos=(1.0, 2.0, "ROOM"))
        assert r.ok
        assert pack.holder is None
        assert pack.owner == "alice"          # left behind, still yours
        assert "pack" not in chars["alice"].character.inventory

    def test_take_unowned_claims_ownership(self):
        coin = Thing(id="coin", name="Coin", holder=None, owner=None)
        chars = {"finder": _cs("finder")}
        transfer_thing(coin, from_id=None, to_id="finder", characters=chars,
                      move_ownership=(coin.owner is None))
        assert coin.owner == "finder" and coin.holder == "finder"

    def test_take_owned_moves_possession_not_ownership(self):
        # A loaf on the baker's shelf: taking it grabs possession but the loaf
        # stays hers — stolen, not owned (detection is Phase 6).
        loaf = Thing(id="loaf", name="Loaf", holder=None, owner="maribel")
        chars = {"thief": _cs("thief"), "maribel": _cs("maribel")}
        transfer_thing(loaf, from_id=None, to_id="thief", characters=chars,
                      move_ownership=(loaf.owner is None))
        assert loaf.holder == "thief"
        assert loaf.owner == "maribel"


class TestCoin:
    def test_direct_coin_gift_moves_only_currency(self):
        chars = {"martha": _cs("martha", purse=20), "player": _cs("player", purse=500)}
        r = transfer_coins(100, from_id="player", to_id="martha", characters=chars)
        assert r.ok
        assert chars["player"].character.purse_cp == 400
        assert chars["martha"].character.purse_cp == 120

    def test_direct_coin_gift_is_atomic_when_payer_is_broke(self):
        chars = {"martha": _cs("martha", purse=20), "player": _cs("player", purse=50)}
        r = transfer_coins(100, from_id="player", to_id="martha", characters=chars)
        assert not r.ok and r.reason == "cannot_afford"
        assert chars["player"].character.purse_cp == 50
        assert chars["martha"].character.purse_cp == 20

    def test_explicit_give_coins_routes_to_named_visible_recipient(self):
        from engine.session import _handle_coin_transfer

        chars = {"martha": _cs("martha", purse=20), "player": _cs("player", purse=500)}
        chars["player"].episodic_memory = []
        log, events = [], []
        handled = _handle_coin_transfer(
            intent_text="I give Martha 1 gp",
            character_id="player",
            characters=chars,
            active_characters={"player", "martha"},
            turn_num=3,
            game_time=None,
            attack_log=log,
            recent_events=events,
            cs=chars["player"],
        )
        assert handled
        assert chars["player"].character.purse_cp == 400
        assert chars["martha"].character.purse_cp == 120
        assert any("SETTLED" in line for line in log)

    def test_buy_moves_item_and_coin_recipient_pays(self):
        pie = Thing(id="pie", name="Pie", holder=None, owner="maribel")
        chars = {"maribel": _cs("maribel", purse=0), "player": _cs("player", purse=100)}
        r = transfer_thing(pie, from_id="maribel", to_id="player",
                           characters=chars, move_ownership=True, coin_cp=4)
        assert r.ok
        assert pie.owner == "player" and pie.holder == "player"
        assert chars["player"].character.purse_cp == 96   # buyer paid
        assert chars["maribel"].character.purse_cp == 4    # seller received

    def test_broke_buyer_aborts_the_whole_transfer(self):
        pie = Thing(id="pie", name="Pie", holder=None, owner="maribel")
        chars = {"maribel": _cs("maribel", purse=0), "player": _cs("player", purse=3)}
        r = transfer_thing(pie, from_id="maribel", to_id="player",
                           characters=chars, move_ownership=True, coin_cp=4)
        assert not r.ok and r.reason == "cannot_afford"
        # Nothing moved — item, ownership, and both purses untouched.
        assert pie.owner == "maribel" and pie.holder is None
        assert chars["player"].character.purse_cp == 3
        assert chars["maribel"].character.purse_cp == 0

    def test_negative_coin_rejected_no_mutation(self):
        pie = Thing(id="pie", name="Pie", holder=None, owner="m")
        chars = {"m": _cs("m"), "p": _cs("p", purse=100)}
        r = transfer_thing(pie, from_id="m", to_id="p", characters=chars,
                           move_ownership=True, coin_cp=-5)
        assert not r.ok and r.reason == "invalid_amount"
        assert pie.owner == "m" and chars["p"].character.purse_cp == 100

    def test_coin_is_conserved(self):
        pie = Thing(id="pie", name="Pie", owner="m")
        chars = {"m": _cs("m", purse=10), "p": _cs("p", purse=100)}
        transfer_thing(pie, from_id="m", to_id="p", characters=chars,
                      move_ownership=True, coin_cp=25)
        assert chars["m"].character.purse_cp + chars["p"].character.purse_cp == 110
        assert chars["p"].character.purse_cp == 75   # buyer p paid 25
