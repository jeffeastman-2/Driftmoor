# CONTENTS.md FORMAT SPECIFICATION

This document specifies the canonical CONTENTS.md format for all
scene/place content files in the Driftmoor engine.

A **CONTENTS.md** file describes the *contents* of a place: the
creatures that inhabit it, the chambers/sub-areas it contains, the
named landmarks within it, and the **items** that exist there.
GEOMETRY.md is the authoritative source for *where* things are;
CONTENTS.md is the authoritative source for *what they are* and *what
happens when characters interact with them*.

The exemplar / reference implementation is:

    scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md

Any change to this spec MUST be reflected in the exemplar before
being adopted elsewhere.

---

## File Locations

Every place may have a CONTENTS.md adjacent to its PLACE.md and
GEOMETRY.md:

    scenario/places/<place_path>/CONTENTS.md

Regional places (driftmoor/, obelisk_reach/) may have a CONTENTS.md
that summarizes the *region*. Scene-level places (echoing_caverns,
fey_glade) have a CONTENTS.md that defines the runnable scene's
content. The format below applies to scene-level files; regional
files are looser and not parsed mechanically.

---

## File Structure

A scene-level CONTENTS.md is composed of the following top-level
sections, in this order. Sections marked **(required)** must be
present; sections marked **(optional)** may be omitted.

1. **File heading** — required. Single H1 line.
2. `## Creatures` — optional.
3. `## Zone Descriptions` — optional but strongly recommended for
   multi-zone scenes.
4. `## Landmarks` — optional.
5. `## Items` — optional.
6. `## Notes for DM` — optional.

Sections may not be reordered. Additional sub-headings within a
section are permitted and free-form.

---

## File Heading

```
# CONTENTS.md — <Scene Display Name>
```

A single H1 line, beginning with `# CONTENTS.md — `. The scene
display name SHOULD match the corresponding GEOMETRY.md and
PLACE.md.

---

## Creatures Section

Free prose. Lists the creatures expected in the scene with brief
notes on count, location, and behavior. Cross-references to
`scenario/creatures/<creature_id>.md` are encouraged for any
creature with a stat block.

This section is **not parsed** by the engine. Placement (of characters and
creatures alike) is authored per-scene in `scenes/<scene>.md` — GEOMETRY.md is a
pure stage and no longer carries a `## Starting Positions` table.

Example:

```markdown
## Creatures
- Giant spider: lairs in the Secret Chamber, clinging to the ceiling.
  See `scenario/creatures/giant_spider.md`.
- Shadowbeasts: 2d4 in the deeper chambers.
```

---

## Zone Descriptions Section

```
## Zone Descriptions

### <Zone Name>
<player-facing prose>

*Connections:* <prose describing how this zone links to others>
```

One `###` sub-heading per zone. Zone names MUST match the zone
names in GEOMETRY.md (case-insensitive). "Zone" is the engine's
structural term; the player-facing prose under each heading is free
to call the place a chamber, room, clearing, alcove, hall, etc. as
fits the scene's locale.

The prose is free-form and player-facing — it is shown to the
LLM-driven characters as part of their scene context. Keep it
sensory and concrete. Avoid mechanical jargon (DC values, hit
points, etc.) — those belong in `## Notes for DM` or in item
Interactions blocks.

The `*Connections:*` italicized line is recommended at the end of
each zone description and lists the doorways, passages, and secret
routes leaving it.

This section is **not parsed** by the engine for individual zone
extraction; the entire section is included in the scene context as
prose.

---

## Landmarks Section

```
## Landmarks

<optional intro paragraph>

- **<landmark_id>** — <description>
- **<landmark_id>** — <description>
```

A bulleted list. Each bullet begins with the landmark's id (in
`**bold**`), an em-dash, and a one- or two-sentence description. The
id MUST match an entry in GEOMETRY.md's `## Landmarks` table.

Landmarks are named waypoints — archways, thresholds, doorway-
equivalents — at zone seams. They are NOT items. Characters use them
as movement destinations.

---

## Items Section

This is the **structured** section. Parser-targetable.

```
## Items

### <item_id>
<one or more paragraphs of player-facing description>

*<properties parenthetical>*

*Interactions (DM ground truth):*
- **<verb>** [(<condition>)] → <DM-authoritative response>
- **<verb>** [(<condition>)] → <DM-authoritative response>
```

### Item id

`### <item_id>` heading line. The id is `[a-z][a-z0-9_]*`,
snake_case, no spaces. It MUST match an entry in the corresponding
GEOMETRY.md's `## Items` table — the parser cross-validates.

### Prose

One or more paragraphs of free-form, player-facing text describing
what a character sees on first encounter with the item. This is
shown to player LLMs verbatim. Keep it sensory; avoid mechanical
jargon.

### Properties parenthetical

A single italicized parenthetical line at the end of the prose
(before any Interactions block):

```
*(<fact>; <fact>; <fact>)*
```

Facts are separated by `;` (preferred) or by `. ` (period followed by
whitespace, which lets writers use natural sentence punctuation). The
parser recognizes the following **reserved keywords**; all other text
is preserved verbatim and shown to LLMs but not interpreted by the
engine.

| keyword                            | meaning                                       |
|------------------------------------|-----------------------------------------------|
| `pickup-able` or `pickable`        | the item can be picked up                     |
| `not pickup-able` or `not pickable`| the item cannot be picked up                  |
| `flavor`                           | item exists for atmosphere; no mechanics      |
| `pressable`                        | item responds to a "press" verb               |
| `quest item for <character_id>`    | item matters to a named NPC                   |
| `see <other_item_id> for interactions` | inherits Interactions from another item   |

Examples:

```
*(Not pickup-able; flavor.)*
*(Pickup-able; +1 mace, 1d6+1 bludgeoning.)*
*(Not pickup-able; pressable. See trigger_glyph_top for interactions.)*
*(Pickup-able with care; quest item for elden.)*
```

A properties parenthetical is OPTIONAL. If absent, the item defaults
to: not pickup-able, no special verbs, descriptive flavor only.

### Size and Appearance by distance

Two OPTIONAL, related lines/blocks control how an item is perceived at a
distance. They model perspective the way 3-D graphics do: an object's
**apparent size** is roughly `physical_size / distance`, so a small item
(a dropped torch) becomes unidentifiable far sooner than a large one (a
head-high obelisk).

A `*Size:*` line declares the item's largest physical dimension, either as
a D&D size keyword or an explicit measurement:

```
*Size:* large
*Size:* 6 ft
```

| keyword      | ~largest dimension |
|--------------|--------------------|
| `tiny`       | 1 ft               |
| `small`      | 2.5 ft             |
| `medium`     | 5 ft (default)     |
| `large`      | 10 ft              |
| `huge`       | 15 ft              |
| `gargantuan` | 25 ft              |

If no `*Size:*` line is present the item is treated as a medium (5 ft)
object.

The engine buckets the apparent size into four bands — `near`,
`intermediate`, `far`, `distant` — and, below the smallest band, the item
is too small to make out at all (omitted from perception). An optional
`*Appearance by distance:*` block supplies authored descriptions for the
vaguer bands:

```
*Appearance by distance:*
- **intermediate** → a short, pale length of wood lying on the stone
- **far** → a slim pale streak low on the cavern floor
- **distant** → a faint pale fleck against the dark floor
```

Resolution per band:

- `near` / `intermediate` → the item is **identified** (its label is shown),
  unless an authored description for that band overrides it.
- `far` / `distant` → an authored description is shown if present; otherwise
  a generic "an indistinct shape, too far to make out".
- below `distant` → the item is too small to perceive and is omitted.

Once any character in the party has examined the item, its identity is known
and the distance banding no longer applies (it is always recalled by label).

Both the `*Size:*` line and the `*Appearance by distance:*` block sit between
the prose/properties and the Interactions block. Both are OPTIONAL.

### Interactions block

Opens with the exact literal line:

```
*Interactions (DM ground truth):*
```

Followed by zero or more bullet lines, each of the form:

```
- **<verb>** [(<condition>)] → <result text>
```

Where:

- **`<verb>`** — one or more words, lowercased. Alternative phrasings
  may be separated by ` / ` (slash with surrounding spaces). The
  parser canonicalizes the verb to the first listed phrasing for
  internal lookups. Examples:
  - `**examine**`
  - `**pick up / take**`
  - `**read / decipher**`
  - `**press**`

- **`<condition>`** (optional) — a free-text precondition or cost.
  May be written either *inside* or *outside* the bold span; both are
  accepted, with inside-bold preferred for short conditions and
  outside-bold reserved for longer or compound ones. The engine does
  not pattern-match condition text initially; it is shown to the DM
  agent as part of the response context. Examples:
  - `**press (when crack is closed)**` — inside the bold
  - `**make rubbing** (requires parchment + charcoal, 30 min/panel)` — outside
  - `**dig out / open** (1 turn)`

  When the same verb appears multiple times with different conditions
  (e.g. `press` for closed vs open), each is parsed as a separate
  interaction. The condition is the discriminator.

- **`→`** — the literal arrow character `→` (U+2192) separates verb
  and result. ASCII `->` is also accepted by the parser but the
  exemplar uses `→`.

- **`<result text>`** — the DM-authoritative response. Free text.
  May continue onto subsequent indented lines. This text is what the
  engine surfaces to the DM agent (and, eventually, directly to the
  acting player) when this verb is invoked on this item.

The Interactions block is OPTIONAL. If absent, the engine treats
the item as having only an implicit `examine` interaction, which
returns the prose paragraphs.

### Cross-references

When several items share the same Interactions (e.g. the three
trigger glyphs in Echoing Caverns), the dependent items omit the
Interactions block and use a properties-parenthetical reference:

```
### trigger_glyph_middle
The middle of three glyphs on the west wall...

*(Not pickup-able; pressable. See trigger_glyph_top for interactions.)*
```

The parser resolves `see <id> for interactions` by copying the
referenced item's Interactions block. The reference target MUST
exist in the same CONTENTS.md.

---

## Notes for DM Section

```
## Notes for DM
- <bullet>
- <bullet>
- **<topic heading>:** <multi-sentence note>
```

Free prose, typically as bullets. This section contains
DM-authoritative scenario information that should NOT be revealed to
players directly: secret door sequences, monster tactics,
trap-springing conditions, NPC motivations, etc.

The DM agent receives this section in its context every turn.
Player LLMs do not.

This section is **not parsed** by the engine; it is passed through
verbatim to the DM context.

---

## Item Lifecycle and the Engine

The parser (`models/contents_loader.py`) produces, for each item, a **`Thing`**
(`models/thing.py`) — the unified type that also represents weapons, armor,
consumables, and shop goods. The fields authored here:

```python
@dataclass
class Thing:
    id: str                              # from heading
    description: str = ""                # prose paragraphs

    # Properties (from the italicized parenthetical line)
    pickable: bool = False
    flavor_only: bool = False
    pressable: bool = False
    quest_item_for: Optional[str] = None
    extra_facts: list[str] = ...         # unrecognized parenthetical text

    # Perception (from *Size:* and *Appearance by distance:*)
    size_ft: float = 0.0                 # largest dimension; drives apparent-size bands
    weight_lb: float = 0.0               # encumbrance
    appearance_bands: dict[str, str] = ...   # near/intermediate/far/distant text

    interactions: list[Interaction] = ...    # in source order
    interactions_ref: Optional[str] = None   # cross-reference target id, if any

    # Populated from GEOMETRY.md by the loader (when a SceneGeometry is given):
    position: Optional[Position] = None
    zone: Optional[str] = None
    label: str = ""

    # Mutable runtime state:
    holder: Optional[str] = None         # character_id if picked up
    state: dict = ...                    # interaction-set flags
    discovered_by: set[str] = ...        # character_ids who know it exists
```

`Thing` carries additional facets that CONTENTS.md does **not** author:

- **affordances / effects** are *derived* at load time (`thing.derive_affordances`)
  from the item's shape — a `*Weapon:*` line makes it wieldable, consumable
  keywords make it edible/drinkable, and so on. Authors describe *what the item
  is*; the engine infers *what you can do with it*. (See the affordance-gated
  verb model in the top-level README.)
- **carry-state** (`in_world` / `carried` / `in_hand` / `worn` / `consumed`)
  tracks where a possessed Thing lives; starting carry-state for a character's
  kit is authored in `scenes/<scene>.md`, not here.
- the **market facet** (`price` / `vendor_id` / …) is populated only for shop
  goods (`models/thing_loader.py`) and left empty for a rapier on a cave floor.

`Interaction` minimally:

```python
@dataclass
class Interaction:
    verb: str                # canonical verb
    aliases: list[str]       # other verbs that resolve here
    condition: str           # parenthetical text, free-form for now
    response: str            # DM-authoritative text
```

An item's interactions are stored as a `list[Interaction]` in source
order — the same verb may appear more than once with different
conditions, and both must be preserved.

The engine resolves player intents to interactions by matching
against `verb` and `aliases`. When no match exists, the DM agent
adjudicates. When the player is not adjacent to the item (within ~5
ft), the engine refuses pre-DM.

---

## Validation

A CONTENTS.md is valid when:

1. The file heading matches the canonical `# CONTENTS.md — <name>`
   form.
2. Every `### <item_id>` under `## Items` corresponds to a row in
   the corresponding GEOMETRY.md's `## Items` table.
3. Every row in GEOMETRY.md's `## Items` table corresponds to a
   `### <item_id>` heading under `## Items` in CONTENTS.md.
4. Every landmark id used in the Landmarks section corresponds to a
   row in GEOMETRY.md's `## Landmarks` table.
5. Every `see <id> for interactions` cross-reference resolves to a
   sibling item in the same CONTENTS.md.
6. Every Interactions bullet line parses as
   `- **<verb>** [(<condition>)] → <result>`.

The parser MAY warn (not fail) on:

- Unrecognized properties keywords (preserved as `extra_facts`).
- Items in CONTENTS.md with no GEOMETRY.md row, when the engine
  would expect a position. Some items (region-level "carved
  symbols", flavor items spread across a zone) may legitimately omit
  position; these should be flagged in the properties as `flavor`.

---

## Migration Status

As of this spec's introduction, only the following CONTENTS.md
files conform fully:

- `scenario/places/obelisk_reach/echoing_caverns/CONTENTS.md` (canonical exemplar)

Other CONTENTS.md files in the workspace pre-date this spec and use
ad-hoc formats. They will be migrated incrementally once the
parser exists and the format has stabilized through use.

Until then: **do not migrate other CONTENTS.md files by hand**. The
spec WILL change as the parser is built and edge cases surface.
Premature migration creates churn.
