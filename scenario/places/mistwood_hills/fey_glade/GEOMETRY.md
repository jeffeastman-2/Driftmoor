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

**Strength varies by conditions:**

| condition                        | effect                                                                                         |
|----------------------------------|------------------------------------------------------------------------------------------------|
| Daylight (default)               | Strong repulsion. Blocked creatures feel deep wrongness and cannot cross.                      |
| Daylight + prey within 10 units  | Creature may attempt DC 15 WIS save to force through. On success: crosses but takes 2d6 radiant damage and is frightened 1 round. On failure: repelled, stunned 1 round. |
| Dusk / dawn                      | Boundary weakens. DC 12 WIS save to cross. On success: 1d6 radiant damage. On failure: repelled. |
| Full darkness                    | Boundary is a faint deterrent only. DC 8 WIS save to cross, no damage on success. On failure: repelled but may retry next turn. |
| Full darkness + prey within 10   | Boundary barely holds. Creature crosses freely but takes 1d4 radiant damage.                   |

## Starting Positions

| character    | x     | y     | zone     |
|--------------|-------|-------|----------|
| aeliana      | 79.0  | 25.0  | TRAIL    |
| fennel       | 44.0  | 52.0  | GLADE    |
| shadowbeast  | 37.0  | 50.0  | FOREST   |
