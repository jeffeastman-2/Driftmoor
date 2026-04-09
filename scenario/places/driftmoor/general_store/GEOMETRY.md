# GEOMETRY.md — The General Store

## Scene

- **name:** The General Store
- **place_path:** places/driftmoor/general_store
- **z_level:** 5.0
- **width:** 14.0
- **height:** 18.0
- **origin:** 2763.0, 2474.0, 5.0

Notes: Stone-and-wood building in the south quarter. Origin at
southwest corner. Shop in front, garden behind (north). Counter
at the back of the shop area.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 7.0  | 0.0  |
| counter         | 7.0  | 7.0  |
| tool_shelves    | 2.0  | 4.0  |
| rope_rack       | 12.0 | 4.0  |
| candle_shelf    | 2.0  | 6.0  |
| back_door       | 7.0  | 9.0  |
| garden_center   | 7.0  | 14.0 |
| garden_gate     | 7.0  | 9.0  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| SHOP       | 1        | (0,0) (14,0) (14,9) (0,9)       |
| GARDEN     | 1        | (2,9) (12,9) (12,18) (2,18)     |
| EXTERIOR   | 0        | (-3,-3) (17,-3) (17,21) (-3,21)  |

---

## Impassable

| description  | vertices                        |
|--------------|---------------------------------|
| Back wall    | (0,8) (14,8) (14,9) (0,9)       |
| Garden fence | (2,17) (12,17) (12,18) (2,18)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 7.0 | 0.0 | places/driftmoor |
