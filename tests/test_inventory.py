"""Tests for item possession: take / drop / give, and ownership persistence."""

import json

import pytest

from engine.session import (
    CharacterSession,
    _apply_item_transfer,
    _handle_item_transfer,
    _resolve_recipient_character,
    _serialize_item_ownership,
    restore_item_ownership,
)
from engine.verb_resolver import detect_transfer_verb
from models.character import PlayerCharacter
from models.condition import CharacterCondition, NeurochemicalState
from models.item import Interaction, Item
from models.space_time import Position


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _session(cid, name, *, race="Human", cclass="", handle=""):
    char = PlayerCharacter(
        id=cid, name=name, race=race, character_type="player",
        character_class=cclass, hp=10, current_hp=10,
    )
    cond = CharacterCondition(
        character_id=cid, character_name=name, state=NeurochemicalState(),
    )
    return CharacterSession(
        character=char, condition=cond, soul="", identity="",
        initial_scene="", scene_handle=handle,
    )


@pytest.fixture
def party():
    return {
        "gilthaness": _session("gilthaness", "Gilthaness", race="High Elf",
                                cclass="Wizard", handle="Gil"),
        "amara": _session("amara", "Amara", race="Human",
                           cclass="Cleric", handle="Sister Amara"),
        "thorgrim": _session("thorgrim", "Thorgrim", race="Dwarf",
                             cclass="Fighter", handle="Thorgrim"),
    }


@pytest.fixture
def mace():
    return Item(
        id="mace_plus_one",
        label="banded mace",
        position=Position(100.0, 50.0),
        zone="Secret Chamber",
        size_ft=2.5,
        interactions=[
            Interaction(verb="take", aliases=[], condition="",
                        response="The mace lifts cleanly from the vault."),
        ],
    )


# ---------------------------------------------------------------------------
# Verb detection
# ---------------------------------------------------------------------------

class TestDetectTransferVerb:
    @pytest.mark.parametrize("text", [
        "I pick up the mace", "pick up the banded mace", "grab the mace",
        "I take the mace", "lift the mace", "pocket the coin",
    ])
    def test_take_phrases(self, text):
        assert detect_transfer_verb(text) == "take"

    @pytest.mark.parametrize("text", [
        "I drop the mace", "put down the mace", "set down the torch",
        "discard the rope", "leave the mace here",
    ])
    def test_drop_phrases(self, text):
        assert detect_transfer_verb(text) == "drop"

    @pytest.mark.parametrize("text", [
        "I give Amara the mace", "hand the mace to the cleric",
        "give the mace to Thorgrim", "I offer the mace to Amara",
        "pass the mace to Thorgrim",
    ])
    def test_give_phrases(self, text):
        assert detect_transfer_verb(text) == "give"

    def test_no_transfer_verb(self):
        assert detect_transfer_verb("I examine the mace") is None
        assert detect_transfer_verb("") is None


# ---------------------------------------------------------------------------
# Recipient resolution
# ---------------------------------------------------------------------------

class TestResolveRecipient:
    def _active(self, party):
        return set(party.keys())

    def test_by_name(self, party):
        rid = _resolve_recipient_character(
            "I give Amara the mace", actor_id="gilthaness",
            characters=party, active_characters=self._active(party),
        )
        assert rid == "amara"

    def test_by_class_role(self, party):
        rid = _resolve_recipient_character(
            "I hand the mace to the cleric", actor_id="gilthaness",
            characters=party, active_characters=self._active(party),
        )
        assert rid == "amara"

    def test_by_race(self, party):
        rid = _resolve_recipient_character(
            "give the mace to the dwarf", actor_id="gilthaness",
            characters=party, active_characters=self._active(party),
        )
        assert rid == "thorgrim"

    def test_actor_excluded(self, party):
        # "the wizard" is the actor; must not resolve to self.
        rid = _resolve_recipient_character(
            "I give the wizard the mace", actor_id="gilthaness",
            characters=party, active_characters=self._active(party),
        )
        assert rid is None

    def test_no_match_returns_none(self, party):
        rid = _resolve_recipient_character(
            "I give the mace to the stranger", actor_id="gilthaness",
            characters=party, active_characters=self._active(party),
        )
        assert rid is None


# ---------------------------------------------------------------------------
# Transfer helper (both sides of ownership)
# ---------------------------------------------------------------------------

class TestApplyItemTransfer:
    def test_take_sets_holder_and_inventory(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party,
                             target_pos=(10.0, 20.0, "Secret Chamber"))
        assert mace.holder == "gilthaness"
        assert "mace_plus_one" in party["gilthaness"].character.inventory

    def test_give_moves_between_inventories(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party)
        _apply_item_transfer(mace, "amara", characters=party)
        assert mace.holder == "amara"
        assert "mace_plus_one" not in party["gilthaness"].character.inventory
        assert "mace_plus_one" in party["amara"].character.inventory

    def test_drop_clears_holder(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party)
        _apply_item_transfer(mace, None, characters=party,
                             target_pos=(5.0, 5.0, "Secret Chamber"))
        assert mace.holder is None
        assert "mace_plus_one" not in party["gilthaness"].character.inventory
        assert mace.position.x == 5.0


# ---------------------------------------------------------------------------
# Turn-loop handler
# ---------------------------------------------------------------------------

class TestHandleItemTransfer:
    def _call(self, *, verb, intent, item, party, actor="gilthaness",
              authored=None):
        attack_log, recent_events = [], []
        positions = {
            "gilthaness": (100.0, 50.0, "Secret Chamber"),
            "amara": (110.0, 55.0, "Secret Chamber"),
            "thorgrim": (90.0, 45.0, "Secret Chamber"),
        }
        _handle_item_transfer(
            transfer_verb=verb, item_obj=item, label=item.label,
            character_id=actor, characters=party,
            active_characters=set(party.keys()),
            current_positions=positions, intent_text=intent,
            actor_zone="Secret Chamber", turn_num=21, game_time=None,
            attack_log=attack_log, recent_events=recent_events,
            cs=party[actor], authored_response=authored,
        )
        return attack_log, recent_events

    def test_take_records_holder(self, party, mace):
        log, _ = self._call(verb="take", intent="I pick up the mace",
                            item=mace, party=party)
        assert mace.holder == "gilthaness"
        assert "gilthaness" in mace.discovered_by
        assert any("ITEM-TRANSFER" in line for line in log)

    def test_give_transfers_to_named_recipient(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party)
        self._call(verb="give", intent="I give Amara the mace",
                   item=mace, party=party)
        assert mace.holder == "amara"
        assert "mace_plus_one" in party["amara"].character.inventory

    def test_give_with_unclear_recipient_does_not_transfer(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party)
        self._call(verb="give", intent="I give the mace to someone",
                   item=mace, party=party)
        assert mace.holder == "gilthaness"

    def test_drop_returns_item_to_zone(self, party, mace):
        _apply_item_transfer(mace, "gilthaness", characters=party)
        self._call(verb="drop", intent="I drop the mace", item=mace,
                   party=party)
        assert mace.holder is None
        assert "mace_plus_one" not in party["gilthaness"].character.inventory

    def test_cannot_take_item_held_by_another(self, party, mace):
        _apply_item_transfer(mace, "amara", characters=party)
        self._call(verb="take", intent="I take the mace", item=mace,
                   party=party, actor="gilthaness")
        assert mace.holder == "amara"


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestOwnershipPersistence:
    def test_serialize_only_held_items(self, mace):
        loose = Item(id="torch", label="torch", position=Position(1.0, 1.0),
                     zone="Entry")
        mace.holder = "amara"
        out = _serialize_item_ownership({"mace_plus_one": mace, "torch": loose})
        assert "mace_plus_one" in out
        assert "torch" not in out
        assert out["mace_plus_one"]["holder"] == "amara"

    def test_restore_round_trip(self, tmp_path, party, mace):
        mace.holder = "amara"
        mace.position = Position(110.0, 55.0)
        mace.zone = "Secret Chamber"
        data = {
            "turn": 31,
            "item_ownership": _serialize_item_ownership(
                {"mace_plus_one": mace}
            ),
        }
        (tmp_path / "day1_14h20m.json").write_text(json.dumps(data))

        # Fresh items + party (no holder, empty inventories).
        fresh_mace = Item(id="mace_plus_one", label="banded mace",
                          position=Position(100.0, 50.0), zone="Secret Chamber")
        items = {"mace_plus_one": fresh_mace}
        restore_item_ownership(tmp_path, items, party)

        assert fresh_mace.holder == "amara"
        assert fresh_mace.position.x == 110.0
        assert "mace_plus_one" in party["amara"].character.inventory

    def test_restore_no_checkpoints_is_noop(self, tmp_path, party):
        items = {"mace_plus_one": Item(id="mace_plus_one", label="mace")}
        restore_item_ownership(tmp_path, items, party)
        assert items["mace_plus_one"].holder is None
