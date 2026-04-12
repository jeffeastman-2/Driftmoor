# GEOMETRY.md — The Cooper's Shed

## Scene

- **name:** The Cooper's Shed
- **place_path:** places/driftmoor/coopers_shed
- **z_level:** 16.25
- **width:** 45.5
- **height:** 32.5
- **origin:** 9012.25, 8609.25, 16.25

Notes: Utilitarian structure near the harbor. Origin at southwest
corner. Open workspace with barrel-making tools. Yard with wooden
staves and iron hoops. Small toys near entrance.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 22.75  | 0.0  |
| main_workspace  | 22.75  | 16.25  |
| stave_pile      | 39.0 | 22.75  |
| hoop_rack       | 6.5  | 22.75  |
| toy_shelf       | 9.75  | 3.25  |
| yard_area       | 22.75  | -6.5 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 3.25        | (0.0,0.0) (45.5,0.0) (45.5,32.5) (0.0,32.5)   |
| YARD       | 0.0        | (6.5,-13.0) (39.0,-13.0) (39.0,0.0) (6.5,0.0)   |
| EXTERIOR   | 0.0        | (-9.75,-19.5) (55.25,-19.5) (55.25,42.25) (-9.75,42.25) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0.0,29.25) (45.5,29.25) (45.5,32.5) (0.0,32.5)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22.75 | 0.0 | places/driftmoor |
