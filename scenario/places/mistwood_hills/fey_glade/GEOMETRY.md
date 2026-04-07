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

| name     | render_z | vertices                                    |
|----------|----------|---------------------------------------------|
| POOL     | 2        | (42,52) (43,52) (43,53) (42,53)             |
| GLADE    | 1        | (40,45) (60,45) (60,55) (40,55)             |
| TRAIL    | 1        | (59,45) (60,45) (100,4) (99,3)              |
| FOREST   | 0        | (0,0) (100,0) (100,100) (0,100)             |

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
- **effect:** wrongness — body stops, cannot cross
- **vertices:** (39,44) (61,44) (61,56) (39,56)

## Starting Positions

| character    | x     | y     | zone     |
|--------------|-------|-------|----------|
| aeliana      | 79.0  | 25.0  | TRAIL    |
| fennel       | 44.0  | 52.0  | GLADE    |
| shadowbeast  | 37.0  | 50.0  | FOREST   |
