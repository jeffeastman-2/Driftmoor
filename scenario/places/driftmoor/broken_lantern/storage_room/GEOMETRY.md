# GEOMETRY.md — The Broken Lantern Storage Room

## Scene

- **name:** The Broken Lantern Storage Room
- **place_path:** places/driftmoor/broken_lantern/storage_room
- **z_level:** 16.25
- **width:** 9
- **height:** 9.5
- **origin:** 12.5, 23, 0

Notes: A compact ground-floor supply room between the meeting room and
stair bay. Its south door opens behind the bar end.

---

## Landmarks

| name              | x | y   | z |
|-------------------|---|-----|---|
| main_room_door    | 4.5 | 0 | 4 |
| ale_barrels       | 2   | 7 | 4 |
| dry_goods         | 7   | 7 | 4 |
| hidden_floorboard | 6.5 | 3 | 0 |

---

## Zones

| name        | floor_z | ceiling_z | render_z | vertices                    |
|-------------|---------|-----------|----------|-----------------------------|
| STORAGE_ROOM | 0      | 8         | 3.25     | (0,0) (9,0) (9,9.5) (0,9.5) |

---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| Barrel stack | (0,6) (4,6) (4,9.5) (0,9.5) |
| Crate stack  | (6,7) (9,7) (9,9.5) (6,9.5) |

---

## Connections

| name         | x | y | destination                              |
|--------------|---|---|------------------------------------------|
| to_main_room | 4.5 | 0 | places/driftmoor/broken_lantern       |

---

## Items

| id                 | x | y | label                  |
|--------------------|---|---|------------------------|
| spare_blanket      | 4.5 | 8 | Spare blanket          |
| crate_saltfish     | 7   | 7 | Crate of saltfish      |
| candle_stub_bundle | 7.5 | 4 | Bundle of candle stubs |
