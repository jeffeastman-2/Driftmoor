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
| main_entrance   | 35 | 0  |
| great_table     | 35 | 16  |
| hearth          | 6  | 16  |
| notice_board    | 9  | 3  |
| office_door     | 52 | 22  |
| mayor_desk      | 58 | 32 |
| records_door    | 26  | 32 |
| filing_shelves  | 16  | 45 |
| staircase       | 65 | 45 |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| LIVING_QUARTERS | 9.75        | (32,39) (71,39) (71,65) (32,65) |
| RECORDS_ROOM    | 6.5        | (0,32) (32,32) (32,65) (0,65)   |
| OFFICE          | 6.5        | (45,22) (71,22) (71,39) (45,39)   |
| MAIN_HALL       | 3.25        | (0,0) (71,0) (71,32) (0,32)     |
| EXTERIOR        | 0.0        | (-9,-9) (81,-9) (81,74) (-9,74)  |

---

## Impassable

| description        | vertices                        |
|--------------------|---------------------------------|
| Hall back wall     | (0,32) (71,32) (71,35) (0,35)    |
| Office divider     | (45,22) (45,39) (48,39) (48,22)    |

---

## Connections

| name           | x    | y   | destination      |
|----------------|------|-----|------------------|
| main_entrance  | 35 | 0 | places/driftmoor |

---

## Boundaries

### Records Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** locked door; town records and correspondence; requires mayor's permission
- **vertices:** (0,32) (32,32) (32,65) (0,65)
