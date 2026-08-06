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
feet above the common room. Six guest rooms open from a broad hall,
three to a side; the stair arrives at the southeast landing.

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
| guest_room_1_door  | 5    | 10   | 4 |
| guest_room_2_door  | 16   | 10   | 4 |
| guest_room_3_door  | 27   | 10   | 4 |
| guest_room_4_bed  | 5    | -9   | 4 |
| guest_room_5_bed  | 16   | -9   | 4 |
| guest_room_6_bed  | 27.5 | -9   | 4 |
| guest_room_4_chest | 2.5 | -3 | 4 |
| guest_room_4_basin | 8.2 | -3 | 4 |
| guest_room_5_chest | 13.5 | -3 | 4 |
| guest_room_5_basin | 19.2 | -3 | 4 |
| guest_room_6_chest | 24.5 | -3 | 4 |
| guest_room_6_basin | 30.2 | -3 | 4 |
| guest_room_4_door  | 5    | 0    | 4 |
| guest_room_5_door  | 16   | 0    | 4 |
| guest_room_6_door  | 27   | 0    | 4 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                              |
|---------------|---------|-----------|----------|---------------------------------------|
| STAIR_LANDING | 0       | 8         | 7.0      | (26,0) (32.5,0) (32.5,10) (26,10)   |
| GUEST_ROOM_1  | 0       | 8         | 6.5      | (0,10) (10.5,10) (10.5,26) (0,26)   |
| GUEST_ROOM_2  | 0       | 8         | 6.5      | (11,10) (21.5,10) (21.5,26) (11,26) |
| GUEST_ROOM_3  | 0       | 8         | 6.5      | (22,10) (32.5,10) (32.5,26) (22,26) |
| GUEST_ROOM_4  | 0       | 8         | 6.5      | (0,-16) (10.5,-16) (10.5,0) (0,0)   |
| GUEST_ROOM_5  | 0       | 8         | 6.5      | (11,-16) (21.5,-16) (21.5,0) (11,0) |
| GUEST_ROOM_6  | 0       | 8         | 6.5      | (22,-16) (32.5,-16) (32.5,0) (22,0) |
| UPSTAIRS_HALL | 0       | 8         | 3.25     | (0,0) (32.5,0) (32.5,10) (0,10)     |

---

## Impassable

Room south walls (the hall/guest-room boundary) are generated
automatically now (guest_room_1_door / guest_room_2_door /
guest_room_3_door carve their gaps — see compute_auto_walls). The
entries below have no zone on their other side (the building's own
outer wall, and the gap between non-adjoining room zones), so auto-wall
can't generate them.

| description          | vertices                              |
|----------------------|---------------------------------------|
| Room 1 north wall    | (0,24) (10.5,24) (10.5,26) (0,26)   |
| Room 2 north wall    | (11,24) (21.5,24) (21.5,26) (11,26) |
| Room 3 north wall    | (22,24) (32.5,24) (32.5,26) (22,26) |
| Rooms 1–2 divider    | (10.5,10) (11,10) (11,26) (10.5,26) |
| Rooms 2–3 divider    | (21.5,10) (22,10) (22,26) (21.5,26) |
| Room 4 south wall    | (0,-16) (10.5,-16) (10.5,-14) (0,-14) |
| Room 5 south wall    | (11,-16) (21.5,-16) (21.5,-14) (11,-14) |
| Room 6 south wall    | (22,-16) (32.5,-16) (32.5,-14) (22,-14) |
| Rooms 4–5 divider    | (10.5,-16) (11,-16) (11,0) (10.5,0) |
| Rooms 5–6 divider    | (21.5,-16) (22,-16) (22,0) (21.5,0) |

---

## Connections

| name          | x    | y | destination                         |
|---------------|------|---|-------------------------------------|
| to_common_room | 27.5 | 5 | places/driftmoor/weary_traveler    |

---

## Fog of War

- **reveal_on_entry:** GUEST_ROOM_1, GUEST_ROOM_2, GUEST_ROOM_3, GUEST_ROOM_4, GUEST_ROOM_5, GUEST_ROOM_6

---

## Boundaries

### Guest Rooms — Rented Access

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** private guest rooms; must rent a room or be invited
- **vertices:** (0,10) (32.5,10) (32.5,26) (0,26)

### Guest Rooms South — Rented Access

- **type:** conditional
- **blocks:** all
- **render:** hidden
- **effect:** private guest rooms; must rent a room or be invited
- **vertices:** (0,-16) (32.5,-16) (32.5,0) (0,0)
