# GEOMETRY.md — The Sea Stacks

## Scene

- **name:** The Sea Stacks
- **place_path:** places/azure_sea/sea_stacks
- **z_level:** 0.0
- **width:** 120.0
- **height:** 100.0
- **origin:** 1140.0, 5750.0, 0.0

Notes: Tall isolated rock formations rising from the water near
shore. Origin at southwest corner of the cluster area. The stacks
themselves are vertical stone pillars 15-30m tall. The bases are
accessible at low tide on foot; at high tide the bases are submerged.
Seabirds nest in the crevices above. The gaps between stacks are
navigable by small boat.

---

## Landmarks

| name            | x     | y     |
|-----------------|-------|-------|
| stack_north     | 50.0  | 80.0  |
| stack_central   | 60.0  | 50.0  |
| stack_south     | 40.0  | 20.0  |
| stack_east      | 90.0  | 55.0  |
| nesting_ledge   | 55.0  | 82.0  |
| shelter_cove    | 70.0  | 40.0  |
| tidal_passage   | 30.0  | 50.0  |

---

## Zones

| name           | render_z | vertices                                    |
|----------------|----------|---------------------------------------------|
| STACK_NORTH    | 3        | (40,70) (60,70) (60,90) (40,90)              |
| STACK_CENTRAL  | 3        | (50,40) (70,40) (70,60) (50,60)              |
| STACK_SOUTH    | 3        | (30,10) (50,10) (50,30) (30,30)              |
| STACK_EAST     | 3        | (80,45) (100,45) (100,65) (80,65)            |
| SHALLOWS       | 1        | (10,5) (110,5) (110,95) (10,95)              |
| EXTERIOR       | 0        | (0,0) (120,0) (120,100) (0,100)              |

---

## Impassable

| description      | vertices                                    |
|------------------|---------------------------------------------|
| Stack North base | (43,73) (57,73) (57,87) (43,87)              |
| Stack Central    | (53,43) (67,43) (67,57) (53,57)              |
| Stack South base | (33,13) (47,13) (47,27) (33,27)              |
| Stack East base  | (83,48) (97,48) (97,62) (83,62)              |

---

## Connections

| name               | x     | y    | destination                    |
|--------------------|-------|------|--------------------------------|
| to_drowned_isle    | 10.0  | 10.0 | places/azure_sea/drowned_isle  |
| to_coastal_path    | 110.0 | 50.0 | places/azure_sea               |

---

## Boundaries

### Tidal Access

- **type:** conditional
- **blocks:** all
- **effect:** stack bases accessible only at low tide on foot; at high tide requires swimming (DC 13 Athletics, cold water)
- **vertices:** (10,5) (110,5) (110,95) (10,95)
