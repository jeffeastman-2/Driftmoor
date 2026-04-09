# GEOMETRY.md — Elyssa Moonglow's Cottage

## Scene

- **name:** Elyssa's Cottage
- **place_path:** places/driftmoor/elyssa_cottage
- **z_level:** 6.0
- **width:** 18.0
- **height:** 14.0
- **origin:** 3036.0, 2559.0, 6.0

Notes: Stone building with slate roof on a low hill overlooking the
Greywater River. Origin at southwest corner. Study (main room) in
front, laboratory side room to the east, small bedroom in the back.
Herb garden on the west side. Ivy on walls.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_path      | 6.0  | 0.0  |
| study_desk      | 5.0  | 5.0  |
| bookshelves     | 2.0  | 6.0  |
| fireplace       | 1.0  | 3.0  |
| lab_door        | 10.0 | 6.0  |
| lab_table       | 14.0 | 5.0  |
| obelisk_notes   | 14.0 | 8.0  |
| bedroom_door    | 5.0  | 9.0  |
| herb_garden     | -2.0 | 7.0  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LABORATORY | 2        | (10,3) (18,3) (18,10) (10,10)    |
| BEDROOM    | 2        | (0,9) (10,9) (10,14) (0,14)      |
| STUDY      | 1        | (0,0) (10,0) (10,9) (0,9)        |
| HERB_GARDEN| 1        | (-4,4) (0,4) (0,10) (-4,10)      |
| EXTERIOR   | 0        | (-6,-3) (21,-3) (21,17) (-6,17)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Lab wall       | (10,3) (10,10) (11,10) (11,3)    |
| Bedroom wall   | (0,9) (10,9) (10,10) (0,10)      |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_path | 6.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Laboratory — Restricted Research

- **type:** conditional
- **blocks:** all
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (10,3) (18,3) (18,10) (10,10)
