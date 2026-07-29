# GEOMETRY.md — The Broken Lantern Meeting Room

## Scene

- **name:** The Broken Lantern Meeting Room
- **place_path:** places/driftmoor/broken_lantern/meeting_room
- **z_level:** 16.25
- **width:** 11.5
- **height:** 9.5
- **origin:** 0, 23, 0

Notes: A private room occupying the northwest corner of the tavern's
ground floor. Its south door opens into the public room.

---

## Landmarks

| name             | x | y   | z |
|------------------|---|-----|---|
| main_room_door   | 6   | 0 | 4 |
| round_table      | 5.75 | 5 | 4 |
| ledger_corner    | 3   | 7 | 4 |
| lamp             | 9   | 7 | 5 |

---

## Zones

| name         | floor_z | ceiling_z | render_z | vertices                    |
|--------------|---------|-----------|----------|-----------------------------|
| MEETING_ROOM | 0       | 8         | 3.25     | (0,0) (11.5,0) (11.5,9.5) (0,9.5) |

---

## Impassable

| description | vertices                         |
|-------------|----------------------------------|
| North wall  | (0,8.5) (11.5,8.5) (11.5,9.5) (0,9.5) |

---

## Connections

| name         | x | y | destination                              |
|--------------|---|---|------------------------------------------|
| to_main_room | 6 | 0 | places/driftmoor/broken_lantern         |

---

## Items

| id            | x | y   | label         |
|---------------|---|-----|---------------|
| ledger_book   | 3 | 7 | Ledger book   |
| sealed_letter | 4 | 7 | Sealed letter |
