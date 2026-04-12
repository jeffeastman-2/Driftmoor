# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 16.25
- **width:** 81.25
- **height:** 65.0
- **origin:** 9321.0, 8021.0, 16.25

Notes: Ground floor contains the main room, bar, stage corner, private
booths, kitchen, storage room, and meeting room. Upper floor (z=26.0)
has three guest rooms accessed by a creaky interior staircase. The
broken lantern hangs above the front door on the south face. The
building is timber with a sloping roof and ivy on the east wall.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| front_door       | 39.0 | 0.0  |
| hearth           | 71.5 | 39.0 |
| bar_counter      | 65.0 | 22.75  |
| stage_corner     | 9.75  | 45.5 |
| booth_row        | 9.75  | 22.75  |
| staircase        | 58.5 | 55.25 |
| kitchen_center   | 65.0 | 55.25 |
| storage_center   | 26.0  | 55.25 |
| meeting_room_ctr | 9.75  | 55.25 |
| broken_lantern   | 39.0 | -3.25 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| STAGE         | 6.5        | (0.0,39.0) (26.0,39.0) (26.0,55.25) (0.0,55.25)           |
| BOOTHS        | 6.5        | (0.0,13.0) (26.0,13.0) (26.0,39.0) (0.0,39.0)             |
| BAR           | 6.5        | (48.75,13.0) (74.75,13.0) (74.75,45.5) (48.75,45.5)         |
| KITCHEN       | 6.5        | (48.75,45.5) (81.25,45.5) (81.25,65.0) (48.75,65.0)       |
| STORAGE_ROOM  | 6.5        | (26.0,45.5) (48.75,45.5) (48.75,65.0) (26.0,65.0)         |
| MEETING_ROOM  | 6.5        | (0.0,45.5) (26.0,45.5) (26.0,65.0) (0.0,65.0)           |
| MAIN_ROOM     | 3.25        | (0.0,0.0) (81.25,0.0) (81.25,45.5) (0.0,45.5)           |
| EXTERIOR      | 0.0        | (-16.25,-16.25) (97.5,-16.25) (97.5,81.25) (-16.25,81.25)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Bar counter      | (48.75,16.25) (74.75,16.25) (74.75,22.75) (48.75,22.75)           |
| Kitchen wall     | (48.75,45.5) (81.25,45.5) (81.25,48.75) (48.75,48.75)       |
| Back wall        | (0.0,61.75) (81.25,61.75) (81.25,65.0) (0.0,65.0)         |

---

## Connections

| name              | x    | y    | destination                    |
|-------------------|------|------|--------------------------------|
| front_door        | 39.0 | 0.0  | places/driftmoor               |
| to_upper_floor    | 58.5 | 55.25 | places/driftmoor/broken_lantern/upper_floor |
| kitchen_back_door | 81.25 | 55.25 | places/driftmoor               |

---

## Boundaries

### Tess's Back Rooms

- **type:** conditional
- **blocks:** all
- **effect:** storage room and meeting room require Tess's permission or a successful Persuasion/Deception check to access
- **vertices:** (0.0,45.5) (81.25,45.5) (81.25,65.0) (0.0,65.0)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| kaelin    | 16.25  | 26.0  | BOOTHS    |
| tess      | 65.0 | 26.0  | BAR       |