# GEOMETRY.md — The Weary Traveler Upstairs

## Scene

- **name:** The Weary Traveler Upstairs
- **place_path:** places/driftmoor/weary_traveler/upstairs
- **z_level:** 25.25
- **width:** 32.5
- **height:** 26
- **origin:** 0, 0, 9

Notes: The upper floor occupies the same horizontal footprint as the
rooming house below. Its local floor is zero at a world elevation nine
feet above the common room. Three guest rooms open from a broad hall;
the stair arrives at the southeast landing.

---

## Landmarks

| name              | x    | y    | z |
|-------------------|------|------|---|
| stair_landing     | 27.5 | 5    | 0 |
| upstairs_hall     | 16   | 5    | 4 |
| guest_room_1_bed  | 5    | 19   | 4 |
| guest_room_2_bed  | 16   | 19   | 4 |
| guest_room_3_bed  | 27.5 | 19   | 4 |
| linen_cupboard    | 3    | 5    | 4 |
| guest_room_1_chest | 2.5 | 13 | 4 |
| guest_room_1_basin | 8.2 | 13 | 4 |
| guest_room_2_chest | 13.5 | 13 | 4 |
| guest_room_2_basin | 19.2 | 13 | 4 |
| guest_room_3_chest | 24.5 | 13 | 4 |
| guest_room_3_basin | 30.2 | 13 | 4 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                              |
|---------------|---------|-----------|----------|---------------------------------------|
| STAIR_LANDING | 0       | 8         | 7.0      | (26,0) (32.5,0) (32.5,10) (26,10)   |
| GUEST_ROOM_1  | 0       | 8         | 6.5      | (0,10) (10.5,10) (10.5,26) (0,26)   |
| GUEST_ROOM_2  | 0       | 8         | 6.5      | (11,10) (21.5,10) (21.5,26) (11,26) |
| GUEST_ROOM_3  | 0       | 8         | 6.5      | (22,10) (32.5,10) (32.5,26) (22,26) |
| UPSTAIRS_HALL | 0       | 8         | 3.25     | (0,0) (32.5,0) (32.5,10) (0,10)     |

---

## Impassable

| description          | vertices                              |
|----------------------|---------------------------------------|
| Room 1 north wall    | (0,24) (10.5,24) (10.5,26) (0,26)   |
| Room 2 north wall    | (11,24) (21.5,24) (21.5,26) (11,26) |
| Room 3 north wall    | (22,24) (32.5,24) (32.5,26) (22,26) |
| Rooms 1–2 divider    | (10.5,10) (11,10) (11,26) (10.5,26) |
| Rooms 2–3 divider    | (21.5,10) (22,10) (22,26) (21.5,26) |
| Room 1 south wall W  | (0,10) (4,10) (4,10.5) (0,10.5)    |
| Room 1 south wall E  | (6,10) (10.5,10) (10.5,10.5) (6,10.5) |
| Room 2 south wall W  | (11,10) (15,10) (15,10.5) (11,10.5) |
| Room 2 south wall E  | (17,10) (21.5,10) (21.5,10.5) (17,10.5) |
| Room 3 south wall W  | (22,10) (26,10) (26,10.5) (22,10.5) |
| Room 3 south wall E  | (28,10) (32.5,10) (32.5,10.5) (28,10.5) |

---

## Connections

| name          | x    | y | destination                         |
|---------------|------|---|-------------------------------------|
| to_common_room | 27.5 | 5 | places/driftmoor/weary_traveler    |

---

## Fog of War

- **reveal_on_entry:** GUEST_ROOM_1, GUEST_ROOM_2, GUEST_ROOM_3

---

## Boundaries

### Guest Rooms — Rented Access

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** private guest rooms; must rent a room or be invited
- **vertices:** (0,10) (32.5,10) (32.5,26) (0,26)
