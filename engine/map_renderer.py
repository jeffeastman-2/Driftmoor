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


def parse_geometry(text: str) -> dict:
    """Return {zones, landmarks, impassable, boundaries, starting_positions}."""
    g: dict = {
        "zones": {}, "landmarks": {}, "impassable": [],
        "boundaries": [], "starting_positions": {},
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
        if len(cells) >= 2:
            g["zones"][cells[0]] = _verts(cells[1])

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

def load_paths_from_snapshots(snapshot_dir: Path) -> dict[str, list[tuple[float, float]]]:
    """Walk ``snapshot_dir/day*.json`` in turn order and collect each
    character's (x, y) trail from ``current_positions``.
    """
    paths: dict[str, list[tuple[float, float]]] = {}
    files = sorted(snapshot_dir.glob("day*.json"))
    snapshots = []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        snapshots.append((data.get("turn", 0), data.get("current_positions") or {}))
    snapshots.sort(key=lambda x: x[0])
    for _, cp in snapshots:
        for cid, pos in cp.items():
            if not isinstance(pos, dict):
                continue
            x, y = pos.get("x"), pos.get("y")
            if x is None or y is None:
                continue
            paths.setdefault(cid, []).append((float(x), float(y)))
    return paths


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

ZONE_COLORS = {
    "POOL":   ("#5b8def", 0.45),
    "GLADE":  ("#7fbf7f", 0.30),
    "TRAIL":  ("#c2a878", 0.40),
    "FOREST": ("#3a5f3a", 0.18),
}

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
    """Render a map PNG.

    Parameters
    ----------
    geometry_path: scenario GEOMETRY.md
    output_path: where to write the PNG
    snapshot_dir: if given, plot each character's full path from its
        ``day*.json`` snapshots.  If None, only the GEOMETRY's
        ``Starting Positions`` are plotted.
    title: figure title
    char_colors: optional override mapping character_id → color
    """
    text = geometry_path.read_text(encoding="utf-8")
    g = parse_geometry(text)

    if snapshot_dir is not None and snapshot_dir.exists():
        paths = load_paths_from_snapshots(snapshot_dir)
        plot_paths = True
        # Prepend GEOMETRY starting positions so the path shows the
        # turn-0 → turn-1 motion. Snapshots only record post-turn state,
        # so without this the first turn's movement would be invisible.
        # Match by id, with shadowbeast → shadowbeast_1 stripping suffix.
        for cid, pts in list(paths.items()):
            if not pts:
                continue
            base_id = re.sub(r"_\d+$", "", cid)
            start = (g["starting_positions"].get(cid)
                     or g["starting_positions"].get(base_id))
            if start is not None and (start[0], start[1]) != pts[0]:
                paths[cid] = [start] + pts
    else:
        # Static map: render starting positions as single-point paths.
        paths = {cid: [xy] for cid, xy in g["starting_positions"].items()}
        plot_paths = False

    fig, ax = plt.subplots(figsize=(11, 11))

    # Zones — FOREST first so others overlay.
    for zname in ("FOREST", "GLADE", "POOL", "TRAIL"):
        v = g["zones"].get(zname)
        if not v:
            continue
        color, alpha = ZONE_COLORS.get(zname, ("#888", 0.2))
        ax.add_patch(patches.Polygon(
            v, closed=True, facecolor=color, alpha=alpha,
            edgecolor="black", linewidth=0.6,
        ))
        cx = sum(p[0] for p in v) / len(v)
        cy = sum(p[1] for p in v) / len(v)
        if zname != "FOREST":
            ax.text(cx, cy, zname, ha="center", va="center",
                    fontsize=11, fontweight="bold", color="black", alpha=0.7)

    # Boundaries
    for name, v in g["boundaries"]:
        if v:
            ax.add_patch(patches.Polygon(
                v, closed=True, fill=False,
                edgecolor="gold", linewidth=2.0, linestyle="--",
                label=name,
            ))

    # Impassable
    for name, v in g["impassable"]:
        if v:
            ax.add_patch(patches.Polygon(
                v, closed=True, facecolor="#1f3a8a", alpha=0.85,
                edgecolor="navy", linewidth=1.0,
            ))

    # Landmarks
    for name, (x, y) in g["landmarks"].items():
        ax.plot(x, y, marker="^" if "oak" in name else "*",
                markersize=10, color="#3b3b3b")
        ax.annotate(name, (x, y), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color="#333")

    # Characters — path or single dot
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

    # Auto-fit
    all_pts: list[tuple[float, float]] = []
    for v in g["zones"].values():
        all_pts.extend(v)
    for pts in paths.values():
        all_pts.extend(pts)
    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        margin = 8
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)

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
