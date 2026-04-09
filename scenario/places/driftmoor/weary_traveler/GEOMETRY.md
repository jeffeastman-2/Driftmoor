# GEOMETRY.md — The Weary Traveler (Rooming House)

## Scene

- **name:** The Weary Traveler
- **place_path:** places/driftmoor/weary_traveler
- **z_level:** 5.0
- **width:** 20.0
- **height:** 16.0
- **origin:** 2875.0, 2632.0, 5.0

Notes: Two-story timber-framed rooming house. Origin at southwest
corner. Common room on the ground floor (tables, hearth), guest
rooms upstairs along a corridor. Storage shed attached to the east.
Martha Greaves runs it.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 10.0 | 0.0  |
| hearth          | 3.0  | 4.0  |
| dining_table    | 8.0  | 4.0  |
| bar_counter     | 14.0 | 4.0  |
| staircase       | 17.0 | 6.0  |
| upstairs_hall   | 10.0 | 12.0 |
| guest_room_1    | 4.0  | 12.0 |
| guest_room_2    | 10.0 | 14.0 |
| guest_room_3    | 16.0 | 12.0 |
| storage_shed    | 22.0 | 4.0  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| GUEST_ROOMS     | 3        | (0,8) (20,8) (20,16) (0,16)      |
| COMMON_ROOM     | 1        | (0,0) (20,0) (20,8) (0,8)        |
| STORAGE_SHED    | 1        | (20,0) (26,0) (26,8) (20,8)      |
| EXTERIOR        | 0        | (-3,-3) (29,-3) (29,19) (-3,19)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Floor division | (0,8) (20,8) (20,9) (0,9)        |
| Back wall      | (0,15) (20,15) (20,16) (0,16)    |

---

## Connections

| name       | x    | y   | destination      |
|------------|------|-----|------------------|
| front_door | 10.0 | 0.0 | places/driftmoor |

---

## Boundaries

### Guest Rooms — Rented Access

- **type:** conditional
- **blocks:** all
- **effect:** upstairs corridor and guest rooms; must rent a room or be invited
- **vertices:** (0,8) (20,8) (20,16) (0,16)
