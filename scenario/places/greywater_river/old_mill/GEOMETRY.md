# GEOMETRY.md — The Old Mill

## Scene

- **name:** The Old Mill
- **place_path:** places/greywater_river/old_mill
- **z_level:** 4.0
- **width:** 60.0
- **height:** 50.0
- **origin:** 5370.0, 4275.0, 4.0

Notes: A large two-story stone building on the Greywater River.
Origin at southwest corner of the mill yard. The mill building
occupies the northeast, with the waterwheel on the north (river)
side. The yard to the south and west is where farmers unload grain.
Willows line the riverbank. Fields stretch in every direction.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| mill_entrance     | 35.0 | 20.0 |
| waterwheel        | 45.0 | 45.0 |
| grinding_stones   | 40.0 | 30.0 |
| grain_yard        | 20.0 | 15.0 |
| loading_dock      | 30.0 | 10.0 |
| willow_bank       | 50.0 | 48.0 |
| field_path_south  | 30.0 | 0.0  |
| field_path_east   | 58.0 | 25.0 |
| staircase         | 48.0 | 28.0 |
| ivy_wall          | 55.0 | 35.0 |

---

## Zones

| name           | render_z | vertices                              |
|----------------|----------|---------------------------------------|
| UPPER_FLOOR    | 3        | (30,22) (55,22) (55,42) (30,42)       |
| MILL_INTERIOR  | 2        | (30,22) (55,22) (55,42) (30,42)       |
| MILL_YARD      | 1        | (5,5) (55,5) (55,22) (5,22)           |
| RIVERBANK      | 1        | (5,42) (55,42) (55,50) (5,50)         |
| FIELDS         | 0        | (0,0) (60,0) (60,50) (0,50)           |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Mill south wall   | (30,20) (55,20) (55,22) (30,22)       |
| Mill north wall   | (30,42) (55,42) (55,44) (30,44)       |
| River             | (0,46) (60,46) (60,50) (0,50)         |

---

## Connections

| name               | x    | y    | destination                               |
|--------------------|------|------|-------------------------------------------|
| field_path_south   | 30.0 | 0.0  | places/greywater_river                    |
| field_path_east    | 58.0 | 25.0 | places/greywater_river                    |
| to_ground_floor    | 35.0 | 22.0 | places/greywater_river/old_mill/ground_floor |
| to_upper_floor     | 48.0 | 28.0 | places/greywater_river/old_mill/upper_floor  |

---

## Starting Positions

| character | x    | y    | zone          |
|-----------|------|------|---------------|
| lilar     | 20.0 | 15.0 | MILL_YARD     |
| gregan    | 40.0 | 30.0 | MILL_INTERIOR |
| tessa     | 48.0 | 28.0 | MILL_INTERIOR |
