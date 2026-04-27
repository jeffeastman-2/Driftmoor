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
| front_door      | 22  | 0  |
| main_workspace  | 22  | 16  |
| stave_pile      | 39 | 22  |
| hoop_rack       | 6  | 22  |
| toy_shelf       | 9  | 3  |
| yard_area       | 22  | -6 |

---

## Zones

| name       | render_z | vertices                      |
|------------|----------|-------------------------------|
| WORKSPACE  | 3.25        | (0,0) (45,0) (45,32) (0,32)   |
| YARD       | 0.0        | (6,-13) (39,-13) (39,0) (6,0)   |
| EXTERIOR   | 0.0        | (-9,-19) (55,-19) (55,42) (-9,42) |

---

## Impassable

| description | vertices                      |
|-------------|-------------------------------|
| Back wall   | (0,29) (45,29) (45,32) (0,32)   |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22 | 0 | places/driftmoor |
