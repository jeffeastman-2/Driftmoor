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
