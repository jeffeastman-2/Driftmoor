# Royal Guard Checkpoint

## Description
A narrow chamber that serves as the main checkpoint for the Royal Precinct.
A heavy iron door with a complex lock mechanism blocks the path forward, while
passages branch off to the barracks and kitchens. The walls are lined with
armor racks and weapon stands, all meticulously maintained.

The air is cool and carries the scent of polished leather and oiled metal. A
torch burns in a bracket above the door, casting a steady light over the
checkpoint.

## Ambient
- light: torchlight provides 30 feet of clear visibility
- sound: the clank of armor on racks, the faint drip of water from the kitchens
- smell: polished leather, oiled metal, and cold iron
- temperature: cool and dry
- footing: even stone floor

## Items
### rusted_gate_lever
- label: Rusted gate lever
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron lever controlling the checkpoint gate mechanism.
- appearance by distance:
  - intermediate: a heavy iron lever on the wall
  - far: a dark knob on the wall
  - distant: a small dark shape on the wall
- interactions:
  - examine: The lever is stiff with disuse but functional.
  - operate: Turning the lever opens or closes the checkpoint gate.

### cracked_statuary
- label: Cracked statuary
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: A cracked statue of a royal figure, its features worn smooth by time.
- appearance by distance:
  - intermediate: a cracked statue in a niche
  - far: a dark shape in a niche
  - distant: a faint outline in a niche
- interactions:
  - examine: The statue's features suggest it once depicted a queen, though time has eroded the details.
  - search: The base of the statue has a hidden compartment.

## Features / landmarks
- heavy_iron_door: gate with complex lock mechanism to the Royal Guard Barracks
- armor_racks: walls lined with meticulously maintained armor

## Creatures present
- none

## Exits
- up: Stairs to Stairs from City
- west: Passage to Royal Guard Barracks
- east: Passage to Court Kitchens

## Puzzles

### checkpoint_lock_mechanism
*Type: lock puzzle*

The checkpoint gate requires a specific sequence to open, either through
pickling or a key.

- **threshold** -> DC 15 Dexterity (Sleight of Hand) to pick the lock
- **step** -> You work at the lock with your tools, the tumblers resisting your touch.
- **step** -> A soft click sounds as the lock yields to your effort.
- **solve** (lock_open) -> The lock mechanism shifts, and the gate swings open.
- **broadcast** (lock_open) -> With a soft click, the gate swings open.
- **reset** -> The gate slams shut, the mechanism resetting.
- **broadcast** (reset) -> The gate slams shut with a heavy crash.
- **reverse** (lock_close) -> The gate slams shut, the mechanism resetting.
- **broadcast** (lock_close) -> The gate slams shut with a heavy crash.
- **prompt** -> The lock responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Sentinel guard - A guard who patrols the checkpoint, ready to challenge intruders. Power: moderate. Role: guardian. Fits because: the checkpoint needs security.

### Treasure & notable items (<= 3 per zone)
- Guard's logbook - A bound book with notes on recent visitors to the Precinct. Tier: valuable. ~Value: 50 coins to interested parties. Affordances: pickable true, wearable false, weight 1 lb. Fits because: the guards keep records of visitors.

### Features (optional)
- A faint draft from the gate that doesn't match the room's ventilation.
