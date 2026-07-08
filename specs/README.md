# Specs

Format specifications for the markdown files that compose a Driftmoor
scenario, plus engine-side design specs for evolving subsystems.

These files document **how the engine reads scenario content** and
**how authors should write that content**. They are the source of
truth for file formats; loader code in `models/` and `engine/` is
expected to conform.

## Scenario file formats

| Spec | Subject | Status |
|---|---|---|
| [CONTENTS.md](CONTENTS.md) | Perceptible items in a scene | implemented |
| [SCENE.md](SCENE.md) | Scene configuration (cast, placement, routing, carry state) | implemented |
| [GEOMETRY.md](GEOMETRY.md) | Zone graph and coordinates | implemented |
| [IDENTITY.md](IDENTITY.md) | Character sheet (PC + NPC) | implemented |
| [SOUL.md](SOUL.md) | Character inner-life context (LLM blob) | convention only |
| [PLACE.md](PLACE.md) | Location description and dynamic state | implemented |
| [LORE.md](LORE.md) | DM-only deep context | convention only |
| [WEAPONS_ARMOR.md](WEAPONS_ARMOR.md) | Weapon and armor library tables | implemented |
| [EXPLORATION.md](EXPLORATION.md) | Party exploration momentum and anti-loop policy | draft |

## Engine subsystem specs

| Spec | Subject | Status |
|---|---|---|
| [SPACE_TIME.md](SPACE_TIME.md) | Spatial and temporal architecture | implemented |
| [SPELLCASTING.md](SPELLCASTING.md) | Spell economy (slots, concentration, rests) | draft |

## Status legend

- **implemented** — a Python parser reads files in this format and
  the spec describes that parser's contract.
- **convention only** — no parser exists; the file is loaded as
  opaque text or read by humans. The spec documents authoring
  conventions, not a code contract.
- **draft** — design specification for work not yet shipped. The
  spec describes the *target* shape; code does not yet enforce it.

## Authoring discipline

When changing a file that has an implemented spec, update both the
spec and the corresponding parser/loader in one commit. When the spec
disagrees with what the parser actually does, the parser is the
ground truth — but that's a bug to fix in the spec.

When adding a new markdown file type used by any loader, write the
spec first. Specs live here, not next to the source files they
describe, so authors can find them in one place.
