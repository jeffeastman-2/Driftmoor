# GEOMETRY.md — The Schoolhouse

## Scene

- **name:** The Schoolhouse
- **place_path:** places/driftmoor/schoolhouse
- **z_level:** 5.0
- **width:** 14.0
- **height:** 10.0
- **origin:** 3013.0, 2624.0, 5.0

Notes: One-room building with bell on the roof. Origin at southwest
corner. Rows of desks facing a chalkboard on the north wall.
Teacher's desk at front. Door faces south. Yard behind for recess.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 7.0  | 0.0  |
| teacher_desk    | 7.0  | 8.0  |
| chalkboard      | 7.0  | 9.0  |
| student_desks   | 7.0  | 4.0  |
| bell_rope       | 12.0 | 8.0  |
| bookshelf       | 1.0  | 8.0  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| CLASSROOM  | 1        | (0,0) (14,0) (14,10) (0,10)     |
| EXTERIOR   | 0        | (-3,-3) (17,-3) (17,13) (-3,13)  |

---

## Impassable

| description | vertices                        |
|-------------|---------------------------------|
| Back wall   | (0,9) (14,9) (14,10) (0,10)     |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_door | 7.0 | 0.0 | places/driftmoor |
