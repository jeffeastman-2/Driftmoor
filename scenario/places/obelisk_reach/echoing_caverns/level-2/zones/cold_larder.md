# Cold Larder

## Description
A frigid chamber where the walls are lined with thick stone shelves. The air
is so cold that condensation forms on the walls and drips to the floor.
Shelves of salted meat and preserved vegetables line the walls, covered in
a fine layer of frost.

The larder's door is a heavy iron-plated slab with a frost-rimed handle. A
small frost-covered lantern hangs from the ceiling, its light weak and pale.

## Ambient
- light: the lantern provides 10 feet of clear visibility
- sound: the crackling of frozen surfaces, faint dripping of condensation
- smell: salt, cold stone, and the faint tang of preserved meat
- temperature: freezing (5°F below normal)
- footing: icy stone floor, slippery

## Items
### cold_larder_door_knob
- label: Cold larder door knob
- size: small
- weight: 2 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A heavy iron knob, frosted over and difficult to grip.
- appearance by distance:
  - intermediate: a frosted iron knob on the door
  - far: a dark knob on the door
  - distant: a small dark shape on the door
- interactions:
  - examine: The knob is so cold it causes discomfort on direct contact.
  - pick up: The knob is securely fixed to the door.

### rusted_scales
- label: Rusted scales
- size: large
- weight: 45 lb
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
- iron_plated_door: heavy iron-plated door with frost-rimed handle
- frost-covered_lantern: ceiling-hung lantern with weak light

## Creatures present
- none

## Exits
- west: Passage to Receiving Floor

## Puzzles

### frost_covered_lock
*Type: cold resistance check*

The door is locked, but the mechanism is frozen and requires warmth to operate.

- **threshold** -> DC 12 Constitution saving throw or touch the frozen mechanism
- **step** -> Your fingers burn with cold as you try to manipulate the mechanism.
- **step** -> The frozen mechanism begins to thaw under the warmth of your touch.
- **solve** (unlock) -> The mechanism thaws, and the door swings open with a groan.
- **broadcast** (unlock) -> With a groan of thawing metal, the door swings open.
- **reverse** (refreeze) -> The mechanism refreezes, locking the door once more.
- **broadcast** (refreeze) -> The mechanism refreezes with a sharp crack.
- **prompt** -> The mechanism responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Frost mite swarm - A swarm of tiny creatures that feed on cold. Power: minor. Role: environmental hazard. Fits because: the frigid environment supports unique life.

### Treasure & notable items (<= 3 per zone)
- Salted provisions - A crate of salted meat and dried vegetables. Tier: mundane. ~Value: 10 coins for supplies. Affordances: pickable true, wearable false, weight 20 lb. Fits because: the larder stores provisions.

### Features (optional)
- A faint warmth source near the back of the room.
