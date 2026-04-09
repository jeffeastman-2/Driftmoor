# GEOMETRY.md — The Mayor's Hall

## Scene

- **name:** The Mayor's Hall
- **place_path:** places/driftmoor/mayors_hall
- **z_level:** 5.0
- **width:** 22.0
- **height:** 20.0
- **origin:** 3009.0, 2680.0, 5.0

Notes: Largest building in Driftmoor. Two stories. Origin at
southwest corner. Main hall (public) in front, mayor's office
to the east, records room behind, living quarters upstairs.
Stone construction, iron-banded door.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| main_entrance   | 11.0 | 0.0  |
| great_table     | 11.0 | 5.0  |
| hearth          | 2.0  | 5.0  |
| notice_board    | 3.0  | 1.0  |
| office_door     | 16.0 | 7.0  |
| mayor_desk      | 18.0 | 10.0 |
| records_door    | 8.0  | 10.0 |
| filing_shelves  | 5.0  | 14.0 |
| staircase       | 20.0 | 14.0 |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| LIVING_QUARTERS | 3        | (10,12) (22,12) (22,20) (10,20) |
| RECORDS_ROOM    | 2        | (0,10) (10,10) (10,20) (0,20)   |
| OFFICE          | 2        | (14,7) (22,7) (22,12) (14,12)   |
| MAIN_HALL       | 1        | (0,0) (22,0) (22,10) (0,10)     |
| EXTERIOR        | 0        | (-3,-3) (25,-3) (25,23) (-3,23)  |

---

## Impassable

| description        | vertices                        |
|--------------------|---------------------------------|
| Hall back wall     | (0,10) (22,10) (22,11) (0,11)    |
| Office divider     | (14,7) (14,12) (15,12) (15,7)    |

---

## Connections

| name           | x    | y   | destination      |
|----------------|------|-----|------------------|
| main_entrance  | 11.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Records Room — Restricted

- **type:** conditional
- **blocks:** all
- **effect:** locked door; town records and correspondence; requires mayor's permission
- **vertices:** (0,10) (10,10) (10,20) (0,20)
