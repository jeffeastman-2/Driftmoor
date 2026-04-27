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
| mistwood_center   | 9100 | 11375 |
| watchtower_hill   | 6175 | 8450 |
| fey_glade         | 9821 | 14326 |
| southern_edge     | 4875 | 1625  |
| eastern_ridge     | 17875 | 9750 |
| hunters_camp      | 3250 | 2600  |
| whispering_hollow | 11375 | 16250 |
| fog_valley        | 8125 | 14625 |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| FEY_GLADE         | 9.75        | (9659,14163) (9984,14163) (9984,14488) (9659,14488)        |
| WATCHTOWER_HILL   | 6.5        | (5525,7800) (6825,7800) (6825,9100) (5525,9100)        |
| DEEP_INTERIOR     | 3.25        | (4225,4875) (17225,4875) (17225,19500) (4225,19500)        |
| FOREST_EDGE       | 3.25        | (0,0) (22100,0) (22100,24375) (0,24375)                    |
| EXTERIOR          | 0.0        | (0,0) (22100,0) (22100,24375) (0,24375)                    |

---

## Impassable

| description              | vertices                                              |
|--------------------------|-------------------------------------------------------|
| Dense interior thicket   | (6500,11375) (13000,11375) (13000,17875) (6500,17875)        |

---

## Connections

| name                | x      | y      | destination                          |
|---------------------|--------|--------|--------------------------------------|
| to_driftmoor_road   | 1625  | 650  | places/greywater_river               |
| to_fey_glade        | 9821 | 14326 | places/mistwood_hills/fey_glade      |
| to_watchtower       | 6175 | 8450 | places/mistwood_hills/old_watchtower |
| to_obelisk_reach    | 650  | 19500 | places/obelisk_reach                 |
| to_river_trail      | 21125 | 3250 | places/greywater_river               |

---

## Boundaries

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 48.75 or party becomes lost; whispers audible
- **vertices:** (4225,4875) (17225,4875) (17225,19500) (4225,19500)
