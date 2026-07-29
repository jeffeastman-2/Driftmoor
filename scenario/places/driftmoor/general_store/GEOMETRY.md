# GEOMETRY.md — The General Store

## Scene

- **name:** The General Store
- **place_path:** places/driftmoor/general_store
- **z_level:** 16.25
- **width:** 22.75
- **height:** 29.25
- **origin:** 235, 82.5, 0

Notes: Stone-and-wood building in the south quarter. Origin at
southwest corner. Shop in front, garden behind (north). Counter
at the back of the shop area.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 11  | 0  |
| counter         | 11  | 11  |
| tool_shelves    | 3  | 6.5  |
| rope_rack       | 19.5 | 6.5  |
| candle_shelf    | 3  | 9.5  |
| back_door       | 11  | 14.5  |
| garden_center   | 11  | 22.5 |
| garden_gate     | 11  | 14.5  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| SHOP       | 3.25        | (0,0) (22.5,0) (22.5,14.5) (0,14.5)       |
| GARDEN     | 3.25        | (3,14.5) (19.5,14.5) (19.5,29) (3,29)     |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (27.5,-4.5) (27.5,34) (-4.5,34)  |

---

## Impassable

| description  | vertices                        |
|--------------|---------------------------------|
| Back wall    | (0,13) (22.5,13) (22.5,14.5) (0,14.5)       |
| Garden fence | (3,27.5) (19.5,27.5) (19.5,29) (3,29)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 11 | 0 | places/driftmoor |
