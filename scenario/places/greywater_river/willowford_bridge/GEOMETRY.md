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
| bridge_south    | 81 | 39 |
| bridge_center   | 81 | 65 |
| bridge_north    | 81 | 91 |
| toll_booth      | 58 | 32 |
| willow_south    | 32 | 26  |
| willow_north    | 32 | 104 |
| ford_crossing   | 26  | 65 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| BRIDGE        | 6.5        | (65,32) (97,32) (97,97) (65,97)        |
| TOLL_BOOTH    | 6.5        | (45,26) (71,26) (71,42) (45,42)          |
| RIVER         | 3.25        | (0,45) (162,45) (162,84) (0,84)          |
| SOUTH_BANK    | 3.25        | (0,0) (162,0) (162,45) (0,45)            |
| NORTH_BANK    | 3.25        | (0,84) (162,84) (162,130) (0,130)          |
| EXTERIOR      | 0.0        | (0,0) (162,0) (162,130) (0,130)            |

---

## Impassable

| description    | vertices                              |
|----------------|---------------------------------------|
| River water    | (0,48) (162,48) (162,81) (0,81)          |

---

## Connections

| name            | x    | y    | destination                    |
|-----------------|------|------|--------------------------------|
| road_south      | 81 | 0  | places/greywater_river         |
| road_north      | 81 | 130 | places/greywater_river         |
| ford_crossing   | 26  | 65 | places/greywater_river         |
