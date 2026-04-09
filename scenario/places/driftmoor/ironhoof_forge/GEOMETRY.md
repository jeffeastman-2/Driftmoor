# GEOMETRY.md — Ironhoof Forge and Stables

## Scene

- **name:** Ironhoof Forge
- **place_path:** places/driftmoor/ironhoof_forge
- **z_level:** 5.0
- **width:** 45.0
- **height:** 35.0
- **origin:** 2968.0, 2455.0, 5.0

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
| anvil            | 8.0  | 22.0 |
| forge_hearth     | 4.0  | 26.0 |
| forge_entrance   | 0.0  | 20.0 |
| stable_entrance  | 20.0 | 0.0  |
| stall_row_center | 32.0 | 17.0 |
| feed_bins        | 38.0 | 8.0  |
| saddle_racks     | 22.0 | 8.0  |
| corral_gate      | 45.0 | 17.0 |
| thorgrim_leanto  | 24.0 | 2.0  |
| forge_wall_marks | 10.0 | 28.0 |
| road_frontage    | 0.0  | 17.0 |

---

## Zones

| name         | render_z | vertices                              |
|--------------|----------|---------------------------------------|
| FORGE        | 2        | (0,18) (18,18) (18,35) (0,35)         |
| LEANTO       | 2        | (18,0) (30,0) (30,8) (18,8)           |
| STABLES      | 1        | (18,0) (45,0) (45,35) (18,35)         |
| CORRAL       | 1        | (45,5) (65,5) (65,30) (45,30)         |
| EXTERIOR     | 0        | (-5,-5) (70,-5) (70,40) (-5,40)       |

---

## Impassable

| description     | vertices                              |
|-----------------|---------------------------------------|
| Forge back wall | (0,33) (18,33) (18,35) (0,35)         |
| Stall partitions | (18,10) (45,10) (45,12) (18,12)      |
| Corral fence    | (45,5) (65,5) (65,7) (45,7)           |

---

## Connections

| name              | x    | y    | destination          |
|-------------------|------|------|----------------------|
| forge_to_street   | 0.0  | 20.0 | places/driftmoor     |
| stable_to_street  | 20.0 | 0.0  | places/driftmoor     |
| corral_gate       | 65.0 | 17.0 | places/driftmoor     |
| road_stonehearth  | 30.0 | -5.0 | places/plains_of_stonehearth |

---

## Boundaries

### Forge Heat Zone

- **type:** conditional
- **blocks:** none
- **effect:** within 3m of hearth — extreme heat; unprotected characters risk exhaustion after prolonged exposure
- **vertices:** (0,22) (10,22) (10,35) (0,35)

---

## Starting Positions

| character | x    | y    | zone    |
|-----------|------|------|---------|
| thorgrim  | 8.0  | 24.0 | FORGE   |
| darrin    | 6.0  | 20.0 | FORGE   |
| kara      | 22.0 | 18.0 | STABLES |