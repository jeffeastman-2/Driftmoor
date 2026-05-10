# LORE.md FORMAT SPECIFICATION

`LORE.md` is a DM-only deep-context document attached to a place, NPC, or
plotline. It holds the *truth* of what something is — the mechanics, the
history, the secrets that the DM uses to adjudicate but that players
discover only through play.

## How the engine uses LORE.md

LORE.md is **not** structurally parsed. There is no Python module that
reads `LORE.md` today. It is intended for one of two uses:

1. **Author / DM reference.** Read by the human author while writing
   adjacent files (CONTENTS.md interactions, scene scripts, NPC
   knowledge). Kept under source control so the canonical truth lives
   alongside the scenario it governs.
2. **DM-agent context (future).** When the DM agent runs in advisory
   mode, LORE.md will be loaded into its prompt to ground adjudications.
   This is not wired up yet. Authors should still write it as if the
   agent will read it.

Because no Python parser exists, the schema below is an authoring
convention. Sections are for the DM (human or AI) — not for code.

## Header banner (required)

```markdown
# LORE.md — <Display Name of Subject>
## DM Eyes Only

---
```

The `DM Eyes Only` line is the load-bearing convention: anything in
this file is privileged information and must never be shown verbatim
to players. It exists so that a careless `grep` or context dump can be
caught before the secret leaks into a prompt.

## Recommended sections

Add or omit as the subject demands. The sections used in current LORE
files (`scenario/places/mistwood_hills/fey_glade/LORE.md`):

### `## Origin`

Where this thing came from, when, and what it actually is. The version
of the story that is true, distinct from whatever the local population
believes.

### `## What [It] Does`

The mechanism. If the subject is a magical pool, what does looking into
it actually do? If an NPC, what are they really concealing? Concrete,
not allusive.

### `### The Cost`, `### The Cycle`, `### The Trigger`, etc.

Sub-sections under the mechanism detailing knock-on effects, timing,
costs, and conditions for activation. Diegetic in tone but precise in
content — the DM should be able to adjudicate "what happens if X" from
the text alone, without inventing on the fly.

### `## The Barrier` / `## The Bond` / `## The Curse` / etc.

Subject-specific named features. Whatever names the lore introduces,
each gets its own section so they're easy to find.

### `## What the Party Can Discover`

A graded list of revelations:

- What's apparent on first arrival.
- What a successful Investigation or Insight uncovers.
- What only a specialist (Elyssa, Lilar's order, a fey-touched character)
  can recognise.
- What can only be learned by experiencing the danger.

This section is the bridge between the lore and the play surface —
it converts secret truth into authored interactions for CONTENTS.md.

### `## Resolution Conditions`

If this lore element is part of a quest, what counts as "resolved"?
Multiple endings allowed; spell out each.

### `## Open Threads`

Hooks that lead elsewhere. Other places that reference this lore.
NPCs whose backstory intersects.

## Authoring rules

1. **Always include the `## DM Eyes Only` banner.** Treat this as the
   marker that delimits privileged content. Any process that aggregates
   markdown for player-facing prompts must strip files containing this
   string.
2. **Be diegetic but precise.** Lore is prose, not bullet-point game
   text, but should be specific enough to adjudicate from.
3. **State the mechanism, not just the mystery.** If a pool "drains
   memory", say *which* memories, on *what schedule*, and *what reverses
   it* (if anything). Mystery in player-facing material; clarity here.
4. **Cross-reference companion files.** When CONTENTS.md authors an
   interaction whose authored response leaks lore, the response should
   not exceed what's safe to reveal at that interaction's difficulty
   level. The LORE entry tells you the ceiling.
5. **Keep one LORE.md per subject.** If a region contains three secrets
   that don't otherwise interact, each gets its own LORE.md in the
   appropriate sub-directory.

## Where LORE.md lives

- `scenario/places/<region>/<sub>/LORE.md` — for place-bound secrets
  (the fey glade pool, the carvings on a chamber wall, etc.).
- `scenario/people/.../LORE.md` (future) — for NPCs whose true history
  is too sensitive for SOUL.md, where another NPC might inadvertently
  see it during prompt aggregation. Not currently used.
- `scenario/things/<artifact>.md` mixes player-facing description with
  some lore today; pull the secret half into a separate LORE.md when
  the artefact's mechanics become discoverable.

## Open issues

- No automated check that `DM Eyes Only` files are never bundled into
  player or NPC prompts. Add a guard in the prompt-builder when DM
  agent integration begins.
- No structured "what's safe to reveal at depth N" gating between
  LORE.md and CONTENTS.md interactions — currently relies on author
  discipline.
