# GEOMETRY.md — Willowford Bridge

## Scene

- **name:** Willowford Bridge
- **place_path:** places/greywater_river/willowford_bridge
- **z_level:** 13.0
- **width:** 162.5
- **height:** 130.0
- **origin:** 15518.75, 12285.0, 13.0

Notes: A sturdy wooden bridge crossing the Greywater River. Wide
enough for a cart. Origin at southwest corner. The bridge runs
north-south across the river. A small toll booth sits on the south
(Driftmoor) side. Willows line both banks.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| bridge_south    | 81.25 | 39.0 |
| bridge_center   | 81.25 | 65.0 |
| bridge_north    | 81.25 | 91.0 |
| toll_booth      | 58.5 | 32.5 |
| willow_south    | 32.5 | 26.0  |
| willow_north    | 32.5 | 104.0 |
| ford_crossing   | 26.0  | 65.0 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| BRIDGE        | 6.5        | (65.0,32.5) (97.5,32.5) (97.5,97.5) (65.0,97.5)        |
| TOLL_BOOTH    | 6.5        | (45.5,26.0) (71.5,26.0) (71.5,42.25) (45.5,42.25)          |
| RIVER         | 3.25        | (0.0,45.5) (162.5,45.5) (162.5,84.5) (0.0,84.5)          |
| SOUTH_BANK    | 3.25        | (0.0,0.0) (162.5,0.0) (162.5,45.5) (0.0,45.5)            |
| NORTH_BANK    | 3.25        | (0.0,84.5) (162.5,84.5) (162.5,130.0) (0.0,130.0)          |
| EXTERIOR      | 0.0        | (0.0,0.0) (162.5,0.0) (162.5,130.0) (0.0,130.0)            |

---

## Impassable

| description    | vertices                              |
|----------------|---------------------------------------|
| River water    | (0.0,48.75) (162.5,48.75) (162.5,81.25) (0.0,81.25)          |

---

## Connections

| name            | x    | y    | destination                    |
|-----------------|------|------|--------------------------------|
| road_south      | 81.25 | 0.0  | places/greywater_river         |
| road_north      | 81.25 | 130.0 | places/greywater_river         |
| ford_crossing   | 26.0  | 65.0 | places/greywater_river         |
