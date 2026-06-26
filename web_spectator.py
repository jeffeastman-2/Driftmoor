"""Driftmoor web spectator — a big-screen, browsable view of a running scene.

Phase 1 of the web UI (read-only): tails a run's checkpoint directory and serves
a single page with the live fog-of-war map beside a streaming narration log — no
engine changes, no Telegram. Point it at a run while it plays (the map and log
update live) or after (full history).

    python web_spectator.py [CHECKPOINT_DIR] [--port 8080]

CHECKPOINT_DIR defaults to the most recent run under runtime/state/. The map it
shows is the ``<scene>_map.html`` that scene_runner regenerates each turn.
"""
from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
from pathlib import Path

from aiohttp import web


def _latest_run() -> Path | None:
    dirs = [Path(p) for p in glob.glob("runtime/state/*/*") if Path(p).is_dir()]
    dirs = [d for d in dirs if list(d.glob("day1_*.json"))]
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)


def _turn_entries(checkpoint_dir: Path) -> list[dict]:
    """All turns so far as {turn, lines:[{cid, prose, spoken}]}, sorted by turn."""
    out: list[dict] = []
    for f in checkpoint_dir.glob("day1_*.json"):
        if f.stem.endswith("transcript"):
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        turn = int(data.get("turn", 0))
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
            out.append({"turn": turn, "lines": lines})
    out.sort(key=lambda e: e["turn"])
    return out


async def handle_index(request: web.Request) -> web.Response:
    scene = request.app["checkpoint_dir"].name.replace("_", " ").title()
    return web.Response(text=_PAGE.replace("__TITLE__", scene),
                        content_type="text/html")


async def handle_map(request: web.Request) -> web.Response:
    d = request.app["checkpoint_dir"]
    candidates = sorted(d.glob("*_map.html"))
    if not candidates:
        return web.Response(text="<p>No map yet — waiting for the first turn…</p>",
                            content_type="text/html")
    return web.Response(text=candidates[0].read_text(encoding="utf-8"),
                        content_type="text/html")


async def handle_events(request: web.Request) -> web.StreamResponse:
    """Server-Sent Events: replay history, then stream new turns as they land."""
    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    })
    await resp.prepare(request)
    d = request.app["checkpoint_dir"]
    sent: set[int] = set()
    try:
        while True:
            for entry in _turn_entries(d):
                if entry["turn"] in sent:
                    continue
                sent.add(entry["turn"])
                await resp.write(f"data: {json.dumps(entry)}\n\n".encode())
            await resp.write(b": keep-alive\n\n")  # comment frame to detect drop
            await asyncio.sleep(1.5)
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    return resp


_PAGE = """<!doctype html><html><head><meta charset='utf-8'>
<title>__TITLE__ — Driftmoor</title><style>
:root{color-scheme:dark;}
body{margin:0;font-family:ui-sans-serif,system-ui,sans-serif;background:#0e0e12;color:#e6e6e6;}
header{padding:8px 14px;font-size:15px;font-weight:700;border-bottom:1px solid #2a2a33;}
.cols{display:flex;height:calc(100vh - 38px);}
.log{flex:1;overflow-y:auto;padding:10px 14px;border-right:1px solid #2a2a33;}
.map{flex:1.3;}
.map iframe{width:100%;height:100%;border:0;background:#0e0e12;}
.turn{margin:0 0 14px;}
.turn h3{margin:0 0 4px;font-size:12px;color:#8a8a99;letter-spacing:.05em;text-transform:uppercase;}
.line{margin:0 0 7px;font-size:14px;line-height:1.45;}
.cid{font-weight:700;color:#9ecbff;}
.spoken{color:#cfe8c0;font-style:italic;}
</style></head><body>
<header>__TITLE__ — live spectator</header>
<div class='cols'>
  <div class='log' id='log'></div>
  <div class='map'><iframe id='mapframe' src='/map'></iframe></div>
</div>
<script>
const log=document.getElementById('log');
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
const es=new EventSource('/events');
es.onmessage=e=>{
  const t=JSON.parse(e.data);
  const div=document.createElement('div');div.className='turn';
  let html='<h3>Turn '+t.turn+'</h3>';
  for(const l of t.lines){
    if(l.spoken){html+='<p class="line"><span class="cid">'+esc(l.cid)+'</span>: <span class="spoken">“'+esc(l.spoken)+'”</span></p>';}
    if(l.prose){html+='<p class="line">'+esc(l.prose)+'</p>';}
  }
  div.innerHTML=html;log.appendChild(div);
  const atBottom=log.scrollHeight-log.scrollTop-log.clientHeight<120;
  if(atBottom)log.scrollTop=log.scrollHeight;
};
// The map follows new turns via its own live-refresh (it reloads only while
// parked on the latest turn), so we don't force-reload the iframe here — that
// would reset the slider and interrupt Play / scrubbing through past turns.
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Driftmoor web spectator")
    ap.add_argument("checkpoint_dir", nargs="?", default=None,
                    help="run dir under runtime/state/<run>/<scene> (default: latest)")
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()

    d = Path(args.checkpoint_dir) if args.checkpoint_dir else _latest_run()
    if d is None or not d.exists():
        raise SystemExit("No checkpoint dir found. Pass one, or run a scene first.")

    app = web.Application()
    app["checkpoint_dir"] = d
    app.add_routes([
        web.get("/", handle_index),
        web.get("/map", handle_map),
        web.get("/events", handle_events),
    ])
    print(f"Spectating {d}")
    print(f"Open http://localhost:{args.port}/")
    web.run_app(app, host="0.0.0.0", port=args.port, print=None)


if __name__ == "__main__":
    main()
