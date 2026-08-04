# GEOMETRY.md — The Mayor's Hall

## Scene

- **name:** The Mayor's Hall
- **place_path:** places/driftmoor/mayors_hall
- **z_level:** 16.25
- **width:** 35.75
- **height:** 32.5
- **origin:** 655, 423, 0

Notes: Largest building in Driftmoor. Two stories. Origin at
southwest corner. Main hall (public) in front, mayor's office
to the east, records room behind, living quarters upstairs.
Stone construction, iron-banded door.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| main_entrance   | 17.5 | 0  |
| great_table     | 17.5 | 8  |
| hearth          | 3  | 8  |
| notice_board    | 4.5  | 1.5  |
| office_door     | 26 | 11  |
| mayor_desk      | 29 | 16 |
| records_door    | 13  | 16 |
| filing_shelves  | 8  | 22.5 |
| staircase       | 32.5 | 22.5 |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| LIVING_QUARTERS | 9.75        | (16,19.5) (35.5,19.5) (35.5,32.5) (16,32.5) |
| RECORDS_ROOM    | 6.5        | (0,16) (16,16) (16,32.5) (0,32.5)   |
| OFFICE          | 6.5        | (22.5,11) (35.5,11) (35.5,19.5) (22.5,19.5)   |
| MAIN_HALL       | 3.25        | (0,0) (35.5,0) (35.5,16) (0,16)     |
| EXTERIOR        | 0.0        | (-4.5,-4.5) (40.5,-4.5) (40.5,37) (-4.5,37)  |

---

## Impassable

| description        | vertices                        |
|--------------------|---------------------------------|
| Hall back wall west | (0,16) (11.5,16) (11.5,17.5) (0,17.5) |
| Hall back wall center | (14.5,16) (30.5,16) (30.5,17.5) (14.5,17.5) |
| Hall back wall east | (34.5,16) (35.5,16) (35.5,17.5) (34.5,17.5) |
| Office divider     | (22.5,11) (22.5,19.5) (24,19.5) (24,11)    |

---

## Connections

| name           | x    | y   | destination      |
|----------------|------|-----|------------------|
| main_entrance  | 17.5 | 0 | places/driftmoor |

---

## Boundaries

### Records Room — Restricted

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** locked door; town records and correspondence; requires mayor's permission
- **vertices:** (0,16) (16,16) (16,32.5) (0,32.5)
