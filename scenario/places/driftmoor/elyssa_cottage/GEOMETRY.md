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
| front_path      | 19  | 0  |
| study_desk      | 16  | 16  |
| bookshelves     | 6  | 19  |
| fireplace       | 3  | 9  |
| lab_door        | 32 | 19  |
| lab_table       | 45 | 16  |
| obelisk_notes   | 45 | 26  |
| bedroom_door    | 16  | 29  |
| herb_garden     | -6 | 22  |

---

## Zones

| name       | render_z | vertices                        |
|------------|----------|---------------------------------|
| LABORATORY | 6.5        | (32,9) (58,9) (58,32) (32,32)    |
| BEDROOM    | 6.5        | (0,29) (32,29) (32,45) (0,45)      |
| STUDY      | 3.25        | (0,0) (32,0) (32,29) (0,29)        |
| HERB_GARDEN| 3.25        | (-13,13) (0,13) (0,32) (-13,32)      |
| EXTERIOR   | 0.0        | (-19,-9) (68,-9) (68,55) (-19,55)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Lab wall       | (32,9) (32,32) (35,32) (35,9)    |
| Bedroom wall   | (0,29) (32,29) (32,32) (0,32)      |

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_path | 19 | 0 | places/driftmoor |

---

## Starting Positions

| character  | x  | y  |
|------------|----|----|
| gilthaness | 19 | 4  |
| elyssa     | 16 | 16 |

---

## Boundaries

### Laboratory — Restricted Research

- **type:** conditional
- **blocks:** all
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (32,9) (58,9) (58,32) (32,32)
