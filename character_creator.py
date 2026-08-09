"""Interactive browser entry point for creating a Driftmoor player character."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from aiohttp import web

from character_generation import (
    CharacterDraft, SYSTEM_PROMPT, fallback_draft, generation_prompt,
    identity_markdown, parse_model_draft, save_draft, soul_markdown, validate_draft,
)
from engine.llm_bridge import make_call_llm
from env_boot import load_project_dotenv


ROOT = Path(__file__).resolve().parent


async def index(_request: web.Request) -> web.Response:
    return web.Response(text=PAGE, content_type="text/html")


async def generate(request: web.Request) -> web.Response:
    payload = await request.json()
    answers = {str(k): str(v) for k, v in (payload.get("answers") or {}).items()}
    call_llm = request.app.get("call_llm")
    warning = ""
    if call_llm:
        try:
            draft = parse_model_draft(await call_llm(SYSTEM_PROMPT, generation_prompt(answers)))
        except Exception as exc:  # keep the creator useful if a local model is offline
            draft = fallback_draft(answers)
            warning = f"Model generation failed; showing a local draft instead: {exc}"
    else:
        draft = fallback_draft(answers)
        warning = "No generation model configured; showing a local draft."
    return web.json_response({"draft": draft.to_dict(), "warning": warning})


async def preview(request: web.Request) -> web.Response:
    draft = CharacterDraft.from_dict((await request.json()).get("draft") or {})
    return web.json_response({
        "errors": validate_draft(draft),
        "identity": identity_markdown(draft),
        "soul": soul_markdown(draft),
    })


async def create(request: web.Request) -> web.Response:
    draft = CharacterDraft.from_dict((await request.json()).get("draft") or {})
    errors = validate_draft(draft)
    if errors:
        return web.json_response({"ok": False, "errors": errors}, status=400)
    try:
        directory = save_draft(draft, ROOT / "scenario/people/players")
    except (ValueError, FileExistsError) as exc:
        return web.json_response({"ok": False, "errors": [str(exc)]}, status=409)
    return web.json_response({
        "ok": True, "player_id": directory.name,
        "message": f"{draft.name} is ready to enter Driftmoor.",
        "play_command": f"python web_play.py driftmoor --player {directory.name}",
    })


async def download_sheet(request: web.Request) -> web.Response:
    from character_sheet_pdf import character_sheet_pdf
    from character_generation import slugify

    if request.content_type == "application/json":
        raw = (await request.json()).get("draft") or {}
    else:
        form = await request.post()
        try:
            raw = json.loads(str(form.get("draft") or "{}"))
        except json.JSONDecodeError:
            return web.json_response(
                {"ok": False, "errors": ["Character sheet request was malformed."]},
                status=400,
            )
    draft = CharacterDraft.from_dict(raw)
    errors = validate_draft(draft)
    if errors:
        return web.json_response({"ok": False, "errors": errors}, status=400)
    filename = f"{slugify(draft.name)}_character_sheet.pdf"
    return web.Response(
        body=character_sheet_pdf(draft), content_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def build_app(provider: str = "", model: str = "") -> web.Application:
    app = web.Application(client_max_size=128 * 1024)
    app["call_llm"] = make_call_llm(provider, model) if provider and model else None
    app.add_routes([web.get("/", index), web.post("/api/generate", generate),
                    web.post("/api/preview", preview), web.post("/api/create", create),
                    web.post("/api/character-sheet", download_sheet)])
    return app


def main() -> None:
    load_project_dotenv()
    ap = argparse.ArgumentParser(description="Create a Driftmoor player in the browser")
    ap.add_argument("--provider", default=os.getenv("DRIFTMOOR_CREATOR_PROVIDER", ""))
    ap.add_argument("--model", default=os.getenv("DRIFTMOOR_CREATOR_MODEL", ""))
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8081)
    args = ap.parse_args()
    print(f"Open http://localhost:{args.port}/")
    web.run_app(build_app(args.provider, args.model), host=args.host, port=args.port, print=None)


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Create a character — Driftmoor</title><style>
:root{color-scheme:light;--ink:#292820;--muted:#706c60;--gold:#8a6129;--panel:#fffdf7;--line:#c8c0ad;--red:#a9443d}
*{box-sizing:border-box}body{margin:0;background:#eee9dc;color:var(--ink);font:16px/1.5 Georgia,serif}
body:before{content:"";position:fixed;inset:0;background:radial-gradient(circle at 15% 8%,#dbe5d3aa,transparent 36%),radial-gradient(circle at 92% 88%,#e7d2bd99,transparent 38%);pointer-events:none}
header{padding:26px 5vw 18px;border-bottom:1px solid var(--line);background:#f8f4e9cc}h1{margin:0;font-size:clamp(26px,4vw,44px);font-weight:500}header p{margin:5px 0;color:var(--muted)}
main{position:relative;display:block;max-width:900px;margin:auto;padding:28px 5vw 70px}main.workshop-open{display:grid;grid-template-columns:minmax(300px,.85fr) minmax(380px,1.4fr);gap:28px;max-width:1320px}
.card{background:#fffdf7ed;border:1px solid var(--line);border-radius:10px;padding:22px;box-shadow:0 16px 42px #514a3824}.card h2{font-weight:500;margin:0 0 4px}.lede{color:var(--muted);margin:0 0 20px}
.q{margin:0 0 18px}.q label,.field label{display:block;color:var(--gold);font-size:13px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:5px}
textarea,input{width:100%;border:1px solid var(--line);border-radius:5px;background:#fffefb;color:var(--ink);padding:10px 11px;font:15px/1.4 ui-sans-serif,system-ui;resize:vertical;box-shadow:inset 0 1px 2px #4a412814}textarea:focus,input:focus{outline:2px solid #b9905570;border-color:var(--gold)}
button{border:1px solid #795723;background:#b88942;color:#21190e;border-radius:5px;padding:10px 16px;font-weight:700;cursor:pointer}button:hover{background:#c79a54}button.secondary{background:#f6f1e4;color:var(--ink);border-color:var(--line)}button.secondary:hover{background:#ebe3d1}button:disabled{opacity:.45;cursor:wait}
.actions{display:flex;gap:9px;align-items:center;flex-wrap:wrap}.status{color:var(--muted);font:13px ui-sans-serif,system-ui}.status.bad{color:#9b312c}.status.good{color:#3d7146}
#workshop{display:none}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.field.wide{grid-column:1/-1}.field.two{grid-column:span 2}.field textarea{min-height:78px}
.stage{border:0;padding:0;margin:0 0 24px}.stage legend{width:100%;padding:0 0 9px;margin-bottom:15px;border-bottom:1px solid var(--line);font-size:20px}.stage legend span{color:var(--gold);font:12px ui-sans-serif,system-ui;margin-right:8px}.choices{display:flex;gap:9px;flex-wrap:wrap;margin:7px 0 12px}.choice{display:inline-flex;align-items:center;gap:6px;padding:6px 9px;background:#f7f2e7;border:1px solid var(--line);border-radius:5px;font:13px ui-sans-serif,system-ui}.choice input{width:auto;box-shadow:none;margin:0}.mini{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.subhead{color:var(--gold);font:700 11px ui-sans-serif,system-ui;letter-spacing:.05em;text-transform:uppercase;margin:15px 0 5px}.qnum{display:inline-grid;place-items:center;width:24px;height:24px;margin-right:7px;border-radius:50%;background:#ede3cf;color:var(--gold);font:700 12px ui-sans-serif,system-ui}select{width:100%;border:1px solid var(--line);border-radius:5px;background:#fffefb;color:var(--ink);padding:10px 11px;font:15px ui-sans-serif,system-ui}
.tabs{display:flex;gap:8px;margin:18px 0 10px}.tabs button{padding:6px 10px}.preview{display:none;white-space:pre-wrap;background:#f6f2e7;border:1px solid var(--line);padding:15px;border-radius:5px;max-height:380px;overflow:auto;font:12px/1.45 ui-monospace,monospace;color:#343229}.preview.on{display:block}
@media(max-width:850px){main{grid-template-columns:1fr}.grid,.mini{grid-template-columns:1fr}.field.two,.field.wide{grid-column:auto}}
</style></head><body><header><h1>Who comes to Driftmoor?</h1><p>Speak plainly. The road will supply the rest.</p></header><main>
<section class="card"><h2>The interview</h2><p class="lede">Eight questions shape the first draft. Leave anything blank and Driftmoor will make a careful suggestion.</p><form id="interview">
<fieldset class="stage"><legend><span>01</span>Identity</legend>
<div class="q"><label for="name">Character name</label><input id="name" placeholder="A name, nickname, or leave it to fate"></div>
<div class="mini"><div class="q"><label for="pronouns">Pronouns</label><select id="pronouns"><option value="">Suggest</option><option>she/her</option><option>he/him</option><option>they/them</option><option value="custom">Custom</option><option>Unspecified</option></select><input id="pronouns_custom" placeholder="Custom pronouns"></div>
<div class="q"><label for="gender">Gender (optional)</label><input id="gender" placeholder="Leave unstated if preferred"></div>
<div class="q"><label for="race">Ancestry / people</label><select id="race"><option value="">Suggest</option><option>Human</option><option>Elf</option><option>Dwarf</option><option>Halfling</option><option value="custom">Other</option></select><input id="race_custom" placeholder="Other ancestry or people"></div></div></fieldset>
<fieldset class="stage"><legend><span>02</span>A soul with edges</legend>
<div class="q"><label for="concept"><span class="qnum">1</span>First impression</label><textarea id="concept" placeholder="What do we notice when they first walk into a room?"></textarea></div>
<div class="q"><label for="past"><span class="qnum">2</span>A life before the road</label><textarea id="past" placeholder="What part of their past still has a hold on them?"></textarea></div>
<div class="q"><label for="desire"><span class="qnum">3</span>The reason to leave</label><textarea id="desire" placeholder="What do they want badly enough to take a dangerous road?"></textarea></div>
<div class="q"><label for="fear"><span class="qnum">4</span>Fear or wound</label><textarea id="fear" placeholder="What would they hate for their companions to discover? What experience still shapes them?"></textarea></div>
<div class="q"><label for="temperament"><span class="qnum">5</span>Voice and manner</label><textarea id="temperament" placeholder="How do they speak, move, joke, or behave under pressure?"></textarea></div>
<div class="q"><label for="loyalty"><span class="qnum">6</span>Loyalty</label><textarea id="loyalty" placeholder="Who, what, or which principle could call them back when leaving would be safer?"></textarea></div>
<div class="q"><label for="contradiction"><span class="qnum">7</span>Contradiction</label><textarea id="contradiction" placeholder="Name two true things about them that do not sit comfortably together."></textarea></div>
<div class="q"><label for="keepsake"><span class="qnum">8</span>Significant object</label><textarea id="keepsake" placeholder="Do they carry something mundane that matters to them? Why can they not let it go?"></textarea></div></fieldset>
<fieldset class="stage"><legend><span>03</span>How do you want to play?</legend><div class="subhead">Choose any that sound fun</div><div class="choices" id="playstyles">
<label class="choice"><input type="checkbox" value="protect allies">Protect allies</label><label class="choice"><input type="checkbox" value="fight up close">Fight up close</label><label class="choice"><input type="checkbox" value="attack at range">Attack at range</label><label class="choice"><input type="checkbox" value="sneak and deceive">Sneak and deceive</label><label class="choice"><input type="checkbox" value="solve mysteries">Solve mysteries</label><label class="choice"><input type="checkbox" value="use broad magic">Use broad magic</label><label class="choice"><input type="checkbox" value="heal and support">Heal and support</label><label class="choice"><input type="checkbox" value="negotiate">Negotiate</label><label class="choice"><input type="checkbox" value="explore wilderness">Explore wilderness</label><label class="choice"><input type="checkbox" value="improvise with tools">Improvise with tools</label></div>
<div class="mini"><div class="q"><label for="complexity">How many rules and options sound fun?</label><select id="complexity"><option>Keep my first game simple</option><option>Give me a few interesting choices</option><option>I enjoy lots of options</option><option>Surprise me</option></select></div><div class="q"><label for="level">How experienced are they?</label><select id="level"><option value="1">Just beginning their dangerous life</option><option value="2">Capable, with a few hard lessons behind them</option><option value="3">Already proven under pressure</option><option value="">Match the rest of the group</option></select></div></div>
<div class="q"><label for="mechanics">Anything mechanics must express</label><textarea id="mechanics" placeholder="A signature tactic, training, spell, disability, tool, or limitation that matters to the concept."></textarea></div></fieldset>
<div class="actions"><button id="gen" type="submit">Reveal my character</button><span class="status" id="genstatus"></span></div></form></section>
<section class="card" id="workshop"><h2 id="drafttitle">Your character</h2><p class="lede">This is a draft, not a verdict. Change anything.</p><div class="grid" id="fields"></div>
<div class="tabs"><button class="secondary" data-tab="identity">IDENTITY.md</button><button class="secondary" data-tab="soul">SOUL.md</button></div><pre class="preview" id="identity"></pre><pre class="preview" id="soul"></pre>
<div class="actions" style="margin-top:18px"><button id="create">Create player</button><button class="secondary" id="sheet">Download character sheet</button><button class="secondary" id="refresh">Refresh preview</button><span class="status" id="savestatus"></span></div></section>
</main><script>
const scalar=['name','player','pronouns','gender','race','character_class','level','background','alignment','hp','ac','speed','strength','dexterity','constitution','intelligence','wisdom','charisma','purse','mood','disposition'];
const prose=['physical_description','internal_contradiction','signature_detail'];const lists=['abilities','spells','equipment','open_threads','values_and_drives','fears_and_wounds','voice_and_manner','loyalties'];let draft={};
const nice=s=>s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
function chosen(id,custom){const value=document.getElementById(id).value;return value==='custom'?document.getElementById(custom).value:value}
function answers(){const out={};['name','gender','concept','past','desire','fear','temperament','loyalty','contradiction','keepsake','mechanics','complexity'].forEach(k=>out[k]=document.getElementById(k).value);out.pronouns=chosen('pronouns','pronouns_custom');out.race=chosen('race','race_custom');out.level=document.getElementById('level').value;out.play_style=[...document.querySelectorAll('#playstyles input:checked')].map(x=>x.value).join(', ');return out}
function render(d){draft=d;document.querySelector('main').classList.add('workshop-open');document.getElementById('drafttitle').textContent=d.name||'Your character';const box=document.getElementById('fields');box.innerHTML='';
 [...scalar,...prose,...lists].forEach(k=>{const div=document.createElement('div');div.className='field '+(prose.includes(k)||lists.includes(k)?'wide':'');const val=lists.includes(k)?(d[k]||[]).join('\n'):(d[k]??'');div.innerHTML=`<label>${nice(k)}</label>${prose.includes(k)||lists.includes(k)?`<textarea data-key="${k}"></textarea>`:`<input data-key="${k}">`}`;div.querySelector('[data-key]').value=val;box.appendChild(div)});document.getElementById('workshop').style.display='block';preview();document.getElementById('workshop').scrollIntoView({behavior:'smooth'})}
function collect(){document.querySelectorAll('[data-key]').forEach(el=>{const k=el.dataset.key;if(lists.includes(k))draft[k]=el.value.split('\n').map(x=>x.trim()).filter(Boolean);else if(['level','hp','ac','strength','dexterity','constitution','intelligence','wisdom','charisma'].includes(k))draft[k]=Number(el.value);else draft[k]=el.value});return draft}
async function api(path,body){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();if(!r.ok)throw new Error((data.errors||[r.statusText]).join(' '));return data}
async function preview(){const data=await api('/api/preview',{draft:collect()});identity.textContent=data.identity;soul.textContent=data.soul;savestatus.textContent=data.errors.length?data.errors.join(' '):'Ready to create';savestatus.className='status '+(data.errors.length?'bad':'good');return !data.errors.length}
interview.onsubmit=async e=>{e.preventDefault();gen.disabled=true;genstatus.textContent='Listening for footsteps…';try{const data=await api('/api/generate',{answers:answers()});render(data.draft);genstatus.textContent=data.warning||'Character revealed.'}catch(err){genstatus.textContent=err.message;genstatus.className='status bad'}finally{gen.disabled=false}};
refresh.onclick=preview;create.onclick=async()=>{if(!await preview())return;create.disabled=true;try{const data=await api('/api/create',{draft:collect()});savestatus.textContent=data.message+' Run: '+data.play_command;savestatus.className='status good'}catch(err){savestatus.textContent=err.message;savestatus.className='status bad'}finally{create.disabled=false}};
document.getElementById('sheet').onclick=async()=>{const button=document.getElementById('sheet');if(!await preview())return;button.disabled=true;try{const form=document.createElement('form');form.method='POST';form.action='/api/character-sheet';form.style.display='none';const payload=document.createElement('input');payload.type='hidden';payload.name='draft';payload.value=JSON.stringify(collect());form.appendChild(payload);document.body.appendChild(form);form.submit();form.remove();document.getElementById('savestatus').textContent='Character sheet download started.';document.getElementById('savestatus').className='status good'}catch(err){document.getElementById('savestatus').textContent=err.message;document.getElementById('savestatus').className='status bad'}finally{button.disabled=false}};
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{const id=b.dataset.tab;document.querySelectorAll('.preview').forEach(p=>p.classList.toggle('on',p.id===id))});
</script></body></html>'''


if __name__ == "__main__":
    main()
