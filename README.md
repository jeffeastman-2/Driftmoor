# Driftmoor

A multi-agent tabletop RPG engine that runs D&D 5e sessions with a mix of
LLM-driven characters and human players. It is built around the town of
Driftmoor and its surrounding region, where a shattered obelisk is destabilizing
the land and something old is waking beneath it.

The engine is written for this campaign. If it generalizes, that's a later
project.

---

## What it is

Driftmoor runs a session as a structured, turn-based simulation over an authored
world of **markdown** files (characters, places, geometry, things). Play centers
on three ideas:

- **A DM agent** with omniscient context drives NPCs, adjudicates dice, applies
  effects, and narrates — while every player (LLM or human) sees only what their
  character could perceive.
- **Natural language in, action out.** A player says *"I sheathe my dagger, draw
  my crossbow, and shoot the spider"* or *"where is the tavern?"*, and the
  **LATN** parser grounds it to engine actions or answers — no command syntax,
  no keyword regexes.
- **A real space.** Scenes have geometry: zones, coordinates, line-of-sight, and
  a live fog-of-war map. Characters move, see, reach, and enter buildings.

Humans play in the **browser** (a streaming narration log beside the live map,
with a box to state intent or ask the DM questions). NPCs run on their own LLMs,
local or cloud.

## Status

A working, actively developed engine — not a finished product. You can play a
scene end-to-end today (`web_play.py`), and the suite runs **~1,400 tests**.
Subsystems are at different maturities; the [`specs/`](specs/) directory marks
each file format and subsystem as *implemented*, *draft*, or *convention only*.

---

## Quick start

**Prerequisites**

- Python 3.12+
- The **LATN** parser, checked out beside this repo (see below).
- A model backend: a local [Ollama](https://ollama.com) (scenes default to
  `gemma4:26b`) **or** cloud API keys (Anthropic / OpenAI / Google).

**Install**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# LATN lives in the sibling layered-atn repo (editable path dependency):
pip install -r requirements-dev.txt          # installs -e ../LATN/layered-atn
# ...or, if your checkout is elsewhere:
#   pip install -e /absolute/path/to/layered-atn
```

**Configure** (optional — copy `.env.example` and source it)

```bash
cp .env.example .env.local && source .env.local
# OLLAMA_HOST, LLM_FORCE_OLLAMA_MODEL (force everything offline),
# ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY, etc.
```

**Play in the browser**

```bash
python web_play.py driftmoor --player gilthaness      # then open http://localhost:8080
```

You control one character; the DM and other characters run on their LLMs. Type
intent in plain English; ask questions (`what can I buy?`, `where is the
forge?`); watch the map update as everyone moves.

For local world debugging, `/goto <place>` performs a cost-free scene jump
through the normal transition loader. For example: `/goto graveyard`,
`/goto living loft`, or `/goto storage room`. It consumes a turn so the scene
can rebuild safely, but ignores doors, range, combat, and spell slots. The
leading slash distinguishes this developer back door from the in-world
Teleport spell.

### v0.1 deployment boundary

Driftmoor v0.1 supports one human player per game-server process.

For local solo play, the default command binds only to `127.0.0.1`:

```bash
python web_play.py driftmoor --player gilthaness
```

For trusted remote solo play, the host may run the game and model backend on a
private machine while the player connects through a private network such as
Tailscale:

```bash
python web_play.py driftmoor --player gilthaness --host 0.0.0.0
```

Open `http://<host-private-address>:8080/` from the trusted remote device. Keep
the host firewall and private-network access controls restricted to intended
devices.

`web_play.py` has no application-level authentication or independent player
identity. Do **not** expose it directly to the public internet. A reverse proxy,
port forward, or public tunnel does not add the missing authorization. Public
hosting and authenticated multi-human sessions are deferred beyond v0.1; see
[`DRIFTMOOR_V0.1.md`](DRIFTMOOR_V0.1.md).

**Run headless (all-LLM), or spectate**

```bash
python run_scene.py echoing_caverns 8                 # 8 turns, everyone LLM-driven
python run_scene.py elyssa_cottage --resume           # resume the latest run
python web_spectator.py                               # read-only view of a run in progress
```

---

## How a game runs

The unit of play is a **Scene**: a set of characters present together in a place,
acting in the same turn structure. A scene is configured by a `scenes/<name>.md`
file that names a geometry, a place, the cast and their starting positions, the
in-world time, and which model runs the DM.

Each turn:

1. Active characters roll **initiative**.
2. In initiative order, each character acts — an LLM generates intent, or a human
   states it via a transport (web / Telegram).
3. Intent is **parsed and grounded** (LATN) to an action: move, attack, cast,
   examine, take/give, buy/sell, enter a building, or a question to answer.
4. The engine resolves it — dice rolls, combat, effects, movement, commerce — and
   the **DM narrates** the outcome to exactly the characters who could perceive
   it.
5. State advances: positions, HP, conditions, the game clock, and the map.
6. A **checkpoint** is written so the run can be resumed or spectated.

Characters have **asymmetric knowledge**, enforced by construction: a character's
context contains only what they were present to witness; internal monologue never
leaves the generating character; the DM alone holds the omniscient view and
DM-only notes. Multiple scenes can run in parallel and merge or split as
characters move between places.

### Create a player in the browser

The character creator turns a short, free-form interview into a complete player
draft, exposes every generated field for revision, previews the canonical
Markdown, and reloads the saved result through the production character loader:

```bash
python character_creator.py
```

Open `http://localhost:8081/`. With no model configured it produces a useful
offline draft. To use an LLM, set `DRIFTMOOR_CREATOR_PROVIDER` and
`DRIFTMOOR_CREATOR_MODEL` (or pass `--provider` and `--model`); for example,
`ollama` and a locally installed model. After creation the interface gives the
exact `web_play.py` command for entering Driftmoor as that character.
The workshop can also download a filled, two-page tabletop character sheet for
printing or sharing with the player.

---

## Core concepts

### Characters — SOUL + IDENTITY

Every character (player or NPC) is two markdown files under
`scenario/people/{players,npcs}/<name>/`:

- **`SOUL.md`** — the stable inner life: values, drives, fears, voice. Loaded as
  LLM context; never edited during play.
- **`IDENTITY.md`** — the character sheet: race/class, stats, proficiencies,
  equipment, HP, spell slots, purse. Parsed into the runtime model.

The roster ships with 13 playable characters and a large NPC cast. Placement (who
starts where) lives in the **scene** file, so one world can host many
scenarios — the geometry is a pure stage.

### Places & geometry

A place is described by `PLACE.md` (atmosphere, occupants, connections) and given
a spatial body by `GEOMETRY.md` (named **zones** as polygons, coordinates,
landmarks, doorways, visibility). The engine tracks each character's `(x, y,
zone)` position, computes line-of-sight and reach, and renders a **fog-of-war
map** (`engine/map_renderer.py`) that reveals zones as they're seen. Buildings are
child places you can *enter* — crossing a doorway spins up a sub-scene.

### Things — the affordance model

Weapons, armor, tools, food, containers, and shop goods are one type,
`models/thing.py`, described by **affordances** (what you can do with it —
`weapon`, `wearable`, `edible`, `container`, …), first-class **effects**, and
**carry-state** (wielded / worn / stowed / on the ground). Verbs are dispatched by
affordance (`engine/manipulation.py`): "drink the potion" works because the thing
affords it; "wield the potion" is refused because it doesn't. Commerce
(`engine/commerce.py`, `models/shop_catalog.py`) settles buys and sells against a
coin purse.

### Natural language — the LATN parser

Player and NPC intent is parsed by **LATN** (a Layered Augmented Transition
Network), a host-neutral grammar engine in the sibling `layered-atn` repo.
Driftmoor injects its own vocabulary, dimensions, and grounding policies without
forking the parser (see [`docs/latn-integration.md`](docs/latn-integration.md)).

- **Actions** ground from the parsed verb-phrase structure, including
  conjunctions ("pick up the mace **and** hand it to Amara").
- **Questions** are parsed as a distinct clause type (the *SQ* interrogative
  nonterminal) and answered by the engine — shop catalog (*"what can I buy?"*),
  geometry (*"where is the tavern?"*), or self (*"how much gold do I have?"*) —
  so the DM/LLM is only a fallback for what LATN can't yet ground.
- The design rule is **beef up the parser, not add regexes**: intent parsing
  lives in LATN's vocabulary and grammar. Words the lexicon doesn't know are
  written to `runtime/unknown_words.json` for review.

### Combat, spells, and dice

Attacks, saves, and damage run through `engine/combat_resolver.py` and
`engine/dice.py`; spells through `engine/spell_resolver.py`
(`models/spellcasting.py`). Every roll draws from **one seeded RNG**
(`engine/game_rng.py`), so a seed reproduces the whole game — combat is
deterministic and testable. Conditions, initiative, and the melee/exploration
clock cadence are modeled explicitly.

### Human play — web and Telegram

Human input arrives over a **transport**. The primary one is the in-process
**web** UI (`web_play.py` + `engine/web_transport.py`): a browser page with the
live map, the narration stream, an inventory panel with a coin purse, and an
input box. **Telegram** (`engine/telegram_transport.py`) is also supported.
(Earlier WhatsApp/OpenClaw routing has been retired.)

### Persistence & determinism

Each turn checkpoints to `runtime/state/<session>/` (JSON + a regenerated
`<scene>_map.html`). Runs can be **resumed** (`--resume`) and **spectated** live.
`runtime/` is gitignored. Session transcripts are the primary record of play.

---

## Repository layout

```
Driftmoor/
├── web_play.py            # play a scene in the browser (primary human entry point)
├── web_spectator.py       # read-only, big-screen view of a running/finished run
├── run_scene.py           # headless all-LLM run of a scene (+ --resume)
│
├── engine/                # the runtime
│   ├── session.py             # the turn loop (iter_session / run_session)
│   ├── scene_manager.py       # scene topology; merge/split; initiative scheduling
│   ├── multi_scene.py         # parallel scenes
│   ├── initiative.py          # roll + ordering
│   ├── dm_agent.py            # omniscient DM: NPC dispatch, adjudication, narration
│   ├── player_router.py       # human vs agent dispatch
│   ├── narrator.py            # per-character narration
│   ├── llm_bridge.py          # provider abstraction (Anthropic / OpenAI / Ollama)
│   │
│   ├── latn.py                # LATN facade (re-exports the parser + seams)
│   ├── latn_lexicon.py        # Driftmoor vocabulary
│   ├── latn_dimensions.py     # Driftmoor vector dimensions
│   ├── latn_adapter.py        # scene grounding (NPs -> world entities)
│   ├── latn_resolver.py       # verbs/questions -> resolved actions
│   ├── latn_integration.py    # turn-loop glue
│   ├── unknown_word_log.py    # record vocabulary gaps hit in play
│   │
│   ├── geometry.py, map_renderer.py       # movement, line-of-sight, fog-of-war maps
│   ├── manipulation.py, loadout.py        # affordance-gated item handling
│   ├── commerce.py                        # buy/sell settlement
│   ├── combat.py, combat_resolver.py, dice.py, game_rng.py   # combat + seeded rolls
│   ├── spell_resolver.py                  # spell economy
│   ├── effects.py, activation.py, puzzles.py
│   ├── web_transport.py, telegram_transport.py   # human I/O
│   ├── game_checkpoint.py, persistence.py, transcript.py, runtime_paths.py
│   └── md_loader.py, *_loader.py          # markdown -> runtime models
│
├── models/                # runtime object model
│   ├── thing.py               # unified affordance/effect/carry-state item
│   ├── character.py           # PlayerCharacter / NPC / Creature
│   ├── place.py, scene.py, game_state.py
│   ├── space_time.py          # positions, zones, geometry primitives
│   ├── currency.py, shop_catalog.py, weapon.py, condition.py, spellcasting.py
│   └── *_loader.py
│
├── scenes/                # scene configs (driftmoor town, its buildings, echoing_caverns, ...)
├── scenario/              # authored world content
│   ├── people/{players,npcs}/<name>/  # SOUL.md + IDENTITY.md (+ icon.svg)
│   ├── places/<region>/<place>/       # PLACE.md, GEOMETRY.md, CONTENTS.md, ...
│   ├── creatures/                     # shadowbeast, giant spider, ...
│   └── things/                        # obelisk shards, item libraries, price lists
│
├── specs/                 # format + subsystem specifications (see specs/README.md)
├── docs/                  # design plans (LATN integration, economy, ...)
├── tests/                 # ~1,400 pytest tests
└── runtime/               # gitignored: checkpoints, maps, logs, unknown_words.json
```

---

## Authoring scenarios

The world is data. The [`specs/`](specs/) directory is the source of truth for
every markdown format the engine reads — `SCENE.md`, `GEOMETRY.md`, `IDENTITY.md`,
`PLACE.md`, `CONTENTS.md`, `ZONES.md`, `WEAPONS_ARMOR.md`, `SPACE_TIME.md`, and
more — each marked *implemented* / *draft* / *convention only*. Discipline: when
you change a file with an implemented spec, update the spec and its loader in the
same commit; the parser is the ground truth.

---

## LLM configuration

Each scene's `.md` selects the DM's provider and model (e.g. `provider: ollama`,
`model: gemma4:26b`); NPCs can run on lighter models for cost. Set
`LLM_FORCE_OLLAMA_MODEL` to force every agent onto one local model for fully
offline or A/B runs. Cloud keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`GOOGLE_API_KEY`) are only needed when a scene selects a cloud provider. All of
this lives in `.env` (not committed — see `.env.example`).

---

## Testing

```bash
pytest -q                    # full suite (~1,400 tests)
pytest tests/test_session.py # one module
```

The suite runs with `pytest-randomly`; combat is deterministic under a fixed seed
because all rolls flow through `engine/game_rng.py`.

---

## Background

The scenario content grew out of a ChatGPT-generated D&D campaign module played
at a real tabletop in winter 2024 — the obelisk, the shadowbeasts, and the town
of Driftmoor are that session's invention. The engine is new.

The multi-agent architecture descends from **Multi-LLM-Bridge**, a framework for
running multi-agent simulations with LLMs playing named roles; that work's
observations on the behavioral fingerprints of different models informed the
SOUL/IDENTITY separation and the omniscient-monitor pattern that becomes the DM
here. The natural-language layer comes from **LATN/ENGRAF**, a by-design (not
learned) vector-embedding parser originally built for a 3D graphics world and now
factored into a host-neutral core that Driftmoor and the CAD host share.

---

## License

TBD.
