# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 16.25
- **width:** 40.5
- **height:** 32.5
- **origin:** 427.5, 252, 0

Notes: Ground floor of a two-story timber tavern. The public room
occupies most of the south and center. A narrow bar and kitchen service
strip runs along the east wall. The enlarged meeting room occupies the
northwest; the stair rises between it and the storeroom, whose east door
opens directly into the kitchen. The broken lantern hangs above the
south entrance.

---

## Landmarks

| name               | x    | y    | z |
|--------------------|------|------|---|
| front_door         | 20   | 0    | 4 |
| table_1            | 12.446   | 5.455    | 4 |
| table_2            | 23.571   | 5.544   | 4 |
| table_3            | 12.473   | 11.872   | 4 |
| table_4            | 23.579   | 11.803   | 4 |
| hearth             | 29.555    | 18.973   | 4 |
| stage              | 14.754    | 19.306   | 4 |
| booth_1            | 2.304 | 3.708   | 4 |
| booth_2            | 2.304 | 9.07   | 4 |
| booth_3            | 2.304 | 14.432  | 4 |
| bar_counter        | 33.195   | 6.665    | 4 |
| bar_cabinet        | 38.265   | 7.234   | 4 |
| bar_stool_2        | 31.178   | 7.043   | 4 |
| bar_stool_3        | 31.178   | 3.899  | 4 |
| kitchen_center     | 37.211   | 24.675   | 4 |
| kitchen_stove      | 37.789 | 30.299 | 4 |
| meeting_room_door  | 8    | 23   | 4 |
| storage_room_door  | 32.5 | 27.75 | 4 |
| stair_foot         | 18.75 | 27.5 | 0 |
| kitchen_back_door  | 40.5 | 25   | 4 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                            |
|---------------|---------|-----------|----------|-------------------------------------|
| BAR           | 0       | 8         | 6.5      | (33.5,0) (40.5,0) (40.5,18) (33.5,18) |
| KITCHEN       | 0       | 8         | 6.5      | (33.5,18) (40.5,18) (40.5,32.5) (33.5,32.5) |
| MEETING_ROOM  | 0       | 8         | 6.5      | (0,23) (16,23) (16,32.5) (0,32.5) |
| STAIRWAY      | 0       | 8         | 7.0      | (16.5,23) (21,23) (21,32.5) (16.5,32.5) |
| STORAGE_ROOM  | 0       | 8         | 6.5      | (21.5,23) (32.5,23) (32.5,32.5) (21.5,32.5) |
| MAIN_ROOM     | 0       | 8         | 3.25     | (0,0) (33.5,0) (33.5,23) (0,23)       |
| EXTERIOR      | 0       | 8         | 0.0      | (-4.5,-4.5) (45,-4.5) (45,37) (-4.5,37) |

---

## Impassable

| description             | vertices                                  |
|-------------------------|-------------------------------------------|
| Bar counter             | (32,2) (34,2) (34,15) (32,15)            |
| Kitchen partition west  | (33,17.5) (35.5,17.5) (35.5,18.5) (33,18.5) |
| Kitchen partition east  | (38,17.5) (40.5,17.5) (40.5,18.5) (38,18.5) |
| Back wall               | (0,31.5) (40.5,31.5) (40.5,32.5) (0,32.5) |

---

## Connections

| name                | x    | y    | destination                                      |
|---------------------|------|------|--------------------------------------------------|
| front_door          | 20   | 0    | places/driftmoor                                 |
| to_meeting_room     | 8    | 23   | places/driftmoor/broken_lantern/meeting_room    |
| to_storage_room     | 32.5 | 27.75 | places/driftmoor/broken_lantern/storage_room   |
| to_upstairs         | 18.75 | 27.5 | places/driftmoor/broken_lantern/upstairs       |
| kitchen_back_door   | 40.5 | 25   | places/driftmoor                                 |

---

## Items

| id                  | x    | y    | label                  |
|---------------------|------|------|------------------------|
| broken_lantern_sign | 20   | -1.5 | Broken lantern sign    |
| bar_stool           | 31.128   | 10.724    | Bar stool              |
| service_bell        | 32.848   | 7.93    | Service bell           |
| room_key_ring       | 37.961   | 8.125    | Room key ring          |
| ale_tankards        | 33.833   | 2.58    | Ale tankards           |
| tip_bowl            | 11.28    | 17.335   | Tip bowl               |
| lute_case           | 17.144    | 20.63   | Lute case              |
| dice_cup            | 12.996   | 5.682    | Dice cup               |
| kitchen_knife       | 37.199   | 24.304   | Kitchen knife          |
| stew_pot            | 38.36   | 30.036   | Stew pot               |
| coal_scuttle        | 35.336   | 30.035   | Coal scuttle           |
