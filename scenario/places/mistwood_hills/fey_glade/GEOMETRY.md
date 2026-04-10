# GEOMETRY.md — The Fey Glade

## Scene

- **name:** The Fey Glade
- **place_path:** places/mistwood_hills/fey_glade
- **z_level:** 0.2
- **width:** 100.0
- **height:** 100.0
- **origin:** 1222.0, 2608.0, 0.2

## Landmarks

| name             | x     | y     |
|------------------|-------|-------|
| glade_center     | 50.0  | 50.0  |
| pool_surface     | 42.5  | 52.5  |
| carved_stone     | 42.0  | 52.0  |
| trail_entrance   | 59.0  | 45.0  |
| oak_west         | 43.0  | 50.0  |
| oak_east         | 57.0  | 50.0  |

## Zones

Zone order matters — first match wins in zone_at(). FOREST must be last.

| name     | vertices                                                   |
|----------|------------------------------------------------------------|
| POOL     | (42,52,0.3) (43,52,0.3) (43,53,0.3) (42,53,0.3)          |
| GLADE    | (40,45,0.2) (60,45,0.2) (60,55,0.2) (40,55,0.2)          |
| TRAIL    | (59,45,0.1) (60,45,0.1) (100,4,0.0) (99,3,0.0)           |
| FOREST   | (0,0,0.0) (100,0,0.0) (100,100,0.0) (0,100,0.0)          |

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| Pool surface | (42,52) (43,52) (43,53) (42,53)  |

## Connections

| name          | x     | y    | destination          |
|---------------|-------|------|----------------------|
| trail_exit    | 99.0  | 4.0  | mistwood_hills path  |

## Boundaries

### Fey Glade Repulsion Boundary

- **type:** magical
- **blocks:** shadowbeast, shadow_creature, undead
- **vertices:** (39,44) (61,44) (61,56) (39,56)

**Nature:** This barrier pre-dates the obelisk civilization. It is fey
in origin — a living ward woven into the glade itself, sustained by
whatever presence inhabits the pool and the carved stone. It was not
built to repel shadowbeasts. It was built to protect something: the
pool, the carved stone, and whatever the pool reveals to those who
watch it at night. Shadow creatures and undead are repelled as a side
effect — the barrier's energy is antithetical to their nature.

The pool's carved stone matches obelisk civilization symbols, and the
pool's luminous cycle tracks with the obelisk's energy pulses. The
glade may have been a node in the same ancient network. The barrier
is a remnant of that network's protective function. What it actually
guards is what Fennel saw on night two and cannot remember.

**Strength varies by conditions:**

| condition                        | effect                                                                                         |
|----------------------------------|------------------------------------------------------------------------------------------------|
| Daylight (default)               | Absolute. No creature of shadow or undeath can cross. There is no save, no override, no exception. The barrier simply does not permit passage. Blocked creatures feel a deep, sourceless wrongness — not pain, but the certainty that they cannot exist here. |
| Dusk / dawn                      | Weakened but substantial. DC 15 WIS save to force through. On success: crosses but takes 2d6 radiant damage and is frightened 1 round. On failure: repelled, stunned 1 round. |
| Full darkness                    | Flickering. DC 10 WIS save to cross. On success: 1d6 radiant damage. On failure: repelled but may retry next turn. |
| Full darkness + prey within 10   | Barely holding. DC 8 WIS save to cross, 1d4 radiant damage on success or failure. |

## Starting Positions

| character    | x     | y     | zone     |
|--------------|-------|-------|----------|
| aeliana      | 79.0  | 25.0  | TRAIL    |
| fennel       | 44.0  | 52.0  | GLADE    |
| shadowbeast  | 37.0  | 50.0  | FOREST   |
