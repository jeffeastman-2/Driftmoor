# Treasury Antechamber

## Description
A narrow chamber that serves as the entry point to the Treasury. The walls
are lined with intricate carvings of royal treasures and ancient artifacts.
A heavy door with a complex lock mechanism blocks the path to the Treasury,
while a passage connects to the Hall of Unchosen Queens.

The air is cool and carries the scent of ancient metal and parchment. A torch
burns in a bracket above the door, casting a steady light over the antechamber.

## Ambient
- light: torchlight provides 25 feet of clear visibility
- sound: the faint echo of footsteps, the distant drip of water
- smell: ancient metal, parchment, and the scent of the deeper chambers
- temperature: cool and dry
- footing: even stone floor

## Items
### treasury_door_knob
- label: Treasury door knob
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron knob controlling the Treasury door mechanism.
- appearance by distance:
  - intermediate: a heavy iron knob on the door
  - far: a dark knob on the door
  - distant: a small dark shape on the door
- interactions:
  - examine: The knob is stiff with disuse but functional.
  - operate: Turning the knob opens or closes the Treasury door.

### rusted_gate_lever
- label: Rusted gate lever
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron lever controlling the Treasury door mechanism.
- appearance by distance:
  - intermediate: a heavy iron lever on the wall
  - far: a dark knob on the wall
  - distant: a small dark shape on the wall
- interactions:
  - examine: The lever is stiff with disuse but functional.
  - operate: Turning the lever opens or closes the Treasury door.

## Features / landmarks
- intricate_wall_carvings: walls lined with carvings of royal treasures
- heavy_door: door with complex lock mechanism to the Royal Treasury

## Creatures present
- none

## Exits
- west: Passage to Hall of Unchosen Queens
- east: Passage to Royal Treasury

## Puzzles

### treasury_lock_mechanism
*Type: lock puzzle*

The Treasury door requires a royal bloodline or a complex key to open.

- **threshold** -> DC 18 Dexterity (Sleight of Hand) to pick the lock
- **step** -> You work at the lock with your tools, the tumblers resisting your touch.
- **step** -> A soft click sounds as the lock yields to your effort.
- **solve** (lock_open) -> The lock mechanism shifts, and the door swings open.
- **broadcast** (lock_open) -> With a soft click, the door swings open.
- **reset** -> The door slams shut, the mechanism resetting.
- **broadcast** (reset) -> The door slams shut with a heavy crash.
- **reverse** (lock_close) -> The door slams shut, the mechanism resetting.
- **broadcast** (lock_close) -> The door slams shut with a heavy crash.
- **prompt** -> The lock responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Treasury guardian - A spectral guardian who protects the Treasury from unauthorized entry. Power: moderate. Role: guardian. Fits because: the Treasury needs protection.

### Treasure & notable items (<= 3 per zone)
- Treasury key ring - A ring of keys for the various Treasury locks. Tier: valuable. ~Value: 200 coins to interested parties. Affordances: pickable true, wearable false, weight 1 lb. Fits because: the Treasury needs keys.

### Features (optional)
- A faint draft from the Treasury, carrying the scent of ancient treasures.
