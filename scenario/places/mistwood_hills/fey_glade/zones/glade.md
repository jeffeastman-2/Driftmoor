# GLADE

## Description
A circular opening in the Mistwood where season and behavior are subtly wrong in life-giving ways. Out-of-season flowers bloom, fey-touched herbs grow thick near the center, and a soft ground-shimmer rises without casting practical light.

The glade feels like sanctuary, but not safety-by-accident. Something is actively holding this place against the surrounding dark.

## Ambient
- light: open-canopy dusk glow with faint sourceless shimmer near center
- sound: subdued birdsong at times, then sudden hushes; distant forest movement beyond boundary
- smell: crushed petals, wet earth, and sharp green herb scent
- temperature: mild cool with less harsh bite than surrounding woods
- footing: springy moss with occasional root ridges

## Items
### fey_flowers
- label: Fey flowers
- size: small
- weight: 0.1 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Pale blue-white blooms opening out of season in clustered patches through the glade.
- appearance by distance:
  - intermediate: clusters of pale blossoms punctuating the moss
  - far: scattered pale flecks through green groundcover
  - distant: faint cool-toned speckling across the clearing floor
- interactions:
  - examine: The flowers are healthy and unwilted despite the wrong season.
  - search: The bloom pattern itself is evidence of fey influence in local growth.
  - pick up: A careful harvest yields enough for several mild restorative infusions.

### fey_herbs
- label: Fey-touched herbs
- size: small
- weight: 0.2 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Familiar woodland herbs with subtly bright veins and a faint hum under touch.
- appearance by distance:
  - intermediate: dense herb patches with slightly luminous-vein leaves
  - far: dark-green clumps around the center approaches
  - distant: uneven green texture bands near the poolward ground
- interactions:
  - examine: They are normal species altered by local fey charge, not wholly foreign plants.
  - search: Leaf structure and scent identify useful apothecary value.
  - pick up: Handfuls harvest cleanly and retain charge for later brewing.

### ground_shimmer
- label: Ground shimmer
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Soft rising light from moss that fades a few feet up, visible signature of the repulsion resonance.
- appearance by distance:
  - intermediate: a low veil of pale shimmer over the center ground
  - far: a faint luminous haze near glade heart
  - distant: barely visible silvering in the clearing center
- interactions:
  - examine: It does not illuminate like a torch; it marks active fey resonance.
  - search: Intensity subtly tracks with time of day and boundary strength.

## Features / landmarks
- glade_center: focal point of visible ground shimmer
- oak_west: western standing oak at glade edge
- oak_east: eastern standing oak at glade edge

## Creatures present
- fennel

## Exits
- south-east: TRAIL via trail_entrance
- outward perimeter: FOREST edge beyond the repulsion boundary
- inward: POOL zone at center

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Thorn-hare pair - Small fey-charged hares that bolt toward the pool when threatened. Power: minor. Role: scavenger. Fits because: the glade is framed as living sanctuary with charged but non-hostile growth patterns.

### Treasure & notable items (<= 3 per zone)
- Petal-thread charm - Woven flower-thread charm left as a fey token, grants no direct combat power. Tier: valuable. ~Value: 15 coins to collectors. Affordances: pickable true, wearable wrist, weight 0.1 lb. Fits because: this zone foregrounds anomalous blooms and subtle fey gifts.
- Herbal ledger scrap - Waterproof note strip listing prior herb harvest tallies. Tier: mundane. ~Value: 5 coins, plus practical gathering guidance. Affordances: pickable true, wearable false, weight 0.1 lb. Fits because: Lytha-facing herb economy is already established in scene notes.

### Features (optional)
- A recurring hush wave where ambient sound drops out for one breath before returning.
