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
from engine.session import run_session, _clean_spoken_output  # noqa: E402
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
            spoken = _clean_spoken_output(
                (cr.get("output") or {}).get("spoken") or "")
            if prose or spoken:
                lines.append({"cid": cr.get("character_id", "?"),
                              "prose": prose, "spoken": spoken})
        if lines:
            out.append({"turn": int(data.get("turn", 0)), "lines": lines})
    out.sort(key=lambda e: e["turn"])
    return out


def _item_icon(label: str) -> str:
    from engine.item_icons import item_icon
    return item_icon(label)


# Words that mark a possession as WORN (vs merely carried). (An "Ingested"
# bucket may join these someday.)
_WORN_KEYWORDS = (
    "armor", "mail", "plate", "cloak", "boots", "gauntlet", "helm", "helmet",
    "bracer", "bracelet", "amulet", "ring", "robe", "belt", "pendant",
    "necklace", "shield", "vestment", "circlet", "worn",
)


def _is_worn(text: str) -> bool:
    low = (text or "").lower()
    return any(k in low for k in _WORN_KEYWORDS)


def _player_inventory(cs, items: dict | None) -> dict:
    """The player's current possessions from the live character, bucketed as
    ``{"hand": [...], "worn": [...], "carried": [...]}`` (each entry {icon,
    label}). Read live so it's current even at turn 0. Wielded weapons + held
    items are in hand; armor and worn gear (by keyword) are worn; everything
    else carried — non-wielded weapons, tools, kits, picked-up scene items."""
    if cs is None:
        return {"hand": [], "worn": [], "carried": [], "purse": ""}
    char = getattr(cs, "character", None)
    weapons = list(getattr(cs, "weapons", None) or [])
    weapon_ids = {w.id for w in weapons}
    weapon_names = [w.name.lower() for w in weapons if getattr(w, "name", "")]
    wielded = set(getattr(cs, "wielded", None) or [])
    held = list(getattr(cs, "held_items", None) or [])
    held_set = set(held)
    inv = list(getattr(char, "inventory", None) or [])
    equipment = list(getattr(char, "equipment", None) or [])
    armor = getattr(cs, "armor", None)
    pack = list(getattr(cs, "pack", None) or [])
    pack_by_id = {getattr(p, "id", ""): p for p in pack}

    def item_chip(iid: str) -> dict:
        it = (items or {}).get(iid)
        if it is None:
            it = pack_by_id.get(iid)
        label = ((getattr(it, "label", "") or "").strip()
                 or (getattr(it, "name", "") or "").strip()   # e.g. bought "Bolts (20)"
                 or iid.replace("_", " "))
        return {"icon": _item_icon(label), "label": label}

    def gear_chip(text: str) -> dict:
        label = re.sub(r"\s*\([^)]*\)", "", text).strip()  # drop "(1d8 piercing)"
        return {"icon": _item_icon(label), "label": label}

    def content_chip(content_id: str, qty: int) -> dict:
        it = (items or {}).get(content_id)
        label = ((getattr(it, "label", "") or "").strip()
                 or (getattr(it, "name", "") or "").strip()
                 or content_id.replace("_", " "))
        if qty > 1:
            label = f"{label} ×{qty}"
        return {"icon": _item_icon(label), "label": label}

    hand: list[dict] = []
    worn: list[dict] = []
    carried: list[dict] = []
    seen_content_ids: set[str] = set()
    for w in weapons:                      # wielded -> in hand; else carried
        chip = {"icon": _item_icon(w.name), "label": w.name}
        (hand if w.id in wielded else carried).append(chip)
    for iid in held:                       # held non-weapon gear (e.g. a torch)
        hand.append(item_chip(iid))
    worn_labels: set[str] = set()
    if armor is not None and getattr(armor, "name", ""):  # structured armor
        worn.append({"icon": _item_icon(armor.name), "label": armor.name})
        worn_labels.add(armor.name.lower())
    for iid in inv:                        # carried scene gear not in hand
        if iid in weapon_ids or iid in held_set:
            continue                       # already shown as a weapon / in hand
        carried.append(item_chip(iid))
    # Free-text possessions from the character sheet: worn (armor, trinkets) vs
    # carried (tools, kits). Skip entries that just restate a weapon, or an
    # armor already covered by the structured armor above.
    for entry in equipment:
        low = entry.lower()
        if any(wn and wn in low for wn in weapon_names):
            continue
        chip = gear_chip(entry)
        if chip["label"].lower() in worn_labels:
            continue
        (worn if _is_worn(entry) else carried).append(chip)
    inv_set = set(inv)
    for prov in pack:   # food, drink, tools, wearables
        from models.thing import WORN
        if getattr(prov, "id", "") in held_set:
            continue
        # A bought/taken item lives in BOTH char.inventory (rendered by the `inv`
        # loop above) and the pack (so use/eat/drink can reach it). Render it once
        # -- skip here if the `inv` loop already showed it.
        if getattr(prov, "id", "") in inv_set:
            continue
        parent_container_id = getattr(prov, "parent_container_id", "")
        if parent_container_id and parent_container_id not in held_set:
            continue
        if parent_container_id:
            seen_content_ids.add(getattr(prov, "id", ""))
        label = getattr(prov, "label", None) or getattr(prov, "id", "")
        qty = int(getattr(prov, "quantity", 1) or 1)
        if qty > 1:
            label = f"{label} ×{qty}"
        chip = {"icon": _item_icon(label), "label": label}
        state = getattr(getattr(prov, "carry", None), "location", "")
        (worn if state == WORN else carried).append(chip)

    # Held scene-item containers may author their own contents directly; surface
    # those contents only while the container is in hand, matching the pack rule.
    for iid in held:
        it = (items or {}).get(iid)
        for content_id, qty in (getattr(it, "contents", None) or []):
            if content_id in seen_content_ids:
                continue
            seen_content_ids.add(content_id)
            carried.append(content_chip(content_id, int(qty or 1)))
    from models.currency import format_coins
    purse_cp = getattr(char, "purse_cp", 0) or 0
    return {"hand": hand, "worn": worn, "carried": carried,
            "purse": format_coins(purse_cp) if purse_cp else ""}


_NAME_TITLES = {"sister", "brother", "father", "mother", "lord", "lady",
                "the", "of", "ser", "sir", "captain"}


def _rt(app: web.Application) -> dict:
    """Mutable runtime state container (safe to mutate post-startup)."""
    return app["runtime"]


def _highlight_names(characters) -> list[str]:
    """Names of every player and monster to highlight in the log — each
    character's id tokens plus the distinctive words of its name (titles
    dropped). Lower-cased and de-duped; matched case-insensitively client-side,
    longest first so multi-word names (e.g. "giant spider") win over a token."""
    names: set[str] = set()
    for cid, cs in (characters or {}).items():
        names.add(cid.replace("_", " "))
        for tok in cid.split("_"):
            if len(tok) >= 4:
                names.add(tok)
        nm = getattr(getattr(cs, "character", None), "name", "") or ""
        for tok in nm.replace(",", " ").split():
            t = tok.strip()
            if len(t) >= 4 and t.lower() not in _NAME_TITLES:
                names.add(t)
    return sorted({n.lower() for n in names if n.strip()}, key=len, reverse=True)


async def handle_index(request: web.Request) -> web.Response:
    rt = _rt(request.app)
    scene = rt["scene"].replace("_", " ").title()
    names = _highlight_names(rt["config"].characters)
    # Build the highlight regex source in Python (re.escape + json.dumps handle
    # all escaping) so the page JS needs no fragile backslash literals.
    pattern = (r"\b(" + "|".join(re.escape(n) for n in names) + r")\b") if names else ""
    page = (_PAGE.replace("__TITLE__", scene)
            .replace("__NAME_PATTERN__", json.dumps(pattern)))
    # no-cache so a new run never serves a stale page from a previous version
    # (e.g. an older inventory bar that didn't know the Worn/Carried groups).
    return web.Response(text=page, content_type="text/html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


async def handle_map(request: web.Request) -> web.Response:
    # no-cache so the iframe's periodic reload always gets the freshly-rendered
    # map (with the latest mid-turn positions), never a stale cached copy.
    headers = {"Cache-Control": "no-cache, no-store, must-revalidate"}
    rt = _rt(request.app)
    f = request.app["checkpoint_dir"] / f"{rt['scene']}_map.html"
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
    sent: set[int] = set()
    last_inv: dict | None = None
    last_turn_active: bool | None = None
    error_reported = False
    try:
        while True:
            cfg = _rt(request.app)["config"]
            items = cfg.items
            player_cs = cfg.characters.get(player)
            for msg in web_transport.drain_outbound(player):
                await resp.write(
                    f"data: {json.dumps({'type': 'dm', 'text': msg})}\n\n".encode())
            # Whether it's the player's turn — reported on change so the browser
            # can enable/disable its input. A fresh connection starts at None, so
            # a page reload mid-turn always re-receives the current state.
            active = web_transport.is_awaiting(player)
            if active != last_turn_active:
                last_turn_active = active
                await resp.write(
                    f"data: {json.dumps({'type': 'turnstate', 'active': active})}\n\n"
                    .encode())
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

            # If the background session task crashed, surface it in-band so the
            # browser does not look frozen with input disabled.
            task = request.app.get("session_task")
            if task is not None and task.done() and not error_reported:
                err = task.exception()
                if err is not None:
                    error_reported = True
                    await resp.write(
                        f"data: {json.dumps({'type': 'dm', 'text': f'[web_play error] {err}'})}\n\n".encode())
                    await resp.write(
                        f"data: {json.dumps({'type': 'turnstate', 'active': False})}\n\n".encode())
            await resp.write(b": keep-alive\n\n")
            await asyncio.sleep(0.8)
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    return resp


def _render_map(app: web.Application, live_positions: dict | None = None) -> None:
    """(Re)write the scene map. ``live_positions`` stamps the latest frame with
    mid-turn positions so the map shows where everyone is now. Best-effort."""
    rt = _rt(app)
    cfg, cd, scene = rt["config"], app["checkpoint_dir"], rt["scene"]
    # Turn-0 (and every) map seeds character markers from scene-authored
    # placement, not the GEOMETRY: geometry is a pure stage now.
    sg = getattr(cfg, "scene_geometry", None)
    start_positions = (
        {cid: (p.x, p.y) for cid, p in sg.starting_positions.items()}
        if sg is not None else None
    )
    try:
        render_turn_slider_html(
            cfg.geometry_path, cd / f"{scene}_map.html",
            snapshot_dir=cd, title=scene.replace("_", " ").title(),
            # Refresh faster than scene_runner's batch maps so per-initiative
            # moves are visible while watching live play.
            live_refresh_secs=4, start_characters=rt["start_characters"],
            item_details=cfg.items or None, live_positions=live_positions,
            start_positions=start_positions, scene_geometry=sg)
    except Exception:  # noqa: BLE001 — map is best-effort
        pass


async def _session_task(app: web.Application) -> None:
    rt = _rt(app)
    cfg, cd = rt["config"], app["checkpoint_dir"]

    def _on_character_acted(cid: str, turn: int, positions: dict, cr) -> None:
        # Runs synchronously inside the turn loop's own window, right after each
        # character acts — so the map and the log update per-initiative instead
        # of only at end of turn (a separate async task gets starved by the busy
        # session loop). Map first, then stream this character's narration.
        web_transport.publish_positions(positions)
        _render_map(app, live_positions=positions)
        prose = (getattr(cr.narration, "prose", "") or "").strip()
        spoken = _clean_spoken_output(
            getattr(cr.output, "spoken", "") or "")
        if prose or spoken:
            web_transport.publish_action(
                {"turn": turn, "cid": cid, "prose": prose, "spoken": spoken})

    def _on_scene_transition(scene_name: str, new_cfg) -> None:
        rt["scene"] = scene_name
        rt["config"] = new_cfg
        rt["start_characters"] = [
            cid for cid, cs in new_cfg.characters.items()
            if (getattr(cs, "activation", "always") or "always") == "always"
        ]
        _render_map(app)

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
        on_scene_transition=_on_scene_transition,
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
.cols{display:grid;grid-template-columns:48% 8px minmax(320px,1fr);}
.log{overflow-y:auto;padding:10px 14px;border-right:1px solid #2a2a33;min-width:260px;}
.split{cursor:col-resize;background:#1a1a22;border-left:1px solid #2a2a33;border-right:1px solid #2a2a33;}
.split:hover{background:#252532;}
.map{min-width:320px;}.map iframe{width:100%;height:100%;border:0;background:#0e0e12;}
.turn{margin:0 0 12px;}.turn h3{margin:0 0 4px;font-size:12px;color:#8a8a99;
  letter-spacing:.05em;text-transform:uppercase;}
.line{margin:0 0 6px;font-size:14px;line-height:1.45;}
.cid{font-weight:700;color:#9ecbff;}.spoken{color:#cfe8c0;font-style:italic;}
.name{font-weight:700;color:#9ecbff;}
.dm{margin:0 0 12px;padding:8px 10px;background:#15212e;border-left:3px solid #4a90d9;
  white-space:pre-wrap;font-size:13px;line-height:1.4;border-radius:3px;}
form{display:flex;gap:8px;padding:8px 14px;border-top:1px solid #2a2a33;}
input{flex:1;font:inherit;padding:7px 10px;background:#1a1a22;color:#e6e6e6;
  border:1px solid #3a3a44;border-radius:4px;}
input:disabled{opacity:.5;cursor:not-allowed;}
button{font:inherit;padding:7px 14px;cursor:pointer;}
button:disabled{opacity:.5;cursor:not-allowed;}
.status{padding:5px 14px;font-size:12px;letter-spacing:.03em;color:#8a8a99;
  border-top:1px solid #2a2a33;transition:color .15s,background .15s;}
.status.active{color:#7fd18c;background:#132015;font-weight:600;}
.inv{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:6px 14px;
  border-top:1px solid #2a2a33;font-size:13px;min-height:22px;}
.inv .grp{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
.inv .lbl{color:#8a8a99;font-size:11px;text-transform:uppercase;letter-spacing:.05em;}
.chip{display:inline-flex;gap:5px;align-items:center;padding:2px 9px;border-radius:12px;
  background:#1a1a22;border:1px solid #3a3a44;}
.chip.hand{border-color:#4a90d9;background:#15212e;}
.chip.worn{border-color:#7a6a3a;background:#1e1a10;}
.chip.coin{border-color:#c9a227;background:#211d0f;color:#f0d477;font-weight:600;}
.chip.empty{opacity:.8;font-style:italic;}
.chip .ic{font-size:15px;line-height:1;}
</style></head><body>
<header>__TITLE__ — you are playing in the browser</header>
<div class='cols' id='cols'>
  <div class='log' id='log'></div>
    <div class='split' id='split' title='Drag to resize narration/map panes'></div>
  <div class='map'><iframe id='mapframe' src='/map'></iframe></div>
</div>
<div class='inv' id='inv'>
    <span class='grp'><span class='lbl'>In hand</span>
        <span class='chip hand empty'>Nothing in hand</span></span>
</div>
<div class='status' id='turnstatus'>Waiting for your turn…</div>
<form id='f'><input id='in' autocomplete='off' disabled
  placeholder='Waiting for your turn…'>
  <button id='send' type='submit' disabled>Send</button></form>
<script>
const log=document.getElementById('log');
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function atBottom(){return log.scrollHeight-log.scrollTop-log.clientHeight<140;}
function add(node){const b=atBottom();log.appendChild(node);if(b)log.scrollTop=log.scrollHeight;}
const es=new EventSource('/events');
const turnBlocks={};
const NAME_PATTERN=__NAME_PATTERN__;
const NAME_RE=NAME_PATTERN?new RegExp(NAME_PATTERN,'gi'):null;
function hi(s){return NAME_RE?s.replace(NAME_RE,'<span class="name">$1</span>'):s;}
function qhi(s){return esc(s);}
function speechKey(s){return (s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
function nameOf(cid){return (cid||'').split('_').map(w=>w?w[0].toUpperCase()+w.slice(1):w).join(' ');}
// One unified line per character:  "spoken" narration  — every player/monster
// name is highlighted, and the narration already opens with the actor's name,
// so no separate name prefix is needed. (A spoken-only line, with no narration
// to name the speaker, still gets a name prefix so the quote is attributed.)
function lineHTML(l){
  let body='';
  const repeated=l.spoken&&l.prose&&speechKey(l.prose).includes(speechKey(l.spoken));
  if(l.spoken&&!repeated)body+='<span class="spoken">“'+qhi(l.spoken)+'”</span> ';
  if(l.prose){
    // Mark quotation spans while this is still plain escaped text. Doing this
    // after hi() would mistake class="name" in its generated markup for speech.
    let prose=esc(l.prose);
    prose=prose.replace(/([“"])([^“”"]+)([”"])/g,'<span class="spoken">$1$2$3</span>');
    prose=hi(prose);
    body+=prose;
  }
  else if(l.spoken)body='<span class="name">'+esc(nameOf(l.cid))+'</span>: '+body;
  return '<p class="line">'+body+'</p>';
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
    // A DM message (turn prompt or an answer to a question) means it's our move.
    setTurn(true);
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
  }else if(m.type==='turnstate'){
    // Authoritative turn state from the server (also fires on reconnect), so
    // the input line settles correctly even if a one-shot 'dm' event was missed.
    setTurn(m.active);
  }
};
function renderInv(m){
  const inv=document.getElementById('inv');
  const chips=(arr,cls)=>arr.map(x=>'<span class="chip '+cls+'"><span class="ic">'
    +x.icon+'</span>'+esc(x.label)+'</span>').join('');
    const grp=(label,arr,cls,opts={})=>{
        const items=(arr&&arr.length)?chips(arr,cls):'';
        const empty=(opts.emptyText)
            ?'<span class="chip '+cls+' empty">'+esc(opts.emptyText)+'</span>':'';
        if(!items && !empty && !opts.always)return '';
        return '<span class="grp"><span class="lbl">'+label+'</span>'+(items||empty)+'</span>';
    };
    const coin=grp('Coin',(m.purse?[{icon:'🪙',label:m.purse}]:[]),'coin');
    const h=coin
        +grp('In hand',m.hand,'hand',{always:true,emptyText:'Nothing in hand'})
        +grp('Worn',m.worn,'worn')
    +grp('Carried',m.carried,'carried');  // (+ grp('Ingested',m.ingested,...) someday)
  inv.innerHTML=h||'<span class="lbl">No possessions yet</span>';
}
const f=document.getElementById('f'),inp=document.getElementById('in'),
      sendBtn=document.getElementById('send'),
      turnStatus=document.getElementById('turnstatus');
const cols=document.getElementById('cols'),split=document.getElementById('split');
const SPLIT_KEY='driftmoor:webplay:split:px';
function setSplit(px){
    const w=cols.clientWidth||1200;
    const minL=260, minR=320;
    const clamped=Math.max(minL,Math.min(w-minR,Math.round(px)));
    cols.style.gridTemplateColumns=clamped+'px 8px minmax('+minR+'px,1fr)';
    try{localStorage.setItem(SPLIT_KEY,String(clamped));}catch(_){}}
try{
    const saved=parseInt(localStorage.getItem(SPLIT_KEY)||'',10);
    if(Number.isFinite(saved))setSplit(saved);
}catch(_){}
let drag=false;
split.addEventListener('pointerdown',ev=>{
    drag=true;split.setPointerCapture(ev.pointerId);ev.preventDefault();
});
split.addEventListener('pointermove',ev=>{
    if(!drag)return;
    const r=cols.getBoundingClientRect();
    setSplit(ev.clientX-r.left);
});
split.addEventListener('pointerup',()=>{drag=false;});
split.addEventListener('pointercancel',()=>{drag=false;});
window.addEventListener('keydown',ev=>{
    if(ev.key==='Escape'&&drag){drag=false;}
});
window.addEventListener('message',ev=>{
    const m=ev.data||{};
    if(!m||m.type!=='driftmoor-map-dblclick')return;
    if(inp.disabled)return; // only draft moves during your active turn
    const x=Number(m.x),y=Number(m.y);
    if(!Number.isFinite(x)||!Number.isFinite(y))return;
    const pt='['+x.toFixed(0)+','+y.toFixed(0)+']';
    const cmd='I move to '+pt;
    const prev=inp.value.trim();
    if(!prev)inp.value=cmd;
    else if(m.shift)inp.value=prev+' -> '+pt;
    else if(/I move to \\[[^\\]]+\\]/i.test(prev))
        inp.value=prev.replace(/I move to \\[[^\\]]+\\]/i,cmd);
    else inp.value=prev+(/[.!?]\\s*$/.test(prev)?' ':'. ')+cmd;
    inp.focus();
    inp.setSelectionRange(inp.value.length,inp.value.length);
});
// Single source of truth for the input's live/idle state. A 'dm' SSE event
// (turn prompt or DM answer) flips us live; submitting an intent flips us idle
// until the next prompt arrives, so out-of-turn input is impossible.
function setTurn(active){
  inp.disabled=!active;sendBtn.disabled=!active;
  turnStatus.className=active?'status active':'status';
  turnStatus.textContent=active
    ?'● Your turn — state your intent, or ask the DM a question':'Waiting for your turn…';
  inp.placeholder=active
    ?'State your intent (or ask the DM a question)…':'Waiting for your turn…';
  if(active)inp.focus();
}
f.addEventListener('submit',async ev=>{
  ev.preventDefault();if(inp.disabled)return;const t=inp.value.trim();if(!t)return;
  inp.value='';setTurn(false);
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


def _build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Driftmoor web play")
    ap.add_argument("scene", nargs="?", default="echoing_caverns")
    ap.add_argument("--player", default="gilthaness")
    ap.add_argument("--turns", type=int, default=None)
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Interface to bind (default: 127.0.0.1, local only). "
            "Use 0.0.0.0 only on a trusted private network."
        ),
    )
    return ap


def main():
    args = _build_arg_parser().parse_args()

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
    app["runtime"] = {
        "config": cfg,
        "scene": args.scene,
    }
    app["player"] = args.player
    app["checkpoint_dir"] = checkpoint_dir
    app["turns"] = args.turns or cfg.default_turns or 40
    # Party = characters active from turn 1; only these seed the turn-0 map, so
    # dormant creatures (e.g. a lurking spider) stay fogged until discovered.
    app["runtime"]["start_characters"] = [
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
    display_host = "localhost" if args.host in {"127.0.0.1", "::1"} else args.host
    print(f"Open http://{display_host}:{args.port}/")
    if args.host not in {"127.0.0.1", "::1", "localhost"}:
        print(
            "WARNING: web_play has no application authentication. "
            "Bind beyond localhost only on a trusted private network."
        )
    web.run_app(app, host=args.host, port=args.port, print=None)


if __name__ == "__main__":
    main()
