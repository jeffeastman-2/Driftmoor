# Zone files (`zone.md`) — authoring spec

Canonical reference for migrating Driftmoor scene content out of the monolithic
`CONTENTS.md` into **one `zone.md` per zone**, each populated from that zone's
high-level description. Agents read this file directly; the inbox kickoff just
points here.

Status: **drafting source files for review** — nothing is wired into the engine
yet. You are producing the source-of-truth content files to the schema below.
Start with `echoing_caverns`.

> ⚠ **Known caveat: the loader that reads these files doesn't exist yet.** This
> schema is provisional and may shift once the loader is built (it could impose
> constraints we haven't anticipated). To keep the eventual loader simple and the
> files safe, **author plain, flat markdown**: the headings and bullet fields
> shown below, no tables, no deep nesting, no HTML. One field per bullet. Flag
> anything the schema doesn't cover back to Jeff instead of improvising syntax.

---

## Invariants — do not violate (these protect the engine)

1. **`GEOMETRY.md` is the spatial source of truth. Never edit it, never invent
   coordinates.** `zone.md` holds narrative + affordances only.
2. **Item ids in the `## Items` section must exactly match the ids in
   `GEOMETRY.md`'s Items table.** The loader merges narrative → geometry *by id*;
   a mismatch silently drops the content.
3. **The `## Items` section covers exactly the GEOMETRY items for that zone — no
   more, no fewer.** Every geometry item gets an entry; nothing placed there that
   isn't in GEOMETRY.
4. **Migrate faithfully first, then enrich.** Where `CONTENTS.md` already authored
   a description or interaction, preserve its intent before adding to it.
5. **New ideas go in `## Proposed`, never in the placed sections, and never with
   coordinates.** (See "Be creative" below — this is where abundance lives.)

One file per zone: `scenario/places/<region>/<scene>/zones/<zone_slug>.md`
(slug = zone name lower-cased, spaces → underscores). One file per zone in
GEOMETRY's Zones table (11 for echoing_caverns).

---

## Schema

```markdown
# <Zone Name>            <!-- must match a zone in GEOMETRY's Zones table -->

## Description           the high-level seed, expanded — what it is, why it matters
## Ambient              sensory bed for narration: light, sound, smell, temp, footing

## Items
### <item_id>            <!-- MUST match the id in GEOMETRY's Items table -->
- label: <short display name>
- size: tiny | small | medium | large
- weight: <e.g. 2 lb>
- pickable: true | false
- wearable: false | body | head | hands | feet | neck | finger | wrist
- flavor_only: true | false
- description: <full prose>
- appearance by distance:
  - intermediate: <how it reads at mid range>
  - far: <...>
  - distant: <...>
- interactions:
  - examine: <DM ground-truth response>
  - pick up: <...>
  - <other authored verbs>: <...>

## Features / landmarks  narrative only; positions stay in GEOMETRY
## Creatures present     ids only; stats live in creature files — do not restate
## Exits                 which zones this connects to (+ direction) — travel cues

## Proposed (review → keep needs GEOMETRY placement, or cut)
```

### "Appearance by distance" — what the bands mean
These are **apparent-size bands, not fixed distances.** The engine computes
`apparent = size_ft ÷ distance` and buckets it: `near` (≥0.50) → `intermediate`
(≥0.15) → `far` (≥0.07) → `distant` (≥0.035) → below that, not perceivable. So a
*large* thing stays identifiable much farther than a *small* one (a head-high
obelisk reads clearly where a dropped torch is already a fleck). Write each band
as **what an observer can actually make out at that apparent size**, degrading
detail outward:
- **near** — full detail (optional to author; the engine falls back to the label).
- **intermediate** — recognizable shape/material: "a short pale length of wood on the stone".
- **far** — vague form/colour: "a slim pale streak low on the floor".
- **distant** — barely a hint: "a faint pale fleck against the dark".

`near`/`intermediate` fall back to the item's label if you omit them; `far`/
`distant` fall back to a generic "indistinct shape" — so **authoring `far` and
`distant` is where you add the most value.**

### Interaction verbs — bounded set
Author `interactions:` **only** under these canonical verbs (what the engine
resolves to your authored response today): **`examine`, `search`, `read`,
`press`** — plus an optional **`pick up`** line for flavour when something is
taken. Possession itself (**take / drop / give / stow**) is *mechanical* — driven
by the `pickable` field, not by an authored interaction, so you don't need to
write those. For **wear / eat / use / open**, set the **affordance fields**
(`wearable`, etc.) rather than authoring an unsupported verb — the grounding
layer will consume those later. **Need a verb outside this set? Flag it to Jeff;
don't invent engine behaviour.**

### Affordance fields matter — fill them carefully
`pickable / wearable / weight / size / flavor_only` are **tabular truth** a coming
grounding policy will project into the vector space to disambiguate verbs ("wear"
→ wearable, "take" → pickable). Get them right now and that work is free later.

---

## Be creative — over-propose, we curate down

The current scenes are too sparse. **Lean generative**: it's easier to delete an
idea than to invent one later, so propose more creatures and treasure than we'll
keep. The catch: anything new needs GEOMETRY placement before it's real, so it
*all* goes in `## Proposed`, self-contained and trivially deletable — nothing in
the placed sections may depend on a proposal.

`## Proposed` format:

```markdown
## Proposed (review → keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates. Keep what we
like (then a human adds it to GEOMETRY and promotes it into the sections above);
cut the rest.

### Creatures (≤ 2 per zone)
- **<name>** — <ecology/lore hook>. Power: minor | moderate | deadly. Role:
  ambush | lurker | scavenger | guardian. Fits because: <REQUIRED — cite a
  concrete hook from this zone, the scene, or the Obelisk Reach theme; "a spider
  because caves have spiders" is not a hook>.

### Treasure & notable items (≤ 3 per zone)
- **<name>** — <what it is + hook>. Tier: mundane | valuable | magical.
  ~Value: <coins or one line>. Affordances: pickable/wearable/weight as above.
  Fits because: <REQUIRED — same lore-check: tie it to who died here, the
  expedition, the shards, etc., not generic loot>.

**Lore-check is mandatory:** every proposal must reference existing zone/scene
lore or the overarching theme. A proposal that could be dropped into any dungeon
unchanged gets cut.

### Features (optional)
- <set-dressing or interactive feature ideas, narrative only>
```

**Limits (the curation guardrails).** The caps aren't an engine limit — they're
about **scene pacing and reviewer load**: a zone crammed with encounters and loot
stops being explorable and becomes a slog to curate. The numbers keep each zone
focused enough to read in one pass and balanced against the others. Over-propose
*within* them, then we cut.
- **≤ 2 proposed creatures and ≤ 3 proposed treasures per zone; ≤ 1 *magical*
  item per zone.**
- **At most one "deadly" threat across the whole scene.** The scene's existing
  monster (echoing_caverns: the giant spider) is the centrepiece — proposals
  complement it, they don't eclipse it.
- **Scale to the party** (read the character sheets — echoing_caverns' party is
  high-level). Plausible, not game-breaking loot; leave exact balance for review.
- **Fit the lore and tone.** Obelisk Reach: corrupted obelisk shards, cold dead
  caverns, old deaths and abandoned expeditions. Grim, archaeological dread —
  match the existing scene intros. No anachronisms, no contradictions with
  established items/lore or other zones.
- **Everything in `## Proposed` is deletable in one stroke.** If cutting a
  proposal would break anything above it, it's in the wrong place.

---

## Roles (eJeff directs; adjust to your agents' strengths)

- **eJeff** — lead. Owns this schema + the id-match invariant; assigns zones;
  validates every draft against GEOMETRY (ids match, all items covered, no
  coordinates, schema-clean, proposals fenced); reconciles tone across zones;
  delivers batches to Jeff.
- **RnD** — the writing. Expands each seed into Ambient + item descriptions +
  appearance bands + interactions + affordances, and generates the `## Proposed`
  creatures/treasure within the limits.
- **BizDev** — consistency & coverage QA. Does it serve the scene's mission and
  pacing; is tone uniform across zones; any lore contradictions; every GEOMETRY
  item covered with nothing extra; proposal counts within limits.

## Process & done

Assign a zone + its seed + the relevant `CONTENTS.md` slice → writer returns a
draft → eJeff validates/fixes → batch to Jeff. **Do Entry Chamber first as the
reference; get Jeff's sign-off on the format before fanning out the other ten.**

Per-zone done: schema-valid; every GEOMETRY item present with description +
affordances; zero coordinates; proposals fenced and within limits; tone
consistent; no contradictions.

> The schema is provisional until the loader that reads these files is built.
> Flag any ambiguity back to Jeff rather than guessing.
