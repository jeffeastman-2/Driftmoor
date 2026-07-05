# POOL

## Description
The spring pool is the glade's still heart: shallow, clear, and unnaturally calm even when branches sway overhead. Its edge is ringed with soft moss and fey herbs, and one worked stone sits half-buried where water meets earth.

This is not a ruin so much as an anchor point. The pool, stone, and glade resonance pulse together as one quiet system.

## Ambient
- light: soft reflected light from open glade canopy; no harsh glare
- sound: very quiet water movement and distant forest rustle
- smell: clean wet stone and sweet crushed herb
- temperature: cool but not biting
- footing: damp edge stones with slick moss at the margin

## Items
### clear_spring
- label: Clear spring
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A shallow pure pool with glass-still surface and faint restorative quality.
- appearance by distance:
  - intermediate: a bright still patch of water with visible pale stone bed
  - far: a smooth silver-blue plate in the glade center
  - distant: a reflective pale blot among green and shadow
- interactions:
  - examine: The water is clear to the bottom and unnaturally still for an open pool.
  - search: No fish or insect life is visible; the stillness is notable but not threatening.

### carved_stone
- label: Carved stone
- size: medium
- weight: n/a
- pickable: false
- wearable: false
- flavor_only: false
- description: A flat worked stone with old spiral grooves at the pool edge, faintly humming on touch.
- appearance by distance:
  - intermediate: a lichen-dusted stone plate with visible spiral carving
  - far: a flat pale slab at water's edge
  - distant: a low angular patch beside the pool
- interactions:
  - examine: The spiral reads as an anchor pattern tied to fey resonance, not a prison seal.
  - search: Roots and earth hold the stone deep; prying finds no quick base or seam.
  - press: The hum deepens briefly; the pool ripples outward and the boundary pulse is momentarily felt.

## Features / landmarks
- pool_surface: the visible center of the spring basin
- carved_stone: worked anchor slab at pool edge

## Creatures present
- none

## Exits
- west/east/north/south: GLADE perimeter around the pool

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Water-mote sprite - A tiny fey mote that mirrors nearby gestures and flees from aggression. Power: minor. Role: lurker. Fits because: this pool is the glade's resonance anchor and the clearest focal point for gentle fey manifestation.

### Treasure & notable items (<= 3 per zone)
- Spring-vial crystal - Clear vial that preserves one day's restorative spring property when stoppered at source. Tier: valuable. ~Value: 30 coins to apothecaries. Affordances: pickable true, wearable false, weight 0.2 lb. Fits because: the pool already has explicit restorative behavior in scene lore.

### Features (optional)
- Brief concentric ripples appear when the carved stone is touched, even in total windless calm.
