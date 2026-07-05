# TRAIL

## Description
A narrow forest trail runs up toward the glade opening and then hesitates at the treeline. Here the signs of pursuit are freshest: churned earth, pacing marks, and repeated turns at the boundary where the shadowbeast refused or failed to cross.

The trail is an approach lane and pressure line, not a safe resting spot.

## Ambient
- light: filtered canopy light with deeper shadow bands between trunks
- sound: branch creak, distant movement, and intermittent quiet from the glade side
- smell: damp earth, bark, and disturbed leaf litter
- temperature: cooler than the glade and more wind-touched
- footing: compacted soil with root snags and soft ruts where tracks deepen

## Items
### shadowbeast_tracks
- label: Shadowbeast tracks
- size: large
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: true
- description: Cloven prints that lead to treeline, pace the edge, and repeatedly turn back without crossing.
- appearance by distance:
  - intermediate: deep cloven impressions in churned trail soil
  - far: interrupted dark track lines toward the glade edge
  - distant: broken soil streaks and compressed leaf patches
- interactions:
  - examine: Track depth and stride indicate sustained patrol and agitation near the boundary.
  - search: Freshness gradient shows repeated passes over multiple days, not a single charge.

## Features / landmarks
- trail_entrance: seam where TRAIL opens into the glade edge
- trail_exit: southern route back to mistwood_hills path

## Creatures present
- aeliana

## Exits
- north-west: GLADE via trail_entrance
- south: mistwood_hills path via trail_exit
- sides: FOREST understory

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Treeline stalker - A minor shadow scavenger that follows the shadowbeast's perimeter route without entering the glade. Power: minor. Role: lurker. Fits because: this lane is the contested threshold where shadow pressure accumulates but the repulsion remains active.

### Treasure & notable items (<= 3 per zone)
- Splintered arrow cluster - Three old fletched shafts broken near the boundary line. Tier: mundane. ~Value: 1 coin total. Affordances: pickable true, wearable false, weight 0.2 lb. Fits because: Fennel's repeated defensive arrow fire is explicit in scene setup.

### Features (optional)
- A narrow strip of unnaturally untouched leaves exactly where the boundary influence first begins to be felt.
