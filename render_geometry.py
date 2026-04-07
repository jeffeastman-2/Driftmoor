#!/usr/bin/env python3
"""VPython renderer for GEOMETRY.md scene files.

Usage:
    python render_geometry.py                                          # Fey Glade (default)
    python render_geometry.py scenario/places/mistwood_hills/fey_glade/GEOMETRY.md
    python render_geometry.py path/to/GEOMETRY.md --no-labels          # hide text labels
    python render_geometry.py path/to/GEOMETRY.md --top                # top-down camera
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vpython import (
    canvas, box, sphere, cylinder, curve, label, cone,
    vector, color, rate, scene as vscene,
)

from models.geometry_loader import load_geometry_full
from models.space_time import Position, Polygon, SceneGeometry, MagicalBoundary


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

ZONE_COLORS = {
    "FOREST":   vector(0.12, 0.28, 0.10),  # dark forest green
    "GLADE":    vector(0.35, 0.60, 0.25),  # bright meadow
    "TRAIL":    vector(0.40, 0.28, 0.12),  # brown dirt path
    "POOL":     vector(0.15, 0.35, 0.55),  # water blue
}
DEFAULT_ZONE_COLOR = vector(0.3, 0.3, 0.3)

# Z-offset increment per zone layer (first zone=0, second=+dz, etc.)
ZONE_Z_STEP = 0.005

IMPASSABLE_COLOR = vector(0.15, 0.12, 0.10)    # dark brown
BOUNDARY_COLOR   = vector(0.6, 0.2, 0.8)        # purple glow
LANDMARK_COLOR   = vector(0.9, 0.8, 0.3)        # gold
CONNECTION_COLOR  = vector(0.3, 0.7, 0.9)       # light blue

CHARACTER_COLORS = {
    "aeliana":     vector(0.2, 0.5, 1.0),   # blue — player ranger
    "fennel":      vector(0.1, 0.75, 0.4),  # green — NPC herbalist
    "shadowbeast": vector(0.9, 0.15, 0.15), # red — monster
}
DEFAULT_CHAR_COLOR = vector(0.9, 0.9, 0.9)

ZONE_SLAB_HEIGHT = 0.05
IMPASSABLE_HEIGHT = 0.4
BOUNDARY_HEIGHT = 0.6
LANDMARK_RADIUS = 0.25
CHARACTER_RADIUS = 0.4


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def _polygon_center(poly: Polygon) -> tuple[float, float]:
    c = poly.centroid()
    return c.x, c.y


def _draw_zone_slab(name: str, poly: Polygon, z_base: float = 0.0):
    """Draw a zone as a flat coloured slab (approximated by a box for rectangles)."""
    verts = poly.vertices
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    clr = ZONE_COLORS.get(name, DEFAULT_ZONE_COLOR)
    box(
        pos=vector(cx, z_base + ZONE_SLAB_HEIGHT / 2, cy),
        size=vector(w, ZONE_SLAB_HEIGHT, h),
        color=clr,
        opacity=0.6,
    )


def _draw_zone_outline(poly: Polygon, z_base: float = 0.0):
    """Draw polygon outline as a curve."""
    pts = [vector(v[0], z_base + ZONE_SLAB_HEIGHT + 0.01, v[1])
           for v in poly.vertices]
    pts.append(pts[0])  # close the loop
    curve(pos=pts, color=vector(0.5, 0.5, 0.5), radius=0.03)


def _draw_impassable(poly: Polygon, z_base: float = 0.0):
    """Draw impassable area as a raised dark slab."""
    verts = poly.vertices
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    box(
        pos=vector(cx, z_base + IMPASSABLE_HEIGHT / 2, cy),
        size=vector(w, IMPASSABLE_HEIGHT, h),
        color=IMPASSABLE_COLOR,
        opacity=0.7,
    )


def _draw_boundary(boundary: MagicalBoundary, z_base: float = 0.0):
    """Draw magical boundary as a glowing translucent wall."""
    verts = boundary.perimeter.vertices
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    box(
        pos=vector(cx, z_base + BOUNDARY_HEIGHT / 2, cy),
        size=vector(w, BOUNDARY_HEIGHT, h),
        color=BOUNDARY_COLOR,
        opacity=0.25,
    )
    # Glowing outline on top
    pts = [vector(v[0], z_base + BOUNDARY_HEIGHT, v[1]) for v in verts]
    pts.append(pts[0])
    curve(pos=pts, color=BOUNDARY_COLOR, radius=0.04)


def _draw_boundary_outline(boundary: MagicalBoundary, z_base: float = 0.0):
    """Draw magical boundary as a glowing outline only (no filled slab)."""
    verts = boundary.perimeter.vertices
    pts = [vector(v[0], z_base + 0.02, v[1]) for v in verts]
    pts.append(pts[0])
    curve(pos=pts, color=BOUNDARY_COLOR, radius=0.15)


def _draw_landmark(name: str, pos: Position, z_base: float = 0.0,
                   show_label: bool = True):
    """Draw a landmark as a small gold sphere with label."""
    sphere(
        pos=vector(pos.x, z_base + LANDMARK_RADIUS, pos.y),
        radius=LANDMARK_RADIUS,
        color=LANDMARK_COLOR,
        opacity=0.8,
    )
    if show_label:
        label(
            pos=vector(pos.x, z_base + LANDMARK_RADIUS * 3, pos.y),
            text=name.replace("_", " "),
            color=LANDMARK_COLOR,
            height=10,
            box=False,
            opacity=0,
        )


def _draw_connection(name: str, pos: Position, z_base: float = 0.0,
                     show_label: bool = True):
    """Draw a connection point as a blue cone."""
    cone(
        pos=vector(pos.x, z_base, pos.y),
        axis=vector(0, 0.5, 0),
        radius=0.3,
        color=CONNECTION_COLOR,
        opacity=0.7,
    )
    if show_label:
        label(
            pos=vector(pos.x, z_base + 0.8, pos.y),
            text=name.replace("_", " "),
            color=CONNECTION_COLOR,
            height=9,
            box=False,
            opacity=0,
        )


def _draw_character(name: str, pos: Position, z_base: float = 0.0,
                    show_label: bool = True):
    """Draw a character as a coloured sphere with label."""
    clr = CHARACTER_COLORS.get(name, DEFAULT_CHAR_COLOR)
    sphere(
        pos=vector(pos.x, z_base + CHARACTER_RADIUS, pos.y),
        radius=CHARACTER_RADIUS,
        color=clr,
        emissive=True,
    )
    if show_label:
        label(
            pos=vector(pos.x, z_base + CHARACTER_RADIUS * 3.5, pos.y),
            text=name.upper(),
            color=clr,
            height=12,
            box=False,
            opacity=0,
            font="monospace",
        )


def _draw_zone_label(name: str, poly: Polygon, z_base: float = 0.0):
    """Draw zone name at center."""
    cx, cy = _polygon_center(poly)
    label(
        pos=vector(cx, z_base + 0.15, cy),
        text=name,
        color=vector(0.8, 0.8, 0.8),
        height=14,
        box=False,
        opacity=0,
        font="monospace",
    )


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_geometry(
    geometry_path: Path,
    show_labels: bool = True,
    top_down: bool = False,
):
    """Load and render a GEOMETRY.md file in VPython."""
    geo, boundaries, starting_positions = load_geometry_full(geometry_path)

    # --- Canvas setup ---
    cx, cy = geo.width / 2, geo.height / 2
    title = f"<b>{geo.name}</b> — {geo.width:.0f}m × {geo.height:.0f}m"

    scene = canvas(
        title=title,
        width=900,
        height=700,
        background=vector(0.08, 0.08, 0.12),
        center=vector(cx, 0, cy),
    )

    if top_down:
        cam_h = max(geo.width, geo.height) * 1.2
        # Look from below so +x = right = east, +z = up = north
        scene.camera.pos = vector(cx, -cam_h, cy)
        scene.camera.axis = vector(0, cam_h, 0)
        scene.up = vector(0, 0, 1)
    else:
        scene.camera.pos = vector(cx, 20, -10)
        scene.camera.axis = vector(0, -15, cy + 10)

    z_base = 0.0

    # --- Draw zones (each layer slightly higher to avoid z-fighting) ---
    for i, (name, poly) in enumerate(geo.zones.items()):
        z = z_base + i * ZONE_Z_STEP
        _draw_zone_slab(name, poly, z)
        _draw_zone_outline(poly, z)
        if show_labels:
            _draw_zone_label(name, poly, z)

    # --- Draw impassable areas ---
    z_imp = z_base + len(geo.zones) * ZONE_Z_STEP
    for poly in geo.impassable:
        _draw_impassable(poly, z_imp)

    # --- Draw boundaries (outline only — no filled slab) ---
    z_bnd = z_imp + ZONE_Z_STEP
    for boundary in boundaries:
        _draw_boundary_outline(boundary, z_bnd)
        if show_labels:
            bx, by = _polygon_center(boundary.perimeter)
            label(
                pos=vector(bx, z_bnd + 0.5, by),
                text=boundary.name,
                color=BOUNDARY_COLOR,
                height=9,
                box=False,
                opacity=0,
            )

    # --- Draw landmarks ---
    z_lm = z_bnd + ZONE_Z_STEP
    for name, pos in geo.landmarks.items():
        _draw_landmark(name, pos, z_lm, show_labels)

    # --- Draw connections ---
    for name, pos in geo.connections.items():
        _draw_connection(name, pos, z_lm, show_labels)

    # --- Draw starting positions ---
    for name, pos in starting_positions.items():
        _draw_character(name, pos, z_lm, show_labels)

    # --- Scale bar ---
    bar_y = -1.5
    curve(
        pos=[vector(0, 0.01, bar_y), vector(5, 0.01, bar_y)],
        color=vector(0.6, 0.6, 0.6),
        radius=0.03,
    )
    if show_labels:
        label(
            pos=vector(2.5, 0.3, bar_y),
            text="5 m",
            color=vector(0.6, 0.6, 0.6),
            height=10,
            box=False,
            opacity=0,
        )

    print(f"Rendering: {geo.name}")
    print(f"  Zones: {', '.join(geo.zones.keys())}")
    print(f"  Landmarks: {len(geo.landmarks)}")
    print(f"  Boundaries: {len(boundaries)}")
    print(f"  Characters: {', '.join(starting_positions.keys())}")
    print(f"\nVPython viewer running — rotate with right-click drag, zoom with scroll")

    # Keep alive
    while True:
        rate(30)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Render a GEOMETRY.md scene file in 3D with VPython",
    )
    parser.add_argument(
        "geometry_file",
        nargs="?",
        default="scenario/places/mistwood_hills/fey_glade/GEOMETRY.md",
        help="Path to GEOMETRY.md (default: Fey Glade)",
    )
    parser.add_argument(
        "--no-labels", action="store_true",
        help="Hide text labels",
    )
    parser.add_argument(
        "--top", action="store_true",
        help="Top-down camera view",
    )
    args = parser.parse_args()

    path = Path(args.geometry_file)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    render_geometry(path, show_labels=not args.no_labels, top_down=args.top)


if __name__ == "__main__":
    main()
