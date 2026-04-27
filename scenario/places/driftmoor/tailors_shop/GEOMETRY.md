# GEOMETRY.md — The Tailor's Shop

## Scene

- **name:** The Tailor's Shop
- **place_path:** places/driftmoor/tailors_shop
- **z_level:** 16.25
- **width:** 39.0
- **height:** 32.5
- **origin:** 9259.25, 8723.0, 16.25

Notes: Tidy shop with mannequins and fabric. Origin at southwest
corner. Display area with mannequins in front, sewing workspace
in the back with bolts of cloth and a cutting table.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 19  | 0  |
| mannequin_3.25     | 9  | 6  |
| mannequin_6.5     | 29  | 6  |
| cutting_table   | 19  | 22  |
| fabric_bolts    | 35 | 26  |
| sewing_station  | 6  | 22  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 6.5        | (0,16) (39,16) (39,32) (0,32)   |
| DISPLAY    | 3.25        | (0,0) (39,0) (39,16) (0,16)     |
| EXTERIOR   | 0.0        | (-9,-9) (48,-9) (48,42) (-9,42) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,29) (39,29) (39,32) (0,32)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19 | 0 | places/driftmoor |
