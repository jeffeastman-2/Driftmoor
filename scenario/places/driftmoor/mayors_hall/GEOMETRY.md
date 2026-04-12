# GEOMETRY.md — The Mayor's Hall

## Scene

- **name:** The Mayor's Hall
- **place_path:** places/driftmoor/mayors_hall
- **z_level:** 16.25
- **width:** 71.5
- **height:** 65.0
- **origin:** 9779.25, 8710.0, 16.25

Notes: Largest building in Driftmoor. Two stories. Origin at
southwest corner. Main hall (public) in front, mayor's office
to the east, records room behind, living quarters upstairs.
Stone construction, iron-banded door.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| main_entrance   | 35.75 | 0.0  |
| great_table     | 35.75 | 16.25  |
| hearth          | 6.5  | 16.25  |
| notice_board    | 9.75  | 3.25  |
| office_door     | 52.0 | 22.75  |
| mayor_desk      | 58.5 | 32.5 |
| records_door    | 26.0  | 32.5 |
| filing_shelves  | 16.25  | 45.5 |
| staircase       | 65.0 | 45.5 |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| LIVING_QUARTERS | 9.75        | (32.5,39.0) (71.5,39.0) (71.5,65.0) (32.5,65.0) |
| RECORDS_ROOM    | 6.5        | (0.0,32.5) (32.5,32.5) (32.5,65.0) (0.0,65.0)   |
| OFFICE          | 6.5        | (45.5,22.75) (71.5,22.75) (71.5,39.0) (45.5,39.0)   |
| MAIN_HALL       | 3.25        | (0.0,0.0) (71.5,0.0) (71.5,32.5) (0.0,32.5)     |
| EXTERIOR        | 0.0        | (-9.75,-9.75) (81.25,-9.75) (81.25,74.75) (-9.75,74.75)  |

---

## Impassable

| description        | vertices                        |
|--------------------|---------------------------------|
| Hall back wall     | (0.0,32.5) (71.5,32.5) (71.5,35.75) (0.0,35.75)    |
| Office divider     | (45.5,22.75) (45.5,39.0) (48.75,39.0) (48.75,22.75)    |

---

## Connections

| name           | x    | y   | destination      |
|----------------|------|-----|------------------|
| main_entrance  | 35.75 | 0.0 | places/driftmoor |

---

## Boundaries

### Records Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** locked door; town records and correspondence; requires mayor's permission
- **vertices:** (0.0,32.5) (32.5,32.5) (32.5,65.0) (0.0,65.0)
