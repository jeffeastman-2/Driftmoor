# GEOMETRY.md — The Mistwood Hills

## Scene

- **name:** The Mistwood Hills
- **place_path:** places/mistwood_hills
- **z_level:** 162.5
- **width:** 22100.0
- **height:** 24375.0
- **origin:** 13650.0, 22750.0, 162.5

Notes: Rolling hills covered in dense fog-laden forest northeast of
Driftmoor. Origin at southwest corner. The interior is a disorientation
zone where paths seem to shift. The Fey Glade is hidden deep inside.
The Old Watchtower sits on a hilltop with views of the region.
Hunters and loggers only venture near the edges.

---

## Landmarks

| name              | x      | y      |
|-------------------|--------|--------|
| mistwood_center   | 9100.0 | 11375.0 |
| watchtower_hill   | 6175.0 | 8450.0 |
| fey_glade         | 9821.5 | 14326.0 |
| southern_edge     | 4875.0 | 1625.0  |
| eastern_ridge     | 17875.0 | 9750.0 |
| hunters_camp      | 3250.0 | 2600.0  |
| whispering_hollow | 11375.0 | 16250.0 |
| fog_valley        | 8125.0 | 14625.0 |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| FEY_GLADE         | 9.75        | (9659.0,14163.5) (9984.0,14163.5) (9984.0,14488.5) (9659.0,14488.5)        |
| WATCHTOWER_HILL   | 6.5        | (5525.0,7800.0) (6825.0,7800.0) (6825.0,9100.0) (5525.0,9100.0)        |
| DEEP_INTERIOR     | 3.25        | (4225.0,4875.0) (17225.0,4875.0) (17225.0,19500.0) (4225.0,19500.0)        |
| FOREST_EDGE       | 3.25        | (0.0,0.0) (22100.0,0.0) (22100.0,24375.0) (0.0,24375.0)                    |
| EXTERIOR          | 0.0        | (0.0,0.0) (22100.0,0.0) (22100.0,24375.0) (0.0,24375.0)                    |

---

## Impassable

| description              | vertices                                              |
|--------------------------|-------------------------------------------------------|
| Dense interior thicket   | (6500.0,11375.0) (13000.0,11375.0) (13000.0,17875.0) (6500.0,17875.0)        |

---

## Connections

| name                | x      | y      | destination                          |
|---------------------|--------|--------|--------------------------------------|
| to_driftmoor_road   | 1625.0  | 650.0  | places/greywater_river               |
| to_fey_glade        | 9821.5 | 14326.0 | places/mistwood_hills/fey_glade      |
| to_watchtower       | 6175.0 | 8450.0 | places/mistwood_hills/old_watchtower |
| to_obelisk_reach    | 650.0  | 19500.0 | places/obelisk_reach                 |
| to_river_trail      | 21125.0 | 3250.0 | places/greywater_river               |

---

## Boundaries

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 48.75 or party becomes lost; whispers audible
- **vertices:** (4225.0,4875.0) (17225.0,4875.0) (17225.0,19500.0) (4225.0,19500.0)
