"""Driftmoor web play — play a scene in the browser (Phase 2, replaces Telegram).

Runs a scene in-process with the human player's I/O bridged to a web page via the
web transport: a streaming narration log and the live fog-of-war map, with an
input box for stating intent (and asking the DM questions). NPCs run on their
LLMs as usual.

    python web_play.py [SCENE] [--player gilthaness] [--turns N] [--port 8080]

Needs the scene's model backend reachable (e.g. local Ollama for gemma4), same
as run_scene.py. Starts a fresh run each launch.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

from env_boot import load_project_dotenv

load_project_dotenv()  # provider keys / env, same as run_scene

from engine.md_loader import configure_from_md          # noqa: E402
from engine.session import run_session                  # noqa: E402
from engine.map_renderer import render_turn_slider_html  # noqa: E402
from engine import web_transport                         # noqa: E402


def _turn_entries(checkpoint_dir: Path) -> list[dict]:
    """Per-turn narration so far: {turn, lines:[{cid, prose, spoken}]}."""
    out: list[dict] = []
    for f in checkpoint_dir.glob("day1_*.json"):
        if f.stem.endswith("transcript"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        lines = []
        for cr in data.get("character_results", []):
            prose = ((cr.get("narration") or {}).get("prose") or "").strip()
            spoken = ((cr.get("output") or {}).get("spoken") or "").strip()
            if spoken.lower() in {"", "(none)", "(silent)", "(silence)"}:
                spoken = ""
            if prose or spoken:
                lines.append({"cid": cr.get("character_id", "?"),
                              "prose": prose, "spoken": spoken})
        if lines:
            out.append({"turn": int(data.get("turn", 0)), "lines": lines})
    out.sort(key=lambda e: e["turn"])
    return out


# Keyword -> emoji "icon" for an item, matched against its label.
_ITEM_ICONS = (
    ("torch", "🔥"), ("crossbow", "🏹"), ("bow", "🏹"), ("dagger", "🗡️"),
    ("rapier", "🗡️"), ("sword", "🗡️"), ("blade", "🗡️"), ("axe", "🪓"),
    ("mace", "🔨"), ("hammer", "🔨"), ("shield", "🛡️"), ("staff", "🪄"),
    ("wand", "🪄"), ("potion", "🧪"), ("vial", "🧪"), ("scroll", "📜"),
    ("key", "🗝️"), ("gem", "💎"), ("shard", "💎"), ("crystal", "💎"),
    ("coin", "🪙"), ("gold", "🪙"), ("book", "📖"), ("tome", "📖"),
    ("rope", "🪢"), ("bone", "🦴"), ("skull", "💀"), ("ring", "💍"),
    ("pack", "🎒"), ("bag", "🎒"), ("chalk", "✏️"), ("charcoal", "✏️"),
    ("armor", "🛡️"), ("leather", "🛡️"), ("tools", "🛠️"), ("kit", "🧰"),
    ("bracelet", "💍"), ("amulet", "🔱"), ("cloak", "🧥"), ("boots", "🥾"),
)


def _item_icon(label: str) -> str:
    low = (label or "").lower()
    for kw, icon in _ITEM_ICONS:
        if kw in low:
            return icon
    return "📦"


def _player_inventory(cs, items: dict | None) -> dict:
    """The player's current possessions from the live character, split into
    what's in hand vs in the pack: {"hand": [...], "pack": [...]} where each
    entry is {icon, label}. Covers the character's own kit (weapons) AND any
    picked-up scene gear — read live so it's current even at turn 0 (before any
    checkpoint exists). Weapons in ``wielded`` and items in ``held_items`` are
    in hand; everything else carried is in the pack."""
    if cs is None:
        return {"hand": [], "pack": []}
    char = getattr(cs, "character", None)
    weapons = list(getattr(cs, "weapons", None) or [])
    weapon_ids = {w.id for w in weapons}
    weapon_names = [w.name.lower() for w in weapons if getattr(w, "name", "")]
    wielded = set(getattr(cs, "wielded", None) or [])
    held = list(getattr(cs, "held_items", None) or [])
    held_set = set(held)
    inv = list(getattr(char, "inventory", None) or [])
    equipment = list(getattr(char, "equipment", None) or [])

    def item_chip(iid: str) -> dict:
        it = (items or {}).get(iid)
        label = (getattr(it, "label", "") or "").strip() or iid.replace("_", " ")
        return {"icon": _item_icon(label), "label": label}

    def gear_chip(text: str) -> dict:
        label = re.sub(r"\s*\([^)]*\)", "", text).strip()  # drop "(1d8 piercing)"
        return {"icon": _item_icon(label), "label": label}

    hand: list[dict] = []
    pack: list[dict] = []
    for w in weapons:
        chip = {"icon": _item_icon(w.name), "label": w.name}
        (hand if w.id in wielded else pack).append(chip)
    for iid in held:                       # held non-weapon gear (e.g. a torch)
        hand.append(item_chip(iid))
    for iid in inv:                        # carried scene gear not in hand
        if iid in weapon_ids or iid in held_set:
            continue                       # already shown as a weapon / in hand
        pack.append(item_chip(iid))
    # Free-text possessions from the character sheet (armor, tools, kits,
    # trinkets). Skip entries that just restate a weapon already listed.
    for entry in equipment:
        low = entry.lower()
        if any(wn and wn in low for wn in weapon_names):
            continue
        pack.append(gear_chip(entry))
    return {"hand": hand, "pack": pack}


async def handle_index(request: web.Request) -> web.Response:
    scene = request.app["scene"].replace("_", " ").title()
    return web.Response(text=_PAGE.replace("__TITLE__", scene),
                        content_type="text/html")


async def handle_map(request: web.Request) -> web.Response:
    # no-cache so the iframe's periodic reload always gets the freshly-rendered
    # map (with the latest mid-turn positions), never a stale cached copy.
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    f = request.app["checkpoint_dir"] / f"{request.app['scene']}_map.html"
    if not f.exists():
        return web.Response(text="<p>No map yet — waiting for the first turn…</p>",
                            content_type="text/html", headers=headers)
    return web.Response(text=f.read_text(encoding="utf-8"),
                        content_type="text/html", headers=headers)


async def handle_input(request: web.Request) -> web.Response:
    data = await request.json()
    text = (data.get("text") or "").strip()
    if text:
        web_transport.submit_inbound(request.app["player"], text)
    return web.json_response({"ok": True})


async def handle_events(request: web.Request) -> web.StreamResponse:
    """SSE: DM/prompt lines (from the outbound queue) interleaved with per-turn
    narration (from the checkpoints)."""
    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    })
    await resp.prepare(request)
    cd, player = request.app["checkpoint_dir"], request.app["player"]
    cfg = request.app["config"]
    items = cfg.items
    player_cs = cfg.characters.get(player)
    sent: set[int] = set()
    last_inv: dict | None = None
    try:
        while True:
            for msg in web_transport.drain_outbound(player):
                await resp.write(
                    f"data: {json.dumps({'type': 'dm', 'text': msg})}\n\n".encode())
            # Live per-character narration as the turn unfolds (progress before
            # the turn's authoritative checkpoint lands below).
            for act in web_transport.drain_actions():
                act["type"] = "action"
                await resp.write(f"data: {json.dumps(act)}\n\n".encode())
            for entry in _turn_entries(cd):
                if entry["turn"] in sent:
                    continue
                sent.add(entry["turn"])
                entry["type"] = "turn"
                await resp.write(f"data: {json.dumps(entry)}\n\n".encode())
            inv = _player_inventory(player_cs, items)
            if inv != last_inv:
                last_inv = inv
                await resp.write(
                    f"data: {json.dumps({'type': 'inventory', **inv})}\n\n".encode())
            await resp.write(b": keep-alive\n\n")
            await asyncio.sleep(0.8)
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    return resp


def _render_map(app: web.Application, live_positions: dict | None = None) -> None:
    """(Re)write the scene map. ``live_positions`` stamps the latest frame with
    mid-turn positions so the map shows where everyone is now. Best-effort."""
    cfg, cd, scene = app["config"], app["checkpoint_dir"], app["scene"]
    try:
        render_turn_slider_html(
            cfg.geometry_path, cd / f"{scene}_map.html",
            snapshot_dir=cd, title=scene.replace("_", " ").title(),
            # Refresh faster than scene_runner's batch maps so per-initiative
            # moves are visible while watching live play.
            live_refresh_secs=4, start_characters=app["start_characters"],
            item_details=cfg.items or None, live_positions=live_positions)
    except Exception:  # noqa: BLE001 — map is best-effort
        pass


async def _session_task(app: web.Application) -> None:
    cfg, cd = app["config"], app["checkpoint_dir"]

    def _on_character_acted(cid: str, turn: int, positions: dict, cr) -> None:
        # Runs synchronously inside the turn loop's own window, right after each
        # character acts — so the map and the log update per-initiative instead
        # of only at end of turn (a separate async task gets starved by the busy
        # session loop). Map first, then stream this character's narration.
        web_transport.publish_positions(positions)
        _render_map(app, live_positions=positions)
        prose = (getattr(cr.narration, "prose", "") or "").strip()
        spoken = (getattr(cr.output, "spoken", "") or "").strip()
        if spoken.lower() in {"", "(none)", "(silent)", "(silence)"}:
            spoken = ""
        if prose or spoken:
            web_transport.publish_action(
                {"turn": turn, "cid": cid, "prose": prose, "spoken": spoken})

    await run_session(
        cfg.characters, cfg.roles, num_turns=app["turns"],
        game_state_summary=cfg.game_state_summary,
        geometry_summary=cfg.geometry_summary,
        scene_geometry=cfg.scene_geometry,
        items=cfg.items or None, puzzles=cfg.puzzles,
        checkpoint_dir=cd, game_time=cfg.game_time,
        character_pronouns=cfg.character_pronouns or None,
        on_turn=lambda _tr: _render_map(app),
        on_character_acted=_on_character_acted,
    )


async def _on_startup(app: web.Application) -> None:
    # Render an initial (turn 0) map from the GEOMETRY starting positions so the
    # browser shows the party's starting layout before the first turn lands.
    _render_map(app)
    app["session_task"] = asyncio.create_task(_session_task(app))


async def _on_cleanup(app: web.Application) -> None:
    task = app.get("session_task")
    if task is not None:
        task.cancel()


_PAGE = """<!doctype html><html><head><meta charset='utf-8'>
<title>__TITLE__ — Driftmoor</title><style>
:root{color-scheme:dark;}
body{margin:0;font-family:ui-sans-serif,system-ui,sans-serif;background:#0e0e12;color:#e6e6e6;
  display:flex;flex-direction:column;height:100vh;}
header{padding:8px 14px;font-size:15px;font-weight:700;border-bottom:1px solid #2a2a33;}
.cols{display:flex;flex:1;min-height:0;}
.log{flex:1;overflow-y:auto;padding:10px 14px;border-right:1px solid #2a2a33;}
.map{flex:1.3;}.map iframe{width:100%;height:100%;border:0;background:#0e0e12;}
.turn{margin:0 0 12px;}.turn h3{margin:0 0 4px;font-size:12px;color:#8a8a99;
  letter-spacing:.05em;text-transform:uppercase;}
.line{margin:0 0 6px;font-size:14px;line-height:1.45;}
.cid{font-weight:700;color:#9ecbff;}.spoken{color:#cfe8c0;font-style:italic;}
.dm{margin:0 0 12px;padding:8px 10px;background:#15212e;border-left:3px solid #4a90d9;
  white-space:pre-wrap;font-size:13px;line-height:1.4;border-radius:3px;}
form{display:flex;gap:8px;padding:8px 14px;border-top:1px solid #2a2a33;}
input{flex:1;font:inherit;padding:7px 10px;background:#1a1a22;color:#e6e6e6;
  border:1px solid #3a3a44;border-radius:4px;}
button{font:inherit;padding:7px 14px;cursor:pointer;}
.inv{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:6px 14px;
  border-top:1px solid #2a2a33;font-size:13px;min-height:22px;}
.inv .grp{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
.inv .lbl{color:#8a8a99;font-size:11px;text-transform:uppercase;letter-spacing:.05em;}
.chip{display:inline-flex;gap:5px;align-items:center;padding:2px 9px;border-radius:12px;
  background:#1a1a22;border:1px solid #3a3a44;}
.chip.hand{border-color:#4a90d9;background:#15212e;}
.chip .ic{font-size:15px;line-height:1;}
</style></head><body>
<header>__TITLE__ — you are playing in the browser</header>
<div class='cols'>
  <div class='log' id='log'></div>
  <div class='map'><iframe id='mapframe' src='/map'></iframe></div>
</div>
<div class='inv' id='inv'><span class='lbl'>No possessions yet</span></div>
<form id='f'><input id='in' autocomplete='off'
  placeholder='State your intent (or ask the DM a question)…' autofocus>
  <button type='submit'>Send</button></form>
<script>
const log=document.getElementById('log');
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function atBottom(){return log.scrollHeight-log.scrollTop-log.clientHeight<140;}
function add(node){const b=atBottom();log.appendChild(node);if(b)log.scrollTop=log.scrollHeight;}
const es=new EventSource('/events');
const turnBlocks={};
function lineHTML(l){
  let h='';
  if(l.spoken)h+='<p class="line"><span class="cid">'+esc(l.cid)+'</span>: <span class="spoken">“'+esc(l.spoken)+'”</span></p>';
  if(l.prose)h+='<p class="line">'+esc(l.prose)+'</p>';
  return h;
}
function turnBlock(t){
  let b=turnBlocks[t];
  if(!b){b=document.createElement('div');b.className='turn';
    b.innerHTML='<h3>Turn '+t+'</h3>';add(b);turnBlocks[t]=b;}
  return b;
}
es.onmessage=e=>{
  const m=JSON.parse(e.data);
  if(m.type==='dm'){
    const d=document.createElement('div');d.className='dm';d.textContent=m.text;add(d);
  }else if(m.type==='action'){
    // Live per-character narration: append to its turn block as it happens.
    const b=turnBlock(m.turn);const at=atBottom();
    b.insertAdjacentHTML('beforeend',lineHTML(m));
    if(at)log.scrollTop=log.scrollHeight;
  }else if(m.type==='turn'){
    // Authoritative end-of-turn record: replace the block built live (also the
    // sole source on reconnect/replay), so nothing is duplicated.
    const b=turnBlock(m.turn);
    b.innerHTML='<h3>Turn '+m.turn+'</h3>'+m.lines.map(lineHTML).join('');
  }else if(m.type==='inventory'){
    renderInv(m);
  }
};
function renderInv(m){
  const inv=document.getElementById('inv');
  const chips=(arr,cls)=>arr.map(x=>'<span class="chip '+cls+'"><span class="ic">'
    +x.icon+'</span>'+esc(x.label)+'</span>').join('');
  let h='';
  if(m.hand&&m.hand.length)h+='<span class="grp"><span class="lbl">In hand</span>'+chips(m.hand,'hand')+'</span>';
  if(m.pack&&m.pack.length)h+='<span class="grp"><span class="lbl">Pack</span>'+chips(m.pack,'pack')+'</span>';
  inv.innerHTML=h||'<span class="lbl">No possessions yet</span>';
}
const f=document.getElementById('f'),inp=document.getElementById('in');
f.addEventListener('submit',async ev=>{
  ev.preventDefault();const t=inp.value.trim();if(!t)return;inp.value='';
  const e=document.createElement('div');e.className='line';
  e.innerHTML='<span class="cid">you</span>: '+esc(t);add(e);
  await fetch('/input',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({text:t})});
});
// The map reloads itself (only while parked on the latest turn) via its own
// live-refresh; don't force-reload the iframe here, or it interrupts Play and
// manual scrubbing through past turns.
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Driftmoor web play")
    ap.add_argument("scene", nargs="?", default="echoing_caverns")
    ap.add_argument("--player", default="gilthaness")
    ap.add_argument("--turns", type=int, default=None)
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()

    cfg = configure_from_md(Path("scenes") / f"{args.scene}.md")
    if args.player not in cfg.characters:
        raise SystemExit(
            f"No character '{args.player}' in {args.scene}. "
            f"Choose from: {', '.join(cfg.characters)}")
    cfg.characters[args.player].player_transport = "web"
    web_transport.reset(args.player)

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
    checkpoint_dir = Path("runtime/state") / f"{stamp}__web__" / args.scene
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    app = web.Application()
    app["config"] = cfg
    app["scene"] = args.scene
    app["player"] = args.player
    app["checkpoint_dir"] = checkpoint_dir
    app["turns"] = args.turns or cfg.default_turns or 40
    # Party = characters active from turn 1; only these seed the turn-0 map, so
    # dormant creatures (e.g. a lurking spider) stay fogged until discovered.
    app["start_characters"] = [
        cid for cid, cs in cfg.characters.items()
        if (getattr(cs, "activation", "always") or "always") == "always"
    ]
    app.add_routes([
        web.get("/", handle_index),
        web.get("/map", handle_map),
        web.get("/events", handle_events),
        web.post("/input", handle_input),
    ])
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    print(f"Playing {args.scene} as {args.player} -> {checkpoint_dir}")
    print(f"Open http://localhost:{args.port}/")
    web.run_app(app, host="0.0.0.0", port=args.port, print=None)


if __name__ == "__main__":
    main()
