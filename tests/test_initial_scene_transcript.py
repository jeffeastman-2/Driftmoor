"""Print a transcript of the initial game setup.

Run with:  python -m pytest tests/test_initial_scene_transcript.py -s
"""

from pathlib import Path

from models.game_init import initialize_game_state
from models.character import PlayerCharacter, NPC

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
