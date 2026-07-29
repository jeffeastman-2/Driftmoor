# GEOMETRY.md — The Broken Lantern Upstairs

## Scene

- **name:** The Broken Lantern Upstairs
- **place_path:** places/driftmoor/broken_lantern/upstairs
- **z_level:** 25.25
- **width:** 40.5
- **height:** 32.5
- **origin:** 0, 0, 9

Notes: The upper floor shares the tavern's horizontal footprint. Three
guest rooms open from a south hall beneath the sloping roof. The stair
arrives at the southeast landing.

---

## Landmarks

| name              | x    | y    | z |
|-------------------|------|------|---|
| stair_landing     | 37   | 5    | 0 |
| upstairs_hall     | 20   | 5    | 4 |
| room_1_bed        | 6.5  | 21   | 4 |
| room_2_bed        | 20.5 | 21   | 4 |
| room_3_bed        | 34   | 21   | 4 |
| linen_chest       | 3    | 5    | 4 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                                  |
|---------------|---------|-----------|----------|-------------------------------------------|
| STAIR_LANDING | 0       | 8         | 7.0      | (33.5,0) (40.5,0) (40.5,10) (33.5,10)   |
| GUEST_ROOM_1  | 0       | 8         | 6.5      | (0,10) (13,10) (13,32.5) (0,32.5)       |
| GUEST_ROOM_2  | 0       | 8         | 6.5      | (13.75,10) (27,10) (27,32.5) (13.75,32.5) |
| GUEST_ROOM_3  | 0       | 8         | 6.5      | (27.75,10) (40.5,10) (40.5,32.5) (27.75,32.5) |
| UPSTAIRS_HALL | 0       | 8         | 3.25     | (0,0) (40.5,0) (40.5,10) (0,10)         |

---

## Impassable

| description       | vertices                                  |
|-------------------|-------------------------------------------|
| Rooms 1–2 divider | (13,10) (13.75,10) (13.75,32.5) (13,32.5) |
| Rooms 2–3 divider | (27,10) (27.75,10) (27.75,32.5) (27,32.5) |
| Room 1 wall west  | (0,9.5) (5.5,9.5) (5.5,10.5) (0,10.5)   |
| Room 1 wall east  | (7.5,9.5) (13,9.5) (13,10.5) (7.5,10.5) |
| Room 2 wall west  | (13.75,9.5) (19.5,9.5) (19.5,10.5) (13.75,10.5) |
| Room 2 wall east  | (21.5,9.5) (27,9.5) (27,10.5) (21.5,10.5) |
| Room 3 wall west  | (27.75,9.5) (33,9.5) (33,10.5) (27.75,10.5) |
| Room 3 wall east  | (35,9.5) (40.5,9.5) (40.5,10.5) (35,10.5) |

---

## Connections

| name          | x  | y | destination                              |
|---------------|----|---|------------------------------------------|
| to_main_room  | 37 | 5 | places/driftmoor/broken_lantern         |
