# Royal Guard Barracks

## Description
A sparsely furnished chamber where several beds and storage lockers line the
walls. The air is cool and carries the scent of leather and metal. A heavy
door with a lock mechanism connects to the Royal Guard Checkpoint.

The barracks are currently empty, but signs of recent habitation suggest the
guard contingent may be nearby.

## Ambient
- light: torchlight provides 25 feet of clear visibility
- sound: the faint drip of water from the kitchens, the occasional creak of the building
- smell: leather, metal, and the faint scent of old sweat
- temperature: cool and dry
- footing: even stone floor

## Items
### guard_barracks_lock
- label: Barracks lock
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron lock securing the barracks door.
- appearance by distance:
  - intermediate: a heavy iron lock on the door
  - far: a dark knob on the door
  - distant: a small dark shape on the door
- interactions:
  - examine: The lock appears to be recently oiled and functional.
  - pick_up: The lock is securely fixed to the door.

### rusted_gate_lever
- label: Rusted gate lever
- size: small
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron lever controlling the barracks mechanism.
- appearance by distance:
  - intermediate: a heavy iron lever on the wall
  - far: a dark knob on the wall
  - distant: a small dark shape on the wall
- interactions:
  - examine: The lever is stiff with disuse but functional.
  - operate: Turning the lever activates the barracks alarm.

## Features / landmarks
- beds_and_lockers: sleeping accommodations for the royal guard
- heavy_door: door with lock mechanism to the Royal Guard Checkpoint

## Creatures present
- none

## Exits
- east: Passage to Royal Guard Checkpoint

## Puzzles

### barracks_alarm_mechanism
*Type: mechanical puzzle*

The barracks have an alarm mechanism that can be activated to alert the guard
contingent.

- **threshold** -> DC 10 Intelligence (Engineering) to understand the alarm mechanism
- **step** -> You examine the lever, the alarm bell, and the chain connecting them.
- **step** -> The mechanism shifts with a groan of metal on metal.
- **solve** (alarm_triggered) -> The alarm bell rings, alerting the entire Precinct.
- **broadcast** (alarm_triggered) -> With a clang, the alarm bell rings, echoing through the Precinct.
- **reset** -> The alarm mechanism resets, ready to be triggered again.
- **broadcast** (reset) -> The alarm mechanism resets, the chain slackening.
- **reverse** (alarm_silenced) -> The alarm bell falls silent, the mechanism resetting.
- **broadcast** (alarm_silenced) -> The alarm bell falls silent, the mechanism resetting.
- **prompt** -> The mechanism responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Night watch guard - A guard who patrols the barracks at night. Power: minor. Role: NPC. Fits because: the barracks need a night watch.

### Treasure & notable items (<= 3 per zone)
- Guard's uniform - A set of royal guard uniform in excellent condition. Tier: valuable. ~Value: 50 coins to collectors. Affordances: pickable true, wearable false, weight 10 lb. Fits because: the guard would wear these during patrols.

### Features (optional)
- A faint vibration in the floor, as though something large moved recently.
