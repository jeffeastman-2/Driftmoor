# GEOMETRY.md — The Sea Stacks

## Scene

- **name:** The Sea Stacks
- **place_path:** places/azure_sea/sea_stacks
- **z_level:** 0.0
- **width:** 390.0
- **height:** 325.0
- **origin:** 3705.0, 18687.5, 0.0

Notes: Tall isolated rock formations rising from the water near
shore. Origin at southwest corner of the cluster area. The stacks
themselves are vertical stone pillars 48.75-97.5m tall. The bases are
accessible at low tide on foot; at high tide the bases are submerged.
Seabirds nest in the crevices above. The gaps between stacks are
navigable by small boat.

---

## Landmarks

| name            | x     | y     |
|-----------------|-------|-------|
| stack_north     | 162.5  | 260.0  |
| stack_central   | 195.0  | 162.5  |
| stack_south     | 130.0  | 65.0  |
| stack_east      | 292.5  | 178.75  |
| nesting_ledge   | 178.75  | 266.5  |
| shelter_cove    | 227.5  | 130.0  |
| tidal_passage   | 97.5  | 162.5  |

---

## Zones

| name           | render_z | vertices                                    |
|----------------|----------|---------------------------------------------|
| STACK_NORTH    | 9.75        | (130.0,227.5) (195.0,227.5) (195.0,292.5) (130.0,292.5)              |
| STACK_CENTRAL  | 9.75        | (162.5,130.0) (227.5,130.0) (227.5,195.0) (162.5,195.0)              |
| STACK_SOUTH    | 9.75        | (97.5,32.5) (162.5,32.5) (162.5,97.5) (97.5,97.5)              |
| STACK_EAST     | 9.75        | (260.0,146.25) (325.0,146.25) (325.0,211.25) (260.0,211.25)            |
| SHALLOWS       | 3.25        | (32.5,16.25) (357.5,16.25) (357.5,308.75) (32.5,308.75)              |
| EXTERIOR       | 0.0        | (0.0,0.0) (390.0,0.0) (390.0,325.0) (0.0,325.0)              |

---

## Impassable

| description      | vertices                                    |
|------------------|---------------------------------------------|
| Stack North base | (139.75,237.25) (185.25,237.25) (185.25,282.75) (139.75,282.75)              |
| Stack Central    | (172.25,139.75) (217.75,139.75) (217.75,185.25) (172.25,185.25)              |
| Stack South base | (107.25,42.25) (152.75,42.25) (152.75,87.75) (107.25,87.75)              |
| Stack East base  | (269.75,156.0) (315.25,156.0) (315.25,201.5) (269.75,201.5)              |

---

## Connections

| name               | x     | y    | destination                    |
|--------------------|-------|------|--------------------------------|
| to_drowned_isle    | 32.5  | 32.5 | places/azure_sea/drowned_isle  |
| to_coastal_path    | 357.5 | 162.5 | places/azure_sea               |

---

## Boundaries

### Tidal Access

- **type:** conditional
- **blocks:** all
- **effect:** stack bases accessible only at low tide on foot; at high tide requires swimming (DC 42.25 Athletics, cold water)
- **vertices:** (32.5,16.25) (357.5,16.25) (357.5,308.75) (32.5,308.75)
