"""Place CONTENTS.md is the sole runtime authority for merchant Things."""

from pathlib import Path

from models.place_thing_loader import load_place_things
from models.shop_catalog import ShopCatalog


ROOT = Path(__file__).resolve().parent.parent
PLACES = ROOT / "scenario" / "places" / "driftmoor"


def test_legacy_global_inventory_files_are_gone():
    assert not (ROOT / "scenario/things/mundane_items.md").exists()
    assert not (ROOT / "scenario/things/magical_items.md").exists()


def test_every_physical_merchant_thing_is_authored_inside_a_container():
    things = load_place_things(PLACES)
    physical = [t for t in things if t.category != "service"]
    assert physical
    assert all(t.container_id for t in physical)


def test_services_are_not_pretended_to_be_physical_stock():
    services = [t for t in load_place_things(PLACES) if t.category == "service"]
    assert services
    assert all(not t.container_id for t in services)


def test_catalog_is_derived_from_place_contents_and_hides_selective_stock():
    catalog = ShopCatalog.from_places_root(PLACES)
    assert "shadowbeast_claw_necklace" in {
        entry.catalog_id for entry in catalog.entries_for("kelem")
    }
    assert "shadow_cloak" not in {
        entry.catalog_id for entry in catalog.entries_for("kelem")
    }
    assert catalog.get("shadow_cloak") is not None


def test_magical_dm_knowledge_survived_migration():
    cloak = next(t for t in load_place_things(PLACES) if t.id == "shadow_cloak")
    assert "shadowbeast" in cloak.dm_properties.lower()
    assert "Stealth" in cloak.properties

