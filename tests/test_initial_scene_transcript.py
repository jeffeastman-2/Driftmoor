"""Print a transcript of the initial game setup.

Run with:  python -m pytest tests/test_initial_scene_transcript.py -s
"""

from pathlib import Path

from models.game_init import initialize_game_state
from models.character import PlayerCharacter, NPC
from engine.context_builder import build_player_context

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenario"


def test_initial_scene_transcript(capsys):
    gs = initialize_game_state(SCENARIO_DIR)

    # Collect occupied places, sorted by name
    occupied: dict[str, list] = {}
    for c in gs.characters:
        if c.location:
            occupied.setdefault(c.location, []).append(c)

    print()
    print("=" * 70)
    print("  DRIFTMOOR — INITIAL SCENE SETUP")
    print(f"  Turn {gs.turn}  |  {len(gs.characters)} characters  "
          f"|  {len(gs.places)} places  |  {len(gs.get_active_scenes())} scenes")
    print("=" * 70)

    # ---- Active scenes first ----
    for scene in gs.get_active_scenes():
        place = gs.get_place(scene.place_id)
        name = place.name if place else scene.place_id
        parent = gs.get_parent(scene.place_id)
        region = f" ({parent.name})" if parent else ""
        chars = [gs.get_character(cid) for cid in scene.character_ids]
        chars = [c for c in chars if c is not None]

        pcs = [c for c in chars if isinstance(c, PlayerCharacter)]
        npcs = [c for c in chars if not isinstance(c, PlayerCharacter)]

        print()
        print(f"  🎬 SCENE: {name}{region}")
        if place and place.description:
            desc = place.description.split(". ")[0].strip().rstrip(".")
            print(f"     {desc}.")
        print(f"     [{len(pcs)} PCs, {len(npcs)} others]")

        for c in sorted(chars, key=lambda x: x.name):
            if isinstance(c, PlayerCharacter):
                tag = "PC"
                detail = f"{c.race} {c.character_class}, Lvl {c.level}, HP {c.hp}, AC {c.ac}"
            elif isinstance(c, NPC):
                tag = c.character_type.upper()
                detail = f"{c.race}, {c.role}" if c.role else c.race
            else:
                tag = "???"
                detail = c.race
            print(f"       [{tag}] {c.name} — {detail}")

    # ---- Non-scene occupied places ----
    scene_place_ids = {s.place_id for s in gs.scenes}
    other_places = sorted(pid for pid in occupied if pid not in scene_place_ids)
    if other_places:
        print()
        print("  ── Other occupied locations (no active scene) ──")
        for place_id in other_places:
            place = gs.get_place(place_id)
            name = place.name if place else place_id
            chars = occupied[place_id]
            names = ", ".join(c.name for c in sorted(chars, key=lambda x: x.name))
            print(f"     📍 {name}: {names}")

    # Unplaced characters
    unplaced = [c for c in gs.characters if not c.location]
    if unplaced:
        print()
        print("  ⚠️  UNPLACED CHARACTERS")
        for c in sorted(unplaced, key=lambda x: x.name):
            print(f"       {c.name} ({c.id})")

    print()
    print("=" * 70)

    # Assertions
    assert len(gs.characters) == 37
    assert len(occupied) > 0
    assert not unplaced, f"Unplaced characters: {[c.id for c in unplaced]}"
    assert len(gs.get_active_scenes()) == 7  # one scene per player


def test_initial_things_deployment(capsys):
    gs = initialize_game_state(SCENARIO_DIR)

    print()
    print("=" * 70)
    print("  DRIFTMOOR — INITIAL THINGS DEPLOYMENT")
    print(f"  {len(gs.things)} things across {len({t.location_id for t in gs.things if t.location_id})} locations")
    print("=" * 70)

    # ---- Things in active scenes ----
    scene_place_ids = {s.place_id for s in gs.get_active_scenes()}
    for scene in gs.get_active_scenes():
        things = gs.get_things_at(scene.place_id)
        if not things:
            continue
        place = gs.get_place(scene.place_id)
        name = place.name if place else scene.place_id

        print()
        print(f"  🎬 {name}")
        _print_things_grouped(things)

    # ---- Things at non-scene locations ----
    locations_with_things: dict[str, list] = {}
    for t in gs.things:
        if t.location_id and t.location_id not in scene_place_ids:
            locations_with_things.setdefault(t.location_id, []).append(t)

    if locations_with_things:
        print()
        print("  ── Items at other locations ──")
        for place_id in sorted(locations_with_things):
            place = gs.get_place(place_id)
            name = place.name if place else place_id
            things = locations_with_things[place_id]
            print()
            print(f"  📍 {name}")
            _print_things_grouped(things)

    # ---- Things with no location (templates) ----
    unplaced = [t for t in gs.things if not t.location_id]
    if unplaced:
        print()
        print("  ── Unlocated items (templates / harvestables) ──")
        for t in sorted(unplaced, key=lambda x: x.name):
            extra = f" — {t.description[:60]}" if t.description else ""
            print(f"     [{t.category}] {t.name}{extra}")

    # ---- Summary by category ----
    cats: dict[str, int] = {}
    for t in gs.things:
        cats[t.category] = cats.get(t.category, 0) + 1
    print()
    print("  ── Summary ──")
    for cat in sorted(cats):
        print(f"     {cat}: {cats[cat]}")

    # ---- Summary by vendor ----
    vendors: dict[str, int] = {}
    for t in gs.things:
        if t.vendor_id:
            vendors[t.vendor_id] = vendors.get(t.vendor_id, 0) + 1
    print()
    print("  ── Items by vendor ──")
    for vid in sorted(vendors, key=lambda v: -vendors[v]):
        vc = gs.get_character(vid)
        vname = vc.name if vc else vid
        print(f"     {vname}: {vendors[vid]} items")

    print()
    print("=" * 70)

    # Assertions
    assert len(gs.things) >= 75
    assert len({t.category for t in gs.things}) == 4
    # Every scene place that is a shop should have things
    for scene in gs.get_active_scenes():
        things = gs.get_things_at(scene.place_id)
        place = gs.get_place(scene.place_id)
        # Fey Glade and Old Mill have no shop items — that's expected
        if scene.place_id not in ("fey_glade", "old_mill"):
            assert len(things) > 0, f"No things at active scene {place.name}"


def _print_things_grouped(things: list):
    """Print things grouped by category."""
    by_cat: dict[str, list] = {}
    for t in things:
        by_cat.setdefault(t.category, []).append(t)
    for cat in sorted(by_cat):
        items = sorted(by_cat[cat], key=lambda x: x.name)
        label = cat.replace("_", " ").title()
        print(f"     [{label}] ({len(items)} items)")
        for t in items:
            price_str = f" ({t.price})" if t.price else ""
            magic = " ✨" if t.category == "magical" else ""
            print(f"       • {t.name}{price_str}{magic}")


def test_player_context_transcript(capsys):
    gs = initialize_game_state(SCENARIO_DIR)

    print()
    print("=" * 70)
    print("  DRIFTMOOR — PLAYER CONTEXT BRIEFINGS")
    print("=" * 70)

    for pc in sorted(gs.get_players(), key=lambda c: c.name):
        ctx = build_player_context(gs, pc.id)
        print()
        print("-" * 70)
        print(f"  📜 CONTEXT FOR: {ctx.character_name}")
        print(f"     Location: {ctx.location_name}")
        print(f"     NPCs present: {len(ctx.scene_characters)}")
        print(f"     Items available: {len(ctx.available_items)}")
        print(f"     Backstory: {ctx.backstory[:80]}..." if ctx.backstory else "     Backstory: (none)")
        print(f"     Character brief: {len(ctx.character_brief)} chars")
        print(f"     Character soul: {len(ctx.character_soul)} chars")
        print(f"     Rendered output: {len(ctx.render())} chars")
        if ctx.scene_characters:
            for sc in ctx.scene_characters:
                role = f" — {sc['role']}" if sc.get("role") else ""
                print(f"       👤 {sc['name']}{role}")
        if ctx.available_items:
            shown = ctx.available_items[:5]
            for item in shown:
                price = f" ({item['price']})" if item.get("price") else ""
                print(f"       🛒 {item['name']}{price}")
            if len(ctx.available_items) > 5:
                print(f"       ... and {len(ctx.available_items) - 5} more items")

    print()
    print("=" * 70)

    # Assertions
    players = gs.get_players()
    assert len(players) == 7
    for pc in players:
        ctx = build_player_context(gs, pc.id)
        assert ctx.character_name
        assert ctx.game_overview
        assert ctx.character_brief
        assert ctx.location_name
        assert len(ctx.render()) > 200
