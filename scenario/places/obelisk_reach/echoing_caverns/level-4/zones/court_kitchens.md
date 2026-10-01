# Court Kitchens

## Description
A large chamber where several cooking hearths and storage shelves line the
walls. The air is warm and carries the scent of food cooking and baking bread.
Shelves are lined with pots, pans, and cooking utensils, all meticulously
maintained.

A door with a heavy iron lock connects to the Royal Guard Checkpoint, while
a narrow corridor leads to the Hall of Unchosen Queens.

## Ambient
- light: torchlight provides 30 feet of clear visibility
- sound: the crackle of cooking hearths, the faint clatter of utensils
- smell: cooking food, baking bread, and hot metal
- temperature: warm and humid
- footing: even stone floor

## Items
### kitchen_utensils
- label: Kitchen utensils
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Rows of cooking utensils hanging from wall mounts.
- appearance by distance:
  - intermediate: rows of cooking utensils on wall mounts
  - far: dark shapes on the walls
  - distant: a collection of dark masses on the walls
- interactions:
  - examine: The utensils are well-maintained and functional.
  - search: One utensil conceals a small compartment behind it.

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
- cooking_hearths: several cooking hearths for preparing meals
- storage_shelves: shelves lined with pots and utensils

## Creatures present
- none

## Exits
- west: Passage to Royal Guard Checkpoint
- north: Corridor to Hall of Unchosen Queens

## Puzzles

### hearth_ignition_mechanism
*Type: fire source*

The cooking hearths can be ignited with the proper fuel and ignition source.

- **threshold** -> DC 10 Dexterity (Tool proficiency) to ignite the hearth
- **step** -> You add fuel to the hearth, striking the flint to ignite it.
- **step** -> The hearth roars to life, casting a warm light over the kitchen.
- **solve** (hearth_ignited) -> The hearth burns steadily, ready for cooking.
- **broadcast** (hearth_ignited) -> With a roar, the hearth burns steadily, casting warm light.
- **reset** -> The hearth cools and dies, the fuel spent.
- **broadcast** (reset) -> The hearth cools and dies, leaving only embers.
- **reverse** (hearth_extinguished) -> The hearth is extinguished, the fire reduced to embers.
- **broadcast** (hearth_extinguished) -> The hearth is extinguished, the fire reduced to embers.
- **prompt** -> The hearth responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Court cook - A chef preparing meals for the royal court. Power: minor. Role: NPC. Fits because: the kitchens need cooks.

### Treasure & notable items (<= 3 per zone)
- Royal recipe book - A bound book with recipes for royal feasts. Tier: scholarly. ~Value: 75 coins to historians. Affordances: pickable true, wearable false, weight 2 lb. Fits because: the cook would keep recipe records.

### Features (optional)
- A faint draft from the corridor, carrying the scent of the Hall of Unchosen Queens.
