# GEOMETRY.md — The Weary Traveler (Rooming House)

## Scene

- **name:** The Weary Traveler
- **place_path:** places/driftmoor/weary_traveler
- **z_level:** 16.25
- **width:** 32.5
- **height:** 26
- **origin:** 435, 361, 0

Notes: Ground floor of a two-story timber-framed rooming house.
Origin is at the southwest corner. The common room fills the main
building footprint; a stair rises along the east wall to the guest
rooms, and a storage shed is attached outside that wall. Martha
Greaves runs the house from behind the counter.

---

## Landmarks

| name            | x    | y    | z    |
|-----------------|------|------|------|
| front_door      | 16 | 0  | 4 |
| common_room_rug | 13.12 | 11.678 | 0 |
| hearth          | 12.55  | 22.12  | 4 |
| dining_table    | 13  | 11.798  | 4 |
| bar_counter     | 25.864 | 5.356  | 4 |
| stair_foot      | 27.5 | 18  | 0 |
| storage_shed    | 36.5 | 21 | 4 |
| kitchen         | 36.5 | 7.542 | 4 |
| kitchen_door    | 32.5 | 10.897 | 4 |
| kitchen_stove   | 36.542   | 2.289 | 4 |
| kitchen_sink    | 38.942   | 13.059 | 4 |
| storage_shed_door | 34.583 | 18 | 4 |

---

## Zones

| name | floor_z | ceiling_z | render_z | auto_wall | vertices |
|-----------------|---------|-----------|----------|---------|---------------------------------|
| STAIRWAY | 0 | 8 | 7.0 |  | (26,14) (32.5,14) (32.5,24) (26,24) |
| COMMON_ROOM | 0 | 8 | 3.25 |  | (0,0) (32.5,0) (32.5,26) (0,26) |
| STORAGE_SHED | 0 | 8 | 3.25 |  | (32.5,18) (40.5,18) (40.5,26) (32.5,26) |
| KITCHEN | 0 | 8 | 3.25 |  | (32.5,0) (40.5,0) (40.5,18) (32.5,18) |
| EXTERIOR | 0 | 8 | 0.0 |  | (-4.5,-4.5) (45,-4.5) (45,30.5) (-4.5,30.5) |
---

## Fog of War

- **reveal_on_entry:** KITCHEN, STORAGE_SHED

## Impassable

Every zone boundary here — including against EXTERIOR — is generated
automatically now (front_door, kitchen and storage_shed_door carve their gaps;
see compute_auto_walls). Only interior furniture that isn't a zone
boundary stays hand-authored.

| description       | vertices                          |
|--------------------|-----------------------------------|

---

## Connections

| name        | x    | y   | destination                                |
|-------------|------|-----|--------------------------------------------|
| front_door  | 16   | 0   | places/driftmoor                           |
| to_upstairs | 27.5 | 18  | places/driftmoor/weary_traveler/upstairs  |
