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


def test_shift_scroll_scales_item_icons_with_character_icons():
    from engine.map_renderer import _PANZOOM_JS

    assert "querySelectorAll('.item-icon')" in _PANZOOM_JS
    assert "bf*iconScale" in _PANZOOM_JS


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
