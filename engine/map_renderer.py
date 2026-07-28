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

import base64
import html
import json
import re
from collections.abc import Iterable
from pathlib import Path

import matplotlib.patches as patches
import matplotlib.pyplot as plt


# Wheel-to-zoom (toward the cursor) + drag-to-pan for the SVG maps, by mutating
# the ``viewBox``. Requires the ``<svg id='map'>`` and an optional ``#fit`` reset
# button. Shared verbatim by the interactive and turn-slider renderers.
_PANZOOM_JS = (
    r"(function(){var s=document.getElementById('map');if(!s)return;"
    r"var b=s.getAttribute('viewBox').trim().split(/[ ,]+/).map(Number);"
    r"var v={x:b[0],y:b[1],w:b[2],h:b[3]};"
    r"var MK=s.getAttribute('data-map-key')||('vb:'+b.join(','));var K='mapView:'+MK;"
    r"var ZK=K+':zoomStep';var zoomStep=0.15;"
    # Persist the view so the live-refresh reload keeps the reader's zoom/pan.
    r"function sv(){try{sessionStorage.setItem(K,JSON.stringify({b:b,v:[v.x,v.y,v.w,v.h]}));}catch(_){}}"
    # Keep labels a constant ON-SCREEN size: font-size is in viewBox units, so
    # counter-scale it by the current zoom (view width / pixel width) so text
    # neither shrinks at fit nor blows up when zoomed in.
    r"function LS(){var r=s.getBoundingClientRect();if(!r.width)return;var k=v.w/r.width;"
    r"s.style.setProperty('--zfs',(9*k).toFixed(2)+'px');"
    r"s.style.setProperty('--lfs',(7.5*k).toFixed(2)+'px');"
    r"s.style.setProperty('--ifs',(7*k).toFixed(2)+'px');"
    r"s.style.setProperty('--cfs',(8.5*k).toFixed(2)+'px');}"
    r"function RF(){v.x=b[0];v.y=b[1];v.w=b[2];v.h=b[3];A();}"
    r"function SZ(n){zoomStep=Math.max(0.05,Math.min(0.40,Number(n)||0.15));"
    r"var zv=document.getElementById('zoomSpeedVal');if(zv)zv.textContent=Math.round(zoomStep*100)+'%';"
    r"var zs=document.getElementById('zoomSpeed');if(zs&&String(zs.value)!==String(Math.round(zoomStep*100)))"
    r"zs.value=String(Math.round(zoomStep*100));"
    r"try{sessionStorage.setItem(ZK,String(zoomStep));}catch(_){}}"
    r"function ZF(d){return d<0?(1-zoomStep):(1+zoomStep);}"
    r"function A(){s.setAttribute('viewBox',v.x+' '+v.y+' '+v.w+' '+v.h);sv();LS();}"
    # Mark interaction so the refresh loop can defer reloads while the user drags.
    r"function I(){window.__mapLastInteract=Date.now();}"
    # Restore a saved view across reload, only if it's the same map (same base box).
    r"try{var st=JSON.parse(sessionStorage.getItem(K)||'null');"
    r"if(st&&st.b&&st.v&&st.b.length===4&&st.b.every(function(n,i){return n===b[i];})){"
    r"v.x=st.v[0];v.y=st.v[1];v.w=st.v[2];v.h=st.v[3];"
    r"s.setAttribute('viewBox',v.x+' '+v.y+' '+v.w+' '+v.h);}}catch(_){}"
    r"function P(e){var r=s.getBoundingClientRect();"
    r"return{x:v.x+(e.clientX-r.left)/r.width*v.w,y:v.y+(e.clientY-r.top)/r.height*v.h};}"
    r"var ii=Array.prototype.slice.call(document.querySelectorAll('.char-icon-img'));"
    r"var id=Array.prototype.slice.call(document.querySelectorAll('.char-icon-dot'));"
    r"var IK=K+':iconScale';var iconScale=1.0;"
    r"function SI(n){iconScale=Math.max(0.2,Math.min(8,Number(n)||1));"
    r"for(var i=0;i<ii.length;i++){var bz=Number(ii[i].getAttribute('data-base-z'))||6;"
    r"var z=bz*iconScale;ii[i].setAttribute('x',(-z/2).toFixed(2));ii[i].setAttribute('y',(-z/2).toFixed(2));"
    r"ii[i].setAttribute('width',z.toFixed(2));ii[i].setAttribute('height',z.toFixed(2));}"
    r"for(var j=0;j<id.length;j++){var br=Number(id[j].getAttribute('data-base-r'))||0.75;"
    r"var bw=Number(id[j].getAttribute('data-base-sw'))||0.35;"
    r"id[j].setAttribute('r',(br*iconScale).toFixed(2));id[j].setAttribute('stroke-width',(bw*iconScale).toFixed(2));}"
    r"var iv=document.getElementById('iconScaleVal');if(iv)iv.textContent=iconScale.toFixed(2)+'x';"
    r"try{sessionStorage.setItem(IK,String(iconScale));}catch(_){}}"
    r"function SIS(d){SI(iconScale*(d>0?1.18:0.85));}"
    r"try{var isv=parseFloat(sessionStorage.getItem(IK)||'1');"
    r"if(isFinite(isv))SI(isv);else SI(1);}catch(_){SI(1);}"
    r"try{var zsv=parseFloat(sessionStorage.getItem(ZK)||'0.15');"
    r"if(isFinite(zsv))SZ(zsv);else SZ(0.15);}catch(_){SZ(0.15);}"
    r"function WD(e){var dx=Number(e.deltaX)||0,dy=Number(e.deltaY)||0;"
    r"return Math.abs(dy)>=Math.abs(dx)?dy:dx;}"
    r"s.addEventListener('wheel',function(e){e.preventDefault();I();if(e.shiftKey){"
    r"if(!(ii.length||id.length))return;var wd=WD(e);if(!wd)return;"
    r"SIS(wd<0?1:-1);"
    r"return;}var p=P(e);var wd=WD(e);if(!wd)return;var f=ZF(wd);"
    r"var nw=Math.max(b[2]/20,v.w*f);f=nw/v.w;"
    r"v.x=p.x-(p.x-v.x)*f;v.y=p.y-(p.y-v.y)*f;v.w*=f;v.h*=f;A();},{passive:false});"
    r"var d=false,l=null;"
    r"s.addEventListener('mousedown',function(e){d=true;I();l={x:e.clientX,y:e.clientY};"
    r"s.style.cursor='grabbing';e.preventDefault();});"
    r"s.addEventListener('dblclick',function(e){e.preventDefault();I();var p=P(e);"
    r"var x=Math.round(p.x);var y=Math.round(-p.y);"
    r"try{if(window.parent&&window.parent!==window)"
    r"window.parent.postMessage({type:'driftmoor-map-dblclick',x:x,y:y,shift:!!e.shiftKey},'*');}catch(_){}"
    r"});"
    r"window.addEventListener('mousemove',function(e){if(!d)return;I();"
    r"var r=s.getBoundingClientRect();v.x-=(e.clientX-l.x)/r.width*v.w;"
    r"v.y-=(e.clientY-l.y)/r.height*v.h;l={x:e.clientX,y:e.clientY};A();});"
    r"window.addEventListener('mouseup',function(){d=false;s.style.cursor='grab';});"
    r"s.style.cursor='grab';"
    r"window.addEventListener('keydown',function(e){"
    r"if(!(ii.length||id.length))return;var t=e.target&&e.target.tagName?e.target.tagName.toLowerCase():'';"
    r"if(t==='input'||t==='textarea')return;"
    r"if(e.key==='+'||e.key==='='||e.key===']'){I();SIS(1);e.preventDefault();}"
    r"else if(e.key==='-'||e.key==='_'||e.key==='['){I();SIS(-1);e.preventDefault();}"
    r"else if(e.key==='0'){I();SI(1);RF();e.preventDefault();}"
    r"else if(e.key==='f'||e.key==='F'){I();RF();e.preventDefault();}});"
    r"var fb=document.getElementById('fit');if(fb)fb.addEventListener('click',function(){I();RF();});"
    r"var zs=document.getElementById('zoomSpeed');if(zs)zs.addEventListener('input',function(){SZ((+zs.value)/100);});"
    r"LS();window.addEventListener('resize',LS);})();"
)


# ---------------------------------------------------------------------------
# Geometry parsing
# ---------------------------------------------------------------------------

_BAND_ORDER = ("near", "intermediate", "far", "distant")

# Cache of icon data-URIs keyed by file path with freshness metadata.
# Value: (mtime_ns, size_bytes, data_uri)
_ICON_CACHE: dict = {}
_PLACE_TITLE_CACHE: dict = {}


def _icon_data_uri(path: "Path") -> "str | None":
    """Return an ``<image href>`` data-URI for a building ``icon.svg``/png, or
    None if absent. Cached so per-turn map regeneration doesn't re-encode."""
    key = str(path)
    if not path.exists():
        _ICON_CACHE.pop(key, None)
        return None

    stat = path.stat()
    mtime_ns = int(stat.st_mtime_ns)
    size = int(stat.st_size)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        c_mtime_ns, c_size, c_uri = cached
        if c_mtime_ns == mtime_ns and c_size == size:
            return c_uri

    uri = None
    try:
        mime = "image/svg+xml" if path.suffix == ".svg" else f"image/{path.suffix.lstrip('.')}"
        uri = f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:  # noqa: BLE001 — art is best-effort
        uri = None
    _ICON_CACHE[key] = (mtime_ns, size, uri)
    return uri


def _zone_icon_uri(scenario_root: "Path | None", place_dir: "Path | None",
                   zname: str, dest: str | None) -> "str | None":
    """Resolve a zone's icon data-URI: first the connected sub-place's icon
    (``<scenario>/<dest>/icon.*``), else the name convention
    ``<place_dir>/<zone-lowercased>/icon.*``. The convention lets non-enterable
    feature zones (graveyard, well, garden, …) carry art without a PLACE.md or a
    ## Connections entry. None if neither has one."""
    dirs = []
    if scenario_root is not None and dest:
        dirs.append(scenario_root / dest)
    if place_dir is not None:
        dirs.append(place_dir / zname.lower())
    for d in dirs:
        for ext in (".svg", ".png", ".webp"):
            uri = _icon_data_uri(d / f"icon{ext}")
            if uri:
                return uri
    return None


def _char_icon_uri(scenario_root: "Path | None", cid: str) -> "str | None":
    """Data-URI for a character token ``<char dir>/icon.svg`` if present. Looks
    in the conventional people/creature dirs, by id then base id (drops _N)."""
    if scenario_root is None:
        return None
    base = re.sub(r"_\d+$", "", cid)
    for who in (cid, base):
        for area in ("people/players", "people/npcs", "creatures"):
            for ext in (".svg", ".png", ".webp"):
                uri = _icon_data_uri(scenario_root / area / who / f"icon{ext}")
                if uri:
                    return uri
    return None


def _zone_icon_dirs(g: dict, place_rel: str | None = None) -> dict:
    """Map each zone name -> the place dir a connection inside it leads to,
    so a zone can find its ``icon.svg``. Reuses ``## Connections``.

    ``place_rel`` is the current place's path relative to ``scenario/`` (e.g.
    ``places/driftmoor``); when given, only connections leading to a *sub-place*
    of it count — so a "leave to region" or exit connection that happens to sit
    inside a building footprint (e.g. ``to_region`` -> ``places/``) can't hijack
    that building's icon."""
    prefix = (place_rel.rstrip("/") + "/") if place_rel else "places/"
    out: dict = {}
    for (_name, cx, cy, dest) in g.get("connections", []):
        if not dest or not dest.startswith(prefix):
            continue
        z = _containing_zone(cx, cy, g["zones"])
        if z is not None and z not in out:
            out[z] = dest
    return out


def _zone_tooltip(zname: str, dest: str | None, scenario_root: Path | None) -> str:
    """Tooltip for a zone. A building zone (one wired to a place that has a
    PLACE.md) reads ``<zone>: <place title>``; every other zone \u2014 terrain,
    water, commons, un-enterable feature zones \u2014 just shows its humanized name.
    (Nothing is labeled "Building:" unless it actually is one.)"""
    if zname.startswith("EXIT_"):
        return "To " + zname[len("EXIT_"):].replace("_", " ").title()
    label = zname.replace("_", " ").title()
    if dest and scenario_root is not None:
        key = str(scenario_root / dest)
        if key in _PLACE_TITLE_CACHE:
            title = _PLACE_TITLE_CACHE[key]
        else:
            title = ""
            try:
                place_md = scenario_root / dest / "PLACE.md"
                if place_md.exists():
                    txt = place_md.read_text(encoding="utf-8")
                    m = re.search(r"^#\s*PLACE\.md\s*[\-\u2014]\s*(.+)$", txt, re.MULTILINE)
                    if m:
                        title = m.group(1).strip()
            except Exception:  # noqa: BLE001 - tooltip enrichment is best-effort
                title = ""
            _PLACE_TITLE_CACHE[key] = title
        if title:
            return f"{label}: {title}"
    return label


_WATER_FILL = "#7c9db0"  # matches the water in the dock/bridge icons
_WATER_WORDS = frozenset({
    "SEA", "RIVER", "OCEAN", "LAKE", "HARBOR", "HARBOUR", "BAY", "POND",
    "CREEK", "STREAM", "LAGOON", "MARSH", "WATER", "SHALLOWS",
})


def _is_water_zone(zname: str) -> bool:
    """True for zones that read as open water (river, sea, harbor, …) so the
    map fills them the same blue the dock/bridge icons use, rather than a
    z-rank palette colour."""
    toks = zname.upper().replace("-", "_").split("_")
    return any(t in _WATER_WORDS or "WATER" in t for t in toks)


def _item_tooltip(label: str, detail: object | None) -> str:
    """Hover text for a map item: its label, full description, and the
    by-distance ("size-relative") appearances an observer sees near vs far.
    ``detail`` is duck-typed (``.description``, ``.appearance_bands``)."""
    lines = [label]
    desc = (getattr(detail, "description", "") or "").strip() if detail else ""
    if desc:
        lines.append(desc)
    bands = getattr(detail, "appearance_bands", None) if detail else None
    if isinstance(bands, dict) and bands:
        shown = [k for k in _BAND_ORDER if (bands.get(k) or "").strip()]
        shown += [k for k in bands if k not in _BAND_ORDER and (bands.get(k) or "").strip()]
        if shown:
            lines.append("Appears by distance:")
            for k in shown:
                lines.append(f"  • {k}: {bands[k].strip()}")
    return "\n".join(lines)


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
        "connections": [],
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
            # Schema is `id | x | y | z | label` with an optional z; _table drops
            # the empty z cell, so the label is always the LAST column. A trailing
            # numeric cell means z is present but the label was omitted -> fall
            # back to the humanized id (otherwise z, e.g. "6", became the label).
            label = cells[0].replace("_", " ")
            if len(cells) >= 4:
                last = cells[-1]
                try:
                    float(last)
                except ValueError:
                    label = last
            g["items"][cells[0]] = (x, y, label)

    # Connections: `name | x | y | destination`. Used to resolve a building
    # zone's art directory (the place a connection inside the zone leads to).
    for cells in _table("Connections"):
        if cells[0].lower() == "name":
            continue
        if len(cells) >= 4:
            try:
                g["connections"].append(
                    (cells[0], float(cells[1]), float(cells[2]), cells[3]))
            except ValueError:
                continue

    # Character placement is a scene concern: callers pass scene-resolved
    # ``start_positions`` into the renderers (which override ``starting_positions``
    # above). GEOMETRY is a pure stage and carries no positions to parse here.

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
    start_positions: dict | None = None,
) -> None:
    """Render a static map image.

    Parameters
    ----------
    geometry_path: scenario GEOMETRY.md
    output_path: where to write the image
    snapshot_dir: if given, plot each character's full path from its
        ``day*.json`` snapshots.  If None, only the scene-provided
        ``start_positions`` are plotted.
    title: figure title
    char_colors: optional override mapping character_id -> color
    start_positions: scene-resolved {char_id: (x, y)} to seed turn-0 markers
        (GEOMETRY is a pure stage and carries no placement)
    """
    text = geometry_path.read_text(encoding="utf-8")
    g = parse_geometry(text)
    if start_positions is not None:                      # scene placement wins
        g["starting_positions"] = {
            cid: (float(p[0]), float(p[1])) for cid, p in start_positions.items()
        }

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
    _scenario_root = next((pp for pp in geometry_path.parents if pp.name == "scenario"), None)
    _place_rel = (geometry_path.parent.relative_to(_scenario_root).as_posix()
                  if _scenario_root else None)
    _zone_dest = _zone_icon_dirs(g, _place_rel)

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
        if _is_water_zone(zname):
            color, alpha = _WATER_FILL, 0.85
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
    start_positions: dict | None = None,
) -> None:
    """Render an interactive HTML map with hover tooltips for turn points.

    Each character point includes a tooltip with character id, turn number,
    coordinates, and zone, so path progression can be inspected with mouse-over.
    """
    text = geometry_path.read_text(encoding="utf-8")
    g = parse_geometry(text)
    if start_positions is not None:                      # scene placement wins
        g["starting_positions"] = {
            cid: (float(p[0]), float(p[1])) for cid, p in start_positions.items()
        }
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

    # SVG font sizes are in viewBox units; scale with map extent so a big map fit
    # to a fixed pixel width keeps legible labels (and a compact indoor map keeps
    # small ones).
    label_base = max(0.85, min(28.0, max(view_w, view_h) / 100.0))
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
    _scenario_root = next((pp for pp in geometry_path.parents if pp.name == "scenario"), None)
    _place_rel = (geometry_path.parent.relative_to(_scenario_root).as_posix()
                  if _scenario_root else None)
    _zone_dest = _zone_icon_dirs(g, _place_rel)

    parts: list[str] = []
    parts.append(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Driftmoor Interactive Map</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
        "margin:0;background:#f7f7f5;color:#111;}"
        ".wrap{padding:12px 14px;}"
        "h1{font-size:14px;margin:0 0 8px 0;}"
        "p{margin:0 0 10px 0;font-size:13px;color:#333;}"
        "svg{width:min(1100px,98vw);height:auto;border:1px solid #c7c7c2;background:#fff;}"
        f".zone-label{{font-size:var(--zfs,{zone_label_size}px);font-weight:700;fill:#1f1f1f;opacity:.8;}}"
        f".lm-label{{font-size:var(--lfs,{landmark_label_size}px);fill:#333;}}"
        f".item-label{{font-size:var(--ifs,{item_label_size}px);fill:#5a4a10;font-style:italic;}}"
        "</style></head><body><div class='wrap'>"
    )
    safe_title = html.escape(title or geometry_path.parent.name.replace("_", " ").title())
    parts.append(f"<h1>{safe_title}</h1>")
    parts.append("<p>Hover over dots to see turn number, coordinates, and zone.</p>")
    parts.append(
        f"<svg id='map' viewBox='{view_x:.2f} {_flip_y(view_y + view_h):.2f} {view_w:.2f} {view_h:.2f}' "
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
        if _is_water_zone(zname):
            color, alpha = _WATER_FILL, 0.85
        points = _fmt_poly(verts)
        zone_tip = _zone_tooltip(zname, _zone_dest.get(zname), _scenario_root)
        parts.append(
            f"<polygon points='{points}' fill='{color}' fill-opacity='{alpha:.3f}' "
            "stroke='#222' stroke-width='0.6'>"
            f"<title>{html.escape(zone_tip)}</title></polygon>"
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
        tip = _landmark_tooltip(name, x, y, g["zones"])
        parts.append(
            f"<circle cx='{x:.2f}' cy='{_flip_y(y):.2f}' r='1.2' fill='#3b3b3b'>"
            f"<title>{html.escape(tip)}</title></circle>"
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
        + _PANZOOM_JS +
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


def _landmark_tooltip(name: str, x: float, y: float, zones: dict) -> str:
    """Build landmark hover text with the containing building name."""
    zone = _containing_zone(x, y, zones)
    if zone:
        return f"{name}\nBuilding: {zone}"
    return name


def render_turn_slider_html(
    geometry_path: Path,
    output_path: Path,
    *,
    snapshot_dir: Path | None = None,
    title: str | None = None,
    char_colors: dict[str, str] | None = None,
    live_refresh_secs: int | None = None,
    start_characters: "Iterable[str] | None" = None,
    item_details: dict | None = None,
    live_positions: dict | None = None,
    start_positions: dict | None = None,
    scene_geometry: "SceneGeometry | None" = None,
) -> None:
    """Interactive turn-slider map with fog of war.

    One self-contained HTML page (SVG + a little vanilla JS, no libraries): a
    slider scrubs through the session's turns. At each turn only the zones the
    party has explored — entered — up to that turn are drawn, with every
    character's marker at its position for that turn. The stage (zones,
    landmarks, items) comes from the scenario GEOMETRY.md; character placement
    comes from ``start_positions`` (scene-resolved) plus the per-turn snapshot
    JSONs in ``snapshot_dir``.

    ``start_characters`` is the set of characters present on the board at scene
    start (the party — those active from turn 1). Only these are seeded at turn 0
    from ``start_positions``, so a *dormant* creature (a monster that activates on
    zone entry) does NOT leak its position or un-fog its lair before the party
    finds it. When omitted, only characters already recorded in the snapshots are
    seeded (so a scene-placed dormant entry never leaks by default).
    """
    g = parse_geometry(geometry_path.read_text(encoding="utf-8"))
    # Character placement is a scene concern: the caller supplies the
    # scene-resolved starting positions (GEOMETRY is a pure stage and carries no
    # placement). Without them, only snapshot-recorded characters are plotted.
    if start_positions is not None:
        g["starting_positions"] = {
            cid: (float(p[0]), float(p[1])) for cid, p in start_positions.items()
        }
    tracks = (load_tracks_from_snapshots(snapshot_dir)
              if snapshot_dir is not None and snapshot_dir.exists() else {})

    # Seed turn 0 from GEOMETRY starting positions so the slider always opens on
    # the party's initial layout — even before the first turn is taken (live web
    # play, when no snapshots exist yet). The starting zone is resolved by
    # point-in-polygon so it reveals at turn 0 like any explored zone. Restrict
    # the seed to the party (``start_characters``) so dormant/hidden creatures
    # stay fogged until discovered.
    start_pos = g.get("starting_positions") or {}
    if start_characters is not None:
        seed_ids = [c for c in start_characters if c in start_pos]
    else:
        seed_ids = [c for c in start_pos if c in tracks]
    for cid in seed_ids:
        sx, sy = start_pos[cid]
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

    # Visibility-based reveal: a zone also reveals the first turn a party observer
    # can SEE it — not only when someone stands in it. Mirrors the engine's
    # perception rule (``SceneGeometry.can_see`` gated by ``ambient_sight_range``):
    # an open, lit scene (ambient = None → unlimited) reveals the districts you can
    # see across the square from turn 0, while a dark cavern (short ambient) still
    # only reveals the chamber you're in plus whatever line-of-sight reaches. The
    # entry-based reveal above stays a floor (you always "see" your own zone).
    # Gated by ``start_characters`` so a dormant creature never reveals its lair.
    sg = scene_geometry
    if sg is None:
        try:
            from models.geometry_loader import load_geometry
            sg = load_geometry(geometry_path)
        except Exception:                          # best-effort: fall back to entry fog
            sg = None
    _reveal_seen_from = None
    if sg is not None and sg.zones:
        import math as _math
        from models.space_time import Position as _Pos
        # g-name → (sg-name, centroid Position); reveal_zone is keyed by g-name.
        _centroids = {zone_by_upper.get(n.upper(), n): p.centroid()
                      for n, p in sg.zones.items()}

        def _reveal_seen_from(ox: float, oy: float, ozone: str, t: int) -> None:
            visual = sg.ambient_sight_range(ozone or (sg.zone_at(_Pos(ox, oy)) or ""))
            visual_ft = _math.inf if visual is None else visual
            obs = _Pos(ox, oy)
            for gname, c in _centroids.items():
                if reveal_zone.get(gname, never + 1) <= t:
                    continue                       # already revealed at/before t
                if _math.hypot(c.x - ox, c.y - oy) <= visual_ft and sg.can_see(obs, c):
                    reveal_zone[gname] = t

        _vis_allowed = set(start_characters) if start_characters is not None else None
        _vis_samples = sorted(
            ((t, x, y, z) for cid, pts in tracks.items()
             if _vis_allowed is None or cid in _vis_allowed
             for (t, x, y, z) in pts),
            key=lambda s: s[0],
        )
        for (t, x, y, z) in _vis_samples:
            _reveal_seen_from(x, y, z, t)

    # Live (mid-turn) override: stamp the latest frame with the positions the turn
    # loop published while waiting on the human, so the map shows where everyone
    # is NOW — including NPCs who already acted this turn — rather than lagging to
    # the last end-of-turn checkpoint. Reveals each live zone at the latest turn.
    if live_positions:
        lt = turn_list[-1]
        allowed = set(start_characters) if start_characters is not None else None
        for cid, pos in live_positions.items():
            if allowed is not None and cid not in allowed:
                continue                      # keep dormant creatures fogged
            if not pos or len(pos) < 2:
                continue
            x, y = float(pos[0]), float(pos[1])
            frames[lt][cid] = (x, y)
            zstr = pos[2] if len(pos) > 2 else ""
            zname = zone_by_upper.get((zstr or "").upper()) or _containing_zone(x, y, g["zones"])
            if zname is not None:
                reveal_zone[zname] = min(reveal_zone.get(zname, never), lt)
            if _reveal_seen_from is not None:      # reveal what this observer sees now
                _reveal_seen_from(x, y, zstr, lt)

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
    # Text is kept a constant on-screen size by the pan/zoom JS (it counter-
    # scales font-size against the zoom), so labels never shrink at fit nor blow
    # up when zoomed. Markers/strokes keep their natural viewBox sizes (sc=1).
    label_base = 1.9
    sc = 1.0

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
             "h1{font-size:14px;margin:0 0 6px;}"
             ".ctl{display:flex;align-items:center;gap:10px;margin:6px 0 10px;"
             "font-size:13px;}.ctl #sl{flex:1;}"
             ".zctl{display:inline-flex;align-items:center;gap:6px;}"
             ".zctl input{width:88px;}"
             ".hint{color:#555;font-size:12px;white-space:nowrap;}"
             "svg{width:min(1100px,98vw);height:auto;border:1px solid #c7c7c2;"
             "background:#0e0e12;}button{font:inherit;padding:3px 10px;cursor:pointer;}")
    # font-size is a JS-controlled var (constant on-screen size across zoom); the
    # fallback keeps a sane value before the pan/zoom script runs.
    p.append(".zlabel{font-size:var(--zfs,2.1px);font-weight:700;fill:#eee;opacity:.85;}")
    p.append(".llabel{font-size:var(--lfs,1.7px);fill:#cfcfcf;}")
    p.append(".ilabel{font-size:var(--ifs,1.6px);fill:#d9c98a;font-style:italic;}")
    p.append(".clabel{font-size:var(--cfs,1.9px);font-weight:700;fill:#fff;"
             "paint-order:stroke;stroke:#000;stroke-width:0.3px;}")
    p.append("</style></head><body><div class='wrap'>")
    p.append(f"<h1>{safe_title}</h1>")
    p.append("<div class='ctl'><button id='play'>&#9654; Play</button>"
             "<button id='fit' title='Reset map view (key: F)'>Fit</button>"
             "<span class='zctl'><span class='hint'>Zoom</span>"
             "<input id='zoomSpeed' type='range' min='5' max='40' value='15' step='1'>"
             "<span class='hint' id='zoomSpeedVal'>15%</span></span>"
             f"<input id='sl' type='range' min='0' max='{len(turn_list)-1}' "
             f"value='{len(turn_list)-1}' step='1'>"
             "<span id='rd' style='min-width:70px;'></span>"
             "<span class='hint'>wheel=zoom, drag=pan, F=fit</span>"
             "</div>")
    p.append(f"<svg id='map' viewBox='{view_x:.2f} {view_top:.2f} {view_w:.2f} {view_h:.2f}' "
             "preserveAspectRatio='xMidYMid meet'>")

    # Building art: a zone whose connection leads to a place dir with an
    # icon.svg is drawn as that illustration (clipped to its footprint) instead
    # of a flat rectangle; others keep the palette fill.
    _scenario_root = next((pp for pp in geometry_path.parents if pp.name == "scenario"), None)
    _place_rel = (geometry_path.parent.relative_to(_scenario_root).as_posix()
                  if _scenario_root else None)
    _zone_dest = _zone_icon_dirs(g, _place_rel)

    # Exclusion (impassable) overlays are drawn *under* the zone layer so that
    # illustrated zones (e.g. a bridge spanning the river) paint on top of the
    # water wash instead of being muddied by it. Open water between zones still
    # shows through wherever no zone sits above it.
    for iname, verts in g["impassable"]:
        if not verts:
            continue
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        p.append(f"<g data-reveal='{_elem_reveal(cx, cy)}'><polygon points='{poly(verts)}' "
                 f"fill='#3a3a42' fill-opacity='0.7' stroke='#22222a' stroke-width='{0.6*sc:.2f}'>"
                 f"<title>{html.escape(iname)}</title></polygon></g>")

    for zname in zone_order:
        verts = g["zones"].get(zname)
        if not verts:
            continue
        zval = g["zone_z"].get(zname, 0.0)
        color, alpha = _Z_PALETTE[z_rank[zval] % len(_Z_PALETTE)]
        if _is_water_zone(zname):
            color, alpha = _WATER_FILL, 0.85
        zone_tip = _zone_tooltip(zname, _zone_dest.get(zname), _scenario_root)
        icon = _zone_icon_uri(_scenario_root, geometry_path.parent, zname,
                              _zone_dest.get(zname))
        p.append(f"<g data-reveal='{reveal_zone.get(zname, never)}'>")
        if icon:
            xs = [x for x, _ in verts]
            ys = [y for _, y in verts]
            p.append(f"<polygon points='{poly(verts)}' fill='none' "
                     f"stroke='#888' stroke-width='{0.6*sc:.2f}'>"
                     f"<title>{html.escape(zone_tip)}</title></polygon>")
            p.append(f"<image href='{icon}' x='{min(xs):.1f}' y='{fy(max(ys)):.1f}' "
                     f"width='{max(xs)-min(xs):.1f}' height='{max(ys)-min(ys):.1f}' "
                     "preserveAspectRatio='xMidYMid meet'>"
                     f"<title>{html.escape(zone_tip)}</title></image>")
        else:
            p.append(f"<polygon points='{poly(verts)}' fill='{color}' "
                     f"fill-opacity='{alpha:.3f}' stroke='#888' stroke-width='{0.6*sc:.2f}'>"
                     f"<title>{html.escape(zone_tip)}</title></polygon>")
        p.append("</g>")

    for bname, verts in g["boundaries"]:
        if not verts:
            continue
        cx = sum(x for x, _ in verts) / len(verts)
        cy = sum(y for _, y in verts) / len(verts)
        p.append(f"<g data-reveal='{_elem_reveal(cx, cy)}'><polygon points='{poly(verts)}' "
                 f"fill='none' stroke='gold' stroke-width='{1.1*sc:.2f}' "
                 f"stroke-dasharray='{2.5*sc:.2f},{2.5*sc:.2f}'>"
                 f"<title>{html.escape(bname)}</title></polygon></g>")

    for name, (x, y) in g["landmarks"].items():
        tip = _landmark_tooltip(name, x, y, g["zones"])
        p.append(f"<g data-reveal='{_elem_reveal(x, y)}'>"
                 f"<circle cx='{x:.2f}' cy='{fy(y):.2f}' r='{1.1*sc:.2f}' fill='#b9b9b9'>"
                 f"<title>{html.escape(tip)}</title></circle></g>")
    for _iid, (x, y, label) in g["items"].items():
        tooltip = _item_tooltip(label, (item_details or {}).get(_iid))
        p.append(f"<g data-reveal='{_elem_reveal(x, y)}'>"
                 f"<circle cx='{x:.2f}' cy='{fy(y):.2f}' r='{0.9*sc:.2f}' fill='#d9c98a'>"
                 f"<title>{html.escape(tooltip)}</title></circle>"
                 f"<text x='{x+1.4*sc:.2f}' y='{fy(y):.2f}' class='ilabel'>{html.escape(label)}</text></g>")

    # Per-character "where you just came from" segment: previous turn -> current.
    # Drawn before the markers so the dot sits on top of its own trail tail.
    for cid in sorted(tracks):
        p.append(f"<line class='trail' data-trail='{html.escape(cid)}' "
                 f"stroke='{cc[cid]}' stroke-width='{0.7*sc:.2f}' stroke-opacity='0.65' "
                 f"stroke-linecap='round' stroke-dasharray='{1.6*sc:.2f},{1.3*sc:.2f}' "
                 f"style='display:none'/>")
    for cid in sorted(tracks):
        ci = _char_icon_uri(_scenario_root, cid)
        if ci:
            z = 6.0 * sc
            marker = (f"<image class='char-icon-img' data-base-z='{z:.2f}' href='{ci}' "
                      f"x='{-z/2:.2f}' y='{-z/2:.2f}' width='{z:.2f}' height='{z:.2f}' "
                      "preserveAspectRatio='xMidYMid meet'/>")
        else:
            r_base = 0.75 * sc
            sw_base = 0.35 * sc
            marker = (f"<circle class='char-icon-dot' data-base-r='{r_base:.2f}' "
                      f"data-base-sw='{sw_base:.2f}' r='{r_base:.2f}' fill='{cc[cid]}' "
                      f"stroke='#000' stroke-width='{sw_base:.2f}'/>")
        name = html.escape(cid.replace("_", " ").title())
        p.append(f"<g class='char' data-char='{html.escape(cid)}' style='display:none'>"
                 f"<g class='char-marker'>{marker}</g>"
                 f"<title>{name}</title></g>")
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
        "const f=FRAMES[t]||{};const pf=i>0?(FRAMES[TURNS[i-1]]||{}):{};"
        "document.querySelectorAll('[data-trail]').forEach(e=>{"
        "const a=pf[e.dataset.trail],b=f[e.dataset.trail];"
        "if(a&&b){e.setAttribute('x1',a[0]);e.setAttribute('y1',-a[1]);"
        "e.setAttribute('x2',b[0]);e.setAttribute('y2',-b[1]);e.style.display='';}"
        "else{e.style.display='none';}});"
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
        # Skip the reload while the reader is actively panning/zooming (a recent
        # interaction) so it doesn't yank the map out from under them; the saved
        # viewBox is restored on the reloads that do fire.
        p.append(
            f"setInterval(function(){{if(+sl.value>=TURNS.length-1&&"
            f"(Date.now()-(window.__mapLastInteract||0))>2500)"
            f"{{location.reload();}}}},{int(live_refresh_secs) * 1000});")
    p.append(_PANZOOM_JS)
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
