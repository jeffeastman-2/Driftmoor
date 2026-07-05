# Bone Chamber

## Description
A low, dry chamber where Father Elden's companions lie undisturbed beneath decades of cave dust. Three dead, three final postures: one clutching faith, one reaching, one curled in solitary failure.

It feels less like a room than a period at the end of a sentence no one wanted to finish.

## Ambient
- light: none without carried light or darkvision
- sound: muted, with only a thin return from the curved walls
- smell: dry dust, old leather rot, and brittle bone
- temperature: cold and dry
- footing: mostly firm stone broken by scattered debris and bone fragments

## Items
### companion_remains
- label: Skeletal remains
- size: medium
- weight: 18 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Three long-dead expeditioners reduced to fragile skeletons with scraps of aged gear.
- appearance by distance:
  - intermediate: a tangle of pale bones and rotted kit
  - far: pale clustered shapes along the floor
  - distant: a low pale scatter against stone
- interactions:
  - examine: The body positions imply panic and fast death rather than orderly rest.
  - search: Personal effects and map fragments can be found among the remains.
  - pick up: The remains can be gathered carefully for return to consecrated ground.

### holy_symbol_pelor
- label: Holy symbol
- size: tiny
- weight: 0.2 lb
- pickable: true
- wearable: neck
- flavor_only: false
- description: A tarnished silver sun-disc on a rotted thong, still recognizable as Pelor's mark.
- appearance by distance:
  - intermediate: a small metal glint among bones
  - far: a tiny pale spark near one skeleton
  - distant: an intermittent pinprick glimmer
- interactions:
  - examine: The symbol is worn but intact and remains suitable as a divine focus.
  - pick up: It can be taken without disturbing the chamber structure.

### parchment_fragment
- label: Parchment fragment
- size: tiny
- weight: 0.1 lb
- pickable: true
- wearable: false
- flavor_only: false
- description: Folded oiled parchment showing a partial lower-cavern sketch with a note indicating deeper space beyond collapse.
- appearance by distance:
  - intermediate: a folded pale scrap near the remains
  - far: a tiny light rectangle on dark stone
  - distant: too small to identify clearly
- interactions:
  - examine: The map note points toward hidden continuation beyond the Pool Cavern collapse.
  - read: The writing is cramped but legible enough to identify a marked deeper route.
  - pick up: The fragment can be removed intact if handled carefully.

## Features / landmarks
- bone_chamber_threshold: north opening to Deep Passage

## Creatures present
- none

## Exits
- north: Deep Passage

## Proposed (review -> keep needs GEOMETRY placement, or cut)
Ideas to enrich the zone. NOT loaded by the engine. No coordinates.

### Creatures (<= 2 per zone)
- Dust sentinel spirit - Weak echo of a failed vow bound to the companions' final stand. Power: minor. Role: guardian. Fits because: this chamber centers on named dead tied to Father Elden's quest.

### Treasure & notable items (<= 3 per zone)
- Expedition signet token - Small brass token stamped with an older Reach expedition mark. Tier: valuable. ~Value: 18 coins. Affordances: pickable true, wearable neck, weight 0.1 lb. Fits because: it supports the identified-history thread of Elden's lost companions.
- Last-rite vellum strip - Narrow prayer strip wrapped around a rib fragment. Tier: mundane. ~Value: none. Affordances: pickable true, wearable false, weight 0.1 lb. Fits because: it reinforces the chamber's devotional and funerary tone.

### Features (optional)
- A shallow ash circle near one skeleton indicating a final failed camp or prayer vigil.
