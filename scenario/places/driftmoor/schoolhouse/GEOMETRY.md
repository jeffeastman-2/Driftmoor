# GEOMETRY.md — The Schoolhouse

## Scene

- **name:** The Schoolhouse
- **place_path:** places/driftmoor/schoolhouse
- **z_level:** 16.25
- **width:** 22.75
- **height:** 16.25
- **origin:** 642.5, 343.5, 0

Notes: One-room building with bell on the roof. Origin at southwest
corner. Rows of desks facing a chalkboard on the north wall.
Teacher's desk at front. Door faces south. Yard behind for recess.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 11  | 0  |
| teacher_desk    | 11.073  | 9.719  |
| chalkboard      | 11  | 14.5  |
| student_desks   | 11.073  | 4.677  |
| bell_rope       | 21.396 | 13.219  |
| bookshelf       | 1.646  | 12.198  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| CLASSROOM  | 3.25        | (0,0) (22.5,0) (22.5,16) (0,16)     |
| EXTERIOR   | 0.0        | (-4.5,-4.5) (27.5,-4.5) (27.5,21) (-4.5,21)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,14.5) (22.5,14.5) (22.5,16) (0,16)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 11 | 0 | places/driftmoor |
