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
| anvil            | 26  | 71 |
| forge_hearth     | 13  | 84 |
| forge_entrance   | 0  | 65 |
| stable_entrance  | 65 | 0  |
| stall_row_center | 104 | 55 |
| feed_bins        | 123 | 26  |
| saddle_racks     | 71 | 26  |
| corral_gate      | 146 | 55 |
| thorgrim_leanto  | 78 | 6  |
| forge_wall_marks | 32 | 91 |
| road_frontage    | 0  | 55 |

---

## Zones

| name         | render_z | vertices                              |
|--------------|----------|---------------------------------------|
| FORGE        | 6.5        | (0,58) (58,58) (58,113) (0,113)         |
| LEANTO       | 6.5        | (58,0) (97,0) (97,26) (58,26)           |
| STABLES      | 3.25        | (58,0) (146,0) (146,113) (58,113)         |
| CORRAL       | 3.25        | (146,16) (211,16) (211,97) (146,97)         |
| EXTERIOR     | 0.0        | (-16,-16) (227,-16) (227,130) (-16,130)       |

---

## Impassable

| description     | vertices                              |
|-----------------|---------------------------------------|
| Forge back wall | (0,107) (58,107) (58,113) (0,113)         |
| Stall partitions | (58,32) (146,32) (146,39) (58,39)      |
| Corral fence    | (146,16) (211,16) (211,22) (146,22)           |

---

## Connections

| name              | x    | y    | destination          |
|-------------------|------|------|----------------------|
| forge_to_street   | 0  | 65 | places/driftmoor     |
| stable_to_street  | 65 | 0  | places/driftmoor     |
| corral_gate       | 211 | 55 | places/driftmoor     |
| road_stonehearth  | 97 | -16 | places/plains_of_stonehearth |

---

## Boundaries

### Forge Heat Zone

- **type:** conditional
- **blocks:** none
- **effect:** within 9.75m of hearth — extreme heat; unprotected characters risk exhaustion after prolonged exposure
- **vertices:** (0,71) (32,71) (32,113) (0,113)

---
