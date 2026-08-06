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
| hearth             | 31.54    | 21.431   | 4 |
| stage              | 15.814    | 20.429   | 4 |
| booth_1            | 2.304 | 3.708   | 4 |
| booth_2            | 2.304 | 9.07   | 4 |
| booth_3            | 2.304 | 14.432  | 4 |
| bar_counter        | 35.223   | 7.546    | 4 |
| bar_cabinet        | 42.401   | 8.912   | 4 |
| bar_stool_2        | 32.017   | 7.163   | 4 |
| bar_stool_3        | 32.316   | 3.42  | 4 |
| kitchen_center     | 39.891   | 26.508   | 4 |
| kitchen_stove      | 40.539 | 32.414 | 4 |
| meeting_room_door  | 8    | 25   | 4 |
| storage_room_door  | 35 | 30 | 4 |
| stair_foot         | 23.399 | 28.291 | 0 |
| kitchen_back_door  | 45 | 21.172   | 4 |
| bar_kitchen_door   | 39.399 | 18  | 4 |
| bar_archway        | 35 | 16.5   | 4 |
| stairway_archway   | 23.5 | 25  | 4 |

---

## Zones

| name | floor_z | ceiling_z | render_z | auto_wall | vertices |
|---------------|---------|-----------|----------|---------|-------------------------------------|
| BAR | 0 | 8 | 6.5 |  | (35,0) (45,0) (45,18) (35,18) |
| KITCHEN | 0 | 8 | 6.5 |  | (35,18) (45,18) (45,35) (35,35) |
| MEETING_ROOM | 0 | 8 | 6.5 |  | (0,25) (22,25) (22,35) (0,35) |
| STAIRWAY | 0 | 8 | 7.0 |  | (22,25) (25,25) (25,35) (22,35) |
| STORAGE_ROOM | 0 | 8 | 6.5 |  | (25,25) (35,25) (35,35) (25,35) |
| MAIN_ROOM | 0 | 8 | 3.25 |  | (0,0) (35,0) (35,25) (0,25) |
| EXTERIOR | 0 | 8 | 0.0 |  | (-4,-4) (49,-4) (49,39) (-4,39) |
---

## Impassable
| description             | vertices                                  |
|-------------------------|-------------------------------------------|
| Bar counter             | (34,2) (37,2) (37,15) (34,15)            |

---

## Fog of War

- **reveal_on_entry:** KITCHEN


## Connections

| name                | x    | y    | destination                                      |
|---------------------|------|------|--------------------------------------------------|
| front_door          | 20   | 0    | places/driftmoor                                 |
| to_meeting_room     | 8    | 25   | places/driftmoor/broken_lantern/meeting_room    |
| to_storage_room     | 35   | 30   | places/driftmoor/broken_lantern/storage_room   |
| to_upstairs         | 23.399 | 28.291 | places/driftmoor/broken_lantern/upstairs       |
| kitchen_back_door   | 42.5 | 32   | places/driftmoor                                 |

---

## Items

| id                  | x    | y    | label                  |
|---------------------|------|------|------------------------|
| broken_lantern_sign | 20   | -1.5 | Broken lantern sign    |
| bar_stool           | 32.087   | 10.724    | Bar stool              |
| service_bell        | 34.526   | 8.17    | Service bell           |
| room_key_ring       | 42.037   | 10.103    | Room key ring          |
| ale_tankards        | 35.451   | 2.64    | Ale tankards           |
| tip_bowl            | 11.28    | 18.141   | Tip bowl               |
| lute_case           | 18.987    | 21.782   | Lute case              |
| dice_cup            | 12.996   | 5.682    | Dice cup               |
| kitchen_knife       | 39.737   | 26.349   | Kitchen knife          |
| stew_pot            | 41.181   | 32.716   | Stew pot               |
| coal_scuttle        | 37.31   | 32.715   | Coal scuttle           |
