# Stairs from City

## Description
A narrow stairway that winds downward from level 3 into the Royal Precinct.
The steps are carved from the natural cave rock, worn smooth by centuries of
foot traffic. The walls are lined with faded murals depicting royal processions
and ceremonial events.

The air is cooler here, and the light from above fades quickly as you descend.
A single torch burns in a bracket at the bottom of the stairs, its light
dim and steady.

## Ambient
- light: torchlight provides 20 feet of clear visibility
- sound: the faint echo of footsteps, the distant drip of water from above
- smell: old stone, dust, and the faint scent of the deeper chambers
- temperature: cool and dry
- footing: even stone steps, potentially slippery with dust

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

## Features / landmarks
- narrow_stairway: downward staircase to level 4
- faded_murals: wall murals depicting royal events

## Creatures present
- none

## Exits
- up: Stairway to level 3
- down: Passage to Royal Guard Checkpoint

## Puzzles

### murals_reveal_secret
*Type: hidden compartment*

One of the faded murals conceals a small compartment that requires careful
examination to find.

- **threshold** -> DC 14 Wisdom (Perception) to notice the loose panel
- **step** -> You run your fingers along the tapestry, feeling for irregularities.
- **step** -> Your fingers brush against a loose panel behind the tapestry.
- **solve** (compartment_open) -> The panel pops free, revealing a small cache.
- **broadcast** (compartment_open) -> With a soft click, the panel pops free.
- **reverse** (compartment_close) -> The panel slides back into place.
- **broadcast** (compartment_close) -> The panel snaps back into the tapestry.
- **prompt** -> The tapestry responds to your touch. What do you do next?

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Stairway sentinel - A spectral guard who patrols the stairs, repelling unauthorized descent. Power: moderate. Role: guardian. Fits because: the stairs are the only entrance to the Royal Precinct.

### Treasure & notable items (<= 3 per zone)
- Royal passport - A sealed document granting passage through the Royal Precinct. Tier: valuable. ~Value: 100 coins to interested parties. Affordances: pickable true, wearable false, weight 0.5 lb. Fits because: the guards would require documentation.

### Features (optional)
- A faint draft from below, carrying the scent of the Royal Precinct.
