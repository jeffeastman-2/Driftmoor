# Secret Chamber

## Description
A small square room beyond Rocky Passage, hewn rather than eroded. The air is dry and still, and heavy web curtains hang from the ceiling corners. In the center sits a stone burial vault with an old weapon laid atop it.

This chamber is a long-held predator lair wrapped around a tomb.

## Ambient
- light: low and often blocked by web curtains
- sound: dampened compared to Echo Chamber
- smell: dry dust, stale silk, and old stone
- temperature: cold and still
- footing: cramped floor, occasional web drag at face level

## Items
### secret_burial_vault
- label: Burial vault
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A plain rectangular sarcophagus with a flush, massively heavy lid and no visible inscription.
- appearance by distance:
  - intermediate: a centered stone vault with clean edges
  - far: a low rectangular block in the room center
  - distant: a compact dark mass at center floor
- interactions:
  - examine: No obvious hinge, seam, latch, or keyway is visible.
  - search: The mace on top is separate and can be removed.

### mace_plus_one
- label: Mace +1
- size: small
- weight: 4 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: A balanced combat mace resting on the vault lid, unusually well-preserved for the chamber age.
- appearance by distance:
  - intermediate: a banded mace laid across the vault top
  - far: a slim dark object on the lid
  - distant: a narrow shape atop the central block
- interactions:
  - examine: The weapon's balance and subtle resonance indicate enchantment.
  - pick up: It lifts cleanly with no trap or visible chamber response.

## Features / landmarks
- secret_chamber_threshold: east opening to Rocky Passage

## Creatures present
- giant_spider

## Exits
- east: Rocky Passage

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Brood tender spider - Larger than spiderlings but weaker than the giant spider, active near upper web curtains. Power: moderate. Role: guardian. Fits because: a stable long-term lair likely includes brood support around the apex resident.

### Treasure & notable items (<= 3 per zone)
- Funerary seal ring - Tarnished ring set near the vault base in old wrappings. Tier: valuable. ~Value: 45 coins. Affordances: pickable true, wearable finger, weight 0.1 lb. Fits because: this chamber is a deliberate burial space, not random cave collapse.

### Features (optional)
- Layered web curtains that distort torchlight and create false silhouettes overhead.
