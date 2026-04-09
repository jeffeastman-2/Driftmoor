# GEOMETRY.md — The Tailor's Shop

## Scene

- **name:** The Tailor's Shop
- **place_path:** places/driftmoor/tailors_shop
- **z_level:** 5.0
- **width:** 12.0
- **height:** 10.0
- **origin:** 2849.0, 2684.0, 5.0

Notes: Tidy shop with mannequins and fabric. Origin at southwest
corner. Display area with mannequins in front, sewing workspace
in the back with bolts of cloth and a cutting table.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 6.0  | 0.0  |
| mannequin_1     | 3.0  | 2.0  |
| mannequin_2     | 9.0  | 2.0  |
| cutting_table   | 6.0  | 7.0  |
| fabric_bolts    | 11.0 | 8.0  |
| sewing_station  | 2.0  | 7.0  |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 2        | (0,5) (12,5) (12,10) (0,10)   |
| DISPLAY    | 1        | (0,0) (12,0) (12,5) (0,5)     |
| EXTERIOR   | 0        | (-3,-3) (15,-3) (15,13) (-3,13) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,9) (12,9) (12,10) (0,10)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 6.0 | 0.0 | places/driftmoor |
