# PLACE.md FORMAT SPECIFICATION

`PLACE.md` describes a location at any granularity — region, settlement,
building, or single room. Every directory under `scenario/places/` whose
contents represent a named location should contain one.

Parser: `models/place_loader.py::parse_place_md`.

## Title line (required)

```markdown
# PLACE.md — <Display Name>
```

## Sections

Sections may appear in any order; unknown sections are ignored. All
sections use prefix-matching on the heading text.

### `## Description and Atmosphere` — required, free prose

One to several paragraphs. Surfaced verbatim to the LLM when characters
are present at this location. Should evoke the *feel* and *sensory
texture* of the place, not exhaustively list every prop (props live in
`CONTENTS.md`, see `specs/CONTENTS.md`).

Parsed into `Place.description: str`.

### `## Sub-Places` — optional, bullet list

`- ` bullets identifying child directories or named sub-areas. Use
backticks around directory names:

```markdown
- `driftmoor/` — the town, population ~500, the heart of the region
- `obelisk_reach/` — jagged cliffs and plateaus north of town
```

The leading backticked token is the sub-place key. Anything after the
em-dash / hyphen is a one-line summary.

Parsed into `Place.sub_places: list[str]` (full bullet text).

### `## Who Is Normally Here` — optional, bullet list

`- ` bullets describing the typical inhabitants or transient visitors.
Population descriptors, not roster lookups — the *kind* of people, not
named individuals.

```markdown
- Farmers moving goods between fields and town
- Fisherfolk on the coast and river
- Shadowbeasts, increasingly, after dark
```

Parsed into `Place.who_is_here: list[str]`.

### `## Connections` — optional, bullet list

`- ` bullets describing routes out of this place. Each entry should
name the connecting place and the direction or mode of travel.

```markdown
- The road north leads to the Obelisk Reach
- The river road northeast follows the Greywater toward the Mistwood Hills
- No major city within easy travel — Driftmoor is genuinely isolated
```

Parsed into `Place.connections: list[str]`.

### `## Dynamic State` — required, structured field list

Maintained by the monitor / orchestrator and consulted at scene entry.
Format is `- **Field:** value`. Recognised fields:

- `**Current threat level:** <str>` — free-form ("Calm", "Elevated", "Combat in progress").
- `**Weather:** <str>` — applies to outdoor places; indoor places typically omit.
- `**Recent events:** <str>` — short note about what just happened here.
- `**Active conditions:** <str>` — ongoing effects (lit/dark, flooded, magical).

Parsed into `Place.dynamic_state: dict[str, str]`.

The leading `*(Updated by monitor agent)*` metadata bullet is recognised
and skipped.

## Per-place companion files

A place directory may contain:

- `PLACE.md` — this file (required for the place to be loaded).
- `GEOMETRY.md` — zone graph and coordinates (`specs/GEOMETRY.md`).
- `CONTENTS.md` — perceptible items in the scene (`specs/CONTENTS.md`).
- `LORE.md` — DM-only deep lore (`specs/LORE.md`).
- Sub-place directories — recursive.

## Authoring rules

1. Every directory directly named after a location must have a
   `PLACE.md`. Container directories that aren't themselves places
   (e.g. `scenario/places/`) may have one describing the parent region.
2. Description should be self-contained — readers shouldn't need to
   open three other files to know what this place feels like.
3. Don't itemise inventory in `Description` — that's CONTENTS.md's job.
   Describe the *texture* (light, sound, smell, mood) and the *spatial
   sense* of the place.
4. Sub-place keys must match the directory name, including trailing
   slash convention (`driftmoor/` not `Driftmoor`).
5. Dynamic State fields should never contain the phrases `None`,
   `None yet`, or `Unknown` — write meaningful initial values, or
   drop the field.

## Open issues

- `Sub-Places` parsing keeps the full bullet string rather than
  separating key from description. Future work could split on the
  em-dash for structured navigation.
- `Connections` is also flat text; eventually a directed graph
  between places could be derived from it.
- No validator confirms `Sub-Places` keys correspond to actual child
  directories.
