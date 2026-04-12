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
| front_door      | 19.5  | 0.0  |
| mannequin_3.25     | 9.75  | 6.5  |
| mannequin_6.5     | 29.25  | 6.5  |
| cutting_table   | 19.5  | 22.75  |
| fabric_bolts    | 35.75 | 26.0  |
| sewing_station  | 6.5  | 22.75  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 6.5        | (0.0,16.25) (39.0,16.25) (39.0,32.5) (0.0,32.5)   |
| DISPLAY    | 3.25        | (0.0,0.0) (39.0,0.0) (39.0,16.25) (0.0,16.25)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (48.75,-9.75) (48.75,42.25) (-9.75,42.25) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0.0,29.25) (39.0,29.25) (39.0,32.5) (0.0,32.5)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 19.5 | 0.0 | places/driftmoor |
