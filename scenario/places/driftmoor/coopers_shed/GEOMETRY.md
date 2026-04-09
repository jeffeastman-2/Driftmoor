# GEOMETRY.md — The Cooper's Shed

## Scene

- **name:** The Cooper's Shed
- **place_path:** places/driftmoor/coopers_shed
- **z_level:** 5.0
- **width:** 14.0
- **height:** 10.0
- **origin:** 2773.0, 2649.0, 5.0

Notes: Utilitarian structure near the harbor. Origin at southwest
corner. Open workspace with barrel-making tools. Yard with wooden
staves and iron hoops. Small toys near entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 7.0  | 0.0  |
| main_workspace  | 7.0  | 5.0  |
| stave_pile      | 12.0 | 7.0  |
| hoop_rack       | 2.0  | 7.0  |
| toy_shelf       | 3.0  | 1.0  |
| yard_area       | 7.0  | -2.0 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 1        | (0,0) (14,0) (14,10) (0,10)   |
| YARD       | 0        | (2,-4) (12,-4) (12,0) (2,0)   |
| EXTERIOR   | 0        | (-3,-6) (17,-6) (17,13) (-3,13) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,9) (14,9) (14,10) (0,10)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 7.0 | 0.0 | places/driftmoor |
