# Echo Chamber

## Description
The largest space in the caverns, this chamber throws every sound back late and wrong. Torchlight cannot fully claim the ceiling, and the room feels shaped to amplify dread. A half-buried obelisk fragment occupies the center while carved script crowds the walls.

A hairline seam and three trigger glyphs on the west wall hide a worked passage. Two descents on the south side lead deeper: one dry, one wet.

## Ambient
- light: torchlight fades before reaching the vault height
- sound: strong unnatural echoes and poor sound localization
- smell: cold stone with faint metallic undertone near the fragment
- temperature: cold and still
- footing: mostly level stone with rough edges near walls

## Items
### carved_symbols
- label: Carved symbols
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Dense angular script carved in long continuous lines across the chamber walls.
- appearance by distance:
  - intermediate: walls crowded with angular carvings
  - far: layered carved texture around the room
  - distant: faint patterned walls with unreadable detail
- interactions:
  - examine: The script is intentional and extensive, but unreadable to current party members.
  - search: These carvings are inscription, not a lock mechanism.
  - read: The language cannot be deciphered by anyone currently in Driftmoor.

### obelisk_fragment
- label: Obelisk fragment
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A dark slab half-buried in the floor, warm to the touch and faintly humming.
- appearance by distance:
  - intermediate: a broad black slab protruding from the stone
  - far: a dense dark mass near center floor
  - distant: a deeper patch of darkness in the chamber
- interactions:
  - examine: The hum is physically perceptible and seems to react to mention of the obelisk.
  - search: No practical seam or leverage point allows mundane removal.

### trigger_glyph_top
- label: Trigger glyph (top)
- size: tiny
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: The upper mark in a vertical set of three glyphs beside a hairline seam.
- appearance by distance:
  - intermediate: a small cut glyph near the seam
  - far: a tiny notch-like mark on the wall
  - distant: too small to resolve
- interactions:
  - examine: One of three pressable glyphs that control the hidden wall mechanism.
  - press: Pressing gives a dry click; effect depends on sequence state.

### trigger_glyph_middle
- label: Trigger glyph (middle)
- size: tiny
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: The middle glyph in the same vertical mechanism set.
- appearance by distance:
  - intermediate: a second cut glyph beneath the top mark
  - far: a tiny notch-like mark on the wall
  - distant: too small to resolve
- interactions:
  - examine: Part of the three-glyph sequence lock.
  - press: Pressing gives a dry click; effect depends on sequence state.

### trigger_glyph_bottom
- label: Trigger glyph (bottom)
- size: tiny
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: The lowest glyph in the lock set beside the seam.
- appearance by distance:
  - intermediate: a third cut glyph below the others
  - far: a tiny notch-like mark on the wall
  - distant: too small to resolve
- interactions:
  - examine: Completes the three-glyph sequence lock.
  - press: Pressing gives a dry click; effect depends on sequence state.

## Features / landmarks
- echo_chamber_arch: north opening to First Passage
- rocky_passage_squeeze: west seam that opens into Rocky Passage when unlocked
- deep_passage_descent: southwest descent toward Bone Chamber route
- pool_passage_descent: southeast descent toward Pool Cavern route

## Creatures present
- none

## Exits
- north: First Passage
- west: Rocky Passage (when west seam is opened)
- south-west: Deep Passage
- south-east: Pool Passage

## Puzzles

### west_wall_glyph_sequence
*Type: sequence*

The three trigger glyphs form one ordered lock. Pressing them **top -> bottom
-> middle** opens the west seam. Pressing any glyph once it is open closes it;
an out-of-order press resets the sequence.

- **solution** -> trigger_glyph_top, trigger_glyph_bottom, trigger_glyph_middle
- **step** -> A faint dry click sounds beneath your fingertip, as though something in the wall has shifted and is listening.
- **step** -> A heavier grinding click answers from within the rock, like a bolt drawing back a fraction.
- **solve** (door_open) -> Stone grinds as the hairline crack widens into a passable hewn opening in the west wall.
- **broadcast** (door_open) -> The west wall grinds open. Vibrations carry through the rock to the Secret Chamber.
- **reset** -> A flat, dead click, and then nothing. The sequence is lost.
- **reverse** (door_close) -> The opening snaps shut to a hairline. Anyone in the squeeze is pushed safely to one side.
- **broadcast** (door_close) -> The hewn opening grinds shut to a hairline crack again.
- **prompt** -> A mechanism is responding to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Resonance skulk - A cave lurker that moves between echo returns and tests prey with thrown pebbles. Power: moderate. Role: lurker. Fits because: this chamber is already defined by hostile acoustics.

### Treasure & notable items (<= 3 per zone)
- Carving rubbing satchel - Stiff satchel with charcoal stubs and folded parchment sheets. Tier: valuable. ~Value: 20 coins to scholars. Affordances: pickable true, wearable false, weight 1 lb. Fits because: this is the primary inscription archive of the scene.

### Features (optional)
- An acoustic dead spot near one wall where words return less distorted, hinting at deliberate chamber shaping.
