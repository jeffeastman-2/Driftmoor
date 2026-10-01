# Fungal Stores

## Description
A dim chamber where rows of wooden shelves stand like sentinels in the gloom.
Mold blooms in vibrant patterns across the walls and ceiling, glowing faintly
in the torchlight. The air is thick with spores, and the floor is covered in
a spongy layer of fungal growth.

The shelves hold crates and barrels, many of them rotted through by the damp.
The fungal growth pulses faintly, as though breathing.

## Ambient
- light: the mold provides dim bioluminescent light; 30 feet of visibility
- sound: a faint rustling, like cloth in the wind, though no breeze exists
- smell: strong mold, mildew, and the earthy scent of fungi
- temperature: warm and humid
- footing: spongy fungal growth, may be slippery

## Items
### damp_sacks
- label: Damp sacks
- size: medium
- weight: 25 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Sacks filled with dried mushrooms, their packaging rotted and crumbling.
- appearance by distance:
  - intermediate: sacks of dried fungi on a shelf
  - far: dark shapes on the shelves
  - distant: a collection of dark masses
- interactions:
  - examine: The mushrooms appear to be of various types, some edible, others dubious.
  - pick up: The sacks are heavy and damp, but can be carried.

### broken_wagon_wheel
- label: Broken wagon wheel
- size: medium
- weight: 35 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A wooden wheel, its rim split and warped by moisture.
- appearance by distance:
  - intermediate: a broken wheel half-buried in fungal growth
  - far: a dark circular shape in the gloom
  - distant: a vague outline in the floor
- interactions:
  - examine: The wheel shows signs of long-term exposure to damp conditions.
  - pick up: The wheel is heavy but manageable with effort.

## Features / landmarks
- fungal_growth: bioluminescent mold covering walls and ceiling, pulses faintly
- collapsed_shelf: one shelf has collapsed under the weight of rotted cargo

## Creatures present
- none

## Exits
- west: Passage to Factor's Office
- east: Passage to Receiving Floor

## Puzzles

### spore_clog
*Type: environmental hazard*

The fungal growth occasionally releases a cloud of spores when disturbed.

- **threshold** -> DC 10 Constitution saving throw orinhale spores
- **step** -> A cloud of glowing spores erupts from the disturbed growth.
- **step** -> The spores hang in the air, catching the torchlight like glittering dust.
- **solve** (dissipation) -> The spores settle to the floor within a round.
- **broadcast** (dissipation) -> The spores sink to the floor, leaving the air clear once more.
- **reverse** (reform) -> The fungal growth begins to pulse again,积蓄 spores.
- **broadcast** (reform) -> The mold begins to glow brighter, its surface quivering.
- **prompt** -> The growth responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Spore sprite - A tiny, floating creature that feeds on the glowing mold. Power: minor. Role: ambient. Fits because: the bioluminescent fungus supports unique life.

### Treasure & notable items (<= 3 per zone)
- Fungal culture vial - A glass vial containing a glowing fungal culture. Tier: alchemical. ~Value: 75 coins to alchemists. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: the stores are a natural alchemical supply.

### Features (optional)
- A faint, sweet scent that seems to come from the pulsing mold.
