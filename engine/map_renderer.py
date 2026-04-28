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

    # Zones — render in ascending render_z so background zones draw first
    # and chambers/POIs overlay them.
    zone_order = sorted(
        g["zones"].keys(),
        key=lambda n: (g["zone_z"].get(n, 0.0), n),
    )
    # Build a z-rank → palette mapping based on the unique render_z values
    # in this map. Same z always gets the same color across all zones.
    unique_z = sorted({g["zone_z"].get(n, 0.0) for n in zone_order})
    z_rank = {z: i for i, z in enumerate(unique_z)}

    # Compute the union bbox of all zones, used to detect "background"
    # zones (those that fill ~the whole scene). Their labels are noisy
    # since they overlap everything else.
    all_pts = [p for n in zone_order for p in g["zones"].get(n, ())]
    if all_pts:
        ux0 = min(p[0] for p in all_pts); ux1 = max(p[0] for p in all_pts)
        uy0 = min(p[1] for p in all_pts); uy1 = max(p[1] for p in all_pts)
        union_area = max((ux1 - ux0) * (uy1 - uy0), 1.0)
    else:
        union_area = 1.0

    pending_zone_labels: list[tuple[float, float, str]] = []
    for zname in zone_order:
        v = g["zones"].get(zname)
        if not v:
            continue
        zval = g["zone_z"].get(zname, 0.0)
        color, alpha = _Z_PALETTE[z_rank[zval] % len(_Z_PALETTE)]
        ax.add_patch(patches.Polygon(
            v, closed=True, facecolor=color, alpha=alpha,
            edgecolor="black", linewidth=0.8,
        ))
        # Skip label for background zones (bbox covers >=80% of all zones).
        x0 = min(p[0] for p in v); x1 = max(p[0] for p in v)
        y0 = min(p[1] for p in v); y1 = max(p[1] for p in v)
        bbox_area = (x1 - x0) * (y1 - y0)
        if bbox_area / union_area < 0.80:
            cx = sum(p[0] for p in v) / len(v)
            cy = sum(p[1] for p in v) / len(v)
            pending_zone_labels.append((cx, cy, zname))

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
                v, closed=True, facecolor="#4a4a4a", alpha=0.75,
                edgecolor="#2a2a2a", linewidth=1.0,
            ))
            cx = sum(p[0] for p in v) / len(v)
            cy = sum(p[1] for p in v) / len(v)
            ax.text(cx, cy, name, ha="center", va="center",
                    fontsize=8, fontstyle="italic",
                    color="white", alpha=0.9)

    # Zone labels — drawn last so they're never covered by overlays.
    for cx, cy, zname in pending_zone_labels:
        ax.text(cx, cy, zname, ha="center", va="center",
                fontsize=10, fontweight="bold", color="black", alpha=0.75)

    # Landmarks
    for name, (x, y) in g["landmarks"].items():
        ax.plot(x, y, marker="^" if "oak" in name else "*",
                markersize=10, color="#3b3b3b")
        ax.annotate(name, (x, y), textcoords="offset points",
                    xytext=(6, 4), fontsize=8, color="#333")

    # Items — small diamonds, distinct from landmark stars.
    for iid, (x, y, label) in g["items"].items():
        ax.plot(x, y, marker="D", markersize=6,
                markerfacecolor="#d4a017", markeredgecolor="#5a4a10",
                markeredgewidth=0.8, zorder=6)
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=(6, -8), fontsize=7, color="#5a4a10",
                    fontstyle="italic")

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
    for _name, v in g["impassable"]:
        all_pts.extend(v)
    for _name, v in g["boundaries"]:
        all_pts.extend(v)
    all_pts.extend(g["landmarks"].values())
    all_pts.extend((x, y) for (x, y, _label) in g["items"].values())
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


def update_place_map(place_path: str | Path) -> Path:
    """Regenerate the static scenario map for a place.

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
    Path to the written PNG (``<place>/<scene>_map.png``).

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
    output_path = p / f"{scene_name}_map.png"
    render_map(
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

