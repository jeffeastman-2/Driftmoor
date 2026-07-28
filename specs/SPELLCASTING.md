# SPELLCASTING.md — Engine spec for spell economy

Status: **partially implemented (MVP)**. An engine spell resolver now exists
(`engine/spell_resolver.py`, with `SpellRuntimeState`): it enforces **slots** and
**concentration** and applies core spell effects for the spells in its book. The
implemented spells and their mechanics are catalogued in [SPELLS.md](SPELLS.md);
`engine/spell_resolver.py` is the source of truth. This document remains the
fuller target — components, rests, and the complete spell economy — that the MVP
converges toward; sections describing behaviour the resolver does not yet enforce
are the spec's *goals*, not current behaviour.

Historically the `## Spells` section of each character's `IDENTITY.md` was opaque
prose handed to the LLM, with slots and concentration unenforced — which let LLM
players re-cast leveled spells freely and stack concurrent concentration effects.
The MVP resolver closes that gap for its supported spells.

## Goals

1. Enforce per-day spell slot consumption per RAW (D&D 5e PHB Ch. 10).
2. Enforce one-concentration-at-a-time; casting a second concentration spell
   drops the first.
3. Track active spell effects with explicit durations (in rounds or minutes
   of game time) and let the game clock expire them.
4. Track class-feature uses separately from slots: Bardic Inspiration,
   Channel Divinity, Sorcery Points, Breath Weapon, etc.
5. Restore on long rest; partial restore on short rest where applicable
   (Warlock slots, BI at L5+, Sorcery Points at L20, etc.).
6. Leave cantrips at-will (no slot cost) but still subject to action economy
   and any per-spell limits like "only one Light at a time per caster".

## Out of scope (for now)

- Material component bookkeeping beyond a ritual/material flag.
- Counterspell timing and reaction stacks.
- Spell scrolls, scribed spellbooks, multiclass slot tables.
- Wild Magic surges.

## Source of truth

Authored in each character's `IDENTITY.md` under `## Spells` (or
`## Spells and Abilities` for half-casters and bards). The `character_loader`
will parse a structured block; everything outside the block remains free
narrative for the LLM.

### Proposed parseable schema (still markdown, still human-friendly)

```markdown
## Spells
**Spellcasting ability:** WIS | **Spell save DC:** 13 | **Spell attack:** +5

**Cantrips known (3, at-will):**
- Sacred Flame: 1d8 radiant, 60 ft, DEX save DC 13
- Light: object up to 10 ft cube, bright 20 / dim 20, 1 hr, one object at a time
- Spare the Dying: stabilize at 0 HP, touch

**1st-level spell slots:** 2 per long rest

**Prepared spells (4):**
- Bless *(Life domain — always prepared)* — 1 action, conc. 1 min, 30 ft, +1d4 to attacks/saves on 3 allies
- Cure Wounds *(Life domain — always prepared)* — 1 action, touch, 1d8+3
- Healing Word — 1 bonus action, 60 ft, 1d4+3
- Guiding Bolt — 1 action, 120 ft, 4d6 radiant, advantage on next attack
- Shield of Faith — 1 bonus action, 60 ft, conc. 10 min, +2 AC to one ally
- Sanctuary — 1 bonus action, 30 ft, conc. 1 min

**Concentration:** one at a time.
```

The parser only needs:

- `cantrips` → list of names.
- `slots_per_level` → `{1: 2}` for L1 cleric.
- `prepared` (cleric/druid/paladin/wizard) **or** `known` (bard/ranger/sorcerer/warlock) → list of `{name, level, action, range, duration, concentration: bool, save: str|None, components: str|None}`.
- `spellcasting_ability` and derived `save_dc`, `attack_bonus`.

Everything else (damage dice, descriptive text) stays prose for the LLM.

## Runtime state additions

`models/character.py` (`Character` dataclass):

```python
spell_slots_max: dict[int, int]           # {1: 2, 2: 0, ...}
spell_slots_used: dict[int, int]          # mirror, increments on cast
concentration: ActiveSpell | None         # None means free
class_feature_uses_max: dict[str, int]    # {"Bardic Inspiration": 3, ...}
class_feature_uses_remaining: dict[str, int]
```

`engine/active_effects.py` (new):

- `ActiveSpell` dataclass: name, caster_id, targets, expires_at_minute,
  concentration, on_break_callback.
- `EffectsRegistry` per scene session, ticked by the game clock at each
  turn boundary so durations expire automatically.

## Resolver flow

When a character's `intent` declares spellcasting (LLM output already
includes a `spell:` field — or the verb resolver detects the cast), the
new pipeline gates the action:

1. **Identify the spell** by name against the character's known/prepared list.
   Reject if unknown.
2. **Action economy check.** Reject if the action type (action / bonus action /
   reaction) conflicts with another action this turn. Concretely: only one
   leveled spell + one cantrip per turn unless the leveled spell is a bonus
   action, in which case the other action must be a cantrip.
3. **Slot check.** If leveled, find the lowest available slot ≥ spell level.
   If none, reject with `"<character> has no <N>th-level slots remaining"`.
4. **Concentration check.** If the new spell is concentration and the caster
   already has one active, drop the prior effect (with a recent_event log
   line: `"<caster>'s concentration on <prior> ends as they begin <new>"`).
5. **Range / line-of-sight check.** Re-use existing geometry helpers; reject
   if target is out of range or LOS-blocked.
6. **Apply effect.** For damage spells, hand off to `combat_resolver`. For
   buffs/debuffs/control, register an `ActiveSpell` in the effects registry.
7. **Decrement resources.** Slot used; class-feature uses decremented if the
   spell was a feature (e.g. Channel Divinity, Sorcery Point cost).

Cantrips skip steps 3 and (mostly) 4 but still hit 1, 2, 5, 6.

## Long / short rest

A new `engine/rest.py`:

- `take_long_rest(character)` — restores all slots, all class-feature uses,
  HP to max, hit dice up to floor(level/2). Currently a stub; eventually
  triggered by scene transition with `game_minutes` advance ≥ 480 or by an
  explicit player declaration during downtime.
- `take_short_rest(character)` — restores Warlock slots, BI (L5+),
  Channel Divinity, Breath Weapon, Bardic Inspiration die size where
  applicable. Triggered by 60-min rest declaration.

## Telemetry / logs

Each spellcast appends to the per-turn `attack_log`-equivalent
`spell_log` so the transcript can reproduce the chain:

```
Amara casts Bless (1st-level slot, conc. 1 min) on Seraphina, Thorgrim, Amara
  - slot expended (1/2 remaining)
  - concentration: Bless (replaces nothing)
  - effect registered until Day 1 16:11
```

## Migration path

1. **Parse + validate** (no enforcement). Parser reads the new schema, fills
   `spell_slots_max` and friends, but the resolver still doesn't gate on
   anything. Adds telemetry only ("would have rejected: no slots"). Lets us
   verify the parser without breaking live runs.
2. **Slot enforcement.** Reject leveled spell casts when no slot remains.
3. **Concentration enforcement.** Drop prior on new conc.
4. **Active effects + duration tick.** Buffs auto-expire; the perception
   block surfaces them so the LLM knows what's running.
5. **Long/short rest support.** Currently no rest mechanism — design that
   alongside scene transitions.

## Authoring rules for IDENTITY.md going forward

- Every spell-using character must have a `## Spells` (or `## Spells and
  Abilities`) section in the schema above.
- Always declare `Spellcasting ability`, `Save DC`, `Attack bonus` on the
  first line.
- Always declare slot table line: `**Nth-level spell slots:** X per long rest`.
- Cantrips and leveled spells in separate bullet lists, no mixing.
- Concentration spells must include `conc.` and a duration ("conc. 1 min",
  "conc. 10 min", "conc. up to 1 hr").
- Domain / always-prepared spells should be marked
  `*(Life domain — always prepared)*` so the parser excludes them from the
  prepared count.
- Save DC referenced inside individual entries should match the header line.

## Open questions — resolved

### Externally generated character content

Existing character files were drafted with help from external LLM
assistants (treat any/all of ChatGPT, Claude, Grok, Gemini, etc. as
interchangeable here). That content is **exemplary, not definitive**:
it served to seed the corpus, but the spec is the source of truth.
As the spec evolves we will migrate existing characters to match
— not the other way around. A validator pass that flags non-conforming
content (wrong level, wrong class list, wrong save DC, missing slot
line) is planned alongside Migration Step 1 (parse + validate).

### No subclassing of `PlayerCharacter`

`PlayerCharacter` will not be subclassed by caster type
(`ClericCharacter`, `WizardCharacter`, etc.). Reasons:

1. **Multiclass.** A `Cleric 3 / Fighter 2` does not fit a single
   class-typed subclass cleanly; picking the highest level is lossy
   and building a `MulticlassCharacter` re-implements everything.
2. **Composition beats inheritance.** Spellcasting is a capability,
   not an identity. A character either has a `SpellcastingProfile`
   attribute or does not. `if pc.spellcasting is not None:` is the
   gate.
3. **Most engine code is class-agnostic.** The resolver, combat,
   movement, and perception subsystems do not care whether the
   character casts spells. Only the spell pipeline cares, and it is
   gated by the attribute.
4. **Other class-feature systems will follow the same shape.** Rage,
   Channel Divinity, Sneak Attack, Wild Shape, Ki points, Sorcery
   Points are all "uses per rest of a named feature". One
   `class_features: dict[str, FeatureUses]` registry covers them all.

Resulting model:

```python
@dataclass
class PlayerCharacter(Character):
    # ... existing fields ...
    classes: list[ClassLevel] = field(default_factory=list)
    spellcasting: SpellcastingProfile | None = None
    class_features: dict[str, FeatureUses] = field(default_factory=dict)
```

`ClassLevel` carries `{class_name, level, subclass}`. For multiclass
casters, the combined slot table is derived from the sum of caster-
level contributions per PHB multiclass spellcasting rules (full
casters count full, half casters half, third-casters one-third).
That lookup lives in a single helper, so per-class IDENTITY.md lines
remain compact.

### Ritual casting

Some spells carry a **`ritual`** tag in the PHB. Casters with the
**Ritual Casting** class feature may cast a ritual-tagged spell they
have prepared/known without expending a spell slot by taking
+10 minutes to cast it.

Who has Ritual Casting at level 1 by default:

- **Wizard** — any ritual-tagged spell in their spellbook.
- **Cleric** — any ritual-tagged spell currently prepared.
- **Druid** — any ritual-tagged spell currently prepared.
- **Bard** — any ritual-tagged spell currently known (Bards gain
  ritual casting at level 1 in 5e 2014; in 5e 2024 the timing has
  shifted, confirm against the player's edition).

**Sorcerer and Warlock do not get ritual casting at all** in 5e 2014
without the Ritual Caster feat.

Spec impact is small. Add:

- `ritual: bool` flag to the parsed `Spell` dataclass.
- `ritual_caster: bool` to `SpellcastingProfile`.

Resolver gate:

```python
if spell.ritual and caster.spellcasting.ritual_caster \
        and intent.cast_time_minutes >= 10:
    # cast without slot expenditure
else:
    # normal slot consumption path
```

This is a minor extension once slot machinery is in place.
**Deferred until Migration Step 2 (slot enforcement) ships.**

### Half-casters and partial casters

Paladin and Ranger gain spellcasting at level 2. Aeliana (Ranger) and
Seraphina (Rogue) do not need spellcasting profiles at level 1.
Arcane Trickster (Rogue 3+) and Eldritch Knight (Fighter 3+) get
limited spellcasting; when those subclasses appear, treat them as
third-casters in the multiclass slot table.
