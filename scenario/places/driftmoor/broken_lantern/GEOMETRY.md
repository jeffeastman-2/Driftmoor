# GEOMETRY.md — The Broken Lantern (Tavern)

## Scene

- **name:** The Broken Lantern
- **place_path:** places/driftmoor/broken_lantern
- **z_level:** 5.0
- **width:** 25.0
- **height:** 20.0
- **origin:** 2868.0, 2468.0, 5.0

Notes: Ground floor contains the main room, bar, stage corner, private
booths, kitchen, storage room, and meeting room. Upper floor (z=8.0)
has three guest rooms accessed by a creaky interior staircase. The
broken lantern hangs above the front door on the south face. The
building is timber with a sloping roof and ivy on the east wall.

---

## Landmarks

| name             | x    | y    |
|------------------|------|------|
| front_door       | 12.0 | 0.0  |
| hearth           | 22.0 | 12.0 |
| bar_counter      | 20.0 | 7.0  |
| stage_corner     | 3.0  | 14.0 |
| booth_row        | 3.0  | 7.0  |
| staircase        | 18.0 | 17.0 |
| kitchen_center   | 20.0 | 17.0 |
| storage_center   | 8.0  | 17.0 |
| meeting_room_ctr | 3.0  | 17.0 |
| broken_lantern   | 12.0 | -1.0 |

---

## Zones

| name          | render_z | vertices                              |
|---------------|----------|---------------------------------------|
| STAGE         | 2        | (0,12) (8,12) (8,17) (0,17)           |
| BOOTHS        | 2        | (0,4) (8,4) (8,12) (0,12)             |
| BAR           | 2        | (15,4) (23,4) (23,14) (15,14)         |
| KITCHEN       | 2        | (15,14) (25,14) (25,20) (15,20)       |
| STORAGE_ROOM  | 2        | (8,14) (15,14) (15,20) (8,20)         |
| MEETING_ROOM  | 2        | (0,14) (8,14) (8,20) (0,20)           |
| MAIN_ROOM     | 1        | (0,0) (25,0) (25,14) (0,14)           |
| EXTERIOR      | 0        | (-5,-5) (30,-5) (30,25) (-5,25)       |

---

## Impassable

| description      | vertices                              |
|------------------|---------------------------------------|
| Bar counter      | (15,5) (23,5) (23,7) (15,7)           |
| Kitchen wall     | (15,14) (25,14) (25,15) (15,15)       |
| Back wall        | (0,19) (25,19) (25,20) (0,20)         |

---

## Connections

| name              | x    | y    | destination                    |
|-------------------|------|------|--------------------------------|
| front_door        | 12.0 | 0.0  | places/driftmoor               |
| to_upper_floor    | 18.0 | 17.0 | places/driftmoor/broken_lantern/upper_floor |
| kitchen_back_door | 25.0 | 17.0 | places/driftmoor               |

---

## Boundaries

### Tess's Back Rooms

- **type:** conditional
- **blocks:** all
- **effect:** storage room and meeting room require Tess's permission or a successful Persuasion/Deception check to access
- **vertices:** (0,14) (25,14) (25,20) (0,20)

---

## Starting Positions

| character | x    | y    | zone      |
|-----------|------|------|-----------|
| kaelin    | 5.0  | 8.0  | BOOTHS    |
| tess      | 20.0 | 8.0  | BAR       |