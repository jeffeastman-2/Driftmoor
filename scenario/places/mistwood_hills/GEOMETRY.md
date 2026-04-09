# GEOMETRY.md — The Mistwood Hills

## Scene

- **name:** The Mistwood Hills
- **place_path:** places/mistwood_hills
- **z_level:** 50.0
- **width:** 6800.0
- **height:** 7500.0
- **origin:** 4200.0, 7000.0, 50.0

Notes: Rolling hills covered in dense fog-laden forest northeast of
Driftmoor. Origin at southwest corner. The interior is a disorientation
zone where paths seem to shift. The Fey Glade is hidden deep inside.
The Old Watchtower sits on a hilltop with views of the region.
Hunters and loggers only venture near the edges.

---

## Landmarks

| name              | x      | y      |
|-------------------|--------|--------|
| mistwood_center   | 2800.0 | 3500.0 |
| watchtower_hill   | 1900.0 | 2600.0 |
| fey_glade         | 3022.0 | 4408.0 |
| southern_edge     | 1500.0 | 500.0  |
| eastern_ridge     | 5500.0 | 3000.0 |
| hunters_camp      | 1000.0 | 800.0  |
| whispering_hollow | 3500.0 | 5000.0 |
| fog_valley        | 2500.0 | 4500.0 |

---

## Zones

| name              | render_z | vertices                                              |
|-------------------|----------|-------------------------------------------------------|
| FEY_GLADE         | 3        | (2972,4358) (3072,4358) (3072,4458) (2972,4458)        |
| WATCHTOWER_HILL   | 2        | (1700,2400) (2100,2400) (2100,2800) (1700,2800)        |
| DEEP_INTERIOR     | 1        | (1300,1500) (5300,1500) (5300,6000) (1300,6000)        |
| FOREST_EDGE       | 1        | (0,0) (6800,0) (6800,7500) (0,7500)                    |
| EXTERIOR          | 0        | (0,0) (6800,0) (6800,7500) (0,7500)                    |

---

## Impassable

| description              | vertices                                              |
|--------------------------|-------------------------------------------------------|
| Dense interior thicket   | (2000,3500) (4000,3500) (4000,5500) (2000,5500)        |

---

## Connections

| name                | x      | y      | destination                          |
|---------------------|--------|--------|--------------------------------------|
| to_driftmoor_road   | 500.0  | 200.0  | places/greywater_river               |
| to_fey_glade        | 3022.0 | 4408.0 | places/mistwood_hills/fey_glade      |
| to_watchtower       | 1900.0 | 2600.0 | places/mistwood_hills/old_watchtower |
| to_obelisk_reach    | 200.0  | 6000.0 | places/obelisk_reach                 |
| to_river_trail      | 6500.0 | 1000.0 | places/greywater_river               |

---

## Boundaries

### Mistwood Disorientation Zone

- **type:** magical
- **blocks:** none
- **effect:** paths shift — navigation DC 15 or party becomes lost; whispers audible
- **vertices:** (1300,1500) (5300,1500) (5300,6000) (1300,6000)
