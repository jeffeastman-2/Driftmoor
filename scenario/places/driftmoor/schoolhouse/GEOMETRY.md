# GEOMETRY.md — The Schoolhouse

## Scene

- **name:** The Schoolhouse
- **place_path:** places/driftmoor/schoolhouse
- **z_level:** 16.25
- **width:** 45.5
- **height:** 32.5
- **origin:** 9792.25, 8528.0, 16.25

Notes: One-room building with bell on the roof. Origin at southwest
corner. Rows of desks facing a chalkboard on the north wall.
Teacher's desk at front. Door faces south. Yard behind for recess.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 22  | 0  |
| teacher_desk    | 22  | 26  |
| chalkboard      | 22  | 29  |
| student_desks   | 22  | 13  |
| bell_rope       | 39 | 26  |
| bookshelf       | 3  | 26  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| CLASSROOM  | 3.25        | (0,0) (45,0) (45,32) (0,32)     |
| EXTERIOR   | 0.0        | (-9,-9) (55,-9) (55,42) (-9,42)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,29) (45,29) (45,32) (0,32)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22 | 0 | places/driftmoor |
