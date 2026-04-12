# GEOMETRY.md — The Old Mill

## Scene

- **name:** The Old Mill
- **place_path:** places/greywater_river/old_mill
- **z_level:** 13.0
- **width:** 195.0
- **height:** 162.5
- **origin:** 17452.5, 13893.75, 13.0

Notes: A large two-story stone building on the Greywater River.
Origin at southwest corner of the mill yard. The mill building
occupies the northeast, with the waterwheel on the north (river)
side. The yard to the south and west is where farmers unload grain.
Willows line the riverbank. Fields stretch in every direction.

---

## Landmarks

| name              | x    | y    |
|-------------------|------|------|
| mill_entrance     | 113.75 | 65.0 |
| waterwheel        | 146.25 | 146.25 |
| grinding_stones   | 130.0 | 97.5 |
| grain_yard        | 65.0 | 48.75 |
| loading_dock      | 97.5 | 32.5 |
| willow_bank       | 162.5 | 156.0 |
| field_path_south  | 97.5 | 0.0  |
| field_path_east   | 188.5 | 81.25 |
| staircase         | 156.0 | 91.0 |
| ivy_wall          | 178.75 | 113.75 |

---

## Zones

| name           | render_z | vertices                              |
|----------------|----------|---------------------------------------|
| UPPER_FLOOR    | 9.75        | (97.5,71.5) (178.75,71.5) (178.75,136.5) (97.5,136.5)       |
| MILL_INTERIOR  | 6.5        | (97.5,71.5) (178.75,71.5) (178.75,136.5) (97.5,136.5)       |
| MILL_YARD      | 3.25        | (16.25,16.25) (178.75,16.25) (178.75,71.5) (16.25,71.5)           |
| RIVERBANK      | 3.25        | (16.25,136.5) (178.75,136.5) (178.75,162.5) (16.25,162.5)         |
| FIELDS         | 0.0        | (0.0,0.0) (195.0,0.0) (195.0,162.5) (0.0,162.5)           |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Mill south wall   | (97.5,65.0) (178.75,65.0) (178.75,71.5) (97.5,71.5)       |
| Mill north wall   | (97.5,136.5) (178.75,136.5) (178.75,143.0) (97.5,143.0)       |
| River             | (0.0,149.5) (195.0,149.5) (195.0,162.5) (0.0,162.5)         |

---

## Connections

| name               | x    | y    | destination                               |
|--------------------|------|------|-------------------------------------------|
| field_path_south   | 97.5 | 0.0  | places/greywater_river                    |
| field_path_east    | 188.5 | 81.25 | places/greywater_river                    |
| to_ground_floor    | 113.75 | 71.5 | places/greywater_river/old_mill/ground_floor |
| to_upper_floor     | 156.0 | 91.0 | places/greywater_river/old_mill/upper_floor  |

---

## Starting Positions

| character | x    | y    | zone          |
|-----------|------|------|---------------|
| lilar     | 65.0 | 48.75 | MILL_YARD     |
| gregan    | 130.0 | 97.5 | MILL_INTERIOR |
| tessa     | 156.0 | 91.0 | MILL_INTERIOR |
