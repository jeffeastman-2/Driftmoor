# GEOMETRY.md — The Stables

## Scene

- **name:** The Stables
- **place_path:** places/driftmoor/stables
- **z_level:** 16.25
- **width:** 44
- **height:** 56.5
- **origin:** 602.5, 75.5, 0

---

## Landmarks

| name             | x  | y  |
|------------------|----|----|
| stable_entrance  | 22  | 0  |
| saddle_racks     | 3.121 | 4.4 |
| stall_row_center | 23 | 27.5 |
| feed_bins        | 32.431 | 5.629 |
| forge_door       | 22 | 56.5 |
| grooming_station | 14.993 | 2.318 |
| hay_bales        | 39.918 | 3.853 |
| water_trough     | 31.522 | 2.341 |
| tack_cabinet     | 8.689 | 5.409 |
| empty_stall      | 36.386 | 47.529 |
| clawed_tracks    | 23.334 | 4.768 |

---

## Zones

| name | render_z | auto_wall | vertices |
|----------|----------|---------|----------------------------------|
| STABLES | 5.0 |  | (0,0) (44,0) (44,56.5) (0,56.5) |
| EXTERIOR | 0.0 |  | (-4,-4) (48,-4) (48,60.5) (-4,60.5) |
---

## Impassable

| description      | vertices                         |
|------------------|----------------------------------|
| West stall wall  | (0,53.5) (19,53.5) (19,56.5) (0,56.5) |
| East stall wall  | (25,53.5) (44,53.5) (44,56.5) (25,56.5) |

---

## Connections

| name             | x | y | destination      |
|------------------|---|---|------------------|
| stable_to_street | 22 | 0 | places/driftmoor |
| stable_to_forge  | 22 | 56.5 | places/driftmoor/forge |

---

## Items

| id | x | y | label |
|---|---:|---:|---|
| clawed_tracks | 23.334 | 4.768 | Fading clawed tracks |
