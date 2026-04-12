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
| front_door      | 22.75  | 0.0  |
| teacher_desk    | 22.75  | 26.0  |
| chalkboard      | 22.75  | 29.25  |
| student_desks   | 22.75  | 13.0  |
| bell_rope       | 39.0 | 26.0  |
| bookshelf       | 3.25  | 26.0  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| CLASSROOM  | 3.25        | (0.0,0.0) (45.5,0.0) (45.5,32.5) (0.0,32.5)     |
| EXTERIOR   | 0.0        | (-9.75,-9.75) (55.25,-9.75) (55.25,42.25) (-9.75,42.25)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0.0,29.25) (45.5,29.25) (45.5,32.5) (0.0,32.5)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 22.75 | 0.0 | places/driftmoor |
