# GEOMETRY.md — The Weary Traveler (Rooming House)

## Scene

- **name:** The Weary Traveler
- **place_path:** places/driftmoor/weary_traveler
- **z_level:** 16.25
- **width:** 65.0
- **height:** 52.0
- **origin:** 9343.75, 8554.0, 16.25

Notes: Two-story timber-framed rooming house. Origin at southwest
corner. Common room on the ground floor (tables, hearth), guest
rooms upstairs along a corridor. Storage shed attached to the east.
Martha Greaves runs it.

---

## Landmarks

| name            | x    | y    |
|-----------------|------|------|
| front_door      | 32 | 0  |
| hearth          | 9  | 13  |
| dining_table    | 26  | 13  |
| bar_counter     | 45 | 13  |
| staircase       | 55 | 19  |
| upstairs_hall   | 32 | 39 |
| guest_room_1    | 13  | 39 |
| guest_room_2    | 32 | 45 |
| guest_room_3    | 52 | 39 |
| storage_shed    | 71 | 13  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| GUEST_ROOMS     | 9.75        | (0,26) (65,26) (65,52) (0,52)      |
| COMMON_ROOM     | 3.25        | (0,0) (65,0) (65,26) (0,26)        |
| STORAGE_SHED    | 3.25        | (65,0) (84,0) (84,26) (65,26)      |
| EXTERIOR        | 0.0        | (-9,-9) (94,-9) (94,61) (-9,61)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Floor division | (0,26) (65,26) (65,29) (0,29)        |
| Back wall      | (0,48) (65,48) (65,52) (0,52)    |

---

## Connections

| name       | x    | y   | destination      |
|------------|------|-----|------------------|
| front_door | 32 | 0 | places/driftmoor |

---

## Boundaries

### Guest Rooms — Rented Access

- **type:** conditional
- **blocks:** all
- **effect:** upstairs corridor and guest rooms; must rent a room or be invited
- **vertices:** (0,26) (65,26) (65,52) (0,52)
