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
| common_room_rug | 13 | 13 | 0 |
| hearth          | 4.5  | 6.5  | 4 |
| dining_table    | 13  | 13  | 4 |
| bar_counter     | 22.5 | 8  | 4 |
| stair_foot      | 27.5 | 18  | 0 |
| storage_shed    | 36.5 | 13 | 4 |

---

## Zones

| name            | floor_z | ceiling_z | render_z | vertices                        |
|-----------------|---------|-----------|----------|---------------------------------|
| STAIRWAY        | 0       | 8         | 7.0      | (26,14) (32.5,14) (32.5,24) (26,24) |
| COMMON_ROOM     | 0       | 8         | 3.25     | (0,0) (32.5,0) (32.5,26) (0,26)    |
| STORAGE_SHED    | 0       | 8         | 3.25     | (32.5,8) (40.5,8) (40.5,18) (32.5,18) |
| EXTERIOR        | 0       | 8         | 0.0      | (-4.5,-4.5) (45,-4.5) (45,30.5) (-4.5,30.5) |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Back wall       | (0,24) (26,24) (26,26) (0,26) |
| Hearth masonry  | (2,16) (5,16) (5,22) (2,22)   |

---

## Connections

| name        | x    | y   | destination                                |
|-------------|------|-----|--------------------------------------------|
| front_door  | 16   | 0   | places/driftmoor                           |
| to_upstairs | 27.5 | 18  | places/driftmoor/weary_traveler/upstairs  |
