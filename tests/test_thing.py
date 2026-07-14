"""Tests for the Thing model."""

import pytest

from models.thing import Thing


class TestThing:
    def test_create_minimal(self):
        t = Thing(id="rope_hempen", name="Rope, hempen (50 ft)")
        assert t.id == "rope_hempen"
        assert t.name == "Rope, hempen (50 ft)"
        assert t.category == ""
        assert t.price == ""
        assert t.description == ""

    def test_mundane_item(self):
        t = Thing(
            id="healing_salve",
            name="Healing Salve",
            category="mundane",
            price="5 gp",
            description="Restores 1d4 HP when applied to wounds",
            vendor_id="lytha",
            location_id="bitter_remedy",
        )
        assert t.category == "mundane"
        assert t.price == "5 gp"
        assert t.vendor_id == "lytha"
        assert t.location_id == "bitter_remedy"

    def test_magical_item(self):
        t = Thing(
            id="shadow_cloak",
            name="Shadow Cloak",
            category="magical",
            price="500 gp",
            description="Advantage on Stealth in dim light or darkness",
            vendor_id="kelem",
            location_id="dustcloaks_curios",
            attunement="Required (1 hour in dim light or darkness)",
            properties="Advantage on Stealth in dim light or darkness. "
                       "Once/day reaction: impose disadvantage on one attack "
                       "targeting wearer in dim light/darkness.",
            dm_properties="Crafted from shadowbeast hide. After 1 week: "
                          "shadowbeasts 50% less likely to target wearer.",
        )
        assert t.category == "magical"
        assert t.attunement.startswith("Required")
        assert "shadowbeast" in t.dm_properties

    def test_obelisk_shard(self):
        t = Thing(
            id="shard_elyssa_lab",
            name="Obelisk Shard (Contained Specimen)",
            category="obelisk_shard",
            location_id="elyssa_cottage",
            description="Full shard in reinforced dome",
            properties="Once/day bonus action: +1d6 necrotic on next attack. "
                       "DC 12 CON save or 1d6 psychic.",
        )
        assert t.category == "obelisk_shard"
        assert t.location_id == "elyssa_cottage"

    def test_shadowbeast_part(self):
        t = Thing(
            id="shadowbeast_pelt",
            name="Shadowbeast Pelt",
            category="shadowbeast_part",
            description="Absorbs some light",
            properties="Harvest DC 12. Yield: 1 per creature.",
        )
        assert t.category == "shadowbeast_part"

    def test_defaults(self):
        t = Thing(id="x", name="X")
        assert t.vendor_id == ""
        assert t.location_id == ""
        assert t.properties == ""
        assert t.dm_properties == ""
        assert t.attunement == ""
        assert t.raw == ""

    def test_raw_preserved(self):
        t = Thing(id="x", name="X", raw="## Some markdown\nContent here.")
        assert "Some markdown" in t.raw


class TestThingOwnershipAndValue:
    """Phase 1 economy fields: owner, value_cp, listed_price_cp, weight_lb."""

    def test_new_fields_default_sanely(self):
        t = Thing(id="rock", name="Rock")
        assert t.owner is None
        assert t.value_cp is None
        assert t.listed_price_cp is None
        assert t.weight_lb == 0.0

    def test_shop_good_derives_value_listing_and_owner(self):
        # A Thing with a price and a vendor is a shop good: value parsed, listed
        # for sale at that value, owned by the vendor.
        t = Thing(id="pie", name="Meat pie", price="4 cp", vendor_id="maribel")
        assert t.value_cp == 4
        assert t.listed_price_cp == 4
        assert t.owner == "maribel"

    def test_scene_prop_has_value_but_is_not_for_sale(self):
        # A price but no vendor: worth something, not on any counter, unowned.
        t = Thing(id="urn", name="Old urn", price="2 gp")
        assert t.value_cp == 200
        assert t.listed_price_cp is None
        assert t.owner is None

    def test_unpriceable_price_leaves_value_none(self):
        t = Thing(id="shard", name="Obelisk Shard", price="Varies", vendor_id="dustcloaks")
        assert t.value_cp is None
        assert t.listed_price_cp is None      # no value → nothing to list
        assert t.owner == "dustcloaks"        # ownership still follows the vendor

    def test_explicit_values_win_over_derivation(self):
        t = Thing(id="relic", name="Relic", price="5 gp", vendor_id="v",
                  value_cp=999, listed_price_cp=None, owner="someone_else")
        assert t.value_cp == 999
        assert t.owner == "someone_else"
        # listed_price_cp was passed None explicitly, but derivation fills it from
        # value_cp for a vendor good — the ask defaults on where it's unset.
        assert t.listed_price_cp == 999
