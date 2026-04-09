# GEOMETRY.md — The Bakery

## Scene

- **name:** The Bakery
- **place_path:** places/driftmoor/bakery
- **z_level:** 5.0
- **width:** 12.0
- **height:** 10.0
- **origin:** 2804.0, 2570.0, 5.0

Notes: A warm single-storey building on the south row. Origin at
southwest corner. Front counter faces south toward the street.
Ovens and workspace behind. Chimney on the north wall.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 6.0  | 0.0  |
| front_counter   | 6.0  | 3.0  |
| ovens           | 3.0  | 8.0  |
| workspace       | 9.0  | 7.0  |
| chimney         | 6.0  | 10.0 |
| display_shelves | 3.0  | 3.0  |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| KITCHEN    | 2        | (0,5) (12,5) (12,10) (0,10) |
| SHOPFRONT  | 1        | (0,0) (12,0) (12,5) (0,5)   |
| EXTERIOR   | 0        | (-3,-3) (15,-3) (15,13) (-3,13) |

---

## Impassable

| description   | vertices                    |
|---------------|-----------------------------|
| Oven wall     | (0,7) (6,7) (6,10) (0,10)   |
| Back wall     | (0,9) (12,9) (12,10) (0,10) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 6.0 | 0.0 | places/driftmoor |
