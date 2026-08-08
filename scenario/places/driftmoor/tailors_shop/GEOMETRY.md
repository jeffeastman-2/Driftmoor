# GEOMETRY.md — The Tailor's Shop

## Scene

- **name:** The Tailor's Shop
- **place_path:** places/driftmoor/tailors_shop
- **z_level:** 16.25
- **width:** 19.5
- **height:** 16.25
- **origin:** 384, 447, 0

Notes: Tidy shop with mannequins and fabric. Origin at southwest
corner. Display area with mannequins in front, sewing workspace
in the back with bolts of cloth and a cutting table.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 9.5  | 0  |
| mannequin_3.25     | 4.5  | 3  |
| mannequin_6.5     | 14.5  | 3  |
| cutting_table   | 10.043  | 8.707  |
| fabric_bolts    | 17.302 | 13.241  |
| sewing_station  | 1.854  | 11.965  |
| workspace_door  | 9.5  | 8  |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|-------------------------------|
| WORKSPACE | 6.5 |  | (0,8) (19.5,8) (19.5,16) (0,16) |
| DISPLAY | 3.25 |  | (0,0) (19.5,0) (19.5,8) (0,8) |
| EXTERIOR | 0.0 |  | (-4.5,-4.5) (24,-4.5) (24,21) (-4.5,21) |
---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,14.5) (19.5,14.5) (19.5,16) (0,16)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 9.5 | 0 | places/driftmoor |
