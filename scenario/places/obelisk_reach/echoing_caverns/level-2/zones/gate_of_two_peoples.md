# Gate of Two Peoples

## Description
A large, arched chamber that serves as the transition point between levels 2
and 3. The gate is a massive iron-plated door with two separate passage
arches on either side. The walls are carved with two opposing heraldic
symbols: a goblin crown and an elven crescent, representing the two peoples
who once shared this cavern.

The air is cool and still, carrying the faint scent of ancient stone. Torches
burn in brackets along the walls, their light steady and unchanging.

## Ambient
- light: torchlight provides 40 feet of clear visibility
- sound: a low hum from the deeper caverns, the faint echo of distant footsteps
- smell: old stone, faint ozone, and the scent of the deeper chambers
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
- description: A heavy iron lever controlling the main gate mechanism.
- appearance by distance:
  - intermediate: a heavy iron lever on the wall
  - far: a dark knob on the wall
  - distant: a small dark shape on the wall
- interactions:
  - examine: The lever is stiff with disuse but functional.
  - operate: Turning the lever opens or closes the gate.

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

## Features / landmarks
- iron_plated_gate: massive gate with two passage arches
- heraldic_carvings: goblin crown and elven crescent on the walls

## Creatures present
- none

## Exits
- up: Gate to level 2 (Freight Quarter)
- down: Gate to level 3 (Sleeping City)

## Puzzles

### dual_gate_mechanism
*Type: coordinated mechanism*

The gate requires both levers to be operated in sequence to open fully.

- **threshold** -> DC 14 Intelligence (Engineering) to understand the dual mechanism
- **step** -> You turn the main lever, the gate shifting slightly but not opening.
- **step** -> The secondary lever responds, the mechanism engaging fully.
- **solve** (gate_open) -> The gate grinds open, revealing the path to level 3.
- **broadcast** (gate_open) -> With a groan of rusted metal, the gate grinds open.
- **reset** -> The gate slams shut, the mechanism resetting.
- **broadcast** (reset) -> The gate slams shut with a heavy crash.
- **reverse** (gate_close) -> The gate grinds shut, the mechanism reversing.
- **broadcast** (gate_close) -> With a groan of rusted metal, the gate grinds shut.
- **prompt** -> The mechanism responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Gatekeeper goblin - A goblin who guards the gate between levels. Power: moderate. Role: NPC. Fits because: the gate requires a keeper.

### Treasure & notable items (<= 3 per zone)
- Gate key ring - A ring of keys for the various gates in the caverns. Tier: valuable. ~Value: 150 coins to interested parties. Affordances: pickable true, wearable false, weight 1 lb. Fits because: the gatekeeper would carry keys.

### Features (optional)
- A faint vibration in the floor, as though something large moves in the distance.
