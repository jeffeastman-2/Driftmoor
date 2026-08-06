# GEOMETRY.md — The Broken Lantern Storage Room

## Scene

- **name:** The Broken Lantern Storage Room
- **place_path:** places/driftmoor/broken_lantern/storage_room
- **z_level:** 16.25
- **width:** 11
- **height:** 9.5
- **origin:** 21.5, 23, 0

Notes: A compact ground-floor supply room east of the stair bay. Its
east door opens directly into the kitchen.

---

## Landmarks

| name              | x | y   | z |
|-------------------|---|-----|---|
| kitchen_door      | 11 | 4.75 | 4 |
| ale_barrels       | 2.558   | 7.343 | 4 |
| dry_goods         | 7   | 7 | 4 |
| hidden_floorboard | 2.894 | 1.712 | 0 |

---

## Zones

| name | floor_z | ceiling_z | render_z | auto_wall | vertices |
|-------------|---------|-----------|----------|---------|-----------------------------|
| STORAGE_ROOM | 0 | 8 | 3.25 |  | (0,0) (11,0) (11,9.5) (0,9.5) |
---

## Impassable

| description  | vertices                         |
|--------------|----------------------------------|
| Barrel stack | (0,6) (4,6) (4,9.5) (0,9.5) |
| Crate stack  | (7.5,7) (11,7) (11,9.5) (7.5,9.5) |

---

## Connections

| name         | x | y | destination                              |
|--------------|---|---|------------------------------------------|
| to_kitchen | 11 | 4.75 | places/driftmoor/broken_lantern       |

---

## Items

| id                 | x | y | label                  |
|--------------------|---|---|------------------------|
| spare_blanket      | 5.53 | 2.248 | Spare blanket          |
| crate_saltfish     | 2.792   | 4.038 | Crate of saltfish      |
| candle_stub_bundle | 8.101 | 1.982 | Bundle of candle stubs |
