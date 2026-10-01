# Broken Lift

## Description
The shaft for the freight lift once connected level 2 to level 1 above. Now
it's a collapsed ruin of bent iron struts and snapped chain links. A rough
wooden platform lies half-buried in the rubble, the only evidence that this
was ever a functioning lift cage. The shaft continues upward, blocked by
thirty feet of collapsed structure.

The floor is uneven with twisted metal and splintered wood. The walls are
damp with condensation, and the air carries the metallic tang of old rust.

## Ambient
- light: torchlight flickers against rusted metal; 20 feet of clear visibility
- sound: a low hum from the shaft above, like wind through a narrow passage
- smell: rust, damp iron, and old oil
- temperature: cool and damp
- footing: uneven with twisted metal protrusions

## Items
### rusted_chain_hook
- label: Rusted chain hook
- size: small
- weight: 15 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A massive iron hook once attached to the lift cage. Now bent and rusted, it serves as a precarious handhold.
- appearance by distance:
  - intermediate: a twisted iron hook dangling from the shaft ceiling
  - far: a dark metal protrusion
  - distant: a faint metallic glint
- interactions:
  - examine: The hook shows signs of shearing under extreme tension.
  - pick up: The chain is still attached to the ceiling; only the hook can be removed.

### broken_wagon_wheel
- label: Broken wagon wheel
- size: medium
- weight: 40 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A solid oak wagon wheel, split along the rim.
- appearance by distance:
  - intermediate: a broken wheel half-buried in the rubble
  - far: a dark circular shape
  - distant: a vague outline in the debris
- interactions:
  - examine: The wheel appears to have been deliberately damaged, not broken in fall.
  - pick up: Possible with two or more strong creatures.

## Features / landmarks
- broken_lift_shaft: collapsed shaft leading to level 1; 30 feet of rubble blocks the way up
- rusted_chain_hook: dangling hook from the shaft ceiling, provides precarious handhold

## Creatures present
- none

## Exits
- up: Shaft to level 1 (blocked by 30 feet of rubble)
- down: Passage to Factor's Office

## Puzzles

### shaft_rubble_clearance
*Type: physical obstacle*

The collapsed shaft is blocked by approximately 30 feet of twisted metal and
wood. Clearing it requires significant effort.

- **threshold** -> DC 16 Strength (Athletics) to clear a passage large enough for one creature
- **step** -> You strain against the rubble. The metal groans and shifts, but the pile remains largely intact.
- **step** -> With a final heave, the debris shifts enough to reveal the continuation of the shaft above.
- **solve** (clearance) -> A narrow passage through the rubble opens, revealing the lift shaft above.
- **broadcast** (clearance) -> With a grinding shriek of tortured metal, the rubble shifts to reveal the shaft above.
- **reverse** (revert) -> The rubble settles back, blocking the passage.
- **broadcast** (revert) -> The rubble shifts back into place, sealing the shaft once more.
- **prompt** -> What do you do to clear the passage?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Shaft crawler - A blind, metallic-insectoid that has made its nest in the lift mechanism. Power: minor. Role: ambush. Fits because: the damp, metallic environment attracts unique creatures.

### Treasure & notable items (<= 3 per zone)
- Lift mechanism schematic - A brittle vellum map of the lift's gear system. Tier: scholarly. ~Value: 25 coins to engineers. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: the freight master would want to preserve knowledge of the lift.

### Features (optional)
- A faint updraft from the shaft, carrying the scent of the level above.
