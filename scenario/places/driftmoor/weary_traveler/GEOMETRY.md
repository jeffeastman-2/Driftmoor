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
| front_door      | 32.5 | 0.0  |
| hearth          | 9.75  | 13.0  |
| dining_table    | 26.0  | 13.0  |
| bar_counter     | 45.5 | 13.0  |
| staircase       | 55.25 | 19.5  |
| upstairs_hall   | 32.5 | 39.0 |
| guest_room_3.25    | 13.0  | 39.0 |
| guest_room_6.5    | 32.5 | 45.5 |
| guest_room_9.75    | 52.0 | 39.0 |
| storage_shed    | 71.5 | 13.0  |

---

## Zones

| name            | render_z | vertices                        |
|-----------------|----------|---------------------------------|
| GUEST_ROOMS     | 9.75        | (0.0,26.0) (65.0,26.0) (65.0,52.0) (0.0,52.0)      |
| COMMON_ROOM     | 3.25        | (0.0,0.0) (65.0,0.0) (65.0,26.0) (0.0,26.0)        |
| STORAGE_SHED    | 3.25        | (65.0,0.0) (84.5,0.0) (84.5,26.0) (65.0,26.0)      |
| EXTERIOR        | 0.0        | (-9.75,-9.75) (94.25,-9.75) (94.25,61.75) (-9.75,61.75)  |

---

## Impassable

| description    | vertices                        |
|----------------|---------------------------------|
| Floor division | (0.0,26.0) (65.0,26.0) (65.0,29.25) (0.0,29.25)        |
| Back wall      | (0.0,48.75) (65.0,48.75) (65.0,52.0) (0.0,52.0)    |

---

## Connections

| name       | x    | y   | destination      |
|------------|------|-----|------------------|
| front_door | 32.5 | 0.0 | places/driftmoor |

---

## Boundaries

### Guest Rooms — Rented Access

- **type:** conditional
- **blocks:** all
- **effect:** upstairs corridor and guest rooms; must rent a room or be invited
- **vertices:** (0.0,26.0) (65.0,26.0) (65.0,52.0) (0.0,52.0)
