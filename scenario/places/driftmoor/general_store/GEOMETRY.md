# GEOMETRY.md — The General Store

## Scene

- **name:** The General Store
- **place_path:** places/driftmoor/general_store
- **z_level:** 16.25
- **width:** 45.5
- **height:** 58.5
- **origin:** 8979.75, 8040.5, 16.25

Notes: Stone-and-wood building in the south quarter. Origin at
southwest corner. Shop in front, garden behind (north). Counter
at the back of the shop area.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 22  | 0  |
| counter         | 22  | 22  |
| tool_shelves    | 6  | 13  |
| rope_rack       | 39 | 13  |
| candle_shelf    | 6  | 19  |
| back_door       | 22  | 29  |
| garden_center   | 22  | 45 |
| garden_gate     | 22  | 29  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| SHOP       | 3.25        | (0,0) (45,0) (45,29) (0,29)       |
| GARDEN     | 3.25        | (6,29) (39,29) (39,58) (6,58)     |
| EXTERIOR   | 0.0        | (-9,-9) (55,-9) (55,68) (-9,68)  |

---

## Impassable

| description  | vertices                        |
|--------------|---------------------------------|
| Back wall    | (0,26) (45,26) (45,29) (0,29)       |
| Garden fence | (6,55) (39,55) (39,58) (6,58)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22 | 0 | places/driftmoor |
