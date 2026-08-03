# GEOMETRY.md — The Bakery

## Scene

- **name:** The Bakery
- **place_path:** places/driftmoor/bakery
- **z_level:** 16.25
- **width:** 19.5
- **height:** 16.25
- **origin:** 313, 252, 0

Notes: A warm single-storey building on the south row. Origin at
southwest corner. Front counter faces south toward the street.
Ovens and workspace behind. Chimney on the north wall.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 9.5  | 0  |
| front_counter   | 9.5  | 5.129  |
| ovens           | 3.716  | 13.543  |
| workspace       | 7.139  | 9.914  |
| chimney         | 9.5  | 16 |
| display_shelves | 2.035  | 2.793  |
| bread_display   | 16.189 | 2.389  |
| flour_sacks     | 16.638   | 13.543   |
| cooling_rack    | 10.543   | 13.594   |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| KITCHEN    | 6.5        | (0,8) (19.5,8) (19.5,16) (0,16) |
| SHOPFRONT  | 3.25        | (0,0) (19.5,0) (19.5,8) (0,8)   |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (24,-4.5) (24,21) (-4.5,21) |

---

## Impassable

| description   | vertices                    |
|---------------|-----------------------------|
| Oven wall     | (0,11) (9.5,11) (9.5,16) (0,16)   |
| Back wall     | (9.5,14.5) (19.5,14.5) (19.5,16) (9.5,16) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 9.5 | 0 | places/driftmoor |
