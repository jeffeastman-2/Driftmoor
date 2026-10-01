# Cistern

## Description
A damp chamber where a large stone cistern occupies the center, its surface
shimmering with reflected torchlight. Water drips from pipes in the ceiling,
collecting in the cistern and overflow channels. The air is cool and humid,
carrying the mineral scent of clean water.

The chamber is connected to the beast pens by a narrow corridor. A rusted
valve mechanism controls the cistern's fill level.

## Ambient
- light: torchlight provides 30 feet of clear visibility
- sound: the steady drip of water, the occasional splash
- smell: clean stone, mineral water, and mildew
- temperature: cool and humid
- footing: wet stone floor, potentially slippery

## Items
### cistern_valve
- label: Cistern valve
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron valve controlling the cistern's fill level.
- appearance by distance:
  - intermediate: a heavy iron valve on the wall
  - far: a dark knob on the wall
  - distant: a small dark shape on the wall
- interactions:
  - examine: The valve is stiff with disuse but functional.
  - operate: Turning the valve controls the water level in the cistern.

### rusted_chain_hook
- label: Rusted chain hook
- size: small
- weight: 8 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A hook from the ceiling, its chain long since rusted away.
- appearance by distance:
  - intermediate: a rusted hook on the ceiling
  - far: a dark protrusion on the ceiling
  - distant: a faint metallic glint
- interactions:
  - examine: The hook appears to have been used to suspend something.
  - pick up: The hook is securely fixed to the ceiling.

## Features / landmarks
- large_stone_cistern: center chamber cistern with shimmering water
- dripping_pipes: ceiling pipes that feed water to the cistern

## Creatures present
- none

## Exits
- south: Corridor to Beast Pens
- east: Passage to Freight Guardroom

## Puzzles

### cistern_water_level
*Type: mechanical puzzle*

The cistern's water level can be adjusted using the valve, affecting the
overflow channels and potentially revealing hidden passages.

- **threshold** -> DC 12 Intelligence (Engineering) to understand the overflow mechanism
- **step** -> You turn the valve, the water level rising or falling with a soft gurgle.
- **step** -> The overflow channels shift, revealing new passage routes.
- **solve** (reveal_passage) -> A hidden passage opens in the east wall.
- **broadcast** (reveal_passage) -> With a gurgle of water, a hidden passage opens.
- **reset** -> The water level returns to normal, closing the passage.
- **broadcast** (reset) -> The water level drops back to normal, sealing the passage.
- **reverse** (close_passage) -> The passage closes as the water level rises.
- **broadcast** (close_passage) -> The passage seals as the water level rises.
- **prompt** -> The valve responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Water mite swarm - A swarm of tiny aquatic creatures that feed on organic matter. Power: minor. Role: environmental hazard. Fits because: the cistern's water supports unique life.

### Treasure & notable items (<= 3 per zone)
- Water purification tablets - A vial of tablets for purifying water. Tier: mundane. ~Value: 15 coins for travelers. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: the cistern would need maintenance supplies.

### Features (optional)
- A faint current in the water, suggesting an underground source.
