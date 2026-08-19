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
    r"var ti=Array.prototype.slice.call(document.querySelectorAll('.item-icon'));"
    r"var IK=K+':iconScale';var iconScale=1.0;"
    r"function SI(n){iconScale=Math.max(0.2,Math.min(8,Number(n)||1));"
    r"for(var i=0;i<ii.length;i++){var bz=Number(ii[i].getAttribute('data-base-z'))||6;"
    r"var z=bz*iconScale;ii[i].setAttribute('x',(-z/2).toFixed(2));ii[i].setAttribute('y',(-z/2).toFixed(2));"
    r"ii[i].setAttribute('width',z.toFixed(2));ii[i].setAttribute('height',z.toFixed(2));}"
    r"for(var j=0;j<id.length;j++){var br=Number(id[j].getAttribute('data-base-r'))||0.75;"
    r"var bw=Number(id[j].getAttribute('data-base-sw'))||0.35;"
    r"id[j].setAttribute('r',(br*iconScale).toFixed(2));id[j].setAttribute('stroke-width',(bw*iconScale).toFixed(2));}"
    r"for(var q=0;q<ti.length;q++){var bf=Number(ti[q].getAttribute('data-base-fs'))||3.2;"
    r"ti[q].setAttribute('font-size',(bf*iconScale).toFixed(2));}"
    r"var iv=document.getElementById('iconScaleVal');if(iv)iv.textContent=iconScale.toFixed(2)+'x';"
    r"try{sessionStorage.setItem(IK,String(iconScale));}catch(_){}}"
    r"function SIS(d){SI(iconScale*(d>0?1.18:0.85));}"
    r"try{var isv=parseFloat(sessionStorage.getItem(IK)||'1');"
    r"if(isFinite(isv))SI(isv);else SI(1);}catch(_){SI(1);}"
    r"try{var zsv=parseFloat(sessionStorage.getItem(ZK)||'0.15');"
    r"if(isFinite(zsv))SZ(zsv);else SZ(0.15);}catch(_){SZ(0.15);}"
    r"function WD(e){var dx=Number(e.deltaX)||0,dy=Number(e.deltaY)||0;"
    r"return Math.abs(dy)>=Math.abs(dx)?dy:dx;}"
    r"s.addEventListener('wheel',function(e){e.preventDefault();if(window.__mapArtEditing)return;I();if(e.shiftKey){"
    r"if(!(ii.length||id.length))return;var wd=WD(e);if(!wd)return;"
    r"SIS(wd<0?1:-1);"
    r"return;}var p=P(e);var wd=WD(e);if(!wd)return;var f=ZF(wd);"
    r"var nw=Math.max(b[2]/20,v.w*f);f=nw/v.w;"
    r"v.x=p.x-(p.x-v.x)*f;v.y=p.y-(p.y-v.y)*f;v.w*=f;v.h*=f;A();},{passive:false});"
    r"var d=false,l=null;"
    r"s.addEventListener('mousedown',function(e){if(window.__mapArtEditing)return;d=true;I();l={x:e.clientX,y:e.clientY};"
    r"s.style.cursor='grabbing';e.preventDefault();});"
    r"s.addEventListener('dblclick',function(e){e.preventDefault();if(window.__mapArtEditing)return;I();var p=P(e);"
    r"var x=Math.round(p.x);var y=Math.round(-p.y);"
    r"try{if(window.parent&&window.parent!==window)"
    r"window.parent.postMessage({type:'driftmoor-map-dblclick',x:x,y:y,shift:!!e.shiftKey},'*');}catch(_){}"
    r"});"
    r"window.addEventListener('mousemove',function(e){if(!d)return;I();"
    r"var r=s.getBoundingClientRect();v.x-=(e.clientX-l.x)/r.width*v.w;"
    r"v.y-=(e.clientY-l.y)/r.height*v.h;l={x:e.clientX,y:e.clientY};A();});"
    r"window.addEventListener('mouseup',function(){d=false;s.style.cursor=window.__mapArtEditing?'default':'grab';});"
    r"s.style.cursor='grab';"
    r"window.addEventListener('keydown',function(e){if(window.__mapArtEditing)return;"
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


def _icon_data_uri(
    path: "Path", *, strip_character_name: bool = False,
) -> "str | None":
    """Return an ``<image href>`` data-URI for a building ``icon.svg``/png, or
    None if absent. Cached so per-turn map regeneration doesn't re-encode."""
    key = f"{path}|strip_name={strip_character_name}"
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
        payload = path.read_bytes()
        if strip_character_name and path.suffix == ".svg":
            svg = payload.decode("utf-8")
            # Character portraits consistently tag their optional embedded
            # banner. Maps already provide a hover <title>, so omit this tiny,
            # poorly scaling duplicate label at embedding time.
            svg = re.sub(
                r"\s*<!--\s*name-label\s*-->\s*"
                r"<rect\b[^>]*/>\s*<text\b[^>]*>.*?</text>",
                "",
                svg,
                flags=re.IGNORECASE | re.DOTALL,
            )
            payload = svg.encode("utf-8")
        uri = f"data:{mime};base64," + base64.b64encode(payload).decode("ascii")
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


def _zone_floor_uri(place_dir: "Path | None", zname: str) -> "str | None":
    """Resolve authored top-down art at ``floor/<normalized-zone>.*``.

    Floor art belongs to the current place, unlike ``icon.svg`` elevations
    which represent a connected place on its parent's map. It is clipped and
    revealed with the semantic zone by the renderer.
    """
    if place_dir is None:
        return None
    stem = re.sub(r"[^a-z0-9]+", "_", (zname or "").strip().lower()).strip("_")
    if not stem:
        return None
    for ext in (".svg", ".png", ".webp"):
        uri = _icon_data_uri(place_dir / "floor" / f"{stem}{ext}")
        if uri:
            return uri
    return None


def _load_visual_overlays(place_dir: "Path | None") -> list[dict]:
    """Load optional positioned artwork from a place's ``VISUALS.md`` table."""
    if place_dir is None:
        return []
    path = place_dir / "VISUALS.md"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[dict] = []
    for i, line in enumerate(lines[:-2]):
        if not line.strip().startswith("|") or "asset" not in line.lower():
            continue
        if not re.match(r"^\|[\s\-:|]+\|$", lines[i + 1].strip()):
            continue
        headers = [h.strip().lower() for h in line.strip().strip("|").split("|")]
        for row_line in lines[i + 2:]:
            if not row_line.strip().startswith("|"):
                break
            cells = [c.strip() for c in row_line.strip().strip("|").split("|")]
            row = dict(zip(headers, cells))
            try:
                rec = {
                    "id": row.get("id", ""), "asset": row.get("asset", ""),
                    "target": row.get("target", ""),
                    "x": float(row.get("x", "0")), "y": float(row.get("y", "0")),
                    "width": float(row.get("width", "4")),
                    "height": float(row.get("height", "4")),
                    "rotation": float(row.get("rotation", "0")),
                    "layer": row.get("layer", "fixture") or "fixture",
                }
            except ValueError:
                continue
            asset_path = place_dir / rec["asset"]
            rec["uri"] = _icon_data_uri(asset_path)
            if rec["id"] and rec["uri"]:
                out.append(rec)
        break
    return out


def _char_icon_uri(scenario_root: "Path | None", cid: str) -> "str | None":
    """Data-URI for a character token ``<char dir>/icon.svg`` if present. Looks
    in the conventional people/creature dirs, by id then base id (drops _N)."""
    if scenario_root is None:
        return None
    base = re.sub(r"_\d+$", "", cid)
    for who in (cid, base):
        for area in ("people/players", "people/npcs", "creatures"):
            for ext in (".svg", ".png", ".webp"):
                uri = _icon_data_uri(
                    scenario_root / area / who / f"icon{ext}",
                    strip_character_name=True,
                )
                if uri:
                    return uri
    return None


def _zone_icon_dirs(g: dict, place_rel: str | None = None) -> dict:
    """Map each zone name -> the place dir a connection inside it leads to,
    so a zone can find its ``icon.svg``. Reuses ``## Connections``.

    ``place_rel`` is the current place's path relative to ``scenario/`` (e.g.
    ``places/driftmoor``); when given, only connections leading to an immediate
    child count. Deeper descendants belong on their parent's map, and an exit
    connection back upward cannot hijack a building or region icon."""
    prefix = (place_rel.rstrip("/") + "/") if place_rel else "places/"
    out: dict = {}
    for (_name, cx, cy, dest) in g.get("connections", []):
        if not dest or not dest.startswith(prefix):
            continue
        remainder = dest[len(prefix):].strip("/")
        if not remainder or "/" in remainder:
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


def _item_is_loose(detail: object | None) -> bool:
    """Return false once a runtime item has been picked up."""
    if detail is None:
        return True
    if isinstance(detail, dict):
        return (not bool(detail.get("holder"))
                and detail.get("carry_location") != "consumed")
    carry_location = getattr(getattr(detail, "carry", None), "location", "")
    return not bool(getattr(detail, "holder", None)) and carry_location != "consumed"


def _item_is_pickable(detail: object | None) -> bool:
    if isinstance(detail, dict):
        return bool(detail.get("pickable"))
    return bool(getattr(detail, "pickable", False)) if detail is not None else False


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
        "zones": {}, "zone_z": {}, "landmarks": {}, "landmark_labels": {},
        "landmark_destinations": {}, "impassable": [],
        "boundaries": [], "starting_positions": {}, "items": {},
        "connections": [], "reveal_on_entry": set(), "reveal_layout": set(),
        "routes": [], "route_styles": {}, "map_styles": {},
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

    _zone_rows = _table("Zones")
    _zone_header_idx = {
        h.strip().lower(): i for i, h in enumerate(_zone_rows[0])
    } if _zone_rows and _zone_rows[0][0] == "name" else {}
    _auto_wall_col = _zone_header_idx.get("auto_wall")
    zone_auto_wall_off: set[str] = set()
    for cells in _zone_rows:
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
        if (
            _auto_wall_col is not None
            and _auto_wall_col < len(cells)
            and cells[_auto_wall_col].strip().lower() in {"false", "no", "0"}
        ):
            zone_auto_wall_off.add(name)

    landmark_rows = _table("Landmarks")
    landmark_header = {
        value.strip().lower(): index for index, value in enumerate(landmark_rows[0])
    } if landmark_rows and landmark_rows[0][0] == "name" else {}
    for cells in landmark_rows:
        if cells[0] == "name":
            continue
        if len(cells) >= 3:
            try:
                g["landmarks"][cells[0]] = (float(cells[1]), float(cells[2]))
                label_i = landmark_header.get("label")
                dest_i = landmark_header.get("destination")
                if label_i is not None and label_i < len(cells) and cells[label_i]:
                    g["landmark_labels"][cells[0]] = cells[label_i]
                if dest_i is not None and dest_i < len(cells) and cells[dest_i]:
                    g["landmark_destinations"][cells[0]] = cells[dest_i].strip("/")
            except ValueError:
                pass

    for cells in _table("Impassable"):
        if cells[0] == "description":
            continue
        if len(cells) >= 2:
            v = _verts(cells[1])
            if v:
                g["impassable"].append((cells[0], v))

    # Connections: `name | x | y | destination`. Parsed ahead of the
    # auto-wall block below (compute_venue_walls needs connection points
    # to identify sealed-venue zones) as well as used to resolve a
    # building zone's art directory (the place a connection leads to).
    for cells in _table("Connections"):
        if cells[0].lower() == "name":
            continue
        if len(cells) >= 4:
            try:
                g["connections"].append(
                    (cells[0], float(cells[1]), float(cells[2]), cells[3]))
            except ValueError:
                continue

    # Optional regional cartography. Routes are presentation-level paths over
    # the authoritative world coordinates; they do not create traversal edges.
    for cells in _table("Routes"):
        if cells[0].lower() == "name":
            continue
        if len(cells) >= 3:
            verts = _verts(cells[-1])
            if verts:
                g["routes"].append((cells[0], cells[1].lower(), verts))
                if len(cells) >= 5:
                    try:
                        width = float(cells[3])
                    except ValueError:
                        width = None
                    g["route_styles"][cells[0]] = {
                        "color": cells[2], "width": width,
                    }

    for cells in _table("Map Styles"):
        if cells[0].lower() != "target" and len(cells) >= 2:
            g["map_styles"][cells[0]] = cells[1]

    # Zone boundaries are impassable by default; door/archway landmarks open
    # them (see models.geometry_loader.compute_auto_walls, the single
    # shared implementation so the rendered map and actual gameplay always
    # agree on where the walls are). On by default; opt out per-scene with
    # "## Walls\n- **auto_wall:** false" (see the loader for why).
    walls_section = re.search(r"##\s+Walls\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    auto_wall_on = True
    if walls_section:
        flag = re.search(
            r"\*\*auto_wall:\*\*\s*([^\n]+)", walls_section.group(1), re.IGNORECASE)
        if flag and flag.group(1).strip().lower() in {"false", "no", "0"}:
            auto_wall_on = False
    if auto_wall_on:
        from models.geometry_loader import compute_auto_walls, compute_venue_walls
        g["impassable"].extend(
            ("Auto wall", verts)
            for verts in compute_auto_walls(
                g["zones"], g["landmarks"],
                excluded_zones=frozenset(zone_auto_wall_off),
            )
        )
        _connection_xy = {name: (x, y) for name, x, y, _dest in g["connections"]}
        g["impassable"].extend(
            ("Venue wall", verts)
            for verts in compute_venue_walls(g["zones"], _connection_xy)
        )

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

    # Character placement is a scene concern: callers pass scene-resolved
    # ``start_positions`` into the renderers (which override ``starting_positions``
    # above). GEOMETRY is a pure stage and carries no positions to parse here.

    bm = re.search(r"##\s+Boundaries\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    if bm:
        for sub in re.finditer(r"###\s+(.+?)\n(.*?)(?=\n###|\Z)",
                               bm.group(1), re.DOTALL):
            render_mode = re.search(
                r"\*\*render:\*\*\s*([^\n]+)", sub.group(2), re.IGNORECASE)
            if render_mode and render_mode.group(1).strip().lower() in {
                "hidden", "none", "false", "no"
            }:
                continue
            vm = re.search(r"\*\*vertices:\*\*\s*([^\n]+)", sub.group(2))
            if vm:
                g["boundaries"].append((sub.group(1).strip(), _verts(vm.group(1))))

    fog = re.search(r"##\s+Fog of War\b(.*?)(?=\n##\s+\w|\Z)", text, re.DOTALL)
    if fog:
        entry = re.search(
            r"\*\*reveal_on_entry:\*\*\s*([^\n]+)", fog.group(1), re.IGNORECASE)
        if entry:
            g["reveal_on_entry"] = {
                name.strip().upper() for name in entry.group(1).split(",")
                if name.strip()
            }
        layout = re.search(
            r"\*\*reveal_layout:\*\*\s*([^\n]+)",
            fog.group(1), re.IGNORECASE,
        )
        if layout:
            g["reveal_layout"] = {
                name.strip().upper() for name in layout.group(1).split(",")
                if name.strip()
            }

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


def load_visited_places_from_snapshots(snapshot_dir: Path | None) -> set[str]:
    """Return authored place paths recorded in a viewer's checkpoint history."""
    visited: set[str] = set()
    if snapshot_dir is None or not snapshot_dir.exists():
        return visited
    for path in snapshot_dir.glob("day*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        place = str(data.get("scene_place_path") or "").strip("/")
        if place:
            visited.add(place)
    return visited


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
    visited_places = load_visited_places_from_snapshots(snapshot_dir)
    for landmark, destination in list(g["landmark_destinations"].items()):
        if destination not in visited_places:
            g["landmarks"].pop(landmark, None)
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
        color = g["map_styles"].get(zname, color)
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
    visited_places = load_visited_places_from_snapshots(snapshot_dir)
    for landmark, destination in list(g["landmark_destinations"].items()):
        if destination not in visited_places:
            g["landmarks"].pop(landmark, None)
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
    for _name, _kind, v in g["routes"]:
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
    raw_extent = max(max_x - min_x, max_y - min_y, 1.0)
    margin = max(8.0, raw_extent * 0.025)

    view_x = min_x - margin
    view_y = min_y - margin
    view_w = max((max_x - min_x) + 2 * margin, 1.0)
    view_h = max((max_y - min_y) + 2 * margin, 1.0)

    # SVG font sizes are in viewBox units; scale with map extent so a big map fit
    # to a fixed pixel width keeps legible labels (and a compact indoor map keeps
    # small ones).
    label_base = max(0.85, max(view_w, view_h) / 100.0)
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
    is_regional = _place_rel == "places"
    _zone_dest = _zone_icon_dirs(g, _place_rel)
    symbol_scale = max(1.0, max(view_w, view_h) / 1000.0)
    line_scale = max(1.0, max(view_w, view_h) / 1400.0)

    parts: list[str] = []
    parts.append(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Driftmoor Interactive Map</title>"
        "<style>"
        "body{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
        "margin:0;background:#20251f;color:#ede7d5;}"
        ".wrap{padding:12px 14px;}"
        "h1{font-size:14px;margin:0 0 8px 0;}"
        "p{margin:0 0 10px 0;font-size:13px;color:#333;}"
        "svg{width:min(1200px,98vw);height:auto;border:1px solid #6f6a58;background:#d8cfb5;}"
        f".zone-label{{font-size:var(--zfs,{zone_label_size}px);font-weight:700;fill:#26251f;opacity:.82;paint-order:stroke;stroke:#e9e0c8;stroke-width:{line_scale * 1.6:.2f};}}"
        f".lm-label{{font-size:var(--lfs,{landmark_label_size}px);fill:#24231f;paint-order:stroke;stroke:#e9e0c8;stroke-width:{line_scale * 1.2:.2f};}}"
        f".item-label{{font-size:var(--ifs,{item_label_size}px);fill:#5a4a10;font-style:italic;}}"
        "</style></head><body><div class='wrap'>"
    )
    safe_title = html.escape(title or geometry_path.parent.name.replace("_", " ").title())
    parts.append(f"<h1>{safe_title}</h1>")
    parts.append("<p>Drag to pan, scroll to zoom. Hover over dots and places for details.</p>")
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
        if is_regional:
            upper = zname.upper()
            if upper == "EXTERIOR":
                color, alpha = "#b8aa7b", 1.0
            elif _is_water_zone(zname):
                color, alpha = "#7897a3", 0.95
            elif "MISTWOOD" in upper:
                color, alpha = "#657958", 0.92
            elif "OBELISK" in upper:
                color, alpha = "#8c8175", 0.94
            elif "CLIFF" in upper:
                color, alpha = "#746f68", 0.94
            elif "PLAINS" in upper or "FIELDS" in upper:
                color, alpha = "#b5a86e", 0.88
            elif "DRIFTMOOR" in upper or "MILL" in upper or "HARBOR" in upper:
                color, alpha = "#9b7658", 0.88
        if _is_water_zone(zname):
            color, alpha = ("#7897a3", 0.95) if is_regional else (_WATER_FILL, 0.85)
        color = g["map_styles"].get(zname, color)
        points = _fmt_poly(verts)
        zone_tip = _zone_tooltip(zname, _zone_dest.get(zname), _scenario_root)
        parts.append(
            f"<polygon points='{points}' fill='{color}' fill-opacity='{alpha:.3f}' "
            f"stroke='#4a463a' stroke-width='{line_scale * 0.7:.2f}'>"
            f"<title>{html.escape(zone_tip)}</title></polygon>"
        )

    # Regional roads, trails, and waterways sit above terrain but below labels.
    for route_name, route_kind, verts in g["routes"]:
        if not verts:
            continue
        if route_kind in {"river", "water"}:
            stroke, dash, width = "#587f91", "", 3.6
        elif route_kind in {"trail", "path"}:
            stroke, dash, width = "#6d5639", "7,6", 2.0
        else:
            stroke, dash, width = "#765f42", "", 2.8
        authored = g["route_styles"].get(route_name, {})
        stroke = authored.get("color") or stroke
        stroke_width = authored.get("width") or (width * line_scale)
        dash_attr = f" stroke-dasharray='{dash}'" if dash else ""
        points = " ".join(f"{x:.2f},{_flip_y(y):.2f}" for x, y in verts)
        parts.append(
            f"<polyline points='{points}' fill='none' stroke='{stroke}' "
            f"stroke-width='{stroke_width:.2f}' stroke-linecap='round' "
            f"stroke-linejoin='round'{dash_attr}><title>{html.escape(route_name)}</title></polyline>"
        )

    if is_regional:
        for zname in zone_order:
            if zname.upper() == "EXTERIOR":
                continue
            verts = g["zones"].get(zname) or []
            if not verts:
                continue
            cx = sum(x for x, _y in verts) / len(verts)
            cy = sum(y for _x, y in verts) / len(verts)
            label = zname.replace("_", " ").title()
            parts.append(
                f"<text x='{cx:.2f}' y='{_flip_y(cy):.2f}' text-anchor='middle' "
                f"class='zone-label'>{html.escape(label)}</text>"
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
        if is_regional:
            parts.append(
                f"<polygon points='{points}' fill='none' stroke='#7b3f35' "
                f"stroke-width='{1.4 * line_scale:.2f}' stroke-dasharray='6,5'>"
                f"<title>{html.escape(iname)} (impassable)</title></polygon>"
            )
            continue
        parts.append(
            f"<polygon points='{points}' fill='#4a4a4a' fill-opacity='0.65' "
            "stroke='#2a2a2a' stroke-width='0.6'>"
            f"<title>{html.escape(iname)}</title></polygon>"
        )

    # Landmarks
    for name, (x, y) in g["landmarks"].items():
        tip = _landmark_tooltip(name, x, y, g["zones"])
        parts.append(
            f"<circle cx='{x:.2f}' cy='{_flip_y(y):.2f}' r='{2.0 * symbol_scale:.2f}' "
            f"fill='#302d25' stroke='#efe4c8' stroke-width='{0.55 * line_scale:.2f}'>"
            f"<title>{html.escape(tip)}</title></circle>"
        )
        if is_regional:
            label = name.replace("_", " ").title()
            parts.append(
                f"<text x='{x + 3.2 * symbol_scale:.2f}' y='{_flip_y(y) - 2.1 * symbol_scale:.2f}' "
                f"class='lm-label'>{html.escape(label)}</text>"
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


def _point_in_or_near_poly(
    x: float, y: float, verts: list[tuple[float, float]], tolerance: float = 0.75,
) -> bool:
    """Containment with the same practical edge tolerance used by movement."""
    if _point_in_poly(x, y, verts):
        return True
    return _point_near_poly_edge(x, y, verts, tolerance)


def _point_near_poly_edge(
    x: float, y: float, verts: list[tuple[float, float]], tolerance: float = 0.75,
) -> bool:
    """Whether the point sits within tolerance of the polygon's *boundary*
    line specifically — unlike ``_point_in_or_near_poly``, this has no
    interior short-circuit, so it does not fire for a point buried deep
    inside a large containing zone (EXTERIOR spans the whole map, nested
    "inside" every other zone by construction — see the "zone order
    matters, first match wins" convention). Used to detect a landmark
    sitting exactly on a *shared* boundary between two real zones (a
    door) without also matching every zone whose fill happens to
    geometrically cover that point.
    """
    if len(verts) < 2:
        return False
    for i, (ax, ay) in enumerate(verts):
        bx, by = verts[(i + 1) % len(verts)]
        dx, dy = bx - ax, by - ay
        denom = dx * dx + dy * dy
        u = 0.0 if denom == 0 else max(
            0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / denom)
        )
        px, py = ax + u * dx, ay + u * dy
        if (x - px) ** 2 + (y - py) ** 2 <= tolerance ** 2:
            return True
    return False


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
    editable_start_characters: "Iterable[str] | None" = None,
    visited_places: "Iterable[str] | None" = None,
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
    visited = {str(place).strip("/") for place in (visited_places or ())}
    for landmark, destination in list(g["landmark_destinations"].items()):
        if destination not in visited:
            g["landmarks"].pop(landmark, None)
    has_discovered_landmarks = any(
        name in g["landmark_destinations"] for name in g["landmarks"]
    )
    editable_start_ids = set(editable_start_characters or ())
    # Runtime-created loose items (purchases subsequently dropped, disarmed
    # weapons, etc.) have no authored GEOMETRY row. Add them to this render from
    # their live Thing position; authored ids retain their authored marker.
    zone_names = {name.upper() for name in g["zones"]}
    for iid, detail in (item_details or {}).items():
        if iid in g["items"] or not _item_is_loose(detail):
            continue
        pos = getattr(detail, "position", None)
        zone = str(getattr(detail, "zone", "") or "").upper()
        if pos is None or (zone_names and zone not in zone_names):
            continue
        label = (
            getattr(detail, "label", None)
            or getattr(detail, "name", None)
            or str(iid).replace("_", " ")
        )
        g["items"][iid] = (float(pos.x), float(pos.y), label)
    # Character placement is a scene concern: the caller supplies the
    # scene-resolved starting positions (GEOMETRY is a pure stage and carries no
    # placement). Without them, only snapshot-recorded characters are plotted.
    if start_positions is not None:
        g["starting_positions"] = {
            cid: (float(p[0]), float(p[1])) for cid, p in start_positions.items()
        }
    tracks = (load_tracks_from_snapshots(snapshot_dir)
              if snapshot_dir is not None and snapshot_dir.exists() else {})

    # A session keeps one checkpoint directory while moving between place maps.
    # Snapshot tracks therefore contain coordinates from earlier scenes. Keep
    # only points whose authoritative zone and coordinates belong to this map;
    # otherwise an old town-scale point stretches a small upstairs viewBox and
    # draws a long dashed trail back to the prior scene.
    zones_by_upper = {name.upper(): verts for name, verts in g["zones"].items()}
    scoped_tracks: dict[str, list[tuple[int, float, float, str]]] = {}
    scene_cast = set(start_characters) if start_characters is not None else None
    for cid, pts in tracks.items():
        if scene_cast is not None and cid not in scene_cast:
            continue
        kept = []
        for point in pts:
            turn, x, y, zone = point
            verts = zones_by_upper.get((zone or "").upper())
            # The engine's authoritative zone can intentionally use an edge
            # tolerance wider than SVG polygon containment. Require that the
            # named zone belongs to this scene, then accept a coordinate inside
            # any of this scene's polygons.
            on_this_map = any(
                _point_in_or_near_poly(float(x), float(y), candidate)
                for candidate in g["zones"].values()
            )
            if verts is not None and on_this_map:
                kept.append(point)
        if kept:
            scoped_tracks[cid] = kept
    tracks = scoped_tracks

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
        _town_buildings: set[str] = set()
        if (sg.place_path or "").strip("/").lower() == "places/driftmoor":
            for _cname, _cpos in sg.connections.items():
                if _cname in {"to_region", "to_harbor_water"}:
                    continue
                _czone = sg.zone_at(_cpos)
                if _czone:
                    _town_buildings.add(_czone.upper())

        def _reveal_seen_from(ox: float, oy: float, ozone: str, t: int) -> None:
            visual = sg.ambient_sight_range(ozone or (sg.zone_at(_Pos(ox, oy)) or ""))
            visual_ft = _math.inf if visual is None else visual
            obs = _Pos(ox, oy)
            for gname, c in _centroids.items():
                if reveal_zone.get(gname, never + 1) <= t:
                    continue                       # already revealed at/before t
                if gname.upper() in g.get("reveal_on_entry", set()):
                    continue                       # authored closed/private room
                sight_target = c
                if gname.upper() in _town_buildings:
                    _poly = next(
                        (poly for name, poly in sg.zones.items()
                         if name.upper() == gname.upper()),
                        None,
                    )
                    if _poly is not None:
                        sight_target = _poly.nearest_point(obs)
                if (_math.hypot(sight_target.x - ox, sight_target.y - oy) <= visual_ft
                        and sg.can_see(obs, sight_target)):
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
        # A landmark sitting exactly on a shared zone boundary (a door,
        # an archway) is "on" both adjacent zones' edges at once as far
        # as ray casting is concerned — which one _containing_zone
        # happens to pick is arbitrary table-order noise. Reveal it as
        # soon as *either* side has been explored (a doorway is visible
        # from the room you're standing in, even if what's beyond it is
        # still fogged) rather than gating it on one arbitrarily-chosen
        # side. This must check proximity to each zone's *boundary
        # line*, not fill: EXTERIOR (and any zone) can geometrically
        # contain another zone's whole interior by construction (see the
        # "zone order matters, first match wins" convention), and a
        # naive "inside or near" containment test would match it for
        # every point on the map, leaking fog-of-war-hidden contents via
        # whichever huge background zone happens to already be revealed.
        touching = [
            zname for zname, verts in g["zones"].items()
            if _point_near_poly_edge(x, y, verts, tolerance=0.1)
        ]
        if touching:
            return min(reveal_zone.get(z, never) for z in touching)
        z = _containing_zone(x, y, g["zones"])
        if z is None:
            return turn_list[0]               # not in any zone -> ungated
        return reveal_zone.get(z, never)

    # viewBox extents (same as the path map).
    all_pts: list[tuple[float, float]] = []
    for v in g["zones"].values():
        all_pts.extend(v)
    for _n, v in g["impassable"]:
        all_pts.extend(v)
    for _n, v in g["boundaries"]:
        all_pts.extend(v)
    for _n, _kind, v in g["routes"]:
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
    route_sc = max(1.0, max(view_w, view_h) / 1400.0)

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
             ".artctl{display:none;gap:4px}.artctl.on{display:inline-flex;}"
             "svg{width:min(1100px,98vw);height:auto;border:1px solid #c7c7c2;"
             "background:#0e0e12;}button{font:inherit;padding:3px 10px;cursor:pointer;}")
    p.append(
        ".coord-readout{display:none;position:fixed;pointer-events:none;"
        "background:#111;color:#eee;font:12px/1.4 ui-monospace,monospace;"
        "padding:2px 6px;border-radius:4px;border:1px solid #555;z-index:9;}")
    # font-size is a JS-controlled var (constant on-screen size across zoom); the
    # fallback keeps a sane value before the pan/zoom script runs.
    p.append(".zlabel{font-size:var(--zfs,2.1px);font-weight:700;fill:#eee;opacity:.85;}")
    p.append(".llabel{font-size:var(--lfs,1.7px);fill:#cfcfcf;}")
    p.append(".ilabel{font-size:var(--ifs,1.6px);fill:#d9c98a;font-style:italic;}")
    p.append(".clabel{font-size:var(--cfs,1.9px);font-weight:700;fill:#fff;"
             "paint-order:stroke;stroke:#000;stroke-width:0.3px;}")
    p.append(".deep-landmark-label{font-size:var(--lfs,1.7px);fill:#f0dfae;"
             "paint-order:stroke;stroke:#17140e;stroke-width:.3px;}")
    p.append("</style></head><body><div class='wrap'>")
    p.append(f"<h1>{safe_title}</h1>")
    p.append("<div class='ctl'><button id='play'>&#9654; Play</button>"
             "<button id='fit' title='Reset map view (key: F)'>Fit</button>"
             "<button id='refreshGeo' title='Re-read GEOMETRY.md from disk — picks up manual edits without exiting the scene'>Refresh scene</button>"
             "<button id='editArt' title='Move authored fixtures and initial NPC positions'>Edit layout</button>"
             "<button id='editTerrain' title='Drag road and river control points'>Edit terrain</button>"
             "<button id='saveTerrain' style='display:none'>Save terrain</button>"
             + ("<label class='hint'><input id='showDeepLandmarks' type='checkbox' checked> Discovered landmarks</label>"
                if has_discovered_landmarks else "") +
             "<span id='artctl' class='artctl'><button id='rotL' title='Rotate counterclockwise'>↶</button>"
             "<button id='rotR' title='Rotate clockwise'>↷</button><button id='smaller'>−</button>"
             "<button id='larger'>+</button><button id='copyVisuals'>Save layout</button>"
             "<button id='copyGeometry'>Copy coordinates</button></span>"
             "<span class='zctl'><span class='hint'>Zoom</span>"
             "<input id='zoomSpeed' type='range' min='5' max='40' value='15' step='1'>"
             "<span class='hint' id='zoomSpeedVal'>15%</span></span>"
             f"<input id='sl' type='range' min='0' max='{len(turn_list)-1}' "
             f"value='{len(turn_list)-1}' step='1'>"
             "<span id='rd' style='min-width:70px;'></span>"
             "<span class='hint'>wheel=zoom, drag=pan, F=fit</span>"
             "</div>")
    p.append("<div id='coordReadout' class='coord-readout'></div>")
    p.append(f"<svg id='map' viewBox='{view_x:.2f} {view_top:.2f} {view_w:.2f} {view_h:.2f}' "
             "preserveAspectRatio='xMidYMid meet'>")

    # Art has two distinct conventions: ``floor/<zone>.svg`` is top-down art
    # for a zone in this place; a connected sub-place's ``icon.svg`` is its
    # exterior elevation on the parent map. Both retain semantic polygon
    # boundaries and fog-of-war reveal.
    _scenario_root = next((pp for pp in geometry_path.parents if pp.name == "scenario"), None)
    _place_rel = (geometry_path.parent.relative_to(_scenario_root).as_posix()
                  if _scenario_root else None)
    _zone_dest = _zone_icon_dirs(g, _place_rel)
    _zone_floors = {
        zname: _zone_floor_uri(geometry_path.parent, zname)
        for zname in g["zones"]
    }
    _visual_overlays = _load_visual_overlays(geometry_path.parent)
    _visual_targets = {
        visual["target"] for visual in _visual_overlays if visual.get("target")
    }

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
        color = g["map_styles"].get(zname, color)
        zone_tip = _zone_tooltip(zname, _zone_dest.get(zname), _scenario_root)
        floor_art = _zone_floors.get(zname)
        icon = floor_art or _zone_icon_uri(
            _scenario_root, geometry_path.parent, zname, _zone_dest.get(zname))
        clip_id = "zone-floor-" + re.sub(r"[^a-zA-Z0-9_-]", "-", zname)
        if icon:
            p.append(f"<defs><clipPath id='{clip_id}'><polygon points='{poly(verts)}'/></clipPath></defs>")
        zone_reveal = (
            turn_list[0]
            if zname.upper() in g.get("reveal_layout", set())
            else reveal_zone.get(zname, never)
        )
        p.append(f"<g data-reveal='{zone_reveal}'>")
        if icon:
            xs = [x for x, _ in verts]
            ys = [y for _, y in verts]
            p.append(f"<polygon points='{poly(verts)}' fill='none' "
                     f"stroke='#888' stroke-width='{0.6*sc:.2f}'>"
                     f"<title>{html.escape(zone_tip)}</title></polygon>")
            art_class = "zone-floor-art" if floor_art else "zone-icon-art"
            p.append(f"<image class='{art_class}' href='{icon}' "
                     f"x='{min(xs):.1f}' y='{fy(max(ys)):.1f}' "
                     f"width='{max(xs)-min(xs):.1f}' height='{max(ys)-min(ys):.1f}' "
                     f"clip-path='url(#{clip_id})' preserveAspectRatio='none'>"
                     f"<title>{html.escape(zone_tip)}</title></image>")
        else:
            p.append(f"<polygon points='{poly(verts)}' fill='{color}' "
                     f"fill-opacity='{alpha:.3f}' stroke='#888' stroke-width='{0.6*sc:.2f}'>"
                     f"<title>{html.escape(zone_tip)}</title></polygon>")
        p.append("</g>")

    # Regional-scale roads and waterways. Each authored vertex gets a hidden
    # drag handle that the in-place terrain editor reveals on demand.
    for route_name, route_kind, verts in g["routes"]:
        if route_kind in {"river", "water"}:
            stroke, dash, width = "#587f91", "", 3.6
        elif route_kind in {"trail", "path"}:
            stroke, dash, width = "#8c724d", "7,6", 2.0
        else:
            stroke, dash, width = "#9a8058", "", 2.8
        authored = g["route_styles"].get(route_name, {})
        stroke = authored.get("color") or stroke
        stroke_width = authored.get("width") or (width * route_sc)
        points = " ".join(f"{x:.2f},{fy(y):.2f}" for x, y in verts)
        dash_attr = f" stroke-dasharray='{dash}'" if dash else ""
        p.append(
            f"<polyline class='terrain-route' data-route='{html.escape(route_name)}' "
            f"data-kind='{html.escape(route_kind)}' points='{points}' fill='none' "
            f"stroke='{stroke}' stroke-width='{stroke_width:.2f}' "
            f"stroke-linecap='round' stroke-linejoin='round'{dash_attr}>"
            f"<title>{html.escape(route_name)}</title></polyline>"
        )
        p.append(f"<g class='route-handles' data-route-handles='{html.escape(route_name)}' style='display:none'>")
        for index, (x, y) in enumerate(verts):
            p.append(
                f"<circle class='route-handle' data-route='{html.escape(route_name)}' "
                f"data-index='{index}' cx='{x:.3f}' cy='{fy(y):.3f}' "
                f"r='{3.0 * route_sc:.2f}' fill='#55ffff' fill-opacity='.82' "
                f"stroke='#102020' stroke-width='{0.5 * route_sc:.2f}'/>"
            )
        p.append("</g>")

    # Positioned authored art sits above the floor and below semantic targets,
    # items, and characters. The data attributes are the editor's source of
    # truth and can be copied back as a complete VISUALS.md table.
    for visual in _visual_overlays:
        x, y = visual["x"], visual["y"]
        w, h = visual["width"], visual["height"]
        rotation = visual["rotation"]
        p.append(
            f"<g class='visual-overlay' data-visual='{html.escape(visual['id'])}' "
            f"data-asset='{html.escape(visual['asset'])}' "
            f"data-target='{html.escape(visual['target'])}' data-x='{x:.3f}' "
            f"data-y='{y:.3f}' data-width='{w:.3f}' data-height='{h:.3f}' "
            f"data-rotation='{rotation:.3f}' data-layer='{html.escape(visual['layer'])}' "
            f"data-reveal='{_elem_reveal(x, y)}' "
            f"transform='translate({x:.3f},{fy(y):.3f}) rotate({-rotation:.3f})'>"
            f"<rect class='visual-selection' x='{-w/2:.3f}' y='{-h/2:.3f}' "
            f"width='{w:.3f}' height='{h:.3f}' fill='none' stroke='#55ffff' "
            f"stroke-width='.18' stroke-dasharray='.45,.3' style='display:none'/>"
            f"<image href='{visual['uri']}' x='{-w/2:.3f}' y='{-h/2:.3f}' "
            f"width='{w:.3f}' height='{h:.3f}' preserveAspectRatio='none'/>"
            f"<title>{html.escape(visual['id'].replace('_', ' ').title())}</title></g>")

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
        label = g["landmark_labels"].get(name, name.replace("_", " ").title())
        tip = _landmark_tooltip(label, x, y, g["zones"])
        zone = _containing_zone(x, y, g["zones"])
        painted = bool(zone and _zone_floors.get(zone)) or name in _visual_targets
        fill = "transparent" if painted else "#b9b9b9"
        radius = 1.8 if painted else 1.1 * sc
        deep_class = "deep-landmark" if name in g["landmark_destinations"] else ""
        p.append(f"<g class='{deep_class}' data-reveal='{_elem_reveal(x, y)}' "
                 f"data-landmark='{html.escape(name)}' data-x='{x:.3f}' data-y='{y:.3f}'>"
                 f"<circle class='landmark-hit' cx='{x:.2f}' cy='{fy(y):.2f}' "
                 f"r='{radius:.2f}' fill='{fill}'>"
                 f"<title>{html.escape(tip)}</title></circle>"
                 f"<text class='deep-landmark-label' x='{x + 2.0*sc:.2f}' "
                 f"y='{fy(y) - 1.5*sc:.2f}'>{html.escape(label)}</text></g>")
    for _iid, (x, y, label) in g["items"].items():
        detail = (item_details or {}).get(_iid)
        if not _item_is_loose(detail):
            continue
        tooltip = _item_tooltip(label, detail)
        authored_visual = _iid in _visual_targets
        if authored_visual:
            marker = (
                f"<circle class='item-hit' cx='{x:.2f}' cy='{fy(y):.2f}' "
                f"r='1.8' fill='transparent'>"
                f"<title>{html.escape(tooltip)}</title></circle>"
            )
        elif _item_is_pickable(detail):
            from engine.item_icons import item_icon
            marker = (
                f"<text class='item-icon' data-base-fs='{3.2*sc:.2f}' "
                f"x='{x:.2f}' y='{fy(y):.2f}' text-anchor='middle' "
                f"dominant-baseline='central' font-size='{3.2*sc:.2f}'>"
                f"{item_icon(label, getattr(detail, 'emoji', ''))}"
                f"<title>{html.escape(tooltip)}</title></text>"
            )
        else:
            zone = _containing_zone(x, y, g["zones"])
            painted = bool(zone and _zone_floors.get(zone))
            marker = (
                f"<circle cx='{x:.2f}' cy='{fy(y):.2f}' "
                f"r='{1.8 if painted else 0.9*sc:.2f}' "
                f"fill='{'transparent' if painted else '#d9c98a'}'>"
                f"<title>{html.escape(tooltip)}</title></circle>"
            )
        zone = _containing_zone(x, y, g["zones"])
        painted_static = bool(
            not _item_is_pickable(detail) and zone and _zone_floors.get(zone))
        label_markup = "" if (painted_static or authored_visual) else (
            f"<text x='{x+1.8*sc:.2f}' y='{fy(y):.2f}' "
            f"class='ilabel'>{html.escape(label)}</text>")
        p.append(f"<g data-reveal='{_elem_reveal(x, y)}' data-item='{html.escape(_iid)}' "
                 f"data-x='{x:.3f}' data-y='{y:.3f}'>{marker}"
                 f"{label_markup}</g>")

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
        editable = cid in editable_start_ids and cid in start_pos
        sx, sy = start_pos.get(cid, (0.0, 0.0))
        edit_attrs = (
            f" data-editable-start='1' data-start-x='{sx:.3f}' data-start-y='{sy:.3f}'"
            if editable else ""
        )
        selection = (
            f"<circle class='npc-selection' r='{4.2*sc:.2f}' fill='none' "
            f"stroke='#55ffff' stroke-width='.22' stroke-dasharray='.5,.35' "
            f"style='display:none'/>" if editable else ""
        )
        p.append(f"<g class='char' data-char='{html.escape(cid)}'{edit_attrs} style='display:none'>"
                 f"<g class='char-marker'>{selection}{marker}</g>"
                 f"<title>{name}</title></g>")
    p.append("</svg>")

    frames_js = json.dumps({
        t: {c: [round(x, 2), round(y, 2)] for c, (x, y) in frames[t].items()}
        for t in turn_list})
    # Zone-boundary edges, for snapping a dragged door onto the wall it
    # actually sits in — the layout editor's only source of truth for
    # "where do zones meet," independent of the (possibly stale) Impassable
    # gap a door's y/x doesn't automatically keep in sync with.
    zone_edges_js = json.dumps([
        [verts[i][0], verts[i][1], verts[(i + 1) % len(verts)][0], verts[(i + 1) % len(verts)][1]]
        for verts in g["zones"].values() for i in range(len(verts))
    ])
    p.append("<script>")
    p.append(f"const FRAMES={frames_js};const TURNS={json.dumps(turn_list)};"
             f"const ZONE_EDGES={zone_edges_js};")
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
        # Skip the reload while the reader is actively panning/zooming/editing
        # (a recent interaction) so it doesn't yank the map out from under
        # them; the saved viewBox is restored on the reloads that do fire.
        # Edit mode alone doesn't block forever, though: if the player leaves
        # the "Edit layout" toggle on and just walks away (in-game, without
        # clicking "Done editing"), __mapArtEditing would otherwise stay true
        # for the rest of this iframe's life, permanently freezing the map
        # and everything downstream of it (SSE-driven turn state, prompts)
        # until a manual full-page refresh. Past EDIT_STALE_MS with no actual
        # editing interaction, treat it as abandoned and resume reloading.
        p.append(
            f"setInterval(function(){{if(+sl.value>=TURNS.length-1&&"
            f"(!window.__mapArtEditing||"
            f"(Date.now()-(window.__mapLastInteract||0))>60000)&&"
            f"(Date.now()-(window.__mapLastInteract||0))>2500)"
            f"{{location.reload();}}}},{int(live_refresh_secs) * 1000});")
    p.append(
        "(function(){const s=document.getElementById('map'),objs=[...document.querySelectorAll('.visual-overlay')],npcs=[...document.querySelectorAll('[data-editable-start]')],"
        "eb=document.getElementById('editArt'),ctl=document.getElementById('artctl'),saveBtn=document.getElementById('copyVisuals'),"
        "coordReadout=document.getElementById('coordReadout');"
        "if(!objs.length&&!npcs.length){eb.style.display='none';return;}let editing=false,sel=null,npcSel=null,drag=null,dirty=false;"
        "function syncTarget(o){let t=o.dataset.target;if(!t)return;let x=+o.dataset.x,y=+o.dataset.y;"
        "let matches=[...document.querySelectorAll('[data-landmark]')].filter(n=>n.dataset.landmark===t);"
        "if(!matches.length)matches=[...document.querySelectorAll('[data-item]')].filter(n=>n.dataset.item===t);"
        "matches.forEach(n=>{let ox=+n.dataset.x,oy=+n.dataset.y;"
        "n.setAttribute('transform','translate('+(x-ox)+','+(-(y-oy))+')');n.dataset.editX=x.toFixed(3);n.dataset.editY=y.toFixed(3);});}"
        "function apply(o){let x=+o.dataset.x,y=+o.dataset.y,r=+o.dataset.rotation;"
        "o.setAttribute('transform','translate('+x+','+(-y)+') rotate('+(-r)+')');"
        "let im=o.querySelector('image'),w=+o.dataset.width,h=+o.dataset.height;"
        "im.setAttribute('x',-w/2);im.setAttribute('y',-h/2);im.setAttribute('width',w);im.setAttribute('height',h);"
        "let box=o.querySelector('.visual-selection');box.setAttribute('x',-w/2);box.setAttribute('y',-h/2);box.setAttribute('width',w);box.setAttribute('height',h);syncTarget(o);}"
        "function clearPick(){if(sel)sel.querySelector('.visual-selection').style.display='none';if(npcSel)npcSel.querySelector('.npc-selection').style.display='none';sel=null;npcSel=null;}"
        "function pick(o){clearPick();sel=o;if(sel)sel.querySelector('.visual-selection').style.display='';}"
        "function pickNpc(o){clearPick();npcSel=o;if(npcSel)npcSel.querySelector('.npc-selection').style.display='';}"
        "function pt(e){let p=s.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(s.getScreenCTM().inverse());}"
        "function records(){return objs.map(o=>({id:o.dataset.visual,asset:o.dataset.asset,target:o.dataset.target,x:+o.dataset.x,y:+o.dataset.y,width:+o.dataset.width,height:+o.dataset.height,rotation:+o.dataset.rotation,layer:o.dataset.layer}));}"
        "function npcRecords(){return npcs.map(o=>({id:o.dataset.char,x:+o.dataset.startX,y:+o.dataset.startY}));}"
        "async function save(){saveBtn.textContent='Saving…';try{let r=await fetch('/map-visuals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({visuals:records(),npc_positions:npcRecords()})});"
        "if(!r.ok)throw new Error(await r.text());dirty=false;saveBtn.textContent='Saved';setTimeout(()=>saveBtn.textContent='Save layout',1200);return true;}"
        "catch(e){saveBtn.textContent='Save failed';console.error(e);return false;}}"
        "eb.onclick=async function(){window.__mapLastInteract=Date.now();if(editing&&dirty&&!(await save()))return;editing=!editing;window.__mapArtEditing=editing;"
        "eb.textContent=editing?'Done editing':'Edit layout';"
        "ctl.classList.toggle('on',editing);s.style.cursor=editing?'default':'grab';"
        "if(editing){sl.value=0;show(0);"
        "document.querySelectorAll('[data-reveal]').forEach(e=>{e.style.display='';});"
        "sl.disabled=true;objs.forEach(o=>s.appendChild(o));npcs.forEach(o=>s.appendChild(o));}"
        "else{sl.disabled=false;clearPick();show(+sl.value);}"
        "objs.forEach(o=>o.style.cursor=editing?'move':'');npcs.forEach(o=>o.style.cursor=editing?'move':'');};"
        "objs.forEach(o=>{o.addEventListener('mousedown',e=>{if(!editing)return;e.stopPropagation();pick(o);"
        "let p=pt(e);drag={kind:'visual',o:o,px:p.x,py:p.y,x:+o.dataset.x,y:+o.dataset.y};e.preventDefault();});});"
        "npcs.forEach(o=>{o.addEventListener('mousedown',e=>{if(!editing)return;e.stopPropagation();pickNpc(o);let p=pt(e);drag={kind:'npc',o:o,px:p.x,py:p.y,x:+o.dataset.startX,y:+o.dataset.startY};e.preventDefault();});});"
        # A door dropped freehand essentially never lands on the exact zone
        # boundary it needs to (any offset, however small, puts it fully on
        # one side or the other — see _entry_point_inside_zone/zone_at,
        # which have no tolerance for "meant to be on the line"). Magnetic
        # snapping to the nearest zone edge removes the guesswork instead of
        # relying on eyeballing the coordinate readout down to the wall.
        "const DOOR_SNAP_FT=1.5;"
        "function snapDoor(asset,x,y){if(!asset||asset.indexOf('door.svg')<0)return null;let best=null;"
        "for(const[x1,y1,x2,y2]of ZONE_EDGES){let ex=x2-x1,ey=y2-y1,len2=ex*ex+ey*ey;"
        "let t=len2>1e-9?((x-x1)*ex+(y-y1)*ey)/len2:0;t=Math.max(0,Math.min(1,t));"
        "let qx=x1+t*ex,qy=y1+t*ey,d=Math.hypot(x-qx,y-qy);"
        "if(!best||d<best.d)best={d:d,x:qx,y:qy,ex:ex,ey:ey};}"
        "if(!best||best.d>DOOR_SNAP_FT)return null;"
        "return{x:best.x,y:best.y,rotation:Math.abs(best.ex)>=Math.abs(best.ey)?0:90};}"
        "window.addEventListener('mousemove',e=>{if(!drag)return;window.__mapLastInteract=Date.now();"
        "let p=pt(e),x=drag.x+p.x-drag.px,y=drag.y-(p.y-drag.py);"
        "if(drag.kind==='npc'){drag.o.dataset.startX=x.toFixed(3);drag.o.dataset.startY=y.toFixed(3);drag.o.setAttribute('transform','translate('+x+','+(-y)+')');}"
        "else{let snapped=snapDoor(drag.o.dataset.asset,x,y);"
        "if(snapped){x=snapped.x;y=snapped.y;drag.o.dataset.rotation=snapped.rotation.toFixed(3);}"
        "drag.o.dataset.x=x.toFixed(3);drag.o.dataset.y=y.toFixed(3);apply(drag.o);}dirty=true;"
        "coordReadout.textContent='x: '+x.toFixed(2)+', y: '+y.toFixed(2);"
        "coordReadout.style.left=(e.clientX+14)+'px';coordReadout.style.top=(e.clientY+18)+'px';"
        "coordReadout.style.display='block';});"
        "window.addEventListener('mouseup',()=>{drag=null;coordReadout.style.display='none';});"
        "function change(kind,n){if(!sel)return;if(kind==='r')sel.dataset.rotation=(+sel.dataset.rotation+n).toFixed(3);"
        "else{sel.dataset.width=(+sel.dataset.width*n).toFixed(3);sel.dataset.height=(+sel.dataset.height*n).toFixed(3);}dirty=true;apply(sel);}"
        # Visual transforms negate authored rotation because map Y is inverted:
        # increasing the stored angle therefore turns counterclockwise on screen.
        "document.getElementById('rotL').onclick=()=>change('r',15);document.getElementById('rotR').onclick=()=>change('r',-15);"
        "document.getElementById('smaller').onclick=()=>change('s',.9);document.getElementById('larger').onclick=()=>change('s',1.1);"
        "saveBtn.onclick=save;"
        "document.getElementById('copyGeometry').onclick=async function(){let rows=['## Landmark coordinate updates','','| name | x | y |','|---|---:|---:|'];"
        "let seen=new Set();objs.forEach(o=>{let t=o.dataset.target;if(!t||seen.has(t))return;seen.add(t);rows.push('| '+t+' | '+o.dataset.x+' | '+o.dataset.y+' |');});"
        "await navigator.clipboard.writeText(rows.join('\\n'));this.textContent='Copied';setTimeout(()=>this.textContent='Copy coordinates',1200);};})();")
    p.append(
        "(function(){const s=document.getElementById('map'),edit=document.getElementById('editTerrain'),save=document.getElementById('saveTerrain'),"
        "groups=[...document.querySelectorAll('[data-route-handles]')],handles=[...document.querySelectorAll('.route-handle')];"
        "if(!groups.length){edit.style.display='none';return;}let editing=false,drag=null,dirty=false;"
        "function pt(e){let p=s.createSVGPoint();p.x=e.clientX;p.y=e.clientY;return p.matrixTransform(s.getScreenCTM().inverse());}"
        "function routeEl(name){return [...document.querySelectorAll('.terrain-route')].find(r=>r.dataset.route===name);}"
        "function redraw(name){let hs=handles.filter(h=>h.dataset.route===name).sort((a,b)=>(+a.dataset.index)-(+b.dataset.index));"
        "routeEl(name).setAttribute('points',hs.map(h=>h.getAttribute('cx')+','+h.getAttribute('cy')).join(' '));}"
        "function records(){return groups.map(g=>{let name=g.dataset.routeHandles,hs=handles.filter(h=>h.dataset.route===name).sort((a,b)=>(+a.dataset.index)-(+b.dataset.index));"
        "return{name:name,vertices:hs.map(h=>[+h.getAttribute('cx'),-(+h.getAttribute('cy'))])};});}"
        "async function persist(){save.textContent='Saving…';try{let r=await fetch('/map-routes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({routes:records()})});"
        "if(!r.ok)throw new Error(await r.text());dirty=false;save.textContent='Saved';setTimeout(()=>save.textContent='Save terrain',1200);return true;}"
        "catch(e){save.textContent='Save failed';console.error(e);return false;}}"
        "edit.onclick=async function(){window.__mapLastInteract=Date.now();if(editing&&dirty&&!(await persist()))return;editing=!editing;window.__mapArtEditing=editing;"
        "edit.textContent=editing?'Done terrain':'Edit terrain';save.style.display=editing?'':'none';document.getElementById('editArt').disabled=editing;"
        "groups.forEach(g=>g.style.display=editing?'':'none');handles.forEach(h=>h.style.cursor=editing?'move':'');};save.onclick=persist;"
        "handles.forEach(h=>h.addEventListener('mousedown',e=>{if(!editing)return;e.stopPropagation();let p=pt(e);drag={h:h,px:p.x,py:p.y,x:+h.getAttribute('cx'),y:+h.getAttribute('cy')};e.preventDefault();}));"
        "window.addEventListener('mousemove',e=>{if(!drag)return;window.__mapLastInteract=Date.now();let p=pt(e),x=drag.x+p.x-drag.px,y=drag.y+p.y-drag.py;"
        "drag.h.setAttribute('cx',x.toFixed(3));drag.h.setAttribute('cy',y.toFixed(3));redraw(drag.h.dataset.route);dirty=true;});"
        "window.addEventListener('mouseup',()=>{drag=null;});})();")
    p.append(
        "(function(){const b=document.getElementById('refreshGeo');"
        "b.onclick=async function(){b.textContent='Refreshing…';b.disabled=true;"
        # A geometry edit can move the content away from a viewport preserved
        # in sessionStorage, leaving a technically valid map entirely blank.
        # Reset to the authored full-map view before regenerating/reloading.
        "const fit=document.getElementById('fit');if(fit)fit.click();"
        "try{let r=await fetch('/refresh-geometry',{method:'POST'});"
        # The POST updates server-side scene_geometry and rewrites this same
        # map HTML file, but this already-loaded page's DOM has no way to
        # know that happened — without an explicit reload here, the button
        # looks like it did nothing even though the edit landed.
        "if(!r.ok)throw new Error(await r.text());location.reload();return;}"
        "catch(e){b.textContent='Refresh failed';b.disabled=false;"
        "setTimeout(()=>b.textContent='Refresh scene',1200);console.error(e);}};})();")
    p.append(
        "(function(){const b=document.getElementById('showDeepLandmarks');if(!b)return;"
        "b.onchange=()=>document.querySelectorAll('.deep-landmark').forEach("
        "e=>e.style.display=b.checked?'':'none');})();")
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
