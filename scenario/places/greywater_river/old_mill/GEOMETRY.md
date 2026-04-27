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
| mill_entrance     | 113 | 65 |
| waterwheel        | 146 | 146 |
| grinding_stones   | 130 | 97 |
| grain_yard        | 65 | 48 |
| loading_dock      | 97 | 32 |
| willow_bank       | 162 | 156 |
| field_path_south  | 97 | 0  |
| field_path_east   | 188 | 81 |
| staircase         | 156 | 91 |
| ivy_wall          | 178 | 113 |

---

## Zones

| name           | render_z | vertices                              |
|----------------|----------|---------------------------------------|
| UPPER_FLOOR    | 9.75        | (97,71) (178,71) (178,136) (97,136)       |
| MILL_INTERIOR  | 6.5        | (97,71) (178,71) (178,136) (97,136)       |
| MILL_YARD      | 3.25        | (16,16) (178,16) (178,71) (16,71)           |
| RIVERBANK      | 3.25        | (16,136) (178,136) (178,162) (16,162)         |
| FIELDS         | 0.0        | (0,0) (195,0) (195,162) (0,162)           |

---

## Impassable

| description       | vertices                              |
|-------------------|---------------------------------------|
| Mill south wall   | (97,65) (178,65) (178,71) (97,71)       |
| Mill north wall   | (97,136) (178,136) (178,143) (97,143)       |
| River             | (0,149) (195,149) (195,162) (0,162)         |

---

## Connections

| name               | x    | y    | destination                               |
|--------------------|------|------|-------------------------------------------|
| field_path_south   | 97 | 0  | places/greywater_river                    |
| field_path_east    | 188 | 81 | places/greywater_river                    |
| to_ground_floor    | 113 | 71 | places/greywater_river/old_mill/ground_floor |
| to_upper_floor     | 156 | 91 | places/greywater_river/old_mill/upper_floor  |

---

## Starting Positions

| character | x    | y    | zone          |
|-----------|------|------|---------------|
| lilar     | 65 | 48 | MILL_YARD     |
| gregan    | 130 | 97 | MILL_INTERIOR |
| tessa     | 156 | 91 | MILL_INTERIOR |
