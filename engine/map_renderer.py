"""Render a scene map showing zones, landmarks, boundaries, and (optionally)
character paths from runtime snapshots.

This is the Python-owned visualization companion to the runtime checkpoints.
Two flavors:

* **Static (scenario) map** — only the starting positions parsed from the
  scenario's GEOMETRY.md.  Lives next to the scenario data and is regenerated
  whenever the scene runs.
* **Runtime (path) map** — every snapshot's ``current_positions`` plotted as a
  per-character path with start/end markers.  Lives in the runtime checkpoint
  directory next to ``*_story.txt`` etc.

Positions come straight from ``runtime/state/<scene>/day*.json`` snapshots —
no intermediate CSV.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Geometry parsing
# ---------------------------------------------------------------------------

def _verts(s: str) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for m in re.finditer(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", s):
        out.append((float(m.group(1)), float(m.group(2))))
    return out


def _verts3(s: str) -> list[tuple[float, float, float]]:
    """Parse vertex tuples capturing z when present (defaults to 0.0)."""
    out: list[tuple[float, float, float]] = []
    pat = re.compile(
        r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
        r"(?:\s*,\s*(-?\d+(?:\.\d+)?))?\s*\)"
    )
    for m in pat.finditer(s):
        x, y = float(m.group(1)), float(m.group(2))
        z = float(m.group(3)) if m.group(3) is not None else 0.0
        out.append((x, y, z))
    return out


def parse_geometry(text: str) -> dict:
    """Return {zones, landmarks, impassable, boundaries, starting_positions}."""
    g: dict = {
        "zones": {}, "zone_z": {}, "landmarks": {}, "impassable": [],
        "boundaries": [], "starting_positions": {}, "items": {},
    }

    def _table(section: str) -> list[list[str]]:
        m = re.search(rf"##\s+{re.escape(section)}\b", text)
        if not m:
            return []
        rows: list[list[str]] = []
        for line in text[m.end():].splitlines():
            stripped = line.strip()
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.split("|") if c.strip()]
                if cells and not all(set(c) <= set("-: ") for c in cells):
                    rows.append(cells)
            elif stripped.startswith("##"):
                break
        return rows

    for cells in _table("Zones"):
        if cells[0] == "name":
            continue
        # Vertices are always in the last column. Per-vertex z (in
        # "(x,y,z)" notation) is the source of truth for stacking; the
        # legacy "render_z" middle column is honored if no per-vertex z
        # is provided.
        verts3 = _verts3(cells[-1])
        if not verts3:
            continue
        name = cells[0]
        g["zones"][name] = [(x, y) for (x, y, _z) in verts3]
        per_vertex_zs = [z for (_x, _y, z) in verts3]
        if any(z != 0.0 for z in per_vertex_zs):
            g["zone_z"][name] = sum(per_vertex_zs) / len(per_vertex_zs)
        elif len(cells) >= 3:
            # Legacy schema: name | render_z | vertices
            try:
                g["zone_z"][name] = float(cells[1])
            except ValueError:
                g["zone_z"][name] = 0.0
        else:
            g["zone_z"][name] = 0.0

    for cells in _table("Landmarks"):
        if cells[0] == "name":
            continue
        if len(cells) >= 3:
            try:
                g["landmarks"][cells[0]] = (float(cells[1]), float(cells[2]))
            except ValueError:
                pass

    for cells in _table("Impassable"):
        if cells[0] == "description":
            continue
        if len(cells) >= 2:
            v = _verts(cells[1])
            if v:
                g["impassable"].append((cells[0], v))

    for cells in _table("Items"):
        if cells[0].lower() == "id":
            continue
        if len(cells) >= 3:
            try:
                x, y = float(cells[1]), float(cells[2])
            except ValueError:
                continue
            # Optional 4th col is label; otherwise humanize the id.
            label = cells[3] if len(cells) >= 4 else cells[0].replace("_", " ")
            g["items"][cells[0]] = (x, y, label)

    for cells in _table("Starting Positions"):
        if cells[0].lower() == "character":
            continue
        if len(cells) >= 3:
            try:
                g["starting_positions"][cells[0]] = (float(cells[1]), float(cells[2]))
            except ValueError:
                pass

    bm = re.search(r"##\s+Boundaries\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    if bm:
        for sub in re.finditer(r"###\s+(.+?)\n(.*?)(?=\n###|\Z)",
                               bm.group(1), re.DOTALL):
            vm = re.search(r"\*\*vertices:\*\*\s*([^\n]+)", sub.group(2))
            if vm:
                g["boundaries"].append((sub.group(1).strip(), _verts(vm.group(1))))

    return g


# ---------------------------------------------------------------------------
# Snapshot loading
# ---------------------------------------------------------------------------

TrackPoint = tuple[int, float, float, str]


def load_tracks_from_snapshots(snapshot_dir: Path) -> dict[str, list[TrackPoint]]:
    """Walk ``snapshot_dir/day*.json`` in turn order and collect each
    character's turn-indexed trail as ``(turn, x, y, zone)``.
    """
    tracks: dict[str, list[TrackPoint]] = {}
    files = sorted(snapshot_dir.glob("day*.json"))
    snapshots: list[tuple[int, dict]] = []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        snapshots.append((int(data.get("turn", 0)), data.get("current_positions") or {}))

    snapshots.sort(key=lambda x: x[0])
    for turn, cp in snapshots:
        for cid, pos in cp.items():
            if not isinstance(pos, dict):
                continue
            x, y = pos.get("x"), pos.get("y")
            if x is None or y is None:
                continue
            zone = str(pos.get("zone") or "")
            tracks.setdefault(cid, []).append((turn, float(x), float(y), zone))
    return tracks


def load_paths_from_snapshots(snapshot_dir: Path) -> dict[str, list[tuple[float, float]]]:
    """Walk ``snapshot_dir/day*.json`` in turn order and collect each
    character's (x, y) trail from ``current_positions``.
    """
    tracks = load_tracks_from_snapshots(snapshot_dir)
    return {
        cid: [(x, y) for (_turn, x, y, _zone) in tps]
        for cid, tps in tracks.items()
    }


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

# Palette indexed by render_z rank within a map (lowest-z = background,
# higher-z = brighter overlay). Colors are light, perceptually distinct,
# and avoid dark blue. Wraps if a map has more z-tiers than entries.
_Z_PALETTE = [
    ("#3a5f3a", 0.18),  # rank 0: muted forest/cave background
    ("#c2a878", 0.40),  # rank 1: warm sand/path
    ("#7fbf7f", 0.30),  # rank 2: soft green
    ("#d8b48a", 0.40),  # rank 3: light tan
    ("#b89a78", 0.40),  # rank 4: dusty earth
    ("#a89878", 0.35),  # rank 5: bone
    ("#c8b4d8", 0.35),  # rank 6: lavender
    ("#a8c8f0", 0.40),  # rank 7: sky blue
    ("#e8d8a8", 0.35),  # rank 8: pale gold
]

# Stable palette for character paths; falls back by hashing the id.
_PALETTE = [
    "#1f77b4", "#2ca02c", "#8e44ad", "#d62728",
    "#ff7f0e", "#17becf", "#bcbd22", "#7f7f7f",
]


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def render_map(
    geometry_path: Path,
    output_path: Path,
    *,
    snapshot_dir: Path | None = None,
    title: str | None = None,
    char_colors: dict[str, str] | None = None,
) -> None:
    """Render a static map image.

    Parameters
    ----------
    geometry_path: scenario GEOMETRY.md
    output_path: where to write the image
    snapshot_dir: if given, plot each character's full path from its
        ``day*.json`` snapshots.  If None, only the GEOMETRY's
        ``Starting Positions`` are plotted.
    title: figure title
    char_colors: optional override mapping character_id -> color
    """
    text = geometry_path.read_text(encoding="utf-8")
    g = parse_geometry(text)

    if snapshot_dir is not None and snapshot_dir.exists():
        paths = load_paths_from_snapshots(snapshot_dir)
        plot_paths = True
        # Prepend GEOMETRY starts so turn-0 -> turn-1 movement is visible.
        for cid, pts in list(paths.items()):
            if not pts:
                continue
            base_id = re.sub(r"_\d+$", "", cid)
            start = (g["starting_positions"].get(cid)
                     or g["starting_positions"].get(base_id))
            if start is not None and (start[0], start[1]) != pts[0]:
                paths[cid] = [start] + pts
    else:
        paths = {cid: [xy] for cid, xy in g["starting_positions"].items()}
        plot_paths = False

    fig, ax = plt.subplots(figsize=(11, 11))

    zone_order = sorted(
        g["zones"].keys(),
        key=lambda n: (g["zone_z"].get(n, 0.0), n),
    )
    unique_z = sorted({g["zone_z"].get(n, 0.0) for n in zone_order})
    z_rank = {z: i for i, z in enumerate(unique_z)}

    zone_pts = [p for n in zone_order for p in g["zones"].get(n, ())]
    if zone_pts:
        ux0 = min(p[0] for p in zone_pts)
        ux1 = max(p[0] for p in zone_pts)
        uy0 = min(p[1] for p in zone_pts)
        uy1 = max(p[1] for p in zone_pts)
        union_area = max((ux1 - ux0) * (uy1 - uy0), 1.0)
    else:
        union_area = 1.0

    bg_impassable: list[tuple[str, list[tuple[float, float]]]] = []
    fg_impassable: list[tuple[str, list[tuple[float, float]]]] = []
    for name, verts in g["impassable"]:
        if not verts:
            continue
        x0 = min(p[0] for p in verts)
        x1 = max(p[0] for p in verts)
        y0 = min(p[1] for p in verts)
        y1 = max(p[1] for p in verts)
        if (x1 - x0) * (y1 - y0) / union_area >= 0.80:
            bg_impassable.append((name, verts))
        else:
            fg_impassable.append((name, verts))

    for _name, verts in bg_impassable:
        ax.add_patch(patches.Polygon(
            verts,
            closed=True,
            facecolor="#b8b8b8",
            alpha=0.85,
            edgecolor="#7a7a7a",
            linewidth=1.0,
        ))

    pending_zone_labels: list[tuple[float, float, str]] = []
    for zname in zone_order:
        verts = g["zones"].get(zname)
        if not verts:
            continue
        zval = g["zone_z"].get(zname, 0.0)
        color, alpha = _Z_PALETTE[z_rank[zval] % len(_Z_PALETTE)]
        ax.add_patch(patches.Polygon(
            verts,
            closed=True,
            facecolor=color,
            alpha=alpha,
            edgecolor="black",
            linewidth=0.8,
        ))
        x0 = min(p[0] for p in verts)
        x1 = max(p[0] for p in verts)
        y0 = min(p[1] for p in verts)
        y1 = max(p[1] for p in verts)
        if ((x1 - x0) * (y1 - y0)) / union_area < 0.80:
            cx = sum(p[0] for p in verts) / len(verts)
            cy = sum(p[1] for p in verts) / len(verts)
            pending_zone_labels.append((cx, cy, zname))

    for name, verts in g["boundaries"]:
        if verts:
            ax.add_patch(patches.Polygon(
                verts,
                closed=True,
                fill=False,
                edgecolor="gold",
                linewidth=2.0,
                linestyle="--",
                label=name,
            ))

    fit_pts: list[tuple[float, float]] = []
    for verts in g["zones"].values():
        fit_pts.extend(verts)
    for _name, verts in g["impassable"]:
        fit_pts.extend(verts)
    for _name, verts in g["boundaries"]:
        fit_pts.extend(verts)
    fit_pts.extend(g["landmarks"].values())
    fit_pts.extend((x, y) for (x, y, _label) in g["items"].values())
    for pts in paths.values():
        fit_pts.extend(pts)

    if fit_pts:
        xs = [p[0] for p in fit_pts]
        ys = [p[1] for p in fit_pts]
        margin = 8
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)
        span = max((max(xs) - min(xs)), (max(ys) - min(ys)), 1.0)
    else:
        span = 100.0
    label_scale = max(0.60, min(1.0, span / 180.0))

    for name, verts in fg_impassable:
        ax.add_patch(patches.Polygon(
            verts,
            closed=True,
            facecolor="#4a4a4a",
            alpha=0.75,
            edgecolor="#2a2a2a",
            linewidth=1.0,
        ))
        cx = sum(p[0] for p in verts) / len(verts)
        cy = sum(p[1] for p in verts) / len(verts)
        ax.text(cx, cy, name, ha="center", va="center",
                fontsize=8 * label_scale, fontstyle="italic",
                color="white", alpha=0.9)

    for cx, cy, zname in pending_zone_labels:
        ax.text(cx, cy, zname, ha="center", va="center",
                fontsize=10 * label_scale, fontweight="bold",
                color="black", alpha=0.75)

    for name, (x, y) in g["landmarks"].items():
        ax.plot(x, y, marker="^" if "oak" in name else "*", markersize=10, color="#3b3b3b")
        ax.annotate(name, (x, y), textcoords="offset points",
                    xytext=(6, 4), fontsize=8 * label_scale, color="#333")

    char_colors = char_colors or {}
    palette_pos = 0
    used_colors: dict[str, str] = {}
    for cid in sorted(paths):
        if cid in char_colors:
            used_colors[cid] = char_colors[cid]
        else:
            used_colors[cid] = _PALETTE[palette_pos % len(_PALETTE)]
            palette_pos += 1

    for cid, pts in paths.items():
        if not pts:
            continue
        color = used_colors[cid]
        if plot_paths and len(pts) > 1:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, "-", color=color, linewidth=1.6, alpha=0.85, zorder=5)
            ax.plot(xs, ys, "o", color=color, markersize=3.5, alpha=0.9, zorder=6)
            ax.plot(xs[0], ys[0], marker="s", markersize=9,
                    markerfacecolor="white", markeredgecolor=color,
                    markeredgewidth=2, zorder=7)
            ax.plot(xs[-1], ys[-1], marker="X", markersize=11,
                    markerfacecolor=color, markeredgecolor="black",
                    markeredgewidth=1.0, zorder=7,
                    label=f"{cid} (n={len(pts)})")
        else:
            x, y = pts[0]
            ax.plot(x, y, marker="o", markersize=11,
                    markerfacecolor=color, markeredgecolor="black",
                    markeredgewidth=1.2, zorder=7, label=cid)

    # Draw items last so they remain visible over paths/markers.
    for _iid, (x, y, label) in g["items"].items():
        ax.plot(x, y, marker="D", markersize=7,
                markerfacecolor="#f0bf2f", markeredgecolor="#5a4a10",
                markeredgewidth=1.0, zorder=8)
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=(5, -8), fontsize=7 * label_scale, color="#5a4a10",
                    fontstyle="italic")

    ax.set_aspect("equal")
    ax.set_xlabel("x (ft)")
    ax.set_ylabel("y (ft)")
    ax.set_title(title or geometry_path.parent.name.replace("_", " ").title())
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


def render_interactive_map_html(
    geometry_path: Path,
    output_path: Path,
    *,
    snapshot_dir: Path | None = None,
    title: str | None = None,
    char_colors: dict[str, str] | None = None,
) -> None:
    """Render an interactive HTML map with hover tooltips for turn points.

    Each character point includes a tooltip with character id, turn number,
    coordinates, and zone, so path progression can be inspected with mouse-over.
    """
    text = geometry_path.read_text(encoding="utf-8")
    g = parse_geometry(text)
    tracks = load_tracks_from_snapshots(snapshot_dir) if snapshot_dir is not None and snapshot_dir.exists() else {}

    if not tracks:
        # Static map: show starting positions as turn 0 markers so the HTML map
        # is still useful even when no snapshot directory is available.
        tracks = {
            cid: [(0, float(x), float(y), "START")]
            for cid, (x, y) in g["starting_positions"].items()
        }

    # Prepend turn 0 from GEOMETRY starting positions so motion begins at start.
    for cid, pts in list(tracks.items()):
        if not pts:
            continue
        base_id = re.sub(r"_\d+$", "", cid)
        start = (g["starting_positions"].get(cid)
                 or g["starting_positions"].get(base_id))
        if start is not None and (start[0], start[1]) != (pts[0][1], pts[0][2]):
            tracks[cid] = [(0, float(start[0]), float(start[1]), "START")] + pts

    all_pts: list[tuple[float, float]] = []
    for v in g["zones"].values():
        all_pts.extend(v)
    for _name, v in g["impassable"]:
        all_pts.extend(v)
    for _name, v in g["boundaries"]:
        all_pts.extend(v)
    all_pts.extend(g["landmarks"].values())
    all_pts.extend((x, y) for (x, y, _label) in g["items"].values())
    for pts in tracks.values():
        all_pts.extend((x, y) for (_t, x, y, _z) in pts)
    if not all_pts:
        all_pts = [(0.0, 0.0), (100.0, 100.0)]

    min_x = min(p[0] for p in all_pts)
    max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts)
    max_y = max(p[1] for p in all_pts)
    margin = 8.0

    view_x = min_x - margin
    view_y = min_y - margin
    view_w = max((max_x - min_x) + 2 * margin, 1.0)
    view_h = max((max_y - min_y) + 2 * margin, 1.0)

    # SVG font sizes are in viewBox units; tune by map extent so compact
    # indoor maps don't get oversized labels.
    label_base = max(0.85, min(1.9, max(view_w, view_h) / 90.0))
    zone_label_size = round(label_base * 1.10, 2)
    landmark_label_size = round(label_base * 0.85, 2)
    item_label_size = round(label_base * 0.78, 2)

    def _fmt_poly(points: list[tuple[float, float]]) -> str:
        return " ".join(f"{x:.2f},{-y:.2f}" for x, y in points)

    def _flip_y(y: float) -> float:
        """Flip Y coordinate for SVG rendering (invert the axis)."""
        return -y

    # Stable character colors
    char_colors = char_colors or {}
    used_colors: dict[str, str] = {}
    palette_pos = 0
    for cid in sorted(tracks):
        if cid in char_colors:
            used_colors[cid] = char_colors[cid]
        else:
            used_colors[cid] = _PALETTE[palette_pos % len(_PALETTE)]
            palette_pos += 1

    # Zone fill colors by z-rank
    zone_order = sorted(
        g["zones"].keys(),
        key=lambda n: (g["zone_z"].get(n, 0.0), n),
    )
    unique_z = sorted({g["zone_z"].get(n, 0.0) for n in zone_order})
    z_rank = {z: i for i, z in enumerate(unique_z)}

    parts: list[str] = []
    parts.append(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Driftmoor Interactive Map</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
        "margin:0;background:#f7f7f5;color:#111;}"
        ".wrap{padding:12px 14px;}"
        "h1{font-size:16px;margin:0 0 8px 0;}"
        "p{margin:0 0 10px 0;font-size:13px;color:#333;}"
        "svg{width:min(1100px,98vw);height:auto;border:1px solid #c7c7c2;background:#fff;}"
        f".zone-label{{font-size:{zone_label_size}px;font-weight:700;fill:#1f1f1f;opacity:.8;}}"
        f".lm-label{{font-size:{landmark_label_size}px;fill:#333;}}"
        f".item-label{{font-size:{item_label_size}px;fill:#5a4a10;font-style:italic;}}"
        "</style></head><body><div class='wrap'>"
    )
    safe_title = html.escape(title or geometry_path.parent.name.replace("_", " ").title())
    parts.append(f"<h1>{safe_title}</h1>")
    parts.append("<p>Hover over dots to see turn number, coordinates, and zone.</p>")
    parts.append(
        f"<svg viewBox='{view_x:.2f} {_flip_y(view_y + view_h):.2f} {view_w:.2f} {view_h:.2f}' "
        "preserveAspectRatio='xMidYMid meet'>"
    )
    parts.append("<style>")
    parts.append(".tooltip{position:relative;display:inline-block;}")
    parts.append(".tooltip .tooltiptext{visibility:hidden;width:120px;background-color:#222;color:#fff;text-align:center;border-radius:4px;padding:5px;position:absolute;z-index:1;bottom:125%;left:50%;margin-left:-60px;opacity:0;transition:opacity 0.3s;font-size:11px;line-height:1.3;white-space:pre-line;}")
    parts.append(".tooltip:hover .tooltiptext{visibility:visible;opacity:1;}")
    parts.append("</style>")

    # Zones
    for zname in zone_order:
        verts = g["zones"].get(zname)
        if not verts:
            continue
        zval = g["zone_z"].get(zname, 0.0)
        color, alpha = _Z_PALETTE[z_rank[zval] % len(_Z_PALETTE)]
        points = _fmt_poly(verts)
        parts.append(
            f"<polygon points='{points}' fill='{color}' fill-opacity='{alpha:.3f}' "
            "stroke='#222' stroke-width='0.6'/>"
        )
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        parts.append(
            f"<text x='{cx:.2f}' y='{_flip_y(cy):.2f}' text-anchor='middle' "
            f"dominant-baseline='middle' class='zone-label'>{html.escape(zname)}</text>"
        )

    # Boundaries
    for bname, verts in g["boundaries"]:
        if not verts:
            continue
        points = _fmt_poly(verts)
        parts.append(
            f"<polygon points='{points}' fill='none' stroke='gold' stroke-width='1.1' "
            "stroke-dasharray='2.5,2.5'>"
            f"<title>{html.escape(bname)}</title></polygon>"
        )

    # Impassable
    for iname, verts in g["impassable"]:
        if not verts:
            continue
        points = _fmt_poly(verts)
        parts.append(
            f"<polygon points='{points}' fill='#4a4a4a' fill-opacity='0.65' "
            "stroke='#2a2a2a' stroke-width='0.6'>"
            f"<title>{html.escape(iname)}</title></polygon>"
        )

    # Landmarks
    for name, (x, y) in g["landmarks"].items():
        parts.append(
            f"<circle cx='{x:.2f}' cy='{_flip_y(y):.2f}' r='1.2' fill='#3b3b3b'>"
            f"<title>{html.escape(name)}</title></circle>"
        )
        parts.append(
            f"<text x='{x + 1.7:.2f}' y='{_flip_y(y) - 1.3:.2f}' class='lm-label'>{html.escape(name)}</text>"
        )

    # Character paths and turn points
    for cid, pts in tracks.items():
        if not pts:
            continue
        color = used_colors[cid]
        poly_points = " ".join(f"{x:.2f},{_flip_y(y):.2f}" for (_t, x, y, _z) in pts)
        if len(pts) > 1:
            parts.append(
                f"<polyline points='{poly_points}' fill='none' stroke='{color}' "
                "stroke-width='0.9' stroke-opacity='0.9'/>"
            )

        for turn, x, y, zone in pts:
            title_text = (
                f"{cid} - turn {turn}\n"
                f"x={x:.1f}, y={y:.1f}\n"
                f"zone={zone or '?'}"
            )
            parts.append(
                f"<circle cx='{x:.2f}' cy='{_flip_y(y):.2f}' r='1.4' fill='{color}' "
                f"stroke='#111' stroke-width='0.35' data-tooltip='{html.escape(title_text)}'>"
                f"<title>{html.escape(title_text)}</title></circle>"
            )

        sx, sy = pts[0][1], pts[0][2]
        ex, ey = pts[-1][1], pts[-1][2]
        parts.append(
            f"<rect x='{sx - 1.8:.2f}' y='{_flip_y(sy) - 1.8:.2f}' width='3.6' height='3.6' "
            f"fill='white' stroke='{color}' stroke-width='0.7'>"
            f"<title>{html.escape(f'{cid} start')}</title></rect>"
        )
        parts.append(
            f"<path d='M {ex - 1.8:.2f} {_flip_y(ey) - 1.8:.2f} L {ex + 1.8:.2f} {_flip_y(ey) + 1.8:.2f} "
            f"M {ex + 1.8:.2f} {_flip_y(ey) - 1.8:.2f} L {ex - 1.8:.2f} {_flip_y(ey) + 1.8:.2f}' "
            "stroke='#111' stroke-width='0.7'>"
            f"<title>{html.escape(f'{cid} end')}</title></path>"
        )

    # Draw items after character overlays so item presence is always visible.
    for _iid, (x, y, label) in g["items"].items():
        parts.append(
            f"<rect x='{x - 1.1:.2f}' y='{_flip_y(y) - 1.1:.2f}' width='2.2' height='2.2' "
            "fill='#f0bf2f' stroke='#5a4a10' stroke-width='0.45' transform='rotate(45 "
            f"{x:.2f} {_flip_y(y):.2f})'>"
            f"<title>{html.escape(label)}</title></rect>"
        )
        parts.append(
            f"<text x='{x + 1.4:.2f}' y='{_flip_y(y) - 1.2:.2f}' class='item-label'>{html.escape(label)}</text>"
        )

    parts.append("</svg></div>")
    parts.append(
        "<script>"
        "document.addEventListener('DOMContentLoaded', function(){"
        "const circles = document.querySelectorAll('circle[data-tooltip]');"
        "circles.forEach(c => {"
        "c.style.cursor = 'pointer';"
        "c.addEventListener('mouseenter', function(e){"
        "const txt = e.target.getAttribute('data-tooltip');"
        "let tooltip = e.target.nextElementSibling;"
        "if(!tooltip || !tooltip.classList.contains('tooltiptext')) {"
        "tooltip = document.createElement('div');"
        "tooltip.className = 'tooltiptext';"
        "tooltip.style.pointerEvents = 'none';"
        "e.target.parentNode.insertBefore(tooltip, e.target.nextSibling);"
        "}"
        "tooltip.textContent = txt;"
        "tooltip.style.visibility = 'visible';"
        "tooltip.style.opacity = '1';"
        "});"
        "c.addEventListener('mouseleave', function(e){"
        "const tooltip = e.target.nextElementSibling;"
        "if(tooltip) {"
        "tooltip.style.visibility = 'hidden';"
        "tooltip.style.opacity = '0';"
        "}"
        "});"
        "});"
        "});"
        "</script>"
    )
    parts.append("</body></html>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(parts), encoding="utf-8")


def _point_in_poly(x: float, y: float, verts: list[tuple[float, float]]) -> bool:
    """Ray-casting point-in-polygon test in world coordinates."""
    n = len(verts)
    if n < 3:
        return False
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = verts[i]
        xj, yj = verts[j]
        denom = (yj - yi) or 1e-12
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / denom + xi):
            inside = not inside
        j = i
    return inside


def _containing_zone(x: float, y: float, zones: dict) -> str | None:
    for name, verts in zones.items():
        if _point_in_poly(x, y, verts):
            return name
    return None


def render_turn_slider_html(
    geometry_path: Path,
    output_path: Path,
    *,
    snapshot_dir: Path | None = None,
    title: str | None = None,
    char_colors: dict[str, str] | None = None,
    live_refresh_secs: int | None = None,
) -> None:
    """Interactive turn-slider map with fog of war.

    One self-contained HTML page (SVG + a little vanilla JS, no libraries): a
    slider scrubs through the session's turns. At each turn only the zones the
    party has explored — entered — up to that turn are drawn, with every
    character's marker at its position for that turn. Rebuilt entirely from the
    per-turn snapshot JSONs in ``snapshot_dir`` plus the scenario GEOMETRY.md.
    """
    g = parse_geometry(geometry_path.read_text(encoding="utf-8"))
    tracks = (load_tracks_from_snapshots(snapshot_dir)
              if snapshot_dir is not None and snapshot_dir.exists() else {})

    # Seed turn 0 from GEOMETRY starting positions so the slider always opens on
    # the party's initial layout — even before the first turn is taken (live web
    # play, when no snapshots exist yet). The starting zone is resolved by
    # point-in-polygon so it reveals at turn 0 like any explored zone.
    start_pos = g.get("starting_positions") or {}
    for cid, (sx, sy) in start_pos.items():
        z0 = _containing_zone(float(sx), float(sy), g["zones"]) or ""
        entry = (0, float(sx), float(sy), z0)
        pts = tracks.get(cid)
        if not pts:
            tracks[cid] = [entry]
        elif pts[0][0] != 0:
            tracks[cid] = [entry] + pts

    turn_list = sorted({t for pts in tracks.values() for (t, _x, _y, _z) in pts})
    if not turn_list:
        turn_list = [0]
    never = turn_list[-1] + 1  # data-reveal sentinel: never <= any slider turn

    # frames[turn] = {cid: (x, y)} — character positions per turn.
    frames: dict[int, dict[str, tuple[float, float]]] = {t: {} for t in turn_list}
    for cid, pts in tracks.items():
        for (t, x, y, _z) in pts:
            frames[t][cid] = (x, y)

    # A zone is "explored" the first turn a character is recorded in it. Use the
    # snapshot's zone (the engine's authoritative zone_at, with its edge
    # tolerance) rather than re-deriving with point-in-polygon, so boundary
    # cases agree with the game.
    zone_by_upper = {n.upper(): n for n in g["zones"]}
    reveal_zone: dict[str, int] = {}
    for pts in tracks.values():
        for (t, _x, _y, zstr) in pts:
            zname = zone_by_upper.get((zstr or "").upper())
            if zname is not None and t < reveal_zone.get(zname, never + 1):
                reveal_zone[zname] = t

    def _elem_reveal(x: float, y: float) -> int:
        z = _containing_zone(x, y, g["zones"])
        if z is None:
            return turn_list[0]               # not in any zone -> ungated
        return reveal_zone.get(z, never)      # zone never explored -> hidden

    # viewBox extents (same as the path map).
    all_pts: list[tuple[float, float]] = []
    for v in g["zones"].values():
        all_pts.extend(v)
    for _n, v in g["impassable"]:
        all_pts.extend(v)
    for _n, v in g["boundaries"]:
        all_pts.extend(v)
    all_pts.extend(g["landmarks"].values())
    all_pts.extend((x, y) for (x, y, _l) in g["items"].values())
    for pts in tracks.values():
        all_pts.extend((x, y) for (_t, x, y, _z) in pts)
    if not all_pts:
        all_pts = [(0.0, 0.0), (100.0, 100.0)]
    min_x = min(p[0] for p in all_pts); max_x = max(p[0] for p in all_pts)
    min_y = min(p[1] for p in all_pts); max_y = max(p[1] for p in all_pts)
    margin = 8.0
    view_x = min_x - margin
    view_w = max((max_x - min_x) + 2 * margin, 1.0)
    view_h = max((max_y - min_y) + 2 * margin, 1.0)
    view_top = -(max_y + margin)
    label_base = max(0.85, min(1.9, max(view_w, view_h) / 90.0))

    def fy(y: float) -> float:
        return -y

    def poly(points: list[tuple[float, float]]) -> str:
        return " ".join(f"{x:.2f},{-y:.2f}" for x, y in points)

    cc = dict(char_colors or {})
    pal = 0
    for cid in sorted(tracks):
        if cid not in cc:
            cc[cid] = _PALETTE[pal % len(_PALETTE)]
            pal += 1

    zone_order = sorted(g["zones"], key=lambda n: (g["zone_z"].get(n, 0.0), n))
    uniq_z = sorted({g["zone_z"].get(n, 0.0) for n in zone_order})
    z_rank = {z: i for i, z in enumerate(uniq_z)}

    p: list[str] = []
    safe_title = html.escape(
        title or geometry_path.parent.name.replace("_", " ").title())
    p.append("<!doctype html><html><head><meta charset='utf-8'>")
    p.append(f"<title>{safe_title} — turn map</title><style>")
    p.append("body{font-family:ui-sans-serif,system-ui,sans-serif;margin:0;"
             "background:#f7f7f5;color:#111;}.wrap{padding:12px 14px;}"
             "h1{font-size:16px;margin:0 0 6px;}"
             ".ctl{display:flex;align-items:center;gap:10px;margin:6px 0 10px;"
             "font-size:13px;}.ctl input[type=range]{flex:1;}"
             "svg{width:min(1100px,98vw);height:auto;border:1px solid #c7c7c2;"
             "background:#0e0e12;}button{font:inherit;padding:3px 10px;cursor:pointer;}")
    p.append(f".zlabel{{font-size:{label_base*1.10:.2f}px;font-weight:700;fill:#eee;opacity:.85;}}")
    p.append(f".llabel{{font-size:{label_base*0.85:.2f}px;fill:#cfcfcf;}}")
    p.append(f".ilabel{{font-size:{label_base*0.78:.2f}px;fill:#d9c98a;font-style:italic;}}")
    p.append(f".clabel{{font-size:{label_base*0.90:.2f}px;font-weight:700;fill:#fff;"
             "paint-order:stroke;stroke:#000;stroke-width:0.3px;}")
    p.append("</style></head><body><div class='wrap'>")
    p.append(f"<h1>{safe_title}</h1>")
    p.append("<div class='ctl'><button id='play'>&#9654; Play</button>"
             f"<input id='sl' type='range' min='0' max='{len(turn_list)-1}' "
             f"value='{len(turn_list)-1}' step='1'>"
             "<span id='rd' style='min-width:70px;'></span></div>")
    p.append(f"<svg viewBox='{view_x:.2f} {view_top:.2f} {view_w:.2f} {view_h:.2f}' "
             "preserveAspectRatio='xMidYMid meet'>")

    for zname in zone_order:
        verts = g["zones"].get(zname)
        if not verts:
            continue
        zval = g["zone_z"].get(zname, 0.0)
        color, alpha = _Z_PALETTE[z_rank[zval] % len(_Z_PALETTE)]
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        p.append(f"<g data-reveal='{reveal_zone.get(zname, never)}'>")
        p.append(f"<polygon points='{poly(verts)}' fill='{color}' "
                 f"fill-opacity='{alpha:.3f}' stroke='#888' stroke-width='0.6'/>")
        p.append(f"<text x='{cx:.2f}' y='{fy(cy):.2f}' text-anchor='middle' "
                 f"dominant-baseline='middle' class='zlabel'>{html.escape(zname)}</text></g>")

    for iname, verts in g["impassable"]:
        if not verts:
            continue
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        p.append(f"<g data-reveal='{_elem_reveal(cx, cy)}'><polygon points='{poly(verts)}' "
                 "fill='#3a3a42' fill-opacity='0.7' stroke='#22222a' stroke-width='0.6'>"
                 f"<title>{html.escape(iname)}</title></polygon></g>")
    for bname, verts in g["boundaries"]:
        if not verts:
            continue
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        p.append(f"<g data-reveal='{_elem_reveal(cx, cy)}'><polygon points='{poly(verts)}' "
                 "fill='none' stroke='gold' stroke-width='1.1' stroke-dasharray='2.5,2.5'>"
                 f"<title>{html.escape(bname)}</title></polygon></g>")

    for name, (x, y) in g["landmarks"].items():
        p.append(f"<g data-reveal='{_elem_reveal(x, y)}'>"
                 f"<circle cx='{x:.2f}' cy='{fy(y):.2f}' r='1.1' fill='#b9b9b9'>"
                 f"<title>{html.escape(name)}</title></circle>"
                 f"<text x='{x+1.5:.2f}' y='{fy(y):.2f}' class='llabel'>{html.escape(name)}</text></g>")
    for _iid, (x, y, label) in g["items"].items():
        p.append(f"<g data-reveal='{_elem_reveal(x, y)}'>"
                 f"<circle cx='{x:.2f}' cy='{fy(y):.2f}' r='0.9' fill='#d9c98a'/>"
                 f"<text x='{x+1.4:.2f}' y='{fy(y):.2f}' class='ilabel'>{html.escape(label)}</text></g>")

    for cid in sorted(tracks):
        p.append(f"<g class='char' data-char='{html.escape(cid)}' style='display:none'>"
                 f"<circle r='1.5' fill='{cc[cid]}' stroke='#000' stroke-width='0.35'/>"
                 f"<text x='2.0' y='-1.0' class='clabel'>{html.escape(cid)}</text></g>")
    p.append("</svg>")

    frames_js = json.dumps({
        t: {c: [round(x, 2), round(y, 2)] for c, (x, y) in frames[t].items()}
        for t in turn_list})
    p.append("<script>")
    p.append(f"const FRAMES={frames_js};const TURNS={json.dumps(turn_list)};")
    p.append(
        "const sl=document.getElementById('sl'),rd=document.getElementById('rd');"
        "function show(i){const t=TURNS[i];"
        "document.querySelectorAll('[data-reveal]').forEach(e=>{"
        "e.style.display=(+e.dataset.reveal<=t)?'':'none';});"
        "const f=FRAMES[t]||{};"
        "document.querySelectorAll('[data-char]').forEach(e=>{const c=f[e.dataset.char];"
        "if(c){e.setAttribute('transform','translate('+c[0]+','+(-c[1])+')');"
        "e.style.display='';}else{e.style.display='none';}});"
        "rd.textContent='Turn '+t;}"
        "sl.addEventListener('input',()=>show(+sl.value));"
        "let timer=null;const pb=document.getElementById('play');"
        "pb.addEventListener('click',()=>{if(timer){clearInterval(timer);timer=null;"
        "pb.innerHTML='&#9654; Play';return;}pb.innerHTML='&#10073;&#10073; Pause';"
        "timer=setInterval(()=>{let v=+sl.value;if(v>=TURNS.length-1){clearInterval(timer);"
        "timer=null;pb.innerHTML='&#9654; Play';return;}sl.value=v+1;show(v+1);},2000);});"
        "show(+sl.value);")
    if live_refresh_secs:
        # Live-follow: while parked on the latest turn, reload to pick up new
        # turns; if the viewer has scrubbed back into history, leave them be.
        p.append(
            f"setInterval(function(){{if(+sl.value>=TURNS.length-1)"
            f"{{location.reload();}}}},{int(live_refresh_secs) * 1000});")
    p.append("</script></body></html>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(p), encoding="utf-8")


def update_place_map(place_path: str | Path) -> Path:
    """Regenerate the static scenario map for a place as HTML.

    Parameters
    ----------
    place_path:
        Path to a place directory containing ``GEOMETRY.md``. May be
        absolute, workspace-relative (e.g.
        ``"scenario/places/obelisk_reach/echoing_caverns"``), or just the
        scene slug (e.g. ``"echoing_caverns"`` or ``"fey_glade"``) — in
        which case the function searches under ``scenario/places``.

    Returns
    -------
    Path to the written HTML file (``<place>/<scene>_map.html``).

    Raises
    ------
    FileNotFoundError if the place directory or its ``GEOMETRY.md`` cannot
    be located.
    """
    p = Path(place_path)

    if not p.exists():
        # Try resolving as a scene slug under scenario/places (any depth).
        slug = p.name or str(place_path)
        roots = [Path("scenario/places"), Path.cwd() / "scenario" / "places"]
        match: Path | None = None
        for root in roots:
            if not root.exists():
                continue
            for cand in root.rglob(slug):
                if cand.is_dir() and (cand / "GEOMETRY.md").is_file():
                    match = cand
                    break
            if match is not None:
                break
        if match is None:
            raise FileNotFoundError(
                f"Could not locate place directory for {place_path!r}"
            )
        p = match

    if not p.is_dir():
        raise FileNotFoundError(f"{p} is not a directory")

    geometry_path = p / "GEOMETRY.md"
    if not geometry_path.is_file():
        raise FileNotFoundError(f"No GEOMETRY.md in {p}")

    scene_name = p.name
    output_path = p / f"{scene_name}_map.html"
    render_interactive_map_html(
        geometry_path,
        output_path,
        snapshot_dir=None,
        title=f"{scene_name.replace('_', ' ').title()} — starting positions",
    )
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        sys.stderr.write(
            "usage: python -m engine.map_renderer <place_path_or_slug> ...\n"
            "  e.g. python -m engine.map_renderer echoing_caverns\n"
            "       python -m engine.map_renderer scenario/places/mistwood_hills/fey_glade\n"
        )
        sys.exit(2)

    for arg in sys.argv[1:]:
        try:
            out = update_place_map(arg)
            print(f"Wrote {out}")
        except FileNotFoundError as exc:
            sys.stderr.write(f"error: {exc}\n")
            sys.exit(1)

