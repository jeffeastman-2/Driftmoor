# GEOMETRY.md — Elyssa Moonglow's Cottage

## Scene

- **name:** Elyssa's Cottage
- **place_path:** places/driftmoor/elyssa_cottage
- **z_level:** 19.5
- **width:** 58.5
- **height:** 45.5
- **origin:** 9867.0, 8316.75, 19.5

Notes: Stone building with slate roof on a low hill overlooking the
Greywater River. Origin at southwest corner. Study (main room) in
front, laboratory side room to the east, small bedroom in the back.
Herb garden on the west side. Ivy on walls.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_path      | 19.5  | 0.0  |
| study_desk      | 16.25  | 16.25  |
| bookshelves     | 6.5  | 19.5  |
| fireplace       | 3.25  | 9.75  |
| lab_door        | 32.5 | 19.5  |
| lab_table       | 45.5 | 16.25  |
| obelisk_notes   | 45.5 | 26.0  |
| bedroom_door    | 16.25  | 29.25  |
| herb_garden     | -6.5 | 22.75  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LABORATORY | 6.5        | (32.5,9.75) (58.5,9.75) (58.5,32.5) (32.5,32.5)    |
| BEDROOM    | 6.5        | (0.0,29.25) (32.5,29.25) (32.5,45.5) (0.0,45.5)      |
| STUDY      | 3.25        | (0.0,0.0) (32.5,0.0) (32.5,29.25) (0.0,29.25)        |
| HERB_GARDEN| 3.25        | (-13.0,13.0) (0.0,13.0) (0.0,32.5) (-13.0,32.5)      |
| EXTERIOR   | 0.0        | (-19.5,-9.75) (68.25,-9.75) (68.25,55.25) (-19.5,55.25)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Lab wall       | (32.5,9.75) (32.5,32.5) (35.75,32.5) (35.75,9.75)    |
| Bedroom wall   | (0.0,29.25) (32.5,29.25) (32.5,32.5) (0.0,32.5)      |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_path | 19.5 | 0.0 | places/driftmoor |

---

## Boundaries

### Laboratory — Restricted Research

- **type:** conditional
- **blocks:** all
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (32.5,9.75) (58.5,9.75) (58.5,32.5) (32.5,32.5)
