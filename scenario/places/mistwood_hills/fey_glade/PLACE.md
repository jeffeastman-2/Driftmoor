# PLACE.md — The Fey Glade

## Description and Atmosphere
Hidden deep in the Mistwood. The trees thin suddenly into a circular clearing. The light here is different — warmer, cleaner than the fog-filtered dimness of the surrounding forest. The grass is impossibly green. Flowers bloom that have no business blooming in this season. At night, the glade shimmers with faint colored light. The air smells of something sweet and entirely unidentifiable.

Time may pass differently here. The party may not notice immediately.

## Zones

Four zones arranged linearly. Movement between adjacent zones costs one ACTION.

### TRAIL
Dense pine approaching the glade from the south. Fog-filtered light. Sound carries far in both directions. High cover. Low visibility beyond 10 feet. The shadowbeast tracks go cold here.

### TREELINE
Where forest meets clearing. The fey barrier runs along this zone's inner edge — an ancient ward that pre-dates the obelisk, woven into the glade itself. The barrier was not built to stop shadowbeasts; it protects the pool and the carved stone. Shadow creatures are repelled as a side effect — the barrier's energy is simply antithetical to their nature. During daylight the barrier is absolute: no creature of shadow or undeath can cross it. At dusk and dawn it weakens. In full darkness it barely holds. Partial cover. Visibility into GLADE: full. Visibility into TRAIL: 20 feet.

### GLADE
Circular clearing approximately 40 feet across. Unnaturally warm. Out-of-season flowers. Air shimmers. No cover. Full visibility to TREELINE and POOL. Safe from the shadowbeast.

### POOL
Far (north) side of glade. Light rises from the ground in a slow shimmer. A flat carved stone lies at the water's edge, half-buried — its symbols match those of the obelisk civilization. The pool's luminous cycle tracks with the obelisk's energy pulses, suggesting the glade was a node in whatever network the obelisk was part of. No cover. Full visibility. Do not look directly into the water. What the barrier actually protects is what Fennel saw on night two and cannot remember.

## Adjacency
TRAIL → TREELINE → GLADE → POOL (linear — must pass through each zone in sequence)

## Who Is Normally Here
- Fey presence (level and nature at DM's discretion)
- Fennel (Lytha's apprentice) — sheltering in GLADE for three days
- Shadowbeast — patrolling TREELINE perimeter, cannot cross boundary into GLADE

## Connections
- Mistwood Hills deep paths (DC 15 Survival to find deliberately; otherwise stumbled upon)

## Shared Facts
- The glade boundary is fey in origin, older than the obelisk — it protects the pool and carved stone
- Shadow creatures and undead are repelled as a side effect, not by design
- During daylight the barrier is absolute — no shadowbeast can cross, no save allowed
- The barrier weakens at dusk/dawn and barely holds in full darkness
- The pool brightens at dusk, peaks at midnight
- The carved stone's symbols match the obelisk civilization
- Something in the trees follows sound
- The shadowbeast tracks on the TRAIL go cold at the TREELINE

## Dynamic State
*(Updated by monitor agent)*

- **Current status:** Active fey presence; shadowbeast standoff at boundary
- **Clock:** Dusk in ~3 hours (mid-afternoon)
- **Tension:** Rising — Aeliana approaching shadowbeast position
- **Active conditions:**
  - The glade's fey barrier is absolute during daylight — shadowbeasts cannot enter, period
  - At dusk (~3 hours) the barrier will begin to weaken
  - Shadowbeast has not yet detected Aeliana
  - Fennel has detected Aeliana and is deciding
  - Aeliana is unaware of both Fennel and the shadowbeast
- **Scene flags:**
  - `fennel_memory_degradation_active`
  - `pool_cycle_approaching` (dusk in 3 hours)
  - `shadowbeast_unaware_of_aeliana` (fragile — ends if she makes sound or crosses into TREELINE)
