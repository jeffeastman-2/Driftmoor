# Throne of Seven Chains

## Description
A grand chamber dominated by a stone dais with seven thick iron chains
hanging from the ceiling. The chains are linked to heavy, rusted manacles,
suggesting they were used to bind prisoners or perhaps a monarch themselves.
The air is cold and carries the scent of ancient metal and the faint tang
of ozone.

The chamber is the heart of the Royal Precinct, its walls lined with faded
tapestries and cracked statuary. A narrow passage connects to the Treasury.

## Ambient
- light: torchlight provides 20 feet of clear visibility
- sound: the faint hum of ancient magic, the distant drip of water
- smell: ancient metal, ozone, and the scent of the deeper chambers
- temperature: cold and dry
- footing: even stone floor, potentially slippery with frost

## Items
### seven_chains
- label: Seven chains
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Seven thick iron chains hanging from the ceiling, each with a heavy, rusted link.
- appearance by distance:
  - intermediate: seven thick chains hanging from the ceiling
  - far: dark chains hanging from the ceiling
  - distant: faint outlines hanging from the ceiling
- interactions:
  - examine: The chains appear to be part of a larger mechanism.
  - search: One chain conceals a small compartment.

### broken_scepter
- label: Broken scepter
- size: small
- weight: 2 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A golden scepter, broken in two at the midpoint.
- appearance by distance:
  - intermediate: a broken golden scepter on the floor
  - far: a dark shape on the floor
  - distant: a faint outline on the floor
- interactions:
  - examine: The scepter appears to have been deliberately broken.
  - pick up: The scepter can be taken, though it's brittle.

## Features / landmarks
- stone_dais: central dais with seven iron chains hanging from the ceiling
- faded_tapestries: walls lined with faded tapestries

## Creatures present
- none

## Exits
- west: Passage to Treasury

## Puzzles

### throne_activation_mechanism
*Type: royal blood requirement*

The throne requires royal blood to activate, either through a blood sacrifice
or the presence of a royal descendant.

- **threshold** -> DC 14 Wisdom (Perception) to notice the royal blood requirement
- **step** -> You feel a magical presence in the throne, demanding recognition.
- **step** -> The chains begin to glow, responding to royal blood.
- **solve** (throne_activated) -> The throne shifts, revealing its true power.
- **broadcast** (throne_activated) -> With a hum of magical energy, the throne shifts, revealing its true power.
- **reset** -> The throne reverts, its power dormant once more.
- **broadcast** (reset) -> The throne reverts, its power fading.
- **reverse** (throne_deactivated) -> The throne deactivates, its power dormant.
- **broadcast** (throne_deactivated) -> The throne deactivates, its power fading.
- **prompt** -> The throne responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Royal spirit - The ghost of a monarch bound to the throne. Power: moderate. Role: guardian. Fits because: the throne is a place of powerful magic.

### Treasure & notable items (<= 3 per zone)
- Throne key - A golden key that unlocks the throne's hidden mechanisms. Tier: legendary. ~Value: 10000 coins to collectors. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: the throne would require a key.

### Features (optional)
- A faint vibration in the floor, as though something large moves beneath the chamber.
