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
| study_desk      | 12.257  | 10.743  |
| bookshelves     | 2.284  | 9.122  |
| fireplace       | 1.783  | 1.946  |
| lab_door        | 16 | 9.5  |
| lab_table       | 22.595 | 7.432  |
| obelisk_notes   | 20.513 | 7.324  |
| bedroom_door    | 8  | 14.5  |
| herb_garden     | -3 | 11  |
| narrow_bed      | 4 | 19 |
| wardrobe        | 14.041 | 19.284 |
| bedside_table   | 7.243 | 20.649 |
| containment_dome | 25.19 | 9.202 |
| map_table       | 8.149 | 6.365 |

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
| Lab wall south | (16,4.5) (17,4.5) (17,8.5) (16,8.5)    |
| Lab wall north | (16,10.5) (17,10.5) (17,16) (16,16)    |
| Bedroom wall west | (0,14.5) (7,14.5) (7,15.5) (0,15.5) |
| Bedroom wall east | (9,14.5) (16,14.5) (16,15.5) (9,15.5) |

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
- **render:** hidden
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (16,4.5) (29,4.5) (29,16) (16,16)

---

## Items

| id | x | y | label |
|---|---|---|---|
| obelisk_shard_contained_specimen | 25.189 | 8.824 | Obelisk Shard (Contained Specimen) |
