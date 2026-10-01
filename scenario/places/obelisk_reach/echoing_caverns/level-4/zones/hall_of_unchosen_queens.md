# Hall of Unchosen Queens

## Description
A grand chamber where statues of queens line the walls, each depicted in
graceful poses and ornate robes. The chamber is dominated by a large, circular
stone dais in the center, surrounded by faintly glowing runes. The air is
cool and carries the scent of ancient stone and the faint tang of ozone.

The walls are lined with faded tapestries, and the ceiling is high and
vaulted. A narrow corridor connects to the Court Kitchens, while a heavy
door leads to the Treasury Antechamber.

## Ambient
- light: faint magical light from the runes provides 30 feet of visibility
- sound: the faint hum of ancient magic, the distant drip of water
- smell: ancient stone, faint ozone, and the scent of faded tapestries
- temperature: cool and dry
- footing: even stone floor

## Items
### faded_tapestries
- label: Faded tapestries
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Faded tapestries on the walls, their colors long since bleached by time.
- appearance by distance:
  - intermediate: faded tapestries depicting royal processions
  - far: colorful bands on the walls
  - distant: faint colored lines on the walls
- interactions:
  - examine: The tapestries show signs of ancient craftsmanship, though time has dimmed their vibrancy.
  - search: One tapestry conceals a small compartment behind it.

### cracked_statuary
- label: Cracked statuary
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Several statues of queens, their features worn smooth by time.
- appearance by distance:
  - intermediate: statues of queens in graceful poses
  - far: dark shapes lining the walls
  - distant: faint outlines lining the walls
- interactions:
  - examine: The statues' features suggest they once depicted queens, though time has eroded the details.
  - search: One statue's base has a hidden compartment.

## Features / landmarks
- circular_stone_dais: center chamber dais with faintly glowing runes
- statues_of_queens: wall statues depicting royal figures

## Creatures present
- none

## Exits
- south: Corridor to Court Kitchens
- east: Passage to Treasury Antechamber

## Puzzles

### dais_rune_sequence
*Type: magical sequence*

The runes on the dais must be touched in the correct sequence to activate
a hidden mechanism.

- **threshold** -> DC 14 Intelligence (Arcana) to understand the rune sequence
- **step** -> You touch the runes, feeling the magical energy flow between them.
- **step** -> The runes glow brighter, responding to your touch.
- **solve** (mechanism_activated) -> The dais shifts, revealing a hidden passage.
- **broadcast** (mechanism_activated) -> With a hum of magical energy, the dais shifts, revealing a hidden passage.
- **reset** -> The runes fade, the mechanism deactivating.
- **broadcast** (reset) -> The runes fade, the mechanism deactivating.
- **reverse** (mechanism_deactivated) -> The dais shifts back, sealing the passage.
- **broadcast** (mechanism_deactivated) -> The dais shifts back, sealing the passage.
- **prompt** -> The runes respond to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Royal historian - A scholar studying the history of the unchosen queens. Power: minor. Role: NPC. Fits because: the Hall of Unchosen Queens is a place of study.

### Treasure & notable items (<= 3 per zone)
- Queen's journal - A bound journal with notes on the history of the unchosen queens. Tier: valuable. ~Value: 150 coins to historians. Affordances: pickable true, wearable false, weight 2 lb. Fits because: the historian would keep research notes.

### Features (optional)
- A faint vibration in the floor, as though something large moves beneath the chamber.
