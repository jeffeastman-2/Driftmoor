# SOUL.md FORMAT SPECIFICATION

`SOUL.md` is the *deep, slow-changing* core of a character — the values,
fears, wounds, voice, and contradictions that drive behaviour. Compare with
`IDENTITY.md` (`specs/IDENTITY.md`), which holds the observable, mechanical,
scenario-adjustable sheet.

## How the engine uses SOUL.md

SOUL.md is **not** structurally parsed. The engine loads it as an opaque
text blob and injects it into the LLM prompt for player and NPC roles
(see `engine/bridge.py::load_character`, `engine/player_router.py`,
`engine/md_loader.py`).

Concretely:
- `Character.soul_raw: str` holds the full file text.
- The text is passed to the LLM at every turn as the character's
  inner-life context, alongside the structured IDENTITY fields.

Because there's no parser, the schema below is an *authoring convention*,
not a runtime contract. Sections are for the LLM's benefit, not Python's.
Adding or renaming sections will not crash anything; it will only change
the model's behaviour.

## Title line (required)

```markdown
# SOUL.md — <Full Display Name>
```

Matches the corresponding IDENTITY.md title for consistency.

## Recommended sections

These section headings have proved useful across PCs and major NPCs.
Drop any that don't apply; add character-specific ones freely.

### `## Core Identity` — short profile

3–6 `- **Field:** value` bullets restating the essentials so the LLM
sees them even when IDENTITY isn't co-loaded:

```markdown
- **Full Name:** ...
- **Player:** ...
- **Race/Class:** ...
- **Alignment:** ...
```

### `## Values and Drives`

Bullet list of motivations stated as actionable beliefs, not adjectives.
"She heals because suffering she can prevent and does not is a wrong she
refuses to carry" — not "compassionate".

### `## Fears and Wounds`

Bullet list of vulnerabilities. Specific incidents preferred over
abstract categories. Lets the LLM portray genuine reluctance, evasion,
or unexpected anger when the right pressure point is touched.

### `## Voice and Manner`

Bullet list describing how the character speaks and moves. Used by the
LLM to shape diction, pacing, and physicality:

- Word choice (formal/informal, archaic/contemporary).
- Pacing (slow and deliberate, rapid-fire, halting).
- Default emotional tone.
- What changes under stress.
- Humour mode.

### `## Loyalties`

Bullet list of allegiances, with their complexity. "Her order, with the
complexity of someone who believes in the mission more than the
institution." Useful for adjudicating conflicts of obligation.

### `## Internal Contradiction`

Free prose, ideally one or two paragraphs. Names the irreducible tension
the character carries — the thing they cannot resolve. The LLM uses
this to portray hesitation, ambivalence, or out-of-character bursts at
plausible moments.

### Character-specific sections

Free to add. Examples that appear in current SOUL.md files:

- `## The Holy Symbol` — Amara: a particular object and its meaning.
- `## What the Pool Remembers` — for characters with mystical tethers.
- `## The Bond` — for characters with a sworn pact or relationship.

## Authoring rules

1. **Write to the LLM, not to Python.** The whole file is prose context.
   No field will be extracted; structure exists only to help the LLM
   organise itself.
2. **Prefer specificity over abstraction.** "Kind" is useless. "Apologises
   when someone else makes a mistake, even when it costs her" is usable.
3. **Avoid contradicting IDENTITY.md mechanics.** SOUL.md can colour how
   a character uses their abilities; it should not silently grant new
   ones. New mechanical capabilities belong in IDENTITY.md.
4. **Keep it under ~2 KB when possible.** SOUL.md is included in every
   prompt that involves this character. Excess length burns tokens
   without proportionate behaviour change.
5. **No structured field lines outside `## Core Identity`.** Don't
   tempt future parser work by mixing `- **Field:** value` lines into
   the narrative sections.

## NPC vs. PC SOUL.md

NPCs may use a lighter SOUL.md — sometimes only `## Values and Drives`,
`## Voice and Manner`, and `## Loyalties`. The full set is reserved for
PCs and major recurring NPCs (Elden, Fennel, Elyssa, etc.). Family-file
NPCs (`davin.md`, `tessa.md`) typically have no separate SOUL.md at all;
their personality fits inside the single file alongside IDENTITY content.

## Open issues

- No validator. A missing or empty SOUL.md silently degrades the LLM's
  characterisation without any visible warning.
- Some legacy SOUL.md files mix structured bullets into narrative sections;
  fix opportunistically when editing.
