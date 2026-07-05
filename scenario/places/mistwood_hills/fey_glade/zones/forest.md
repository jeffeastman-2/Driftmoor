# FOREST

## Description
Dense Mistwood closes around the clearing on all sides: root-tangled floor, low hanging boughs, and limited sightlines. This is where normal woodland threat behavior returns, except at the glade edge where repulsion pressure creates a palpable wrongness for shadow-bound things.

The forest zone is broad by geometry and intentionally diffuse in detail; it frames the glade as rare open ground.

## Ambient
- light: heavily filtered and quickly occluded beyond short range
- sound: layered leaf movement, distant animal calls, occasional abrupt silences
- smell: wet bark, fern, and old loam
- temperature: cool and damp with stronger drafts than inside the glade
- footing: roots, soft duff, and concealed hollows

## Items
### dense_cover
- label: Dense cover
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Interwoven ferns, roots, and low boughs that provide concealment and break clean ranged lanes.
- appearance by distance:
  - intermediate: thick layered vegetation and branch tangle
  - far: dark uneven wall of undergrowth
  - distant: mottled green-black massing between trunks
- interactions:
  - examine: This is ideal concealment terrain and difficult to move through quickly.
  - search: Small movement lanes exist but are narrow and easy to lose.

## Features / landmarks
- treeline ring: boundary-facing edge around the glade perimeter

## Creatures present
- shadowbeast

## Exits
- inward: GLADE perimeter approaches
- outward: wider mistwood_hills forest
- nearest route out: TRAIL corridor to south

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Shadowbeast scavenger whelps - Lesser shadow-fed creatures that trail the main beast's patrol. Power: minor. Role: scavenger. Fits because: three-day perimeter pressure implies supporting ecology feeding on failed incursions.

### Treasure & notable items (<= 3 per zone)
- Resin-black totem chip - Fragment of old warded wood with charred runes, half-swallowed by roots. Tier: valuable. ~Value: 25 coins to occult buyers. Affordances: pickable true, wearable false, weight 0.4 lb. Fits because: this perimeter has sustained magical conflict between shadow force and repulsion effect.

### Features (optional)
- Patchy boundary pressure where shadow-touched creatures hesitate, pace, and turn before entering the glade ring.
