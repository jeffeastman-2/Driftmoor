# GEOMETRY.md — The Broken Lantern Meeting Room

## Scene

- **name:** The Broken Lantern Meeting Room
- **place_path:** places/driftmoor/broken_lantern/meeting_room
- **z_level:** 16.25
- **width:** 16
- **height:** 9.5
- **origin:** 0, 23, 0

Notes: A private room occupying the northwest corner of the tavern's
ground floor. Its south door opens into the public room.

---

## Landmarks

| name             | x | y   | z |
|------------------|---|-----|---|
| main_room_door   | 8   | 0 | 4 |
| round_table      | 8   | 5 | 4 |
| ledger_corner    | 3   | 7 | 4 |
| lamp             | 8.709   | 6.156 | 5 |

---

## Zones

| name         | floor_z | ceiling_z | render_z | vertices                    |
|--------------|---------|-----------|----------|-----------------------------|
| MEETING_ROOM | 0       | 8         | 3.25     | (0,0) (16,0) (16,9.5) (0,9.5) |

---

## Impassable

| description | vertices                         |
|-------------|----------------------------------|
| North wall  | (0,8.5) (16,8.5) (16,9.5) (0,9.5) |

---

## Connections

| name         | x | y | destination                              |
|--------------|---|---|------------------------------------------|
| to_main_room | 8 | 0 | places/driftmoor/broken_lantern         |

---

## Items

| id            | x | y   | label         |
|---------------|---|-----|---------------|
| ledger_book   | 7.48 | 4.178 | Ledger book   |
| sealed_letter | 6.996 | 6.447 | Sealed letter |
