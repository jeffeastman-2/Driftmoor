# GEOMETRY.md — The Obelisk Reach

## Scene

- **name:** The Obelisk Reach
- **place_path:** places/obelisk_reach
- **z_level:** 80.0
- **width:** 2800.0
- **height:** 3500.0
- **origin:** 2400.0, 11500.0, 80.0

Notes: Jagged cliffs and rocky plateaus north of Driftmoor. Origin
at southwest corner. The Shattered Obelisk dominates the northern
portion. The Echoing Caverns entrance is a crack in the cliff face
west of the obelisk. Strange symbols are carved into the cliffs.
Animals avoid this area. The terrain is treacherous with narrow paths.

---

## Landmarks

| name                  | x      | y      |
|-----------------------|--------|--------|
| obelisk_reach_edge    | 1100.0 | 1300.0 |
| shattered_obelisk     | 1000.0 | 2300.0 |
| echoing_caverns_mouth | 1300.0 | 2000.0 |
| cliff_approach        | 800.0  | 800.0  |
| symbol_cliff          | 500.0  | 1500.0 |
| narrow_path           | 1200.0 | 1600.0 |
| scorched_ground       | 1000.0 | 2500.0 |
| outlook_ledge         | 1800.0 | 1800.0 |

---

## Zones

| name               | render_z | vertices                                              |
|--------------------|----------|-------------------------------------------------------|
| SHATTERED_OBELISK  | 3        | (700,2000) (1300,2000) (1300,2700) (700,2700)          |
| ECHOING_CAVERNS    | 3        | (1100,1700) (1600,1700) (1600,2300) (1100,2300)        |
| CLIFF_PLATEAU      | 2        | (200,1000) (2200,1000) (2400,3200) (0,3200)            |
| APPROACH_PATH      | 1        | (400,200) (1400,200) (1400,1000) (400,1000)            |
| CLIFFS             | 1        | (0,0) (2800,0) (2800,3500) (0,3500)                    |
| EXTERIOR           | 0        | (0,0) (2800,0) (2800,3500) (0,3500)                    |

---

## Impassable

| description          | vertices                                              |
|----------------------|-------------------------------------------------------|
| Western cliff face   | (0,1500) (200,1500) (200,3500) (0,3500)                |
| Eastern cliff drop   | (2400,1500) (2800,1500) (2800,3500) (2400,3500)        |

---

## Connections

| name                | x      | y      | destination                              |
|---------------------|--------|--------|------------------------------------------|
| approach_south      | 900.0  | 100.0  | places/driftmoor                         |
| to_obelisk          | 1000.0 | 2300.0 | places/obelisk_reach/shattered_obelisk   |
| to_caverns          | 1300.0 | 2000.0 | places/obelisk_reach/echoing_caverns     |
| to_mistwood_east    | 2600.0 | 1500.0 | places/mistwood_hills                    |

---

## Boundaries

### Obelisk Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker; stronger near the obelisk
- **vertices:** (200,1000) (2400,1000) (2400,3200) (200,3200)
