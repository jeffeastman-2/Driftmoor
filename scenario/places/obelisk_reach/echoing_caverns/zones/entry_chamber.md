# Entry Chamber

## Description
The crack in the cliff face opens into a low, wide chamber. Daylight bleeds in as a pale wedge that dies quickly against dark stone. The floor is uneven with old rockfall, smoothed by water in places, jagged in others. The air is too cold for the season and unnaturally still.

The room is full of evidence. A snapped torch lies near the south passage mouth. A dark bloodstain smears toward the same passage. A leather pack sits half-buried against the west wall. Parallel scrapes run across the floor and end at the threshold. Someone died here, and someone moved the body deeper into the cave.

## Ambient
- light: pale daylight near the entrance only; beyond that, torchlight or darkvision
- sound: faint rhythmic hum from deeper chambers; footsteps echo with slight delay
- smell: damp mineral stone and very old blood
- temperature: cold and still
- footing: uneven stone with slick water-worn patches

## Items
### torch_bracket
- label: Torch bracket
- size: small
- weight: 2 lb
- pickable: false
- wearable: false
- flavor_only: true
- description: An iron wall bracket near the entrance, rusted through and no longer usable.
- appearance by distance:
  - intermediate: a rusted iron bracket fixed to the entrance wall
  - far: a small dark fixture on the wall near the cave mouth
  - distant: a dark nub on the entrance wall
- interactions:
  - examine: The bracket is deeply corroded and flakes when touched. It has not held a working torch in years.

### wall_scratches
- label: Tally scratches
- size: tiny
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Nineteen tally marks and a faltering twentieth cut into the wall with a hard point.
- appearance by distance:
  - intermediate: faint tally scratches near the entrance
  - far: a small cluster of marks on the wall
  - distant: a faint rough patch on the wall
- interactions:
  - examine: The count reaches nineteen and trails off on the twentieth mark, suggesting someone was counting days and did not finish.
  - search: The cuts were made with something harder than common cave stone.

### snapped_torch
- label: Snapped torch
- size: small
- weight: 1 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A torch broken across the grain. The pitch head is intact but never lit.
- appearance by distance:
  - intermediate: a broken pale torch shaft on the floor
  - far: a slim pale streak low on the stone
  - distant: a faint pale fleck against dark floor
- interactions:
  - examine: The break looks violent, not deliberate. The unburned head implies it was dropped before being lit.
  - pick up: The pieces can be taken. The pitch head is still usable if rehafted.

### old_bloodstain
- label: Dark stain
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A blackened old blood smear drawn into a tapered streak that points south toward First Passage.
- appearance by distance:
  - intermediate: a dark directional stain near the south wall
  - far: a dark patch low on the floor
  - distant: a shadowed blot on stone
- interactions:
  - examine: The shape indicates a body was dragged rather than walking away.
  - search: The residue is old and flakes dryly. Without alchemy, no finer result is available.

### discarded_pack
- label: Discarded pack
- size: small
- weight: 3 lb
- pickable: true
- wearable: false
- flavor_only: false
- contents: rope, tin_cup, reach_map
- description: A brittle leather expedition pack half-buried under older rockfall.
- appearance by distance:
  - intermediate: a slumped bundle against the west wall
  - far: a dark heap at the base of the wall
  - distant: a low shadow at the wall-foot
- interactions:
  - examine: It is expedition gear, old but intentionally placed before later rockfall covered it.
  - search: Digging it free reveals mildewed rope, a tin cup, and a water-stained Reach map showing the obelisk and entrance crack.
  - pick up: The pack can be taken, though the leather is brittle.

### drag_marks
- label: Drag marks
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: Two parallel floor scrapes running several paces toward the passage threshold.
- appearance by distance:
  - intermediate: twin scored lines in the stone floor
  - far: faint parallel streaks toward the passage
  - distant: pale linear marks on the floor
- interactions:
  - examine: The marks match the bloodstain direction and are consistent with dragged heels.
  - search: The trail disappears at First Passage where damp uneven stone stops preserving the scrape pattern.

## Features / landmarks
- entrance_crack: narrow north-wall crack to the surface, easy to miss from outside
- first_passage_mouth: south threshold where the floor drops into First Passage

## Creatures present
- none

## Exits
- north: entrance_crack to places/obelisk_reach
- south: First Passage

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Spiderling clutch - Small brood scouts active near the threshold webbing. Power: minor. Role: ambush. Fits because: this is the main prey-entry point into the giant spider's territory.
- Echo skitterer - A fist-sized cave predator that follows vibration and retreats from bright flame. Power: minor. Role: scavenger. Fits because: the chamber already emphasizes distorted sound and signs of old kills.

### Treasure & notable items (<= 3 per zone)
- Cliff-script shard - Broken inscribed stone from the entrance crack. Tier: mundane. ~Value: scholarly curiosity. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: it links the entrance carvings to Echo Chamber inscriptions.

### Features (optional)
- Thin interior webbing near the crack that is visible only when torchlight catches it at an angle.
- A faint updraft from First Passage that pulses in time with the deeper hum.
