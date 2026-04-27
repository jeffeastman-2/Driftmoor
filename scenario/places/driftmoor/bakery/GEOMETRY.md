# GEOMETRY.md — The Bakery

## Scene

- **name:** The Bakery
- **place_path:** places/driftmoor/bakery
- **z_level:** 16.25
- **width:** 39.0
- **height:** 32.5
- **origin:** 9113.0, 8352.5, 16.25

Notes: A warm single-storey building on the south row. Origin at
southwest corner. Front counter faces south toward the street.
Ovens and workspace behind. Chimney on the north wall.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 19  | 0  |
| front_counter   | 19  | 9  |
| ovens           | 9  | 26  |
| workspace       | 29  | 22  |
| chimney         | 19  | 32 |
| display_shelves | 9  | 9  |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| KITCHEN    | 6.5        | (0,16) (39,16) (39,32) (0,32) |
| SHOPFRONT  | 3.25        | (0,0) (39,0) (39,16) (0,16)   |
| EXTERIOR   | 0.0        | (-9,-9) (48,-9) (48,42) (-9,42) |

---

## Impassable

| description   | vertices                    |
|---------------|-----------------------------|
| Oven wall     | (0,22) (19,22) (19,32) (0,32)   |
| Back wall     | (0,29) (39,29) (39,32) (0,32) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19 | 0 | places/driftmoor |
