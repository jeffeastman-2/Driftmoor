# GEOMETRY.md — The Obelisk Reach

## Scene

- **name:** The Obelisk Reach
- **place_path:** places/obelisk_reach
- **z_level:** 260.0
- **width:** 9100.0
- **height:** 11375.0
- **origin:** 7800.0, 37375.0, 260.0

Notes: Jagged cliffs and rocky plateaus north of Driftmoor. Origin
at southwest corner. The Shattered Obelisk dominates the northern
portion. The Echoing Caverns entrance is a crack in the cliff face
west of the obelisk. Strange symbols are carved into the cliffs.
Animals avoid this area. The terrain is treacherous with narrow paths.

---

## Landmarks

| name                  | x      | y      |
|-----------------------|--------|--------|
| obelisk_reach_edge    | 3575.0 | 4225.0 |
| shattered_obelisk     | 3250.0 | 7475.0 |
| echoing_caverns_mouth | 4225.0 | 6500.0 |
| cliff_approach        | 2600.0  | 2600.0  |
| symbol_cliff          | 1625.0  | 4875.0 |
| narrow_path           | 3900.0 | 5200.0 |
| scorched_ground       | 3250.0 | 8125.0 |
| outlook_ledge         | 5850.0 | 5850.0 |

---

## Zones

| name               | render_z | vertices                                              |
|--------------------|----------|-------------------------------------------------------|
| SHATTERED_OBELISK  | 9.75        | (2275.0,6500.0) (4225.0,6500.0) (4225.0,8775.0) (2275.0,8775.0)          |
| ECHOING_CAVERNS    | 9.75        | (3575.0,5525.0) (5200.0,5525.0) (5200.0,7475.0) (3575.0,7475.0)        |
| CLIFF_PLATEAU      | 6.5        | (650.0,3250.0) (7150.0,3250.0) (7800.0,10400.0) (0.0,10400.0)            |
| APPROACH_PATH      | 3.25        | (1300.0,650.0) (4550.0,650.0) (4550.0,3250.0) (1300.0,3250.0)            |
| CLIFFS             | 3.25        | (0.0,0.0) (9100.0,0.0) (9100.0,11375.0) (0.0,11375.0)                    |
| EXTERIOR           | 0.0        | (0.0,0.0) (9100.0,0.0) (9100.0,11375.0) (0.0,11375.0)                    |

---

## Impassable

| description          | vertices                                              |
|----------------------|-------------------------------------------------------|
| Western cliff face   | (0.0,4875.0) (650.0,4875.0) (650.0,11375.0) (0.0,11375.0)                |
| Eastern cliff drop   | (7800.0,4875.0) (9100.0,4875.0) (9100.0,11375.0) (7800.0,11375.0)        |

---

## Connections

| name                | x      | y      | destination                              |
|---------------------|--------|--------|------------------------------------------|
| approach_south      | 2925.0  | 325.0  | places/driftmoor                         |
| to_obelisk          | 3250.0 | 7475.0 | places/obelisk_reach/shattered_obelisk   |
| to_caverns          | 4225.0 | 6500.0 | places/obelisk_reach/echoing_caverns     |
| to_mistwood_east    | 8450.0 | 4875.0 | places/mistwood_hills                    |

---

## Boundaries

### Obelisk Distortion Field

- **type:** magical
- **blocks:** none
- **effect:** perception checks degraded, compasses spin, light sources flicker; stronger near the obelisk
- **vertices:** (650.0,3250.0) (7800.0,3250.0) (7800.0,10400.0) (650.0,10400.0)
