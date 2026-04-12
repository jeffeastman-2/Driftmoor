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
| front_door      | 22.75  | 0.0  |
| counter         | 22.75  | 22.75  |
| tool_shelves    | 6.5  | 13.0  |
| rope_rack       | 39.0 | 13.0  |
| candle_shelf    | 6.5  | 19.5  |
| back_door       | 22.75  | 29.25  |
| garden_center   | 22.75  | 45.5 |
| garden_gate     | 22.75  | 29.25  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| SHOP       | 3.25        | (0.0,0.0) (45.5,0.0) (45.5,29.25) (0.0,29.25)       |
| GARDEN     | 3.25        | (6.5,29.25) (39.0,29.25) (39.0,58.5) (6.5,58.5)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (55.25,-9.75) (55.25,68.25) (-9.75,68.25)  |

---

## Impassable

| description  | vertices                        |
|--------------|---------------------------------|
| Back wall    | (0.0,26.0) (45.5,26.0) (45.5,29.25) (0.0,29.25)       |
| Garden fence | (6.5,55.25) (39.0,55.25) (39.0,58.5) (6.5,58.5)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22.75 | 0.0 | places/driftmoor |
