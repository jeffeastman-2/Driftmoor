"""Tests for web_play helpers — the browser play app's inventory readout.

These cover the pure helpers (icon mapping, possession split from the live
character); the interactive LLM play itself is validated by running the app.
"""
from types import SimpleNamespace as NS
import asyncio
import json

import web_play


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
        "hand": [], "worn": [], "carried": [], "purse": ""}


def test_inventory_ui_keeps_in_hand_group_when_empty():
    assert "Nothing in hand" in web_play._PAGE


def test_inventory_default_markup_shows_empty_in_hand_group():
    assert "<span class='lbl'>In hand</span>" in web_play._PAGE
    assert "chip hand empty" in web_play._PAGE


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
