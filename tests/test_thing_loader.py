"""Tests for the thing_loader module."""

import pytest
from pathlib import Path

from models.thing import Thing
from models.thing_loader import (
    parse_mundane_items,
    parse_magical_items,
    parse_obelisk_shards,
    parse_shadowbeast_parts,
    load_all_things,
)

THINGS_DIR = Path(__file__).resolve().parent.parent / "scenario" / "things"


# ---- Mundane items parsing ----

class TestParseMundaneItems:
    @pytest.fixture(scope="class")
    def items(self):
        return parse_mundane_items(THINGS_DIR / "mundane_items.md")

    def test_returns_list_of_things(self, items):
        assert isinstance(items, list)
        assert all(isinstance(t, Thing) for t in items)

    def test_has_substantial_count(self, items):
        """Should parse many items from vendor tables."""
        assert len(items) >= 60

    def test_all_mundane_category(self, items):
        assert all(t.category == "mundane" for t in items)

    def test_no_duplicate_ids(self, items):
        ids = [t.id for t in items]
        assert len(ids) == len(set(ids)), f"Duplicates: {[i for i in ids if ids.count(i) > 1]}"

    def test_all_have_names(self, items):
        for t in items:
            assert t.name, f"Item {t.id} has no name"

    def test_all_have_price(self, items):
        """Most items have prices; some deals/bundles use terms instead."""
        no_price = [t for t in items if not t.price]
        for t in no_price:
            assert t.description, f"Item {t.id} ({t.name}) has neither price nor description"

    def test_salt_iron_rope(self, items):
        rope = next((t for t in items if "rope" in t.name.lower() and "hempen" in t.name.lower()), None)
        assert rope is not None
        assert rope.price == "1 gp"
        assert rope.vendor_id == "jorgen"
        assert rope.location_id == "salt_and_iron"

    def test_bitter_remedy_healing_salve(self, items):
        salve = next((t for t in items if "healing salve" in t.name.lower()), None)
        assert salve is not None
        assert salve.price == "5 gp"
        assert salve.vendor_id == "lytha"
        assert salve.location_id == "bitter_remedy"

    def test_broken_lantern_ale(self, items):
        ale = next((t for t in items if "driftmoor ale" in t.name.lower()), None)
        assert ale is not None
        assert ale.vendor_id == "tess"
        assert ale.location_id == "broken_lantern"

    def test_ironhoof_forge_item(self, items):
        shoes = next((t for t in items if "horseshoe" in t.name.lower()), None)
        assert shoes is not None
        assert shoes.vendor_id == "darrin"
        assert shoes.location_id == "ironhoof_forge"

    def test_gilded_trinket_item(self, items):
        lock = next((t for t in items if "iron lock" in t.name.lower()), None)
        assert lock is not None
        assert lock.vendor_id == "tavian"
        assert lock.location_id == "gilded_trinket"

    def test_dustcloak_curios_item(self, items):
        necklace = next((t for t in items if "claw necklace" in t.name.lower()), None)
        assert necklace is not None
        assert necklace.vendor_id == "kelem"
        assert necklace.location_id == "dustcloaks_curios"

    def test_beacon_church_service(self, items):
        healing = next((t for t in items if "basic healing" in t.name.lower()), None)
        assert healing is not None
        assert healing.vendor_id == "elden"
        assert healing.location_id == "beacon_church"

    def test_bakery_item(self, items):
        bread = next((t for t in items if "bread loaf" in t.name.lower()), None)
        assert bread is not None
        assert bread.vendor_id == "maribel"
        assert bread.location_id == "bakery"

    def test_description_populated(self, items):
        """Items with a Description/Effect/Notes column should have descriptions."""
        rope = next((t for t in items if "rope" in t.name.lower() and "hempen" in t.name.lower()), None)
        assert rope.description != ""

    def test_services_included(self, items):
        """Services (haircut, appraisal, etc.) should be parsed as items."""
        haircut = next((t for t in items if "haircut" in t.name.lower()), None)
        assert haircut is not None
        assert haircut.vendor_id == "arlan"


# ---- Magical items parsing ----

class TestParseMagicalItems:
    @pytest.fixture(scope="class")
    def items(self):
        return parse_magical_items(THINGS_DIR / "magical_items.md")

    def test_returns_list_of_things(self, items):
        assert isinstance(items, list)
        assert all(isinstance(t, Thing) for t in items)

    def test_item_count(self, items):
        """Kelem has 6, Gilded Trinket has 4, Elyssa has 1 = 11 total."""
        assert len(items) >= 11

    def test_all_magical_category(self, items):
        assert all(t.category == "magical" for t in items)

    def test_no_duplicate_ids(self, items):
        ids = [t.id for t in items]
        assert len(ids) == len(set(ids))

    def test_shadow_cloak(self, items):
        cloak = next((t for t in items if "shadow cloak" in t.name.lower()), None)
        assert cloak is not None
        assert cloak.price == "500 gp"
        assert "Required" in cloak.attunement
        assert cloak.vendor_id == "kelem"
        assert cloak.location_id == "dustcloaks_curios"

    def test_shadow_cloak_properties(self, items):
        cloak = next((t for t in items if "shadow cloak" in t.name.lower()), None)
        assert "Stealth" in cloak.properties
        assert "shadowbeast" in cloak.dm_properties.lower()

    def test_lantern_of_revealing(self, items):
        lantern = next((t for t in items if "lantern" in t.name.lower()), None)
        assert lantern is not None
        assert lantern.price == "400 gp"
        assert "Not required" in lantern.attunement

    def test_strange_stone_amulet(self, items):
        """Gilded Trinket secretly magical item."""
        amulet = next((t for t in items if "stone amulet" in t.name.lower()), None)
        assert amulet is not None
        assert "25 gp" in amulet.price
        assert amulet.vendor_id == "tavian"
        assert amulet.location_id == "gilded_trinket"

    def test_cracked_compass(self, items):
        compass = next((t for t in items if "compass" in t.name.lower()), None)
        assert compass is not None
        assert "obelisk" in compass.dm_properties.lower()

    def test_elyssa_shard(self, items):
        shard = next((t for t in items if "elyssa" in t.location_id or
                       ("shard" in t.name.lower() and "contained" in t.name.lower())), None)
        assert shard is not None
        assert shard.location_id == "elyssa_cottage"

    def test_shadowbane_dagger(self, items):
        dagger = next((t for t in items if "shadowbane" in t.name.lower()), None)
        assert dagger is not None
        assert dagger.price == "1,200 gp"
        assert "+1" in dagger.properties

    def test_all_have_raw(self, items):
        for t in items:
            assert t.raw, f"{t.name} has no raw content"


# ---- Obelisk shards parsing ----

class TestParseObeliskShards:
    @pytest.fixture(scope="class")
    def items(self):
        return parse_obelisk_shards(THINGS_DIR / "obelisk_shards.md")

    def test_returns_list_of_things(self, items):
        assert isinstance(items, list)
        assert all(isinstance(t, Thing) for t in items)

    def test_shard_count(self, items):
        """6 known shard locations in the table."""
        assert len(items) == 6

    def test_all_obelisk_shard_category(self, items):
        assert all(t.category == "obelisk_shard" for t in items)

    def test_elyssa_shard(self, items):
        shard = next((t for t in items if "elyssa" in t.location_id), None)
        assert shard is not None
        assert "reinforced dome" in shard.description.lower() or "reinforced dome" in shard.name.lower()

    def test_dustcloak_shopfront_shard(self, items):
        shard = next((t for t in items if t.location_id == "dustcloaks_curios"), None)
        assert shard is not None

    def test_shattered_obelisk_shard(self, items):
        shard = next((t for t in items if t.location_id == "shattered_obelisk"), None)
        assert shard is not None

    def test_drowned_isle_shard(self, items):
        shard = next((t for t in items if t.location_id == "drowned_isle"), None)
        assert shard is not None

    def test_all_have_location(self, items):
        for t in items:
            assert t.location_id, f"Shard {t.id} has no location"

    def test_no_duplicate_ids(self, items):
        ids = [t.id for t in items]
        assert len(ids) == len(set(ids))


# ---- Shadowbeast parts parsing ----

class TestParseShadowbeastParts:
    @pytest.fixture(scope="class")
    def items(self):
        return parse_shadowbeast_parts(THINGS_DIR / "shadowbeast_parts.md")

    def test_returns_list_of_things(self, items):
        assert isinstance(items, list)
        assert all(isinstance(t, Thing) for t in items)

    def test_part_count(self, items):
        """4 harvestable part types: pelt, claws, blood, eyes."""
        assert len(items) == 4

    def test_all_shadowbeast_part_category(self, items):
        assert all(t.category == "shadowbeast_part" for t in items)

    def test_pelt(self, items):
        pelt = next((t for t in items if "pelt" in t.name.lower()), None)
        assert pelt is not None
        assert "12" in pelt.properties  # harvest DC 12

    def test_claws(self, items):
        claws = next((t for t in items if "claw" in t.name.lower()), None)
        assert claws is not None

    def test_blood(self, items):
        blood = next((t for t in items if "blood" in t.name.lower()), None)
        assert blood is not None

    def test_eyes(self, items):
        eyes = next((t for t in items if "eye" in t.name.lower()), None)
        assert eyes is not None

    def test_all_have_raw(self, items):
        for t in items:
            assert t.raw, f"{t.name} has no raw content"

    def test_no_duplicate_ids(self, items):
        ids = [t.id for t in items]
        assert len(ids) == len(set(ids))


# ---- load_all_things integration ----

class TestLoadAllThings:
    @pytest.fixture(scope="class")
    def all_things(self):
        return load_all_things(THINGS_DIR)

    def test_returns_list(self, all_things):
        assert isinstance(all_things, list)

    def test_substantial_count(self, all_things):
        """Mundane + magical + shards + parts."""
        assert len(all_things) >= 75

    def test_no_duplicate_ids(self, all_things):
        ids = [t.id for t in all_things]
        dupes = [i for i in ids if ids.count(i) > 1]
        assert len(ids) == len(set(ids)), f"Duplicates: {set(dupes)}"

    def test_has_all_categories(self, all_things):
        cats = {t.category for t in all_things}
        assert cats == {"mundane", "magical", "obelisk_shard", "shadowbeast_part"}

    def test_mundane_majority(self, all_things):
        mundane = [t for t in all_things if t.category == "mundane"]
        assert len(mundane) >= 60

    def test_magical_items_present(self, all_things):
        magical = [t for t in all_things if t.category == "magical"]
        # 12 parsed from magical_items.md minus 2 obelisk shard cross-refs
        assert len(magical) == 10

    def test_shards_present(self, all_things):
        shards = [t for t in all_things if t.category == "obelisk_shard"]
        assert len(shards) == 6

    def test_parts_present(self, all_things):
        parts = [t for t in all_things if t.category == "shadowbeast_part"]
        assert len(parts) == 4
