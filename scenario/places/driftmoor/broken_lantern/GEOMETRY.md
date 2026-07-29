# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 16.25
- **width:** 40.5
- **height:** 32.5
- **origin:** 427.5, 252, 0

Notes: Ground floor of a two-story timber tavern. The public room
occupies the south and west, the bar runs along the east side, and the
kitchen fills the northeast corner. A meeting room and storage room
have distinct footprints along the rear wall. The stair rises between
the back rooms and kitchen. The broken lantern hangs above the south
entrance.

---

## Landmarks

| name               | x    | y    | z |
|--------------------|------|------|---|
| front_door         | 20   | 0    | 4 |
| central_tables     | 17   | 11   | 4 |
| hearth             | 3    | 18   | 4 |
| stage              | 7    | 17   | 4 |
| booth_row          | 6    | 7    | 4 |
| bar_counter        | 28   | 9    | 4 |
| kitchen_center     | 34   | 25   | 4 |
| meeting_room_door  | 6    | 23   | 4 |
| storage_room_door  | 17   | 23   | 4 |
| stair_foot         | 24.5 | 27.5 | 0 |
| kitchen_back_door  | 40.5 | 25   | 4 |
| broken_lantern     | 20   | -1.5 | 5 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                            |
|---------------|---------|-----------|----------|-------------------------------------|
| STAGE         | 0       | 8         | 6.5      | (1,14) (11,14) (11,21.5) (1,21.5) |
| BOOTHS        | 0       | 8         | 6.5      | (1,3) (11,3) (11,13) (1,13)        |
| BAR           | 0       | 8         | 6.5      | (27,0) (40.5,0) (40.5,18) (27,18) |
| KITCHEN       | 0       | 8         | 6.5      | (27,18) (40.5,18) (40.5,32.5) (27,32.5) |
| MEETING_ROOM  | 0       | 8         | 6.5      | (0,23) (11.5,23) (11.5,32.5) (0,32.5) |
| STORAGE_ROOM  | 0       | 8         | 6.5      | (12.5,23) (21.5,23) (21.5,32.5) (12.5,32.5) |
| STAIRWAY      | 0       | 8         | 7.0      | (22.5,23) (27,23) (27,32.5) (22.5,32.5) |
| MAIN_ROOM     | 0       | 8         | 3.25     | (0,0) (27,0) (27,23) (0,23)       |
| EXTERIOR      | 0       | 8         | 0.0      | (-4.5,-4.5) (45,-4.5) (45,37) (-4.5,37) |

---

## Impassable

| description             | vertices                                  |
|-------------------------|-------------------------------------------|
| Bar counter             | (26,2) (28,2) (28,15) (26,15)            |
| Kitchen partition north | (27,17.5) (33,17.5) (33,18.5) (27,18.5) |
| Kitchen partition south | (35,17.5) (40.5,17.5) (40.5,18.5) (35,18.5) |
| Back wall               | (0,31.5) (40.5,31.5) (40.5,32.5) (0,32.5) |

---

## Connections

| name                | x    | y    | destination                                      |
|---------------------|------|------|--------------------------------------------------|
| front_door          | 20   | 0    | places/driftmoor                                 |
| to_meeting_room     | 6    | 23   | places/driftmoor/broken_lantern/meeting_room    |
| to_storage_room     | 17   | 23   | places/driftmoor/broken_lantern/storage_room    |
| to_upstairs         | 24.5 | 27.5 | places/driftmoor/broken_lantern/upstairs        |
| kitchen_back_door   | 40.5 | 25   | places/driftmoor                                 |

---

## Items

| id                  | x    | y    | label                  |
|---------------------|------|------|------------------------|
| broken_lantern_sign | 20   | -1.5 | Broken lantern sign    |
| bar_stool           | 25   | 8    | Bar stool              |
| service_bell        | 31   | 9    | Service bell           |
| room_key_ring       | 33   | 9    | Room key ring          |
| ale_tankards        | 35   | 9    | Ale tankards           |
| tip_bowl            | 7    | 15   | Tip bowl               |
| lute_case           | 8    | 11   | Lute case              |
| dice_cup            | 15   | 8    | Dice cup               |
| kitchen_knife       | 33   | 24   | Kitchen knife          |
| stew_pot            | 36   | 27   | Stew pot               |
| coal_scuttle        | 38   | 20   | Coal scuttle           |
