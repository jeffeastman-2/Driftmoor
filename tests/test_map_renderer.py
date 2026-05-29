from __future__ import annotations

import json
from pathlib import Path

from engine.map_renderer import load_tracks_from_snapshots, render_interactive_map_html


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
    assert "Hover character dots" in html_text
