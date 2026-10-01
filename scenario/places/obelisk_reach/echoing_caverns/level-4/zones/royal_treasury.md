# Royal Treasury

## Description
A grand chamber where the walls are lined with treasure chests and display
cases. The air is cool and carries the scent of ancient metal and parchment.
A heavy door with a complex lock mechanism connects to the Treasury
Antechamber.

The Treasury is currently sealed, its contents hidden behind a magical
warding that requires royal blood to bypass.

## Ambient
- light: torchlight provides 25 feet of clear visibility
- sound: the faint echo of footsteps, the distant drip of water
- smell: ancient metal, parchment, and the scent of the deeper chambers
- temperature: cool and dry
- footing: even stone floor

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

### royal_crest
- label: Royal crest
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: A large royal crest carved into the ceiling.
- appearance by distance:
  - intermediate: a large royal crest carved into the ceiling
  - far: a dark shape on the ceiling
  - distant: a faint outline on the ceiling
- interactions:
  - examine: The crest is finely carved, though time has worn some details.
  - search: The crest conceals a small compartment.

## Features / landmarks
- treasure_chests: walls lined with treasure chests
- display_cases: cases displaying ancient artifacts

## Creatures present
- none

## Exits
- west: Passage to Treasury Antechamber

## Puzzles

### treasury_ward_mechanism
*Type: magical ward*

The Treasury is protected by a magical ward that requires royal blood to bypass.

- **threshold** -> DC 16 Wisdom (Perception) to notice the ward's presence
- **step** -> You sense a magical barrier blocking access to the Treasury.
- **step** -> The ward responds to your touch, its energy fluctuating.
- **solve** (ward_bypassed) -> The ward dissolves, revealing the Treasury's contents.
- **broadcast** (ward_bypassed) -> With a shimmer of magical energy, the ward dissolves.
- **reset** -> The ward reappears, blocking access once more.
- **broadcast** (reset) -> The ward reappears, its energy flaring brightly.
- **reverse** (ward_reasserted) -> The ward reasserts itself, blocking access.
- **broadcast** (ward_reasserted) -> The ward reasserts itself, its energy flaring.
- **prompt** -> The ward responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Treasury guardian - A spectral guardian who protects the Treasury from unauthorized entry. Power: moderate. Role: guardian. Fits because: the Treasury needs protection.

### Treasure & notable items (<= 3 per zone)
- Royal crown - A golden crown set with precious gems. Tier: legendary. ~Value: 5000 coins to collectors. Affordances: pickable true, wearable false, weight 5 lb. Fits because: the Treasury would hold royal regalia.

### Features (optional)
- A faint vibration in the floor, as though something large moves beneath the chamber.
