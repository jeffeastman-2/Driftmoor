# GEOMETRY.md — The Broken Lantern Upstairs

## Scene

- **name:** The Broken Lantern Upstairs
- **place_path:** places/driftmoor/broken_lantern/upstairs
- **z_level:** 25.25
- **width:** 45
- **height:** 35
- **origin:** 0, 0, 9

Notes: The upper floor shares the tavern's horizontal footprint. Three
guest rooms occupy the south side beneath the sloping roof and open north
into the hall. The stair arrives on the hall's north side.

---

## Landmarks

| name              | x    | y    | z |
|-------------------|------|------|---|
| stair_landing     | 18.75 | 27.5 | 0 |
| upstairs_hall     | 20   | 27.5 | 4 |
| room_1_bed        | 6.5  | 6.218 | 4 |
| room_2_bed        | 20.255 | 6.341 | 4 |
| room_3_bed        | 34   | 6.219 | 4 |
| linen_chest       | 2.266    | 27.5 | 4 |
| room_1_desk       | 6.575   | 12.708 | 4 |
| room_2_desk       | 20.207   | 12.708 | 4 |
| room_3_desk       | 33.942   | 12.096 | 4 |
| room_1_basin      | 2.266    | 20.479 | 4 |
| room_2_basin      | 16.133 | 20.356 | 4 |
| room_3_basin      | 30.011 | 20.234 | 4 |

---

## Zones

| name          | floor_z | ceiling_z | render_z | vertices                                  |
|---------------|---------|-----------|----------|-------------------------------------------|
| GUEST_BEDROOM_1 | 0     | 8         | 6.5      | (0,0) (13,0) (13,22.5) (0,22.5)       |
| GUEST_BEDROOM_2 | 0     | 8         | 6.5      | (13.75,0) (27,0) (27,22.5) (13.75,22.5) |
| GUEST_BEDROOM_3 | 0     | 8         | 6.5      | (27.75,0) (40.5,0) (40.5,22.5) (27.75,22.5) |
| UPSTAIRS_HALL | 0       | 8         | 3.25     | (0,22.5) (40.5,22.5) (40.5,32.5) (0,32.5) |
| STAIR_LANDING | 0       | 8         | 7.0      | (16.5,22.5) (21,22.5) (21,32.5) (16.5,32.5) |

---

## Fog of War

- **reveal_on_entry:** GUEST_BEDROOM_1, GUEST_BEDROOM_2, GUEST_BEDROOM_3
- **reveal_layout:** GUEST_BEDROOM_1, GUEST_BEDROOM_2, GUEST_BEDROOM_3

---

## Impassable
| description          | vertices                              |
|----------------------|---------------------------------------|

---

## Connections

| name          | x  | y | destination                              |
|---------------|----|---|------------------------------------------|
| to_main_room  | 18.75 | 27.5 | places/driftmoor/broken_lantern   |
