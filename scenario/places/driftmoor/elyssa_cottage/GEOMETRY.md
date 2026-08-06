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
| front_path      | 8.684  | -0.117  |
| study_desk      | 12.257  | 10.743  |
| bookshelves     | 26.649  | 9.413  |
| fireplace       | 13.266  | 2.645  |
| lab_door        | 16 | 6.785  |
| lab_table       | 22.942 | 2.196  |
| obelisk_notes   | 21.035 | 2.263  |
| bedroom_door    | 8  | 14.5  |
| garden_door     | 0  | 11  |
| herb_garden     | -3 | 11  |
| narrow_bed      | 4 | 19 |
| wardrobe        | 14.041 | 19.284 |
| bedside_table   | 7.243 | 20.649 |
| containment_dome | 19.944 | 11.141 |
| map_table       | 8.149 | 6.365 |

---

## Zones

| name | render_z | auto_wall | vertices |
|------------|----------|---------|---------------------------------|
| LABORATORY | 6.5 |  | (16,0) (29,0) (29,14) (16,14) |
| BEDROOM | 6.5 |  | (0,14.5) (16,14.5) (16,22.5) (0,22.5) |
| STUDY | 3.25 |  | (0,0) (16,0) (16,14.5) (0,14.5) |
| HERB_GARDEN | 3.25 |  | (-6.5,6.5) (0,6.5) (0,16) (-6.5,16) |
| EXTERIOR | 0.0 |  | (-9.5,-4.5) (34,-4.5) (34,27.5) (-9.5,27.5) |
---

## Fog of War

- **reveal_on_entry:** BEDROOM, LABORATORY
- **reveal_layout:** BEDROOM, LABORATORY

## Impassable

Empty: STUDY/LABORATORY and STUDY/BEDROOM walls are generated
automatically now (lab_door and bedroom_door landmarks carve their gaps —
see compute_auto_walls / "## Walls" in the tavern's GEOMETRY.md for the
opt-out story). STUDY/HERB_GARDEN stays open via garden_door.

---

## Connections

| name       | x   | y   | destination      |
|------------|-----|-----|------------------|
| front_path | 8.684 | 0.3 | places/driftmoor |

---

## Boundaries

### Laboratory — Restricted Research

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** Elyssa's private obelisk research; door usually locked; contains sensitive materials
- **vertices:** (16,0) (29,0) (29,14) (16,14)

---

## Items

| id | x | y | label |
|---|---|---|---|
| obelisk_shard_contained_specimen | 19.943 | 10.819 | Obelisk Shard (Contained Specimen) |
