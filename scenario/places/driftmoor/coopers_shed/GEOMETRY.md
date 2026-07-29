# GEOMETRY.md — The Cooper's Shed

## Scene

- **name:** The Cooper's Shed
- **place_path:** places/driftmoor/coopers_shed
- **z_level:** 16.25
- **width:** 22.75
- **height:** 16.25
- **origin:** 265, 388, 0

Notes: Utilitarian structure near the harbor. Origin at southwest
corner. Open workspace with barrel-making tools. Yard with wooden
staves and iron hoops. Small toys near entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 11  | 0  |
| main_workspace  | 11  | 8  |
| stave_pile      | 19.5 | 11  |
| hoop_rack       | 3  | 11  |
| toy_shelf       | 4.5  | 1.5  |
| yard_area       | 11  | -3 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 3.25        | (0,0) (22.5,0) (22.5,16) (0,16)   |
| YARD       | 0.0        | (3,-6.5) (19.5,-6.5) (19.5,0) (3,0)   |
| EXTERIOR   | 0.0        | (-4.5,-9.5) (27.5,-9.5) (27.5,21) (-4.5,21) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,14.5) (22.5,14.5) (22.5,16) (0,16)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 11 | 0 | places/driftmoor |
