from __future__ import annotations

import json
import shutil
from pathlib import Path

from engine.map_renderer import (
    load_tracks_from_snapshots,
    render_interactive_map_html,
    update_place_map,
)


GEOMETRY = Path("scenario/places/obelisk_reach/echoing_caverns/GEOMETRY.md")


def test_load_tracks_from_snapshots_includes_turns_and_zone(tmp_path):
    snap1 = {
        "turn": 1,
        "current_positions": {
            "thorgrim": {"x": 138.0, "y": 295.0, "zone": "ENTRY CHAMBER"}
        },
    }
    snap2 = {
        "turn": 2,
        "current_positions": {
            "thorgrim": {"x": 137.0, "y": 265.0, "zone": "FIRST PASSAGE"}
        },
    }

    (tmp_path / "day1_14h00m.json").write_text(json.dumps(snap1), encoding="utf-8")
    (tmp_path / "day1_14h10m.json").write_text(json.dumps(snap2), encoding="utf-8")

    tracks = load_tracks_from_snapshots(tmp_path)
    assert "thorgrim" in tracks
    assert tracks["thorgrim"] == [
        (1, 138.0, 295.0, "ENTRY CHAMBER"),
        (2, 137.0, 265.0, "FIRST PASSAGE"),
    ]


def test_render_interactive_map_html_contains_turn_hover(tmp_path):
    snap = {
        "turn": 3,
        "current_positions": {
            "amara": {"x": 130.0, "y": 268.0, "zone": "ENTRY CHAMBER"}
        },
    }
    (tmp_path / "day1_14h20m.json").write_text(json.dumps(snap), encoding="utf-8")

    out_html = tmp_path / "echoing_caverns_map.html"
    render_interactive_map_html(
        GEOMETRY,
        out_html,
        snapshot_dir=tmp_path,
        title="Echoing Caverns Interactive",
    )

    assert out_html.exists()
    html_text = out_html.read_text(encoding="utf-8")
    assert "turn 3" in html_text
    assert "zone=ENTRY CHAMBER" in html_text
    assert "Hover over dots" in html_text


def test_update_place_map_writes_html(tmp_path):
    place_dir = tmp_path / "echoing_caverns"
    place_dir.mkdir()
    geometry_copy = place_dir / "GEOMETRY.md"
    shutil.copyfile(GEOMETRY, geometry_copy)

    out_html = update_place_map(place_dir)

    assert out_html.name == "echoing_caverns_map.html"
    assert out_html.exists()
    assert not any(path.suffix == ".png" for path in place_dir.iterdir())


def test_point_in_poly():
    from engine.map_renderer import _point_in_poly
    sq = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert _point_in_poly(5, 5, sq)
    assert not _point_in_poly(15, 5, sq)
    assert not _point_in_poly(5, 15, sq)
    assert not _point_in_poly(-1, 5, sq)


def test_parse_geometry_item_labels_with_z_column():
    # Items table is `id | x | y | z | label`; the optional z must not be read
    # as the label. Regression: torch_bracket (z=6) showed "6", not its name.
    from engine.map_renderer import parse_geometry
    g = parse_geometry(GEOMETRY.read_text(encoding="utf-8"))
    items = g["items"]
    assert items["torch_bracket"][2] == "Torch bracket"   # had z=6
    assert items["wall_scratches"][2] == "Tally scratches"  # had z=3
    assert items["snapped_torch"][2] == "Snapped torch"   # no z
    assert items["mace_plus_one"][2] == "Mace +1"         # had z=3


def test_containing_zone_matches_geometry():
    from engine.map_renderer import parse_geometry, _containing_zone
    g = parse_geometry(GEOMETRY.read_text(encoding="utf-8"))
    # Zone centroids — unambiguously interior (boundary points can read as the
    # adjacent zone under the engine's edge tolerance, which is exactly why
    # zone reveal uses the snapshot's authoritative zone string).
    assert _containing_zone(137.5, 292.5, g["zones"]) == "Entry Chamber"
    assert _containing_zone(137.5, 243.5, g["zones"]) == "First Passage"


def test_render_turn_slider_fog_and_slider(tmp_path):
    from engine.map_renderer import render_turn_slider_html
    (tmp_path / "day1_01.json").write_text(json.dumps({
        "turn": 1,
        "current_positions": {"thorgrim": {"x": 138.0, "y": 295.0, "zone": "ENTRY CHAMBER"}},
    }), encoding="utf-8")
    (tmp_path / "day1_02.json").write_text(json.dumps({
        "turn": 2,
        "current_positions": {"thorgrim": {"x": 137.0, "y": 265.0, "zone": "FIRST PASSAGE"}},
    }), encoding="utf-8")
    out = tmp_path / "slider.html"
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="Echoing Caverns",
                            start_positions={"thorgrim": (138.0, 295.0)})
    t = out.read_text(encoding="utf-8")
    # Slider UI present.
    assert "id='sl'" in t and "const FRAMES=" in t and "id='play'" in t
    # Turn-0 seeding from the scene: the starting zone (Entry Chamber) is revealed
    # from the start; First Passage is explored at turn 2.
    assert "data-reveal='0'" in t and "data-reveal='2'" in t
    # Fog of war: never-entered zones carry the sentinel (maxturn+1 = 3) -> hidden.
    assert "data-reveal='3'" in t
    # The slider opens on the party's starting layout (turn 0).
    assert "const TURNS=[0, 1, 2]" in t
    # The character appears in the per-turn frames.
    assert "thorgrim" in t


def test_render_turn_slider_seeds_only_start_characters(tmp_path):
    """Turn-0 seeding is restricted to the named party; the dormant giant_spider
    (present in the scene's start_positions) must NOT leak onto the map or
    un-fog its lair before the party finds it."""
    from engine.map_renderer import render_turn_slider_html
    out = tmp_path / "init.html"  # no snapshots: live initial render
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
                            start_characters=["thorgrim", "gilthaness"],
                            start_positions={"thorgrim": (138.0, 295.0),
                                             "gilthaness": (145.0, 300.0),
                                             "giant_spider": (64.0, 195.0)})
    t = out.read_text(encoding="utf-8")
    assert "thorgrim" in t and "gilthaness" in t
    assert "giant_spider" not in t            # dormant creature stays fogged
    assert "data-reveal='0'" in t             # party's start zone is revealed


def test_render_turn_slider_has_trail_segments(tmp_path):
    """Each tracked character gets a single prev->current trail segment (the JS
    repositions it per turn); the full route is not drawn."""
    from engine.map_renderer import render_turn_slider_html
    (tmp_path / "day1_01.json").write_text(json.dumps({
        "turn": 1,
        "current_positions": {"thorgrim": {"x": 138.0, "y": 295.0,
                                           "zone": "ENTRY CHAMBER"}},
    }), encoding="utf-8")
    out = tmp_path / "slider.html"
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
                            start_characters=["thorgrim"],
                            start_positions={"thorgrim": (138.0, 295.0)})
    t = out.read_text(encoding="utf-8")
    assert "data-trail='thorgrim'" in t
    assert t.count("data-trail=") == 1   # one segment per character, not a path
    assert "data-trail" in t and "x1" in t  # show() positions the segment


def test_render_turn_slider_item_tooltip_has_size_descriptions(tmp_path):
    """Item hover text carries the by-distance ("size-relative") appearances."""
    from types import SimpleNamespace as NS
    from engine.map_renderer import render_turn_slider_html, _item_tooltip
    detail = NS(description="A snapped torch on the floor.",
                appearance_bands={"intermediate": "a short pale length of wood",
                                  "far": "a slim pale streak"})
    tip = _item_tooltip("Snapped torch", detail)
    assert "Appears by distance" in tip
    assert "intermediate: a short pale length of wood" in tip
    assert "far: a slim pale streak" in tip
    # And it reaches the rendered SVG <title>.
    out = tmp_path / "m.html"
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
                            start_characters=["thorgrim"],
                            item_details={"snapped_torch": detail})
    assert "Appears by distance" in out.read_text(encoding="utf-8")


def test_item_tooltip_label_only_without_detail():
    from engine.map_renderer import _item_tooltip
    assert _item_tooltip("Torch bracket", None) == "Torch bracket"


def test_turn_slider_hides_item_after_pickup(tmp_path):
    from types import SimpleNamespace as NS
    from engine.map_renderer import render_turn_slider_html

    out = tmp_path / "held.html"
    detail = NS(description="A snapped torch.", appearance_bands={},
                holder="thorgrim")
    render_turn_slider_html(
        GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
        start_characters=["thorgrim"],
        item_details={"snapped_torch": detail},
    )
    assert "Snapped torch" not in out.read_text(encoding="utf-8")


def test_turn_slider_uses_icon_for_loose_pickable_item(tmp_path):
    from types import SimpleNamespace as NS
    from engine.map_renderer import render_turn_slider_html

    out = tmp_path / "pickable.html"
    detail = NS(description="A snapped torch.", appearance_bands={},
                holder=None, pickable=True)
    render_turn_slider_html(
        GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
        start_characters=["thorgrim"],
        item_details={"snapped_torch": detail},
    )
    rendered = out.read_text(encoding="utf-8")
    assert "🔥" in rendered
    assert "class='item-icon'" in rendered
    assert "data-base-fs=" in rendered


def test_zone_floor_art_is_embedded_clipped_and_keeps_semantic_hits(tmp_path):
    from engine.map_renderer import render_turn_slider_html
    from engine.md_loader import configure_from_place_path

    geometry = Path("scenario/places/driftmoor/forge/GEOMETRY.md")
    cfg = configure_from_place_path("places/driftmoor/forge")
    out = tmp_path / "forge.html"
    render_turn_slider_html(
        geometry, out, snapshot_dir=tmp_path, title="Forge",
        item_details=cfg.items, live_refresh_secs=2,
    )
    rendered = out.read_text(encoding="utf-8")

    assert "class='zone-floor-art'" in rendered
    assert "class='visual-overlay'" in rendered
    assert "data-visual='forge_wall_marks_visual'" in rendered
    assert "clip-path='url(#zone-floor-FORGE)'" in rendered
    assert "class='landmark-hit'" in rendered
    assert "shadow-burned wall marks" in rendered.lower()
    assert "id='editArt'" in rendered
    assert "Save layout" in rendered
    assert "fetch('/map-visuals'" in rendered
    assert "!window.__mapArtEditing" in rendered
    assert "window.__mapArtEditing=editing" in rendered
    assert "class='visual-selection'" in rendered
    assert "if(window.__mapArtEditing)return" in rendered
    assert "s.appendChild(o)" in rendered
    assert "data-landmark='forge_wall_marks'" in rendered
    assert "Copy coordinates" in rendered
    assert "function syncTarget(o)" in rendered
    assert "data-landmark='forge_wall_marks'" in rendered
    landmark_start = rendered.index("data-landmark='forge_wall_marks'")
    landmark_markup = rendered[landmark_start:landmark_start + 350]
    assert "fill='transparent'" in landmark_markup
    # The marks are painted into the floor art, so their semantic Item remains
    # hoverable without a duplicate text label on top.
    assert ">Shadow-burned wall marks</text>" not in rendered


def test_initial_npc_positions_are_editable_but_other_characters_are_not(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    out = tmp_path / "npc-layout.html"
    render_turn_slider_html(
        Path("scenario/places/driftmoor/broken_lantern/GEOMETRY.md"), out,
        snapshot_dir=tmp_path,
        start_characters=["tess", "gilthaness"],
        start_positions={"tess": (31, 9), "gilthaness": (20, 2)},
        editable_start_characters={"tess"},
    )
    rendered = out.read_text(encoding="utf-8")
    tess = rendered[rendered.index("data-char='tess'"):]
    gil = rendered[rendered.index("data-char='gilthaness'"):]
    assert "data-editable-start='1'" in tess[:300]
    assert "class='npc-selection'" in tess[:500]
    assert "data-editable-start='1'" not in gil[:300]
    assert "npc_positions:npcRecords()" in rendered


def test_barbershop_floor_and_fixtures_are_independently_editable(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    geometry = Path("scenario/places/driftmoor/rusty_razor/GEOMETRY.md")
    out = tmp_path / "barbershop.html"
    render_turn_slider_html(geometry, out, snapshot_dir=tmp_path,
                            title="The Rusty Razor")
    rendered = out.read_text(encoding="utf-8")

    assert "class='zone-floor-art'" in rendered
    assert rendered.count("class='visual-overlay'") == 8
    for target in (
        "barber_chair_3.25", "barber_chair_6.5", "mirror", "tonic_shelf",
        "potbelly_stove", "washstand", "striped_pole", "central_rug",
    ):
        assert f"data-target='{target}'" in rendered
        start = rendered.index(f"data-landmark='{target}'")
        assert "fill='transparent'" in rendered[start:start + 350]


def test_weary_traveler_uses_separate_zone_art_downstairs_and_upstairs(tmp_path):
    import re
    from engine.map_renderer import render_turn_slider_html

    downstairs = Path("scenario/places/driftmoor/weary_traveler/GEOMETRY.md")
    upstairs = Path("scenario/places/driftmoor/weary_traveler/upstairs/GEOMETRY.md")
    down_out, up_out = tmp_path / "down.html", tmp_path / "up.html"
    render_turn_slider_html(downstairs, down_out, snapshot_dir=tmp_path)
    render_turn_slider_html(
        upstairs, up_out, snapshot_dir=tmp_path,
        start_characters=["gilthaness"],
        start_positions={"gilthaness": (16, 5)},
    )
    down = down_out.read_text(encoding="utf-8")
    up = up_out.read_text(encoding="utf-8")

    assert down.count("class='zone-floor-art'") == 3
    assert down.count("class='visual-overlay'") == 4
    assert up.count("class='zone-floor-art'") == 5
    assert up.count("class='visual-overlay'") == 10
    # Private-room access remains mechanical but is not painted as a magical
    # gold boundary on an ordinary guesthouse floor.
    assert "Guest Rooms — Rented Access</title>" not in up
    assert re.search(r"<g data-reveal='0'><polygon[^>]*><title>Upstairs Hall", up)
    for room in ("Guest Room 1", "Guest Room 2", "Guest Room 3"):
        assert re.search(
            rf"<g data-reveal='1'><polygon[^>]*><title>{room}", up)


def test_broken_lantern_has_editable_art_in_each_interior_scene(tmp_path):
    import re
    from engine.map_renderer import render_turn_slider_html

    root = Path("scenario/places/driftmoor/broken_lantern")
    expected = {
        root / "GEOMETRY.md": (6, 27),
        root / "meeting_room/GEOMETRY.md": (1, 4),
        root / "storage_room/GEOMETRY.md": (1, 6),
        root / "upstairs/GEOMETRY.md": (5, 10),
    }
    rendered = {}
    for index, (geometry, counts) in enumerate(expected.items()):
        out = tmp_path / f"lantern-{index}.html"
        kwargs = {}
        if geometry == root / "upstairs/GEOMETRY.md":
            kwargs = {
                "start_characters": ["gilthaness"],
                "start_positions": {"gilthaness": (20, 27.5)},
            }
        render_turn_slider_html(
            geometry, out, snapshot_dir=tmp_path, **kwargs
        )
        html = out.read_text(encoding="utf-8")
        rendered[geometry] = html
        assert html.count("class='zone-floor-art'") == counts[0]
        assert html.count("class='visual-overlay'") == counts[1]

    main = rendered[root / "GEOMETRY.md"]
    for target in (
        "hearth", "stage", "booth_1", "booth_2", "booth_3",
        "table_1", "table_2", "table_3",
        "bar_counter", "bar_cabinet", "kitchen_center", "stair_foot",
        "broken_lantern_sign",
    ):
        assert f"data-target='{target}'" in main

    upstairs = rendered[root / "upstairs/GEOMETRY.md"]
    assert re.search(r"<g data-reveal='0'><polygon[^>]*><title>Upstairs Hall", upstairs)
    for room in ("Guest Bedroom 1", "Guest Bedroom 2", "Guest Bedroom 3"):
        assert re.search(
            rf"<g data-reveal='0'><polygon[^>]*><title>{room}", upstairs)


def test_apothecary_and_mercantile_have_editable_interior_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    expected = {
        Path("scenario/places/driftmoor/bitter_remedy/GEOMETRY.md"): (2, 8),
        Path("scenario/places/driftmoor/salt_and_iron/GEOMETRY.md"): (2, 13),
        Path("scenario/places/driftmoor/salt_and_iron/upper_floor/GEOMETRY.md"): (2, 6),
    }
    for index, (geometry, counts) in enumerate(expected.items()):
        out = tmp_path / f"shop-{index}.html"
        render_turn_slider_html(geometry, out, snapshot_dir=tmp_path)
        rendered = out.read_text(encoding="utf-8")
        assert rendered.count("class='zone-floor-art'") == counts[0]
        assert rendered.count("class='visual-overlay'") == counts[1]

    apothecary = (tmp_path / "shop-0.html").read_text(encoding="utf-8")
    assert "data-target='back_room_vines'" in apothecary
    assert "Back Room — Restricted</title>" not in apothecary

    mercantile = (tmp_path / "shop-1.html").read_text(encoding="utf-8")
    for target in ("counter_center", "central_display_w", "central_display_e", "clock"):
        assert f"data-target='{target}'" in mercantile


def test_pawnshop_bakery_and_cobbler_have_editable_interior_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    expected = {
        Path("scenario/places/driftmoor/gilded_trinket/GEOMETRY.md"): (2, 11),
        Path("scenario/places/driftmoor/bakery/GEOMETRY.md"): (2, 7),
        Path("scenario/places/driftmoor/cobblers_shop/GEOMETRY.md"): (1, 8),
    }
    rendered = {}
    for index, (geometry, counts) in enumerate(expected.items()):
        out = tmp_path / f"craft-shop-{index}.html"
        render_turn_slider_html(geometry, out, snapshot_dir=tmp_path)
        html = out.read_text(encoding="utf-8")
        rendered[geometry] = html
        assert html.count("class='zone-floor-art'") == counts[0]
        assert html.count("class='visual-overlay'") == counts[1]

    pawnshop = rendered[Path("scenario/places/driftmoor/gilded_trinket/GEOMETRY.md")]
    assert "data-target='obsidian_ring'" in pawnshop
    assert "Tavian's Counter Line</title>" not in pawnshop
    assert "Display Case — Obelisk Ring Aura</title>" not in pawnshop

    bakery = rendered[Path("scenario/places/driftmoor/bakery/GEOMETRY.md")]
    assert "data-target='ovens'" in bakery
    assert "data-target='bread_display'" in bakery

    cobbler = rendered[Path("scenario/places/driftmoor/cobblers_shop/GEOMETRY.md")]
    assert "data-target='workbench'" in cobbler
    assert "data-target='boot_forms'" in cobbler


def test_elyssa_forge_and_stables_have_editable_interior_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    expected = {
        Path("scenario/places/driftmoor/elyssa_cottage/GEOMETRY.md"): (4, 12),
        Path("scenario/places/driftmoor/forge/GEOMETRY.md"): (1, 8),
        Path("scenario/places/driftmoor/stables/GEOMETRY.md"): (1, 8),
    }
    rendered = {}
    for index, (geometry, counts) in enumerate(expected.items()):
        out = tmp_path / f"research-smith-{index}.html"
        render_turn_slider_html(geometry, out, snapshot_dir=tmp_path)
        html = out.read_text(encoding="utf-8")
        rendered[geometry] = html
        assert html.count("class='zone-floor-art'") == counts[0]
        assert html.count("class='visual-overlay'") == counts[1]

    cottage = rendered[Path("scenario/places/driftmoor/elyssa_cottage/GEOMETRY.md")]
    assert "data-target='obelisk_shard_contained_specimen'" in cottage
    assert "Laboratory — Restricted Research</title>" not in cottage

    forge = rendered[Path("scenario/places/driftmoor/forge/GEOMETRY.md")]
    for target in ("forge_hearth", "anvil", "bellows", "quench_trough"):
        assert f"data-target='{target}'" in forge

    stables = rendered[Path("scenario/places/driftmoor/stables/GEOMETRY.md")]
    assert "data-target='empty_stall'" in stables
    assert "data-target='clawed_tracks'" in stables


def test_corral_has_sparse_editable_fixture_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    geometry = Path("scenario/places/driftmoor/corral/GEOMETRY.md")
    out = tmp_path / "corral.html"
    render_turn_slider_html(geometry, out, snapshot_dir=tmp_path)
    rendered = out.read_text(encoding="utf-8")

    assert rendered.count("class='zone-floor-art'") == 1
    assert rendered.count("class='visual-overlay'") == 2
    assert "data-target='water_trough'" in rendered
    assert "data-target='hay_bale'" in rendered


def test_subscene_filters_same_scale_characters_from_parent_snapshots(tmp_path):
    import json
    from engine.map_renderer import render_turn_slider_html

    (tmp_path / "day1_01.json").write_text(json.dumps({
        "turn": 1,
        "current_positions": {
            "gilthaness": {"x": 8, "y": 5, "zone": "MEETING_ROOM"},
            "tess": {"x": 9, "y": 5, "zone": "MEETING_ROOM"},
        },
    }), encoding="utf-8")
    out = tmp_path / "meeting.html"
    render_turn_slider_html(
        Path("scenario/places/driftmoor/broken_lantern/meeting_room/GEOMETRY.md"),
        out, snapshot_dir=tmp_path, start_characters=["gilthaness"],
    )
    rendered = out.read_text(encoding="utf-8")
    assert "data-char='gilthaness'" in rendered
    assert "data-char='tess'" not in rendered


def test_shift_scroll_scales_item_icons_with_character_icons():
    from engine.map_renderer import _PANZOOM_JS

    assert "querySelectorAll('.item-icon')" in _PANZOOM_JS
    assert "bf*iconScale" in _PANZOOM_JS


def test_character_map_icon_omits_embedded_name_banner_but_keeps_tooltip(tmp_path):
    import base64
    import re
    from engine.map_renderer import render_turn_slider_html

    out = tmp_path / "character-icon.html"
    render_turn_slider_html(
        Path("scenario/places/driftmoor/GEOMETRY.md"),
        out,
        snapshot_dir=tmp_path,
        start_characters=["gilthaness"],
        start_positions={"gilthaness": (406.0, 341.0)},
    )
    rendered = out.read_text(encoding="utf-8")
    match = re.search(
        r"class='char-icon-img'[^>]*href='data:image/svg\+xml;base64,([^']+)'",
        rendered,
    )
    assert match
    embedded = base64.b64decode(match.group(1)).decode("utf-8")
    assert "name-label" not in embedded
    assert ">Gilthaness</text>" not in embedded
    assert "<title>Gilthaness</title>" in rendered


def test_turn_slider_adds_runtime_dropped_item_without_geometry_row(tmp_path):
    from types import SimpleNamespace as NS
    from engine.map_renderer import render_turn_slider_html

    out = tmp_path / "dropped.html"
    detail = NS(
        label="Driftmoor Ale", description="", appearance_bands={},
        holder=None, pickable=True, position=NS(x=138.0, y=295.0),
        zone="ENTRY CHAMBER", carry=NS(location="in_world"),
    )
    render_turn_slider_html(
        GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
        start_characters=["thorgrim"],
        item_details={"driftmoor_ale_i1": detail},
    )
    rendered = out.read_text(encoding="utf-8")
    assert "Driftmoor Ale" in rendered
    assert "🍺" in rendered


def test_building_zone_tooltip_title_cases_type(tmp_path):
    from engine.map_renderer import _zone_tooltip

    place = tmp_path / "places" / "driftmoor" / "coopers_shed"
    place.mkdir(parents=True)
    (place / "PLACE.md").write_text(
        "# PLACE.md — The Cooper's Shed\n", encoding="utf-8"
    )

    assert _zone_tooltip(
        "COOPER", "places/driftmoor/coopers_shed", tmp_path
    ) == "Cooper: The Cooper's Shed"


def test_map_double_click_emits_integer_coordinates():
    from engine.map_renderer import _PANZOOM_JS

    assert "var x=Math.round(p.x);var y=Math.round(-p.y);" in _PANZOOM_JS
    assert "Math.round(p.x*10)/10" not in _PANZOOM_JS


def test_render_turn_slider_live_positions_override(tmp_path):
    """Live (mid-turn) positions stamp the latest frame so the map shows current
    positions; a dormant creature passed in live_positions stays fogged."""
    import re
    from engine.map_renderer import render_turn_slider_html
    out = tmp_path / "m.html"  # no snapshots -> turn 0 only
    render_turn_slider_html(
        GEOMETRY, out, snapshot_dir=tmp_path, title="EC",
        start_characters=["thorgrim"],
        start_positions={"thorgrim": (138.0, 295.0)},
        live_positions={"thorgrim": (137.0, 243.5, "FIRST PASSAGE"),
                        "giant_spider": (64.0, 195.0, "SECRET CHAMBER")})
    t = out.read_text(encoding="utf-8")
    assert "data-char='thorgrim'" in t
    assert "giant_spider" not in t  # not in start_characters -> stays fogged
    frames = json.loads(re.search(r"const FRAMES=(\{.*?\});const TURNS", t).group(1))
    assert frames[list(frames)[-1]]["thorgrim"] == [137.0, 243.5]


def test_subscene_ignores_snapshot_tracks_from_previous_scene(tmp_path):
    """Town coordinates must not stretch an upstairs map or draw a trail to it."""
    import re
    from engine.map_renderer import render_turn_slider_html

    geometry = Path(
        "scenario/places/driftmoor/weary_traveler/upstairs/GEOMETRY.md"
    )
    (tmp_path / "day1_01.json").write_text(json.dumps({
        "turn": 1,
        "current_positions": {
            "gilthaness": {"x": 450.0, "y": 370.0, "zone": "TOWN_COMMON"}
        },
    }), encoding="utf-8")
    (tmp_path / "day1_02.json").write_text(json.dumps({
        "turn": 2,
        "current_positions": {
            "gilthaness": {"x": 27.5, "y": 5.0, "zone": "STAIR_LANDING"}
        },
    }), encoding="utf-8")
    out = tmp_path / "upstairs.html"
    render_turn_slider_html(
        geometry, out, snapshot_dir=tmp_path, title="Upstairs",
        start_characters=["gilthaness"],
        start_positions={"gilthaness": (27.5, 5.0)},
    )
    rendered = out.read_text(encoding="utf-8")
    viewbox = re.search(r"viewBox='([^']+)'", rendered).group(1).split()
    assert float(viewbox[2]) < 60.0
    frames = json.loads(
        re.search(r"const FRAMES=(\{.*?\});const TURNS", rendered).group(1)
    )
    assert all(
        position[0] < 60.0
        for frame in frames.values()
        for position in frame.values()
    )


def test_town_fog_reveals_visible_building_but_hides_one_behind_it(tmp_path):
    import re
    from engine.map_renderer import render_turn_slider_html

    geometry = Path("scenario/places/driftmoor/GEOMETRY.md")
    out = tmp_path / "town.html"
    render_turn_slider_html(
        geometry,
        out,
        snapshot_dir=tmp_path,
        title="Driftmoor",
        start_characters=["gilthaness"],
        start_positions={"gilthaness": (414.0, 340.0)},
    )
    rendered = out.read_text(encoding="utf-8")
    barber = re.search(
        r"<g data-reveal='(\d+)'><polygon[^>]*><title>Barber:.*?</title>",
        rendered,
        re.DOTALL,
    )
    tailor = re.search(
        r"<g data-reveal='(\d+)'><polygon[^>]*><title>Tailor:.*?</title>",
        rendered,
        re.DOTALL,
    )
    assert barber and barber.group(1) == "0"
    assert tailor and tailor.group(1) != "0"


def test_render_turn_slider_default_seeds_only_tracked_chars(tmp_path):
    """With no start_characters, only characters recorded in the snapshots are
    seeded at turn 0 — a GEOMETRY-only entry (the spider) never leaks."""
    from engine.map_renderer import render_turn_slider_html
    (tmp_path / "day1_01.json").write_text(json.dumps({
        "turn": 1,
        "current_positions": {"thorgrim": {"x": 138.0, "y": 295.0,
                                           "zone": "ENTRY CHAMBER"}},
    }), encoding="utf-8")
    out = tmp_path / "slider.html"
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="EC")
    t = out.read_text(encoding="utf-8")
    assert "thorgrim" in t
    assert "giant_spider" not in t


def test_north_bank_places_have_authored_editable_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    expected = {
        Path("scenario/places/driftmoor/dustcloaks_curios/GEOMETRY.md"): (3, 14),
        Path("scenario/places/driftmoor/dustcloaks_curios/living_loft/GEOMETRY.md"): (1, 5),
        Path("scenario/places/driftmoor/graveyard/GEOMETRY.md"): (1, 7),
        Path("scenario/places/driftmoor/beacon_church/GEOMETRY.md"): (4, 13),
    }
    rendered = {}
    for index, (geometry, counts) in enumerate(expected.items()):
        out = tmp_path / f"north-bank-{index}.html"
        render_turn_slider_html(geometry, out, snapshot_dir=tmp_path)
        html = out.read_text(encoding="utf-8")
        rendered[geometry] = html
        assert html.count("class='zone-floor-art'") == counts[0]
        assert html.count("class='visual-overlay'") == counts[1]

    curios = rendered[Path("scenario/places/driftmoor/dustcloaks_curios/GEOMETRY.md")]
    for target in ("shop_counter", "display_table_w", "display_table_e", "locked_box"):
        assert f"data-target='{target}'" in curios
    assert "Backroom — Private Research</title>" not in curios

    church = rendered[Path("scenario/places/driftmoor/beacon_church/GEOMETRY.md")]
    for target in ("altar", "pew_sw", "pew_se", "pew_nw", "pew_ne", "herb_bed_w", "herb_bed_e"):
        assert f"data-target='{target}'" in church
    assert "Pelor's Sanctified Ground</title>" not in church
    assert "The Beacon Lantern Aura</title>" not in church


def test_remaining_driftmoor_places_have_authored_editable_art(tmp_path):
    from engine.map_renderer import render_turn_slider_html

    expected = {
        "carpenters_workshop": (2, 5), "coopers_shed": (2, 5),
        "fisherfolk": (2, 4), "fishmongers_shack": (1, 5),
        "general_store": (2, 5), "mayors_hall": (4, 6),
        "midwifes_home": (3, 5), "schoolhouse": (1, 5),
        "tailors_shop": (2, 5), "tannery": (2, 5),
        "watchtower": (2, 4), "weavers_cottage": (2, 5),
    }
    root = Path("scenario/places/driftmoor")
    for index, (place, counts) in enumerate(expected.items()):
        out = tmp_path / f"remaining-{index}.html"
        render_turn_slider_html(root / place / "GEOMETRY.md", out, snapshot_dir=tmp_path)
        html = out.read_text(encoding="utf-8")
        assert html.count("class='zone-floor-art'") == counts[0], place
        assert html.count("class='visual-overlay'") == counts[1], place

    mayor = (tmp_path / "remaining-5.html").read_text(encoding="utf-8")
    assert "Records Room — Restricted</title>" not in mayor
