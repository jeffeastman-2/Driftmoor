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
| front_door      | 19.5  | 0.0  |
| front_counter   | 19.5  | 9.75  |
| ovens           | 9.75  | 26.0  |
| workspace       | 29.25  | 22.75  |
| chimney         | 19.5  | 32.5 |
| display_shelves | 9.75  | 9.75  |

---

## Zones

| name       | render_z | vertices                    |
|------------|----------|-----------------------------|
| KITCHEN    | 6.5        | (0.0,16.25) (39.0,16.25) (39.0,32.5) (0.0,32.5) |
| SHOPFRONT  | 3.25        | (0.0,0.0) (39.0,0.0) (39.0,16.25) (0.0,16.25)   |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (48.75,-9.75) (48.75,42.25) (-9.75,42.25) |

---

## Impassable

| description   | vertices                    |
|---------------|-----------------------------|
| Oven wall     | (0.0,22.75) (19.5,22.75) (19.5,32.5) (0.0,32.5)   |
| Back wall     | (0.0,29.25) (39.0,29.25) (39.0,32.5) (0.0,32.5) |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19.5 | 0.0 | places/driftmoor |
