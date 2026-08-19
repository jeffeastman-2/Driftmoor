"""Tests for web_play helpers — the browser play app's inventory readout.

These cover the pure helpers (icon mapping, possession split from the live
character); the interactive LLM play itself is validated by running the app.
"""
from types import SimpleNamespace as NS
import asyncio
import json

import web_play


def test_geometry_reload_applies_compiled_file_without_resetting_scene(tmp_path, monkeypatch):
    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text("## Zones\n", encoding="utf-8")
    reloaded = []
    scene_geometry = NS(
        place_path="places",
        reload_from=lambda fresh: reloaded.append(fresh),
    )
    cfg = NS(
        geometry_path=geometry,
        scene_geometry=scene_geometry,
        game_time=object(),
    )
    app = {"runtime": {"config": cfg}}
    fresh_geometry = object()
    monkeypatch.setattr(
        web_play,
        "configure_from_place_path",
        lambda place_path, game_time: NS(scene_geometry=fresh_geometry),
    )
    rendered = []
    monkeypatch.setattr(web_play, "_render_map", lambda target: rendered.append(target))

    web_play._reload_geometry_from_disk(app)

    assert reloaded == [fresh_geometry]
    assert rendered == [app]
    assert app["geometry_stamp"] == web_play._geometry_stamp(app)


def test_rewrite_routes_updates_only_matching_route_vertices():
    source = (
        "## Routes\n\n"
        "| name | kind | vertices |\n|---|---|---|\n"
        "| Greywater River | river | (1,2) (3,4) |\n"
        "| Old Road | road | (5,6) (7,8) |\n\n## Boundaries\n"
    )
    updated = web_play._rewrite_routes(source, [{
        "name": "Greywater River", "vertices": [(10.0, 20.0), (30.0, 40.0)]
    }])
    assert "| Greywater River | river | (10,20) (30,40) |" in updated
    assert "| Old Road | road | (5,6) (7,8) |" in updated


def test_turn_entries_preserve_player_action_for_reload(tmp_path):
    checkpoint = {
        "turn": 4,
        "character_results": [
            {
                "character_id": "gilthaness",
                "output": {
                    "spoken": "",
                    "action": "I investigate the wall marks",
                },
                "narration": {"prose": "Fine dark residue marks the stone."},
            },
            {
                "character_id": "darrin",
                "output": {"spoken": "", "action": "I watch Gil."},
                "narration": {"prose": "Darrin watches."},
            },
        ],
    }
    (tmp_path / "day1_19h30m.json").write_text(
        json.dumps(checkpoint), encoding="utf-8")

    entries = web_play._turn_entries(tmp_path, "gilthaness")

    assert entries[0]["lines"][0]["action"] == "I investigate the wall marks"
    assert entries[0]["lines"][1]["action"] == ""


def test_page_renders_player_action_before_outcome():
    assert '<span class="you">you</span>: ' in web_play._PAGE
    assert "action+(body?" in web_play._PAGE


def test_map_visual_save_is_scoped_and_updates_bound_landmark(tmp_path, monkeypatch):
    from models.space_time import Position

    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text(
        "## Landmarks\n\n| name | x | y |\n|---|---:|---:|\n"
        "| chair | 1 | 2 |\n\n## Zones\n",
        encoding="utf-8",
    )
    asset = tmp_path / "floor" / "assets" / "chair.svg"
    asset.parent.mkdir(parents=True)
    asset.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    scene_geometry = NS(landmarks={"chair": Position(1, 2)})
    cfg = NS(geometry_path=geometry, scene_geometry=scene_geometry)
    app = {"runtime": {"config": cfg}}
    payload = {"visuals": [{
        "id": "chair_visual", "asset": "floor/assets/chair.svg",
        "target": "chair", "x": 4.5, "y": 6.25,
        "width": 3, "height": 4, "rotation": 15, "layer": "fixture",
    }]}

    async def request_json():
        return payload

    monkeypatch.setattr(web_play, "_render_map", lambda _app: None)
    response = asyncio.run(web_play.handle_map_visuals(
        NS(json=request_json, app=app)))

    assert json.loads(response.body)["saved"] == 1
    assert "| chair | 4.5 | 6.25 |" in geometry.read_text(encoding="utf-8")
    assert "| chair_visual | floor/assets/chair.svg | chair | 4.5 | 6.25 |" in (
        tmp_path / "VISUALS.md").read_text(encoding="utf-8")
    assert scene_geometry.landmarks["chair"] == Position(4.5, 6.25)


def test_map_visual_save_can_update_an_authored_item(tmp_path, monkeypatch):
    from models.space_time import Position

    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text(
        "## Landmarks\n\n| name | x | y | z |\n|---|---:|---:|---:|\n"
        "| door | 0 | 0 | 4 |\n\n"
        "## Items\n\n| id | x | y | label |\n|---|---:|---:|---|\n"
        "| ledger | 1 | 2 | Ledger |\n",
        encoding="utf-8",
    )
    asset = tmp_path / "floor/assets/ledger.svg"
    asset.parent.mkdir(parents=True)
    asset.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>", encoding="utf-8")
    thing = NS(position=Position(1, 2))
    cfg = NS(
        geometry_path=geometry,
        scene_geometry=NS(landmarks={"door": Position(0, 0)}),
        items={"ledger": thing},
    )
    payload = {"visuals": [{
        "id": "ledger_visual", "asset": "floor/assets/ledger.svg",
        "target": "ledger", "x": 4.5, "y": 6.25,
        "width": 2, "height": 1, "rotation": 0, "layer": "item",
    }]}

    async def request_json():
        return payload

    monkeypatch.setattr(web_play, "_render_map", lambda _app: None)
    asyncio.run(web_play.handle_map_visuals(NS(
        json=request_json, app={"runtime": {"config": cfg}}
    )))

    assert "| ledger | 4.5 | 6.25 | Ledger |" in geometry.read_text(encoding="utf-8")
    assert thing.position == Position(4.5, 6.25)


def test_map_layout_save_updates_place_initial_npc_position(tmp_path, monkeypatch):
    from models.space_time import Position

    geometry = tmp_path / "GEOMETRY.md"
    geometry.write_text("## Zones\n", encoding="utf-8")
    place = tmp_path / "PLACE.md"
    place.write_text(
        "## Initial Positions\n\n"
        "| character | x | y |\n|---|---:|---:|\n| tess | 1 | 2 |\n",
        encoding="utf-8",
    )
    npc = NS(character=NS(character_type="npc"))
    scene_geometry = NS(landmarks={}, starting_positions={"tess": Position(1, 2)})
    cfg = NS(
        geometry_path=geometry, scene_geometry=scene_geometry,
        items={}, characters={"tess": npc},
    )

    async def request_json():
        return {"visuals": [], "npc_positions": [{"id": "tess", "x": 7.5, "y": 8.25}]}

    monkeypatch.setattr(web_play, "_render_map", lambda _app: None)
    response = asyncio.run(web_play.handle_map_visuals(NS(
        json=request_json, app={"runtime": {"config": cfg}}
    )))

    assert json.loads(response.body)["npcs_saved"] == 1
    assert "| tess | 7.5 | 8.25 |" in place.read_text(encoding="utf-8")
    assert scene_geometry.starting_positions["tess"] == Position(7.5, 8.25)
    assert not (tmp_path / "VISUALS.md").exists()


def test_web_server_defaults_to_localhost():
    args = web_play._build_arg_parser().parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 8080


def test_web_server_allows_explicit_private_network_bind():
    args = web_play._build_arg_parser().parse_args(
        ["driftmoor", "--host", "0.0.0.0", "--port", "8090"]
    )
    assert args.host == "0.0.0.0"
    assert args.port == 8090


def test_web_server_accepts_resume_flag():
    args = web_play._build_arg_parser().parse_args(
        ["driftmoor", "--turns", "200", "--resume"]
    )
    assert args.resume
    assert args.turns == 200


def test_latest_web_checkpoint_dir_selects_newest_checkpointed_run(tmp_path):
    old = tmp_path / "2026-08-03T120000__web__" / "driftmoor"
    new = tmp_path / "2026-08-04T120000__web__" / "driftmoor"
    empty = tmp_path / "2026-08-05T120000__web__" / "driftmoor"
    for path in (old, new, empty):
        path.mkdir(parents=True)
    (old / "day1_19h00m.json").write_text('{"turn": 1}', encoding="utf-8")
    (new / "day1_19h10m.json").write_text('{"turn": 2}', encoding="utf-8")

    assert web_play._latest_web_checkpoint_dir("driftmoor", tmp_path) == new


def test_visited_places_are_loaded_from_session_history(tmp_path):
    (tmp_path / "day1_1.json").write_text(
        json.dumps({"scene_place_path": "places/greywater_river/old_mill"}),
        encoding="utf-8",
    )
    assert web_play._visited_place_paths(tmp_path, "places/") == {
        "places", "places/greywater_river/old_mill",
    }


def test_resume_place_infers_elyssa_cottage_for_legacy_checkpoint():
    checkpoint = {
        "active_characters": ["gilthaness", "elyssa"],
        "current_positions": {
            "gilthaness": {"x": 9.5, "y": 0, "zone": "STUDY"},
            "elyssa": {"x": 8, "y": 9.23, "zone": "STUDY"},
        },
    }

    assert web_play._resume_place_path("driftmoor", checkpoint) == (
        "places/driftmoor/elyssa_cottage"
    )


def test_resume_place_prefers_new_checkpoint_metadata():
    assert web_play._resume_place_path("driftmoor", {
        "scene_place_path": "places/driftmoor/stables",
        "active_characters": ["gilthaness", "elyssa"],
    }) == "places/driftmoor/stables"


def test_map_double_click_command_uses_integer_coordinates():
    assert "x.toFixed(0)" in web_play._PAGE
    assert "y.toFixed(0)" in web_play._PAGE


def _weapon(wid, name):
    return NS(id=wid, name=name)


def _cs(weapons=(), wielded=(), held_items=(), inventory=(), equipment=(), armor=None, pack=()):
    return NS(weapons=list(weapons), wielded=list(wielded),
              held_items=list(held_items), armor=armor,
              pack=list(pack),
              character=NS(inventory=list(inventory), equipment=list(equipment)))


def test_highlight_names_collects_player_and_monster_names():
    chars = {
        "seraphina": NS(character=NS(name="Seraphina Duskwhisper")),
        "amara": NS(character=NS(name="Sister Amara Solbright")),
        "giant_spider": NS(character=NS(name="Giant Spider")),
    }
    names = web_play._highlight_names(chars)
    assert "seraphina" in names and "amara" in names      # cids
    assert "giant spider" in names and "spider" in names  # monster, full + token
    assert "sister" not in names                          # title dropped
    assert all(n == n.lower() for n in names)             # lower-cased
    assert names == sorted(names, key=len, reverse=True)  # longest-first


def test_item_icon_keyword_and_fallback():
    assert web_play._item_icon("Snapped torch") == "🔥"
    assert web_play._item_icon("Rapier") == "🗡️"
    assert web_play._item_icon("Light crossbow") == "🏹"
    assert web_play._item_icon("Sealed letter") == "✉️"
    assert web_play._item_icon("Silver handled longsword") == "🗡️"
    assert web_play._item_icon("Glowing orb") == "📦"  # no keyword -> fallback
    assert web_play._item_icon("Glowing orb", "🔮") == "🔮"


def test_inventory_none_character_is_empty():
    assert web_play._player_inventory(None, {}) == {
        "hand": [], "worn": [], "carried": [], "purse": "",
        "hp": "", "ac": None}


def test_inventory_reports_hp_and_ac():
    cs = _cs()
    cs.character.hp = 17
    cs.character.current_hp = 12
    cs.character.ac = 15
    inv = web_play._player_inventory(cs, {})
    assert inv["hp"] == "12/17"
    assert inv["ac"] == 15


def test_inventory_ui_keeps_in_hand_group_when_empty():
    assert "Nothing in hand" in web_play._PAGE


def test_inventory_default_markup_shows_empty_in_hand_group():
    assert "<span class='lbl'>In hand</span>" in web_play._PAGE
    assert "chip hand empty" in web_play._PAGE


def test_inventory_markup_renders_hp_and_ac_groups():
    assert "grp('HP',(m.hp?[{icon:'❤️',label:m.hp}]:[]),'hp')" in web_play._PAGE
    assert "grp('AC',(m.ac!=null?" in web_play._PAGE


def test_events_handler_delivers_primary_prompt_by_diffing_durable_state():
    """The primary per-turn prompt must be delivered by comparing
    web_transport's awaiting generation counter against what this connection
    already showed (last_generation_shown), evaluated on every poll inside
    the loop — not by draining a one-shot queue, and not by a special
    one-time check before the loop. A queue-based (or connect-time-only)
    delivery races the session task's own queue push of the same content:
    whichever fires first either duplicates it or, if a reconnect lands
    between the two, loses it silently (see
    test_events_handler_never_discards_pending_outbound_on_connect for the
    discard variant of this same bug).

    The generation counter — not the awaiting boolean or the prompt text —
    is what must be compared: a turn that resolves faster than one poll
    interval (a fast-pathed move with no LLM narration) can flip the
    boolean True -> False -> True between two polls, which a boolean-only
    diff would never observe, leaving the player stuck until a reload
    re-derives state from scratch. Comparing prompt text has its own gap
    (the web prompt is often intentionally empty, so two different turns
    can look identical)."""
    import inspect
    src = inspect.getsource(web_play.handle_events)
    loop_idx = src.index("while True:")
    body = src[loop_idx:]
    assert "last_generation_shown" in src
    assert "web_transport.awaiting_generation(player)" in body
    assert "web_transport.is_awaiting(player)" in body
    assert "web_transport.latest_prompt(player)" in body
    assert "generation != last_generation_shown" in body


def test_events_handler_never_discards_pending_outbound_on_connect():
    """Regression: an earlier version drained the outbound queue at
    connection start to avoid re-showing stale content. It wasn't always
    stale — a question answer or DM sub-dialog reply genuinely pending for
    this same connection's own upcoming poll got silently discarded
    whenever a reconnect landed between the player asking and the queue
    being drained, leaving the player looking at a hang with no answer and
    no way to get one. There must be no queue drain before the loop at all."""
    import inspect
    src = inspect.getsource(web_play.handle_events)
    assert "drain_outbound(player)" not in src.split("while True:")[0]


def test_dm_event_skips_empty_div_but_still_activates_turn():
    """The web turn prompt is now often intentionally empty (position/
    perception/carrying already live elsewhere) — an empty 'dm' message must
    still flip the input active, just without adding a blank line to the log."""
    assert "if(m.text){const d=document.createElement('div');" in web_play._PAGE
    assert "setTurn(true);" in web_play._PAGE


def test_page_deduplicates_spoken_words_and_highlights_prose_dialogue():
    assert "function qhi(s){return esc(s);}" in web_play._PAGE
    assert "speechKey(l.prose).includes(speechKey(l.spoken))" in web_play._PAGE
    assert "prose.replace" in web_play._PAGE
    # Quote markup must be inserted before name markup; otherwise the quote
    # regex consumes class="name" and leaks `"name">` into the transcript.
    assert web_play._PAGE.index("prose=prose.replace") < web_play._PAGE.index(
        "prose=hi(prose)")


def test_inventory_weapons_split_by_wielded():
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger"),
                      _weapon("light_crossbow", "Light Crossbow")],
             wielded=["rapier"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]
    assert {c["label"] for c in inv["carried"]} == {"Dagger", "Light Crossbow"}


def test_inventory_unwielded_weapons_all_carried():
    # Turn 0: nothing wielded yet -> the whole weapon kit shows as carried.
    cs = _cs(weapons=[_weapon("rapier", "Rapier"), _weapon("dagger", "Dagger")])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == []
    assert {c["label"] for c in inv["carried"]} == {"Rapier", "Dagger"}


def test_inventory_held_torch_in_hand_then_carried():
    items = {"snapped_torch": NS(label="Snapped torch")}
    # Held: torch in hand alongside the wielded rapier.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             held_items=["snapped_torch"], inventory=["snapped_torch"])
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier", "Snapped torch"}
    assert inv["carried"] == []
    # Stowed: torch moves to carried (still on the character, not in hand).
    cs.held_items = []
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Rapier"}
    assert {c["label"] for c in inv["carried"]} == {"Snapped torch"}


def test_inventory_held_pack_item_not_also_carried():
    backpack = NS(label="Gil's Pack", id="gils_pack", quantity=1,
                  carry=NS(location="in_hand"))
    cs = _cs(held_items=["gils_pack"], pack=[backpack])
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["hand"]} == {"Gil's Pack"}
    assert inv["carried"] == []


def test_inventory_picked_up_weapon_not_double_listed():
    # A picked-up weapon lands in BOTH cs.weapons and character.inventory; it
    # must appear once (as a weapon), not twice.
    cs = _cs(weapons=[_weapon("mace", "Mace")], inventory=["mace"])
    inv = web_play._player_inventory(cs, {"mace": NS(label="Mace")})
    labels = [c["label"] for c in inv["hand"] + inv["worn"] + inv["carried"]]
    assert labels.count("Mace") == 1


def test_inventory_worn_vs_carried_split():
    # Character-sheet equipment splits: armor/trinkets -> worn; tools/kits ->
    # carried. Weapon restatements de-duped, stat parentheticals stripped.
    cs = _cs(weapons=[_weapon("rapier", "Rapier")], wielded=["rapier"],
             equipment=["Rapier (1d8 piercing)", "Studded leather armor",
                        "Thieves' tools", "Wooden vine-carved bracelet"])
    inv = web_play._player_inventory(cs, {})
    assert inv["hand"] == [{"icon": "🗡️", "label": "Rapier"}]      # wielded
    assert {c["label"] for c in inv["worn"]} == {
        "Studded leather armor", "Wooden vine-carved bracelet"}    # armor + trinket
    assert {c["label"] for c in inv["carried"]} == {"Thieves' tools"}  # Rapier de-duped


def test_inventory_structured_armor_is_worn():
    cs = _cs(weapons=[], armor=NS(name="Chain Mail"))
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["worn"]} == {"Chain Mail"}


def test_inventory_pack_items_use_carry_state_for_worn_bucket():
    worn_item = NS(label="Wooden bracelet", id="bracelet", quantity=1,
                   carry=NS(location="worn"))
    carried_item = NS(label="Traveler's cloak", id="cloak", quantity=1,
                      carry=NS(location="carried"))
    cs = _cs(pack=[worn_item, carried_item])
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["worn"]} == {"Wooden bracelet"}
    assert {c["label"] for c in inv["carried"]} == {"Traveler's cloak"}


def test_inventory_container_contents_visible_only_when_container_held():
    backpack = NS(label="Gil's Pack", id="gils_pack", quantity=1,
                  carry=NS(location="worn"))
    torch = NS(label="Torch", id="torch", quantity=1,
               parent_container_id="gils_pack", carry=NS(location="carried"))

    cs = _cs(pack=[backpack, torch])
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["worn"]} == {"Gil's Pack"}
    assert {c["label"] for c in inv["carried"]} == set()

    cs.held_items = ["gils_pack"]
    inv = web_play._player_inventory(cs, {})
    assert {c["label"] for c in inv["hand"]} == {"Gil's Pack"}
    assert {c["label"] for c in inv["carried"]} == {"Torch"}


def test_inventory_scene_container_contents_visible_only_when_held():
    discarded_pack = NS(label="Discarded pack", id="discarded_pack",
                        contents=[("rope", 1), ("tin_cup", 1), ("reach_map", 1)])
    items = {"discarded_pack": discarded_pack}

    cs = _cs(inventory=["discarded_pack"])
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["carried"]} == {"Discarded pack"}

    cs.held_items = ["discarded_pack"]
    inv = web_play._player_inventory(cs, items)
    assert {c["label"] for c in inv["hand"]} == {"Discarded pack"}
    assert {c["label"] for c in inv["carried"]} == {"rope", "tin cup", "reach map"}


def test_inventory_container_contents_are_not_duplicated_when_held():
    backpack = NS(label="Gil's Pack", id="gils_pack", quantity=1,
                  carry=NS(location="carried"))
    torch = NS(label="Torch", id="torch", quantity=1,
               parent_container_id="gils_pack", carry=NS(location="carried"))
    items = {"gils_pack": backpack, "torch": torch}
    cs = _cs(held_items=["gils_pack"], pack=[backpack, torch])

    inv = web_play._player_inventory(cs, items)
    labels = [c["label"] for c in inv["hand"] + inv["worn"] + inv["carried"]]
    assert labels.count("Torch") == 1


def test_inventory_bought_item_shown_once_by_name():
    """A bought/taken item lives in BOTH char.inventory and the pack (display vs
    use-dispatch); it must render exactly once, labelled by its name rather than
    the raw instance id. Regression for the duplicate 'bolts 20 i1' + 'bolts_20_i1'."""
    from models.thing import Thing
    bolt = Thing(id="bolts_20_i1", name="Bolts (20)")   # materialized: name set, label empty
    cs = _cs(inventory=["bolts_20_i1"], pack=[bolt])
    inv = web_play._player_inventory(cs, {})
    assert [c["label"] for c in inv["carried"]] == ["Bolts (20)"]


def test_bought_worn_item_uses_authored_emoji_and_worn_bucket():
    from models.thing import Thing, WEARABLE, WORN
    necklace = Thing(
        id="necklace_i1", name="Shadowbeast Claw Necklace", emoji="📿",
        affordances={WEARABLE},
    )
    necklace.carry.location = WORN
    cs = _cs(inventory=[necklace.id], pack=[necklace])
    inv = web_play._player_inventory(cs, {})
    assert inv["carried"] == []
    assert inv["worn"] == [{"icon": "📿", "label": "Shadowbeast Claw Necklace"}]


def test_inventory_surfaces_purse_from_character():
    """The Coin indicator: _player_inventory reports the character's purse via
    format_coins, empty when broke. (The panel renders it as a 🪙 chip.)"""
    from types import SimpleNamespace as NS
    from models.character import Character

    def _pcs(purse_cp):
        c = Character(id="p", name="Gil", race="Elf", character_type="player",
                      purse_cp=purse_cp)
        return NS(weapons=[], wielded=[], held_items=[], armor=None, pack=[], character=c)

    assert web_play._player_inventory(_pcs(100), {})["purse"] == "1 gp"
    assert web_play._player_inventory(_pcs(0), {})["purse"] == ""
