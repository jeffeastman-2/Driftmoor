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
    render_turn_slider_html(GEOMETRY, out, snapshot_dir=tmp_path, title="Echoing Caverns")
    t = out.read_text(encoding="utf-8")
    # Slider UI present.
    assert "id='sl'" in t and "const FRAMES=" in t and "id='play'" in t
    # Turn-0 seeding from GEOMETRY: the starting zone (Entry Chamber) is revealed
    # from the start; First Passage is explored at turn 2.
    assert "data-reveal='0'" in t and "data-reveal='2'" in t
    # Fog of war: never-entered zones carry the sentinel (maxturn+1 = 3) -> hidden.
    assert "data-reveal='3'" in t
    # The slider opens on the party's starting layout (turn 0).
    assert "const TURNS=[0, 1, 2]" in t
    # The character appears in the per-turn frames.
    assert "thorgrim" in t
