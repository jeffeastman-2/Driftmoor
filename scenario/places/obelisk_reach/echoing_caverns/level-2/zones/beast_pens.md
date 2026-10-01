# Beast Pens

## Description
A cavernous chamber where iron-barred pens line the walls, each large enough
to hold a giant lizard or similar creature. The air is thick with the stench
of beasts and their waste. Chains hang from iron bollards, and the floor is
hard-packed earth covered in a thin layer of straw.

The pens are currently empty, but the iron bollards and chains suggest they
were recently occupied. A heavy gate with a rusted lever mechanism closes
the chamber from the outside.

## Ambient
- light: torchlight provides 25 feet of clear visibility
- sound: the distant rustling of chains, the faint dripping of water
- smell: strong beast stench, straw, and iron
- temperature: warm and humid
- footing: uneven earth, potentially slippery

## Items
### iron_bollard
- label: Iron bollard
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A heavy iron bollard embedded in the floor, its chain long since rusted away.
- appearance by distance:
  - intermediate: a heavy bollard in the floor
  - far: a dark post in the floor
  - distant: a small dark shape in the floor
- interactions:
  - examine: The bollard shows signs of recent use, with fresh wear on the chain ring.
  - search: A small compartment in the bollard base may hold a key.

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
- iron_barred_pens: wall-mounted pens with iron bars
- rusted_gate_lever: gate mechanism with rusted lever

## Creatures present
- none (currently empty pens)

## Exits
- west: Passage to Cistern

## Puzzles

### gate_lever_mechanism
*Type: mechanical*

The gate is controlled by a rusted lever mechanism that requires a specific
sequence to operate.

- **threshold** -> DC 10 Intelligence (Engineering) to understand the mechanism
- **step** -> You examine the lever, the rusted gears, and the chain connecting it to the gate.
- **step** -> The mechanism shifts with a groan of metal on metal.
- **solve** (gate_open) -> The gate grinds open, revealing the path beyond.
- **broadcast** (gate_open) -> With a groan of rusted metal, the gate grinds open.
- **reset** -> The gate slams shut, the mechanism resetting.
- **broadcast** (reset) -> The gate slams shut with a heavy crash.
- **reverse** (gate_close) -> The gate grinds shut, the mechanism reversing.
- **broadcast** (gate_close) -> With a groan of rusted metal, the gate grinds shut.
- **prompt** -> The mechanism responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Escapee giant lizard - A large lizard that escaped during a recent disturbance. Power: moderate. Role: ambush predator. Fits because: the pens were recently occupied.

### Treasure & notable items (<= 3 per zone)
- Beast taming kit - A satchel containing reagents and tools for taming creatures. Tier: valuable. ~Value: 100 coins to beast tamers. Affordances: pickable true, wearable false, weight 5 lb. Fits because: the pens would need taming supplies.

### Features (optional)
- A faint vibration in the floor, as though something large moved recently.
