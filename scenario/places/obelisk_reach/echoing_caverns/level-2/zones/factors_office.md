# Factor's Office

## Description
The factor's office is a cramped chamber at the rear of the Freight Quarter,
its walls lined with heavy oak shelves that once held ledgers and supply
manifests. A massive oak desk dominates the room, its surface scarred with
knife marks and ink stains. The door, reinforced with iron bands, is slightly
ajar.

The air is stale, carrying the scent of old ink and damp paper. A single
torch burns in a bracket above the door, casting long, shifting shadows.

## Ambient
- light: dim torchlight provides 20 feet of clear visibility
- sound: the faint scratching of pens on paper (though the office is empty)
- smell: old ink, damp paper, and pipe smoke
- temperature: cool and dry
- footing: even stone floor

## Items
### crate_labels
- label: Crate labels
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Dozens of wax-sealed crate labels hang from a rack near the door, each bearing a faded destination mark.
- appearance by distance:
  - intermediate: a rack of wax-sealed labels
  - far: a collection of dark patches on the wall
  - distant: a dark line along the wall
- interactions:
  - examine: The labels bear various seals and destination marks, but most are illegible.
  - search: Among the labels, one bears a fresh seal and the coordinates of the Cold Larder.

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
  - search: Beneath the rust, a hidden compartment is visible with a hidden latch.

### damp_sacks
- label: Damp sacks
- size: medium
- weight: 20 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Two burlap sacks, damp and smelling of mildew.
- appearance by distance:
  - intermediate: two burlap sacks on a collapsed shelf
  - far: a dark heap on the floor
  - distant: a shadowed lump
- interactions:
  - examine: The sacks contain something damp and heavy, but the burlap is too damaged to tell what.
  - pick up: The sacks are heavy but manageable for one or two creatures.

## Features / landmarks
- factor_office_door: reinforced oak door with iron bands to the Receiving Floor

## Creatures present
- none

## Exits
- east: Passage to Receiving Floor
- west: Passage to Fungal Stores

## Puzzles

### desk_hidden_compartment
*Type: lock/puzzle*

The factor's desk has a hidden compartment that requires a specific sequence
of movements to open.

- **solution** -> Push the left leg, then the right leg, then the center drawer
- **step** -> The desk leg clicks softly as you press it.
- **step** -> A second click answers from the opposite side.
- **solve** (compartment_open) -> A hidden drawer slides open, revealing the freight manifest.
- **broadcast** (compartment_open) -> With a soft grinding sound, a hidden drawer slides open.
- **reset** -> The drawer slides shut, the mechanism resetting.
- **reverse** (compartment_close) -> The drawer slides shut with a soft thud.
- **broadcast** (compartment_close) -> The drawer slides shut, the mechanism resetting.
- **prompt** -> The desk responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Shadow spy - A goblin who has taken refuge in the ceiling rafters, observing the party. Power: minor. Role: scout. Fits because: the factor would want to keep tabs on visitors.

### Treasure & notable items (<= 3 per zone)
- Freight manifest - A bound book listing recent shipments and their destinations. Tier: valuable. ~Value: 50 coins to interested parties. Affordances: pickable true, wearable false, weight 2 lb. Fits because: the factor's job was to keep track of shipments.

### Features (optional)
- A draft from the door that doesn't match the room's ventilation.
