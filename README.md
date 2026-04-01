# Driftmoor

A multi-agent tabletop RPG engine for running D&D 5e sessions with a mix of LLM-driven characters and human players. Built around the town of Driftmoor and its surrounding region, where a shattered obelisk is destabilizing the land and something old is waking up beneath it.

The engine is designed for this campaign. If it works well enough to generalize, that's a future project.

---

## What This Is

Driftmoor runs a D&D session as a structured multi-agent simulation. A DM agent with omniscient context manages the world, drives NPCs, adjudicates dice rolls, and maintains narrative coherence. Player characters are driven either by LLM agents or by human players connecting via WhatsApp through an OpenClaw interface. Both types of player participate in the same turn structure.

The fundamental unit of play is a **Scene** — a set of characters present together in a place, active simultaneously. Multiple scenes can run in parallel (different characters in different locations), merge (characters entering the same space), or split (a character leaving the group). Initiative determines scene order and action order within scenes.

---

## Architecture Overview

### The Three-File Persona Model

Every character — player or NPC — is defined by two static files and participates in one active scene file:

**`SOUL.md`** — Stable psychological core. Values, drives, fears, wounds, voice, internal contradictions. Written once, never updated during play. The character's permanent identity.

**`IDENTITY.md`** — Static profile plus dynamic state. Stats, equipment, proficiencies, and initial values for: current HP, spell slots, mood, disposition, active conditions, open threads. At runtime these fields will be maintained in memory but the initial values here are for game initialization only.

**`SCENE.md`** — The initial units of play. Which place, which characters, what is happening right now, initiative order, scene history filtered by character presence. At runtime, scenes will be managed in memory so this information is used to load those models at game initialization.

### Information Architecture

Characters have asymmetric knowledge. The engine enforces this:

- **INTERNAL** monologue never leaves the generating character's context
- **BODY LANGUAGE** and **SPOKEN** content enters the shared scene history
- Scene history is filtered on assembly — each character's context contains only what they were present to witness
- The DM agent has full omniscient context including DM-only notes in place and item files
- Human players receive a narrative feed via WhatsApp; their "context" is their OpenClaw conversation history

### Turn Structure

```
Each Turn:
  1. All active entities roll Initiative
  2. Scenes ordered by highest Initiative within them
  3. For each Scene (in Initiative order):
     a. Entities act in Initiative order within the Scene
     b. Human players prompted via OpenClaw/WhatsApp
     c. NPC and agent players generate responses
     d. DM agent adjudicates, narrates, updates state
  4. Scene topology evaluated:
     - Merge: character enters another Scene's Place
     - Split: character leaves current Scene
  5. IDENTITY dynamic sections updated
  6. SCENE files updated
  7. New Initiative → next Turn
```

---

## Scenario Files

The `scenarios/driftmoor/` directory contains the full static campaign content:

```
scenarios/driftmoor/
├── people/
│   ├── seraphina/         # Half-elf Rogue
│   ├── thorgrim/          # Dwarf Fighter
│   ├── aeliana/           # Wood Elf Ranger
│   ├── lilar/             # Human Cleric
│   ├── kaelin/            # Halfling Bard
│   └── npcs/
│       ├── aldren/        # Mayor
│       ├── elyssa/        # Scholar / quest giver
│       ├── kelem/         # Antiquities merchant
│       ├── ...            # Full NPC roster
│       ├── haversteads/   # Mill family
│       └── background/    # 12 background NPCs
├── places/
│   ├── PLACE.md           # Regional overview
│   ├── CONTENTS.md        # Regional threats and wildlife
│   ├── driftmoor/         # Town and all buildings
│   ├── obelisk_reach/     # The central mystery location
│   ├── greywater_river/   # River corridor and Old Mill
│   ├── mistwood_hills/    # Fog-laden forest
│   ├── azure_sea/         # Coast, sea stacks, Drowned Isle
│   └── plains_of_stonehearth/
└── things/
    ├── obelisk_shards.md  # Campaign MacGuffin — full lore and mechanics
    ├── shadowbeast_parts.md # Harvesting rules and alchemical values
    ├── magical_items.md   # DM reference — true properties of all magical items
    └── mundane_items.md   # Master price list across all vendors
```

Every place directory contains `PLACE.md` (description, atmosphere, who is here, connections, dynamic state) and `CONTENTS.md` (items, creatures, DM notes). Places with meaningful sub-spaces have subdirectories following the same pattern.

---

## Engine Modules

```
engine/
├── bridge.py          # Entry point; multi-scene router
├── orchestrator.py    # Single-scene turn management
├── scene_manager.py   # Scene topology; merge/split; initiative scheduling
├── initiative.py      # Roll and ordering logic
├── dm_agent.py        # Omniscient context; NPC dispatch; adjudication
├── player_router.py   # Human (OpenClaw/WhatsApp) vs agent dispatch
└── context_builder.py # Assembles filtered per-character context
```

---

## Runtime Object Model

```
models/
├── character.py   # Character (base), PlayerCharacter, NPC
├── place.py       # Place hierarchy
├── thing.py       # Thing, MagicalItem, Consumable, Container
├── scene.py       # Scene, history records, participant management
└── game_state.py  # Top-level state; scene registry; turn counter
```

Things have defined fields for id, name, canonical reference, current location, current holder, condition, and type-specific state (charges, attunement, etc.). Characters track current place, current scene, inventory, and dynamic stat state. Places track current occupants and contents. The DM agent is the sole writer of runtime state; all other agents are readers.

---

## Player Configuration

Players are defined in a configuration file (not committed — see `.env.example`):

```yaml
players:
  - name: Thorgrim
    character: thorgrim
    type: human
    channel: whatsapp
    contact: "+1..."
  - name: Seraphina
    character: seraphina
    type: human
    channel: whatsapp
    contact: "+1..."
  - name: Aeliana
    character: aeliana
    type: agent
    model: claude-opus-4-6
  - name: Lilar
    character: lilar
    type: agent
    model: claude-opus-4-6
```

Human players receive prompts and narration via WhatsApp through the OpenClaw infrastructure. Agent players are driven by the configured LLM with their SOUL.md and IDENTITY.md loaded into context.

---

## LLM Configuration

Driftmoor supports multiple LLM providers via the same interface abstraction inherited from Multi-LLM-Bridge:

- **Anthropic Claude** (claude-opus-4-6, claude-sonnet-4-6) — primary
- **OpenAI** — supported
- **Ollama** (local models) — supported; Qwen3:14b tested as fourth agent

Provider credentials go in `.env` (not committed). See `.env.example`.

The DM agent runs on the most capable available model. NPC agents can run on lighter models for cost efficiency.

---

## Runtime State

```
runtime/               # gitignored entirely
├── scenes/            # Active SCENE.md files
├── state/             # Serialized game state (JSON)
└── logs/              # Session transcripts
```

Runtime state is not committed. Session logs are the primary record of play and should be archived separately if you want to keep them.

---

## Dependencies

```
anthropic
openai
ollama
pyyaml
python-dotenv
```

Full list in `requirements.txt`.

---

## Status

**Scenario content:** Complete. All people, places, and things files generated and ready.

**Engine:** In development.

**Runtime object model:** In development.

**Human player routing:** OpenClaw/WhatsApp infrastructure exists in Multi-LLM-Bridge; integration pending.

---

## Background

The scenario content was developed from a ChatGPT-generated D&D campaign module for a real tabletop session played in winter 2024. The obelisk, the shadowbeasts, and the town of Driftmoor are the work of that session's DM. The engine is new.

The multi-agent architecture descends from Multi-LLM-Bridge, a Python framework for running geopolitical wargame simulations with multiple LLM agents playing named roles. The wargame work produced observations about behavioral fingerprinting of LLMs that informed the design decisions here — particularly the SOUL/IDENTITY file separation and the monitor agent pattern that becomes the DM agent in this context.

---

## License

TBD