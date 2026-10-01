# Freight Guardroom

## Description
A small, cramped chamber that serves as the guard post for the Freight Quarter.
A heavy iron-bound door leads to the Receiving Floor, while a narrow corridor
connects to the Cistern. The room is sparsely furnished with a simple cot, a
rusted weapon rack, and a small table with a single candle burning low.

The air is still and carries the scent of old sweat and iron. A shield rests
against the wall, its surface dented and scorched from some long-forgotten
encounter.

## Ambient
- light: the candle provides 15 feet of clear visibility
- sound: the faint dripping of water from the cistern corridor
- smell: old sweat, iron, and extinguished smoke
- temperature: cool and dry
- footing: even stone floor

## Items
### broken_shackle
- label: Broken shackle
- size: small
- weight: 5 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: An iron shackle, broken at one end as though forcibly opened.
- appearance by distance:
  - intermediate: a broken shackle on the floor
  - far: a dark shape on the floor
  - distant: a vague outline on the floor
- interactions:
  - examine: The break shows signs of being forced, not fatigue.
  - pick up: The shackle is light and easy to carry.

### rusted_chain_hook
- label: Rusted chain hook
- size: small
- weight: 10 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A hook from the wall, its chain long since rusted away.
- appearance by distance:
  - intermediate: a rusted hook on the wall
  - far: a dark protrusion on the wall
  - distant: a faint metallic glint
- interactions:
  - examine: The hook appears to have been used to chain prisoners.
  - pick up: The hook is securely fixed to the wall.

## Features / landmarks
- iron_bound_door: heavy iron-bound door to the Receiving Floor
- narrow_corridor: passage to the Cistern

## Creatures present
- none

## Exits
- east: Passage to Receiving Floor
- north: Corridor to Cistern

## Puzzles

### weapon_rack_reveal
*Type: hidden compartment*

The weapon rack conceals a hidden compartment that requires examination to find.

- **threshold** -> DC 12 Wisdom (Perception) to notice the loose plate
- **step** -> You run your hand along the rack, feeling for irregularities.
- **step** -> Your fingers brush against a loose plate in the rack's base.
- **solve** (compartment_open) -> The plate pops free, revealing a hidden cache.
- **broadcast** (compartment_open) -> With a soft click, the plate pops free.
- **reverse** (compartment_close) -> The plate slides back into place.
- **broadcast** (compartment_close) -> The plate snaps back into the rack.
- **prompt** -> The rack responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Former prisoner - A gaunt figure who was once chained here, now hiding in the shadows. Power: minor. Role: NPC. Fits because: the broken shackle suggests recent imprisonment.

### Treasure & notable items (<= 3 per zone)
- Guard's journal - A water-stained journal with notes on recent freight shipments. Tier: scholarly. ~Value: 30 coins to historians. Affordances: pickable true, wearable false, weight 1 lb. Fits because: the guard would keep records of passing traffic.

### Features (optional)
- A faint draft from the door that doesn't match the room's ventilation.
