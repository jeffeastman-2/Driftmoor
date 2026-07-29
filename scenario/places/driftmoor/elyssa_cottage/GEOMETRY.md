# GEOMETRY.md — Elyssa Moonglow's Cottage

## Scene

- **name:** Elyssa's Cottage
- **place_path:** places/driftmoor/elyssa_cottage
- **z_level:** 19.5
- **width:** 29.25
- **height:** 22.75
- **origin:** 688, 227, 3.25

Notes: Stone building with slate roof on a low hill overlooking the
Greywater River. Origin at southwest corner. Study (main room) in
front, laboratory side room to the east, small bedroom in the back.
Herb garden on the west side. Ivy on walls.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_path      | 9.5  | 0  |
| study_desk      | 8  | 8  |
| bookshelves     | 3  | 9.5  |
| fireplace       | 1.5  | 4.5  |
| lab_door        | 16 | 9.5  |
| lab_table       | 22.5 | 8  |
| obelisk_notes   | 22.5 | 13  |
| bedroom_door    | 8  | 14.5  |
| herb_garden     | -3 | 11  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LABORATORY | 6.5        | (16,4.5) (29,4.5) (29,16) (16,16)    |
| BEDROOM    | 6.5        | (0,14.5) (16,14.5) (16,22.5) (0,22.5)      |
| STUDY      | 3.25        | (0,0) (16,0) (16,14.5) (0,14.5)        |
| HERB_GARDEN| 3.25        | (-6.5,6.5) (0,6.5) (0,16) (-6.5,16)      |
| EXTERIOR   | 0.0        | (-9.5,-4.5) (34,-4.5) (34,27.5) (-9.5,27.5)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Lab wall       | (16,4.5) (16,16) (17.5,16) (17.5,4.5)    |
| Bedroom wall   | (0,14.5) (16,14.5) (16,16) (0,16)      |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_path | 9.5 | 0 | places/driftmoor |

---

## Boundaries

### Laboratory — Restricted Research

- **type:** conditional
- **blocks:** all
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (16,4.5) (29,4.5) (29,16) (16,16)
