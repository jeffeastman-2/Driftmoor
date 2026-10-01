# Receiving Floor

## Description
The Receiving Floor is a large, open chamber where goods are unloaded from
level 1 and staged for transport deeper into the caverns. A wide archway
leads up to the level 1 lift shaft, while corridors branch off in multiple
directions. The floor is worn smooth by cart wheels and foot traffic.

Torches burn in brackets along the walls, casting a steady light over the
activity below. A heavy wooden table stands near the center, covered in
parchments and wax-sealed crate labels.

## Ambient
- light: torchlight provides 30 feet of clear visibility
- sound: the clatter of distant carts, muffled voices from other chambers
- smell: damp earth, old sweat, and the faint tang of metal
- temperature: cool and dry
- footing: even stone floor, worn smooth

## Items
### crate_labels
- label: Crate labels
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Dozens of wax-sealed crate labels are pinned to a board near the archway.
- appearance by distance:
  - intermediate: a board of wax-sealed labels
  - far: a collection of dark patches on the wall
  - distant: a dark line along the wall
- interactions:
  - examine: The labels bear various seals and destination marks.
  - search: One label bears a fresh seal and the coordinates of the Cold Larder.

### rusted_scales
- label: Rusted scales
- size: large
- weight: 50 lb
- pickable: false
- wearable: false
- flavor_only: false
- description: A large brass scale, its pan rusted through and its mechanism seized.
- appearance by distance:
  - intermediate: a large scale beneath a collapsed shelf
  - far: a dark mass on the floor
  - distant: a vague outline on the floor
- interactions:
  - examine: The scale was used to weigh freight before the rust claimed it.
  - search: Beneath the rust, a hidden compartment is visible.

## Features / landmarks
- receiving_floor_arch: wide archway leading to level 1 lift shaft
- heavy_table: wooden table covered in parchment and crate labels
- wall_brackets: torch brackets along the walls

## Creatures present
- none

## Exits
- up: Archway to level 1 lift shaft
- west: Passage to Fungal Stores
- south: Passage to Freight Guardroom
- east: Passage to Cold Larder

## Puzzles

### table_lockbox
*Type: lock/puzzle*

The table has a lockbox secured beneath its surface, requiring a key or
picking to open.

- **threshold** -> DC 13 Dexterity (Sleight of Hand) to pick the lock
- **step** -> You work at the lock with your tools, the tumblers resisting your touch.
- **step** -> A soft click sounds as the lock yields to your effort.
- **solve** (lock_open) -> The lockbox slides open, revealing a small key.
- **broadcast** (lock_open) -> With a soft click, the lockbox slides open.
- **reset** -> The lockbox slides shut, the mechanism resetting.
- **reverse** (lock_close) -> The lockbox snaps shut with a soft click.
- **broadcast** (lock_close) -> The lockbox snaps shut, the mechanism resetting.
- **prompt** -> The table responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Cart driver goblin - A wiry goblin pushing a loaded cart, oblivious to the party. Power: minor. Role: NPC. Fits because: the receiving floor should have freight activity.

### Treasure & notable items (<= 3 per zone)
- Receiving manifest - A bound book listing incoming shipments and their destinations. Tier: valuable. ~Value: 50 coins to interested parties. Affordances: pickable true, wearable false, weight 2 lb. Fits because: the receiving floor is the entry point for goods.

### Features (optional)
- A faint draft from the archway, carrying the scent of the level above.
