# IDENTITY.md FORMAT SPECIFICATION

`IDENTITY.md` is the *scenario-facing* character sheet — what the character
shows the world. It contains everything observable, mechanical, or
situationally adjustable. Compare with `SOUL.md`, which holds the deep
unchanging core (values, fears, voice). See `specs/SOUL.md`.

Parsers:
- `models/character_loader.py::parse_player_identity` — for PCs in
  `scenario/people/players/<name>/IDENTITY.md`.
- `models/character_loader.py::parse_npc_identity` — for NPCs in
  `scenario/people/npcs/<name>/IDENTITY.md`.

Both parsers use section-prefix matching (case-insensitive), so heading
wording can vary mildly (`## Spells` and `## Spells and Abilities` both
work). Sections may appear in any order, and unknown sections are ignored.

## Title line (required)

```markdown
# IDENTITY.md — <Full Display Name>
```

Used as a fallback for the character's name if `Full Name` field is absent.

## Sections

### `## Static Profile` (PC) — required, structured field list

Pipe-style `- **Field:** value` entries. Recognised keys:

| Field | Type | Notes |
|---|---|---|
| Full Name | str | Authoritative display name. |
| Player | str | Free text; "TBD" allowed. |
| Race | str | `Human`, `Half-Elf`, `Dragonborn (Red)`, etc. |
| Class | `<Class>, Level <N>` | Parser splits on the comma; level extracted as int. |
| Background | str | 5e background label. |
| Alignment | str | e.g. `Chaotic Good`. |
| Pronouns | str | Optional; not parsed but read by LLM. |

### `## Physical Description` — required, free prose

Single paragraph. Surfaced verbatim to the LLM and to perception
contexts when other characters observe this one.

### `## Combat Statistics` — required, structured field list

Recognised fields:

- `**HP:** <int>` — max hit points.
- `**AC:** <int> (<source>)` — armour class; the leading integer is parsed.
  Parenthetical source text is ignored.
- One stat line with all six abilities:
  `**STR:** 14 (+2) | **DEX:** 10 | **CON:** 12 (+1) | **INT:** 10 | **WIS:** 16 (+3) | **CHA:** 14 (+2)`
  Each ability is extracted from `**<ABBR>:** <int>`.

### `## Abilities and Proficiencies` — optional, bullet list

`- ` bullets describing class features, skill proficiencies, racial traits.
Each line becomes one entry in `Character.abilities: list[str]`.

### `## Spells` or `## Spells and Abilities` — optional, structured

Follows `specs/SPELLCASTING.md`. Currently parsed only as a flat list of
strings (one per `- ` bullet). Bold subheaders (`**Cantrips known...**`)
and non-bullet lines are skipped silently. The future structured parser
will read save DC / attack bonus / slot tables / concentration flags.

### `## Equipment` — required, bullet list

`- ` bullets. Each entry becomes one string in `Character.equipment`.
Free text — no mechanical parsing today.

### `## Dynamic State` — required, structured field list

Updated each round by the monitor / orchestrator. Recognised fields:

- `**Current HP:** <int>`
- `**Mood:** <str>`
- `**Disposition toward party:** <str>`
- `**Open threads:** <semicolon-separated>` — split on `;` into a list.
  `None` / `None yet` produces an empty list.

The leading `*(Updated by monitor agent each round)*` line is recognised
as metadata and skipped by `_parse_list_items`.

## NPC variant — sections specific to NPCs

NPCs use the same skeleton but with additional sections:

- `## Role` — single-line role descriptor.
- `## Key Relationships` — bullets of `- **Name:** Description`. Parsed
  into a `dict[str, str]`.
- `## What He Knows` / `## What She Knows` / `## What They Know` — bullet
  list of knowledge items. Heading variant chosen by character's pronouns.
- `## Adventure Hooks` / `## Adventure Hooks He Can Offer` / etc. — bullet
  list of plot hooks.
- `## What He Wants From the Party` / `## What She Needs From the Party` /
  etc. — bullet list, merged into `hooks` at parse time.
- Dynamic state may include `**Current mood:**` and `**Active concerns:**`
  or `**Active schemes:**` (comma- or semicolon-separated).

NPCs also accept optional `HP`, `AC`, and ability scores in `Combat
Statistics` (used by NPCs that may enter combat, like Fennel).

## Family-file variant

NPCs may be defined as a single `.md` file inside a household directory
(e.g. `scenario/people/families/haversteads/davin.md`) rather than a
folder with `IDENTITY.md` + `SOUL.md`. Family-file format:

- `# <Name> — <Role, age N>` as the title (em-dash separator parsed).
- `## Role`, `## Physical Description`, knowledge headings, and
  `## Adventure Hooks` are the recognised sections.
- No separate SOUL.md — the file is the whole character.

## Authoring rules

1. Heading text must start with `## ` followed by the heading name; deeper
   headings inside a section are ignored by the parser but visible to the
   LLM.
2. Field syntax is strict: `- **<Field>:** <value>`. Mis-bolded or
   alternate punctuation prevents extraction.
3. Lists must use `- ` (with the trailing space) or `1. ` numbered form.
4. Metadata bullets that start with `*(` are silently skipped.
5. The first list bullet after a heading determines the section's parsed
   items; intervening prose paragraphs are ignored.

## Open issues

- `## Spells` parsing is flat; structured spell economy is pending
  (see `specs/SPELLCASTING.md`).
- Equipment is flat strings; integration with `specs/WEAPONS.md` and
  `specs/ARMOR.md` libraries is not yet automatic.
- No validator pass exists today. Author-time errors surface only when
  a field is missing and the runtime substitutes a default.
