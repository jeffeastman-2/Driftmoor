# GEOMETRY.md — Ironhoof Forge and Stables

## Scene

- **name:** Ironhoof Forge
- **place_path:** places/driftmoor/ironhoof_forge
- **z_level:** 16.25
- **width:** 146.25
- **height:** 113.75
- **origin:** 9646.0, 7978.75, 16.25

Notes: The forge occupies the northwest portion of the building; the
stables run along the east and south. The corral is an open fenced
yard to the east of the stables. Thorgrim's lean-to is tucked against
the stable's rear (south) wall. The forge is open to the road on the
west side — visible from the street. Origin at southwest corner of
the combined forge+stable footprint, excluding corral.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| anvil            | 26.0  | 71.5 |
| forge_hearth     | 13.0  | 84.5 |
| forge_entrance   | 0.0  | 65.0 |
| stable_entrance  | 65.0 | 0.0  |
| stall_row_center | 104.0 | 55.25 |
| feed_bins        | 123.5 | 26.0  |
| saddle_racks     | 71.5 | 26.0  |
| corral_gate      | 146.25 | 55.25 |
| thorgrim_leanto  | 78.0 | 6.5  |
| forge_wall_marks | 32.5 | 91.0 |
| road_frontage    | 0.0  | 55.25 |

---

## Zones

| name         | render_z | vertices                              |
|--------------|----------|---------------------------------------|
| FORGE        | 6.5        | (0.0,58.5) (58.5,58.5) (58.5,113.75) (0.0,113.75)         |
| LEANTO       | 6.5        | (58.5,0.0) (97.5,0.0) (97.5,26.0) (58.5,26.0)           |
| STABLES      | 3.25        | (58.5,0.0) (146.25,0.0) (146.25,113.75) (58.5,113.75)         |
| CORRAL       | 3.25        | (146.25,16.25) (211.25,16.25) (211.25,97.5) (146.25,97.5)         |
| EXTERIOR     | 0.0        | (-16.25,-16.25) (227.5,-16.25) (227.5,130.0) (-16.25,130.0)       |

---

## Impassable

| description     | vertices                              |
|-----------------|---------------------------------------|
| Forge back wall | (0.0,107.25) (58.5,107.25) (58.5,113.75) (0.0,113.75)         |
| Stall partitions | (58.5,32.5) (146.25,32.5) (146.25,39.0) (58.5,39.0)      |
| Corral fence    | (146.25,16.25) (211.25,16.25) (211.25,22.75) (146.25,22.75)           |

---

## Connections

| name              | x    | y    | destination          |
|-------------------|------|------|----------------------|
| forge_to_street   | 0.0  | 65.0 | places/driftmoor     |
| stable_to_street  | 65.0 | 0.0  | places/driftmoor     |
| corral_gate       | 211.25 | 55.25 | places/driftmoor     |
| road_stonehearth  | 97.5 | -16.25 | places/plains_of_stonehearth |

---

## Boundaries

### Forge Heat Zone

- **type:** conditional
- **blocks:** none
- **effect:** within 9.75m of hearth — extreme heat; unprotected characters risk exhaustion after prolonged exposure
- **vertices:** (0.0,71.5) (32.5,71.5) (32.5,113.75) (0.0,113.75)

---

## Starting Positions

| character | x    | y    | zone    |
|-----------|------|------|---------|
| thorgrim  | 26.0  | 78.0 | FORGE   |
| darrin    | 19.5  | 65.0 | FORGE   |
| kara      | 71.5 | 58.5 | STABLES |