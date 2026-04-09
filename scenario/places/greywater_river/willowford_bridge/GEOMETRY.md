# GEOMETRY.md — Willowford Bridge

## Scene

- **name:** Willowford Bridge
- **place_path:** places/greywater_river/willowford_bridge
- **z_level:** 4.0
- **width:** 50.0
- **height:** 40.0
- **origin:** 4775.0, 3780.0, 4.0

Notes: A sturdy wooden bridge crossing the Greywater River. Wide
enough for a cart. Origin at southwest corner. The bridge runs
north-south across the river. A small toll booth sits on the south
(Driftmoor) side. Willows line both banks.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| bridge_south    | 25.0 | 12.0 |
| bridge_center   | 25.0 | 20.0 |
| bridge_north    | 25.0 | 28.0 |
| toll_booth      | 18.0 | 10.0 |
| willow_south    | 10.0 | 8.0  |
| willow_north    | 10.0 | 32.0 |
| ford_crossing   | 8.0  | 20.0 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| BRIDGE        | 2        | (20,10) (30,10) (30,30) (20,30)        |
| TOLL_BOOTH    | 2        | (14,8) (22,8) (22,13) (14,13)          |
| RIVER         | 1        | (0,14) (50,14) (50,26) (0,26)          |
| SOUTH_BANK    | 1        | (0,0) (50,0) (50,14) (0,14)            |
| NORTH_BANK    | 1        | (0,26) (50,26) (50,40) (0,40)          |
| EXTERIOR      | 0        | (0,0) (50,0) (50,40) (0,40)            |

---

## Impassable

| description    | vertices                              |
|----------------|---------------------------------------|
| River water    | (0,15) (50,15) (50,25) (0,25)          |

---

## Connections

| name            | x    | y    | destination                    |
|-----------------|------|------|--------------------------------|
| road_south      | 25.0 | 0.0  | places/greywater_river         |
| road_north      | 25.0 | 40.0 | places/greywater_river         |
| ford_crossing   | 8.0  | 20.0 | places/greywater_river         |
